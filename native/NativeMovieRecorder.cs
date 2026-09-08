using System;
using System.Diagnostics;
using System.IO;
using System.IO.Pipes;
using System.Text;
using System.Threading;

// Records ONLY the renderer's real RGBA Frame packets, never any desktop pixels.
// .NET Framework 4.8 / C# 5; no NuGet dependencies and no UI-thread encoder work.
//
// Usage:
//   recorder.Start(path, ffmpegExe, firstFrame.CanvasW, firstFrame.CanvasH);
//   recorder.Submit(frame); // frame.RGBA must remain immutable after submission.
//   recorder.Stop();        // requests EOF/finalization, returns immediately.
//   if (recorder.IsCompleted) { inspect recorder.LastError / OutputPath; }
// WaitForCompletion is for tests/shutdown background work, not an interactive UI callback.
internal sealed class NativeMovieRecorder : IDisposable {
    private const int FramesPerSecond = 30;
    private const int OutputWidth = 1280;
    private const int MaxPixels = 16777216;
    private readonly object gate = new object();
    private Session session;

    public void Start(string file, string ffmpegPath, int canvasWidth, int canvasHeight) {
        if (String.IsNullOrWhiteSpace(file)) throw new ArgumentException("An output MP4 path is required.", "file");
        if (String.IsNullOrWhiteSpace(ffmpegPath)) throw new ArgumentException("An ffmpeg executable path is required.", "ffmpegPath");
        if (canvasWidth < 1 || canvasHeight < 1 || canvasWidth > 8192 || canvasHeight > 8192 ||
            (long)canvasWidth * canvasHeight > MaxPixels || (double)canvasHeight * OutputWidth / canvasWidth > 8192)
            throw new ArgumentOutOfRangeException("canvasWidth", "Canonical canvas exceeds supported dimensions/pixel budget.");
        string output = Path.GetFullPath(file), encoder = Path.GetFullPath(ffmpegPath);
        if (!File.Exists(encoder)) throw new FileNotFoundException("ffmpeg was not found.", encoder);
        if (output.IndexOf('\r') >= 0 || output.IndexOf('\n') >= 0 || output.IndexOf('"') >= 0)
            throw new ArgumentException("Invalid movie output path.", "file");
        lock (gate) {
            if (session != null && !session.Completed.WaitOne(0))
                throw new InvalidOperationException("A recording is running or still finalizing.");
            session = new Session(output, encoder, canvasWidth, canvasHeight);
            session.Worker = new Thread(session.Run);
            session.Worker.Name = "HELIOS movie encoder";
            session.Worker.IsBackground = true;
            session.Worker.Start();
        }
    }

    public void Submit(Frame frame) {
        Session s;
        lock (gate) { s = session; }
        if (s == null || Interlocked.Read(ref s.StopTimestamp) != 0 || s.Completed.WaitOne(0)) return;
        if (frame == null || frame.RGBA == null || frame.W < 1 || frame.H < 1 ||
            (long)frame.W * frame.H > MaxPixels || (long)frame.W * frame.H * 4 > frame.RGBA.LongLength ||
            frame.CanvasW < 1 || frame.CanvasH < 1) {
            Interlocked.Increment(ref s.RejectedFrames);
            return;
        }
        // Retain this immutable frame until encoding finishes using it. The native
        // display may reuse its pooled backing only after all owners release it.
        Packet p = new Packet(frame);
        Packet replaced=Interlocked.Exchange(ref s.Latest, p);if(replaced!=null)replaced.Release();
        Interlocked.Increment(ref s.SubmittedFrames);
    }

    public void Stop() {
        Session s;
        lock (gate) { s = session; }
        if (s != null) s.RequestStop();
    }

    public bool IsRecording {
        get { Session s = Current; return s != null && !s.Completed.WaitOne(0) && Interlocked.Read(ref s.StopTimestamp) == 0; }
    }
    public bool IsFinalizing {
        get { Session s = Current; return s != null && !s.Completed.WaitOne(0) && Interlocked.Read(ref s.StopTimestamp) != 0; }
    }
    public bool IsCompleted { get { Session s = Current; return s == null || s.Completed.WaitOne(0); } }
    public string LastError { get { Session s = Current; return s == null ? null : s.Error; } }
    public string OutputPath { get { Session s = Current; return s == null ? null : s.Output; } }
    public long FramesWritten { get { Session s = Current; return s == null ? 0 : Interlocked.Read(ref s.WrittenFrames); } }
    public long FramesSubmitted { get { Session s = Current; return s == null ? 0 : Interlocked.Read(ref s.SubmittedFrames); } }
    public long FramesRejected { get { Session s = Current; return s == null ? 0 : Interlocked.Read(ref s.RejectedFrames); } }
    public double DurationSeconds { get { return FramesWritten / (double)FramesPerSecond; } }
    private Session Current { get { lock (gate) { return session; } } }

    public bool WaitForCompletion(int millisecondsTimeout) {
        if (millisecondsTimeout < -1) throw new ArgumentOutOfRangeException("millisecondsTimeout");
        Session s = Current;
        return s == null || s.Completed.WaitOne(millisecondsTimeout);
    }
    public void Dispose() { Stop(); }

    private sealed class Packet {
        internal readonly int W, H, X, Y, CanvasW, CanvasH, Fade;
        internal readonly byte[] Rgba;
        private readonly Frame owner;
        internal Packet(Frame f) {
            owner=f;f.Retain();
            W = f.W; H = f.H; X = f.X; Y = f.Y; CanvasW = f.CanvasW; CanvasH = f.CanvasH;
            Fade = Math.Max(0, Math.Min(255, f.Fade)); Rgba = f.RGBA;
        }
        internal void Release(){owner.Release();}
    }

    private sealed class Session {
        internal readonly string Output, Encoder;
        internal readonly int Width, Height;
        internal readonly long Started = Stopwatch.GetTimestamp();
        internal readonly ManualResetEvent StopRequested = new ManualResetEvent(false);
        internal readonly ManualResetEvent Completed = new ManualResetEvent(false);
        internal Thread Worker;
        internal Packet Latest;
        internal long StopTimestamp, WrittenFrames, SubmittedFrames, RejectedFrames;
        internal volatile string Error;
        private readonly object processGate = new object(), stderrGate = new object();
        private readonly StringBuilder stderr = new StringBuilder();
        private readonly ManualResetEvent encoderExited = new ManualResetEvent(false);
        private Process process;
        private Timer stopWatchdog;

        internal Session(string output, string encoder, int width, int height) {
            Output = output; Encoder = encoder; Width = width; Height = height;
        }

        internal void RequestStop() {
            if (Completed.WaitOne(0)) return;
            if (Interlocked.CompareExchange(ref StopTimestamp, Stopwatch.GetTimestamp(), 0) == 0) {
                StopRequested.Set();
                // Stop remains nonblocking even if an encoder/pipe fails. This timer kills only
                // our own child, releasing a stalled pipe write on the independent worker.
                Timer watchdog = new Timer(delegate { AbortEncoder(); }, null, 20000, Timeout.Infinite);
                Interlocked.Exchange(ref stopWatchdog, watchdog);
                if (Completed.WaitOne(0)) watchdog.Dispose();
            }
        }

        private void AbortEncoder() {
            lock (processGate) {
                if (Completed.WaitOne(0)) return;
                Error = "Movie encoder did not finalize within 20 seconds after Stop().";
                try { if (process != null && !process.HasExited) process.Kill(); } catch { }
            }
        }

        internal void Run() {
            string temporary = null;
            NamedPipeServerStream pixelPipe = null;
            bool committed = false;
            try {
                string folder = Path.GetDirectoryName(Output);
                Directory.CreateDirectory(folder);
                temporary = Path.Combine(folder, "." + Path.GetFileNameWithoutExtension(Output) + ".recording-" + Guid.NewGuid().ToString("N") + ".mp4");
                int outputHeight = Math.Max(2, (int)Math.Round((double)Height * OutputWidth / Width / 2.0) * 2);
                string pipeName = "HELIOS_Movie_" + Guid.NewGuid().ToString("N");
                pixelPipe = new NamedPipeServerStream(pipeName, PipeDirection.Out, 1, PipeTransmissionMode.Byte,
                    PipeOptions.Asynchronous, 65536, 65536);
                ProcessStartInfo info = new ProcessStartInfo();
                info.FileName = Encoder;
                info.Arguments = "-hide_banner -loglevel warning -nostdin -y -f rawvideo -pixel_format bgra -video_size " + Width + "x" + Height +
                    " -framerate 30 -i " + Quote(@"\\.\pipe\" + pipeName) + " -an -vf scale=" + OutputWidth + ":" + outputHeight + ":flags=lanczos:out_color_matrix=bt709:in_range=full:out_range=tv" +
                    " -c:v libx264 -preset veryfast -crf 18 -pix_fmt yuv420p -r 30 -color_primaries bt709 -color_trc bt709 -colorspace bt709 -color_range tv -movflags +faststart -f mp4 " + Quote(temporary);
                info.UseShellExecute = false;
                info.CreateNoWindow = true;
                info.WindowStyle = ProcessWindowStyle.Hidden;
                // A binary named pipe avoids .NET Framework's redirected stdin StreamWriter,
                // which can prepend a UTF-8 BOM depending on the host console encoding.
                // It also avoids changing the parent process's global console encoding.
                info.RedirectStandardError = true;
                Process child = new Process(); child.StartInfo = info; child.EnableRaisingEvents = true;
                child.Exited += delegate { encoderExited.Set(); };
                child.ErrorDataReceived += delegate(object sender, DataReceivedEventArgs e) {
                    if (e.Data == null) return;
                    lock (stderrGate) {
                        if (stderr.Length > 12000) stderr.Remove(0, stderr.Length - 12000);
                        stderr.AppendLine(e.Data);
                    }
                };
                lock (processGate) { process = child; child.Start(); child.BeginErrorReadLine(); }
                IAsyncResult connection = pixelPipe.BeginWaitForConnection(null, null);
                using (WaitHandle connectionWait = connection.AsyncWaitHandle) {
                    int ready = WaitHandle.WaitAny(new WaitHandle[] { connectionWait, encoderExited }, 10000);
                    if (ready == 1) throw new IOException("ffmpeg exited before connecting to the binary pixel pipe.");
                    if (ready == WaitHandle.WaitTimeout) throw new IOException("ffmpeg did not connect to the binary pixel pipe.");
                    pixelPipe.EndWaitForConnection(connection);
                }
                byte[] bgra = new byte[checked(Width * Height * 4)]; FillBackground(bgra);
                Stream pipe = pixelPipe;
                for (;;) {
                    long stop = Interlocked.Read(ref StopTimestamp);
                    long now = stop == 0 ? Stopwatch.GetTimestamp() : stop;
                    double elapsed = Math.Max(0, (now - Started) / (double)Stopwatch.Frequency);
                    long due = stop == 0 ? (long)Math.Floor(elapsed * FramesPerSecond) + 1 : Math.Max(1, (long)Math.Ceiling(elapsed * FramesPerSecond));
                    long written = Interlocked.Read(ref WrittenFrames);
                    if (written < due) {
                        Packet latest = Interlocked.Exchange(ref Latest, null);
                        if (latest != null) {try{Compose(latest, bgra, Width, Height);}finally{latest.Release();}}
                        // When encoder scheduling misses a tick, duplicate the most recent real
                        // rendered frame rather than shortening video time or inventing motion.
                        pipe.Write(bgra, 0, bgra.Length);
                        Interlocked.Increment(ref WrittenFrames);
                        continue;
                    }
                    if (stop != 0) break;
                    double nextSeconds = written / (double)FramesPerSecond;
                    int wait = Math.Max(1, Math.Min(34, (int)Math.Ceiling((nextSeconds - elapsed) * 1000)));
                    StopRequested.WaitOne(wait);
                }
                pixelPipe.WaitForPipeDrain();
                pixelPipe.Dispose(); pixelPipe = null; // EOF flushes MP4 trailer; UI never waits.
                if (!child.WaitForExit(15000)) { AbortEncoder(); throw new IOException("ffmpeg finalization timed out."); }
                child.WaitForExit(); // Complete asynchronous stderr delivery after the bounded exit wait.
                if (child.ExitCode != 0) throw new IOException("ffmpeg exited with code " + child.ExitCode + ". " + StderrText());
                if (Error != null) throw new IOException(Error);
                if (!File.Exists(temporary) || new FileInfo(temporary).Length == 0) throw new IOException("ffmpeg produced no movie.");
                // Keep an existing movie intact until a new MP4 has fully finalized.
                if (File.Exists(Output)) File.Replace(temporary, Output, null);
                else File.Move(temporary, Output);
                committed = true;
            } catch (Exception ex) {
                if (Error == null) Error = ex.Message;
                string details = StderrText();
                if (details.Length != 0 && Error.IndexOf(details, StringComparison.Ordinal) < 0) Error += Environment.NewLine + details;
            } finally {
                if (pixelPipe != null) { try { pixelPipe.Dispose(); } catch { } }
                lock (processGate) {
                    Timer watchdog = Interlocked.Exchange(ref stopWatchdog, null);
                    if (watchdog != null) watchdog.Dispose();
                    try { if (process != null && !process.HasExited) process.Kill(); } catch { }
                    if (process != null) { process.Dispose(); process = null; }
                }
                if (!committed && temporary != null) { try { File.Delete(temporary); } catch { } }
                Packet remaining=Interlocked.Exchange(ref Latest, null);if(remaining!=null)remaining.Release();
                Completed.Set();
            }
        }

        private string StderrText() { lock (stderrGate) { return stderr.ToString().Trim(); } }
        private static string Quote(string path) { return "\"" + path + "\""; } // no shell involved

        private static void FillBackground(byte[] dst) {
            // Opaque, neutral dark gray #1D2025. No desktop screenshot/surface is consulted.
            for (int i = 0; i < dst.Length; i += 4) { dst[i] = 37; dst[i + 1] = 32; dst[i + 2] = 29; dst[i + 3] = 255; }
        }

        private static void Compose(Packet f, byte[] dst, int width, int height) {
            FillBackground(dst);
            if (f.Fade == 0) return;
            if (f.CanvasW == width && f.CanvasH == height) {
                // Crop origin is relative to full canonical canvas, NOT recentered per packet.
                int x0 = (int)Math.Max(0L, f.X), y0 = (int)Math.Max(0L, f.Y);
                int x1 = (int)Math.Min((long)width, (long)f.X + f.W), y1 = (int)Math.Min((long)height, (long)f.Y + f.H);
                if (x1 <= x0 || y1 <= y0) return;
                for (int y = y0; y < y1; ++y) {
                    int si = ((y - f.Y) * f.W + x0 - f.X) * 4, di = (y * width + x0) * 4;
                    for (int x = x0; x < x1; ++x, si += 4, di += 4) {
                        int a = (f.Rgba[si + 3] * f.Fade + 127) / 255, inverse = 255 - a;
                        dst[di] = (byte)((f.Rgba[si + 2] * a + 37 * inverse + 127) / 255);
                        dst[di + 1] = (byte)((f.Rgba[si + 1] * a + 32 * inverse + 127) / 255);
                        dst[di + 2] = (byte)((f.Rgba[si] * a + 29 * inverse + 127) / 255);
                    }
                }
                return;
            }
            // Resolution/aspect changes are fitted by the DECLARED whole source canvas, never
            // by the cropped object bounds. Bilinear premultiplied-alpha sampling avoids halos.
            double scale = Math.Min(width / (double)f.CanvasW, height / (double)f.CanvasH);
            double ox = (width - f.CanvasW * scale) * .5, oy = (height - f.CanvasH * scale) * .5;
            int left = Clamp((int)Math.Floor(ox + f.X * scale), 0, width), right = Clamp((int)Math.Ceiling(ox + ((long)f.X + f.W) * scale), 0, width);
            int top = Clamp((int)Math.Floor(oy + f.Y * scale), 0, height), bottom = Clamp((int)Math.Ceiling(oy + ((long)f.Y + f.H) * scale), 0, height);
            double fade = f.Fade / 255.0;
            for (int y = top; y < bottom; ++y) {
                double sy = (y + .5 - oy) / scale - f.Y - .5;
                int ya = (int)Math.Floor(sy); double fy = sy - ya;
                for (int x = left; x < right; ++x) {
                    double sx = (x + .5 - ox) / scale - f.X - .5;
                    int xa = (int)Math.Floor(sx); double fx = sx - xa;
                    double a = 0, r = 0, g = 0, b = 0;
                    for (int yy = 0; yy < 2; ++yy) for (int xx = 0; xx < 2; ++xx) {
                        int px = xa + xx, py = ya + yy;
                        if (px < 0 || py < 0 || px >= f.W || py >= f.H) continue;
                        double weight = (xx == 0 ? 1 - fx : fx) * (yy == 0 ? 1 - fy : fy);
                        int si = (py * f.W + px) * 4; double alpha = f.Rgba[si + 3] / 255.0 * weight * fade;
                        a += alpha; r += f.Rgba[si] * alpha; g += f.Rgba[si + 1] * alpha; b += f.Rgba[si + 2] * alpha;
                    }
                    int di = (y * width + x) * 4;
                    dst[di] = ToByte(b + 37 * (1 - a)); dst[di + 1] = ToByte(g + 32 * (1 - a)); dst[di + 2] = ToByte(r + 29 * (1 - a));
                }
            }
        }
        private static int Clamp(int value, int lo, int hi) { return Math.Max(lo, Math.Min(hi, value)); }
        private static byte ToByte(double value) { return (byte)Math.Max(0, Math.Min(255, (int)Math.Round(value))); }
    }
}
