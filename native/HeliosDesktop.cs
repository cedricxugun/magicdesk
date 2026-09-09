using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Drawing;
using System.Drawing.Imaging;
using System.IO;
using System.IO.Compression;
using System.Net;
using System.Net.Sockets;
using System.Reflection;
using System.Runtime.InteropServices;
using System.Text;
using System.Threading;
using System.Windows.Forms;

[assembly: AssemblyTitle("MagicDesk · 机械藏品")]
[assembly: AssemblyProduct("MagicDesk")]
[assembly: AssemblyDescription("Original interactive 3D mechanical desktop sculpture")]
[assembly: AssemblyVersion("0.4.0.0")]
[assembly: AssemblyFileVersion("0.4.0.0")]

internal static class Native {
    [StructLayout(LayoutKind.Sequential)] public struct POINT { public int X,Y; public POINT(int x,int y){X=x;Y=y;} }
    [StructLayout(LayoutKind.Sequential)] public struct SIZE { public int X,Y; public SIZE(int x,int y){X=x;Y=y;} }
    [StructLayout(LayoutKind.Sequential,Pack=1)] public struct BLEND { public byte Op,Flags,Alpha,Format; }
    [StructLayout(LayoutKind.Sequential)] public struct INFOHEADER { public uint Size; public int Width,Height; public ushort Planes,BitCount; public uint Compression,SizeImage; public int XPels,YPels; public uint Used,Important; }
    [StructLayout(LayoutKind.Sequential)] public struct INFO { public INFOHEADER Header; public uint Colors; }
    [StructLayout(LayoutKind.Sequential)] public struct RECT { public int Left,Top,Right,Bottom; }
    [DllImport("user32.dll",SetLastError=true)] public static extern bool UpdateLayeredWindow(IntPtr h,IntPtr dst,ref POINT pos,ref SIZE size,IntPtr src,ref POINT srcpos,int key,ref BLEND blend,uint flags);
    [DllImport("user32.dll")] public static extern IntPtr GetDC(IntPtr h);
    [DllImport("user32.dll")] public static extern int ReleaseDC(IntPtr h,IntPtr dc);
    [DllImport("gdi32.dll")] public static extern IntPtr CreateCompatibleDC(IntPtr h);
    [DllImport("gdi32.dll")] public static extern bool DeleteDC(IntPtr h);
    [DllImport("gdi32.dll")] public static extern IntPtr CreateDIBSection(IntPtr dc,ref INFO info,uint usage,out IntPtr bits,IntPtr section,uint offset);
    [DllImport("gdi32.dll")] public static extern IntPtr SelectObject(IntPtr dc,IntPtr o);
    [DllImport("gdi32.dll")] public static extern bool DeleteObject(IntPtr h);
    [DllImport("user32.dll")] public static extern IntPtr WindowFromPoint(POINT point);
    [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
    [DllImport("user32.dll")] public static extern bool SetProcessDpiAwarenessContext(IntPtr context);
    [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h,int state);
    [DllImport("dwmapi.dll")] public static extern int DwmSetWindowAttribute(IntPtr h,int attribute,ref int value,int size);
    [DllImport("user32.dll")] public static extern bool PostMessage(IntPtr h,int msg,IntPtr wp,IntPtr lp);
    [DllImport("winmm.dll")] public static extern uint timeBeginPeriod(uint milliseconds);
    [DllImport("winmm.dll")] public static extern uint timeEndPeriod(uint milliseconds);
    [DllImport("user32.dll",EntryPoint="GetWindowLongPtrW")] public static extern IntPtr GetWindowLongPtr(IntPtr h,int index);
    [DllImport("user32.dll",EntryPoint="SetWindowLongPtrW")] public static extern IntPtr SetWindowLongPtr(IntPtr h,int index,IntPtr value);
    [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr h);
    [DllImport("user32.dll")] public static extern short GetAsyncKeyState(int key);
    [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h,out RECT rect);
    [DllImport("user32.dll")] public static extern bool SetWindowPos(IntPtr h,IntPtr after,int x,int y,int w,int height,uint flags);
}

internal sealed class Frame {
    public int W,H,X,Y,CanvasW,CanvasH,BaseY,Sequence,Fade=255;
    public int[] Buttons=new int[14];
    public byte[] RGBA;
    public double CropMilliseconds;
    public Rectangle[] InteractiveRegions=new Rectangle[0];
    public bool Pooled;
    private int references=1;
    public void Retain(){Interlocked.Increment(ref references);}
    public void Release(){if(Interlocked.Decrement(ref references)==0&&Pooled)FrameBuffers.Return(RGBA);}
}

internal static class FrameBuffers {
    private static readonly object gate=new object();
    private static readonly Dictionary<int,Stack<byte[]>> free=new Dictionary<int,Stack<byte[]>>();
    private static long retained;
    public static byte[] Rent(int length){
        int capacity=checked(((length+1048575)/1048576)*1048576);
        lock(gate){Stack<byte[]> bucket;if(free.TryGetValue(capacity,out bucket)&&bucket.Count>0){retained-=capacity;return bucket.Pop();}}
        return new byte[capacity];
    }
    public static void Return(byte[] bytes){
        lock(gate){if(retained+bytes.Length>64L*1024*1024)return;Stack<byte[]> bucket;if(!free.TryGetValue(bytes.Length,out bucket)){bucket=new Stack<byte[]>();free.Add(bytes.Length,bucket);}if(bucket.Count>=6)return;bucket.Push(bytes);retained+=bytes.Length;}
    }
}

internal sealed class HeliosForm : Form {
    private readonly object frameLock=new object(), sendLock=new object();
    private Frame pending,current;
    private TcpListener listener;
    private TcpClient client;
    private NetworkStream stream;
    private Process renderer;
    private IntPtr memoryDC,bitmap,bits,oldBitmap;
    private int dibWidth,dibHeight;
    private volatile bool closing;
    private bool firstFrame=true,baseDrag,mouseDown;
    private bool forceClose,shutdownRequested,verificationWritten;
    private double shutdownStarted;
    private Point anchor,mouseOrigin,anchorOrigin;
    private System.Windows.Forms.Timer timer;
    private NotifyIcon tray;
    private ContextMenuStrip context;
    private bool muted;
    private readonly string rootDir,diagnosticDir,controlFile;
    private string lastControl="";
    private bool testRun;
    private bool performanceOnly;
    private bool steamTest;
    private bool assemblyTest;
    private double testStart;
    private readonly Stopwatch lifetime=Stopwatch.StartNew();
    private int drawn,nonblank,updateErrors,blankFrames;
    private long lastSequence=-1;
    private long receivedPackets;
    private int presentQueued;
    private double firstFrameTime,lastFrameTime,maxPresentationGap;
    private readonly List<double> frameGaps=new List<double>();
    private readonly List<string> frameTrace=new List<string>();
    private int bitmapAllocations;
    private readonly List<string> events=new List<string>();
    private readonly Dictionary<string,bool> testEvents=new Dictionary<string,bool>();
    private Frame testBefore;
    private Point[] testButtonDesktop;
    private Point? syntheticClickPoint;
    private int hitTransparentFailures,hitOpaqueFailures;
    private IntPtr expectedHandle;
    private StreamWriter log;
    private string[] args;
    private NativeMovieRecorder movie;
    private bool movieStarted,movieFinishing;
    private string moviePath,ffmpegPath;
    private IntPtr workerWindow;
    private readonly EventWaitHandle activateEvent;
    private const int WM_NCHITTEST=0x84,WM_ERASEBKGND=0x14,WM_PAINT=0xF,WM_MOUSEACTIVATE=0x21;

    public HeliosForm(string[] arguments,EventWaitHandle activation){
        activateEvent=activation;
        args=arguments; rootDir=Path.GetDirectoryName(Assembly.GetExecutingAssembly().Location);
        steamTest=Has("--steam-test");
        assemblyTest=Has("--assembly-test");
        performanceOnly=Has("--performance-only")||steamTest;
        testRun=Has("--self-test")||performanceOnly||assemblyTest;
        diagnosticDir=Value("--diagnostics=")??Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),"HeliosIncubator","logs");
        controlFile=Value("--control=")??"";
        moviePath=Value("--record=");ffmpegPath=Value("--ffmpeg=");
        if(moviePath!=null&&ffmpegPath!=null)movie=new NativeMovieRecorder();
        Directory.CreateDirectory(diagnosticDir);
        log=new StreamWriter(Path.Combine(diagnosticDir,"native.log"),false,Encoding.UTF8);log.AutoFlush=true;
        Text="MagicDesk · 机械藏品";FormBorderStyle=FormBorderStyle.None;ShowInTaskbar=true;TopMost=testRun;
        StartPosition=FormStartPosition.Manual;Size=new Size(1,1);Location=new Point(-32000,-32000);
        AutoScaleMode=AutoScaleMode.None;KeyPreview=true;
        SetStyle(ControlStyles.AllPaintingInWmPaint|ControlStyles.UserPaint,true);
        try {Icon=Icon.ExtractAssociatedIcon(Assembly.GetExecutingAssembly().Location);} catch{}
        context=new ContextMenuStrip();
        string[] names={"1  唤醒 / 休眠","2  绽放 / 闭合","3  核心过载","4  分解组件","5  组装 / 收拢","6  旋转 / 暂停","7  收拢并退出"};
        if(Has("--helios-only"))for(int i=0;i<7;i++){int index=i;context.Items.Add(names[i],null,delegate{SendAction(index);});}
        else{
            context.Items.Add("唤醒 / 休眠",null,delegate{SendAction(0);});
            context.Items.Add("展开 / 收起装置档案",null,delegate{Send("{\"type\":\"selector\"}");});
            context.Items.Add("展示旋转 / 暂停",null,delegate{Send("{\"type\":\"rotation\"}");});
        }
        context.Items.Add(new ToolStripSeparator());
        ToolStripMenuItem mute=new ToolStripMenuItem("静音");mute.CheckOnClick=true;mute.CheckedChanged+=delegate{muted=mute.Checked;Send("{\"type\":\"mute\",\"value\":"+(muted?"true":"false")+"}");};context.Items.Add(mute);
        ToolStripMenuItem top=new ToolStripMenuItem("始终置顶");top.CheckOnClick=true;top.CheckedChanged+=delegate{TopMost=top.Checked;};context.Items.Add(top);
        context.Items.Add("重置位置与朝向",null,delegate{ResetAnchor();Send("{\"type\":\"reset\"}");});
        context.Items.Add("退出",null,delegate{Close();});
        tray=new NotifyIcon();tray.Icon=Icon??SystemIcons.Application;tray.Text="MagicDesk · 机械藏品";tray.ContextMenuStrip=context;tray.Visible=true;
        tray.DoubleClick+=delegate{ResetAnchor();};
        timer=new System.Windows.Forms.Timer();timer.Interval=15;timer.Tick+=OnTick;
        Load+=delegate{
            expectedHandle=Handle;
            int disable=1;Native.DwmSetWindowAttribute(Handle,2,ref disable,4);
            InitializeTransparentPixel();
            StartRenderer();timer.Start();
        };
    }
    protected override CreateParams CreateParams {get{var p=base.CreateParams;p.ExStyle|=0x00080000;p.Style&=~0x00C00000;return p;}}
    protected override bool ShowWithoutActivation {get{return true;}}
    private bool Has(string arg){return Array.IndexOf(args,arg)>=0;}
    private string Value(string prefix){foreach(var arg in args)if(arg.StartsWith(prefix,StringComparison.Ordinal))return arg.Substring(prefix.Length);return null;}
    private void Log(string value){try{lock(log){log.WriteLine(DateTime.Now.ToString("HH:mm:ss.fff")+" "+value);}}catch{}}

    private string ExtractRenderer(){
        string explicitEngine=Value("--engine=");if(explicitEngine!=null)return explicitEngine;
        var resource=Assembly.GetExecutingAssembly().GetManifestResourceStream("Helios.Renderer");
        if(resource==null)throw new FileNotFoundException("未找到内置渲染程序。");
        string version=Assembly.GetExecutingAssembly().ManifestModule.ModuleVersionId.ToString("N");
        string directory=Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),"HeliosIncubator","runtime",version);
        Directory.CreateDirectory(directory);string target=Path.Combine(directory,"HeliosRenderer.exe");
        if(!File.Exists(target)||new FileInfo(target).Length!=resource.Length){
            string temp=target+".tmp";using(var output=new FileStream(temp,FileMode.Create,FileAccess.Write,FileShare.None)){resource.CopyTo(output);}
            if(File.Exists(target))File.Delete(target);File.Move(temp,target);
        }
        resource.Dispose();return target;
    }
    private void StartRenderer(){
        try{
            listener=new TcpListener(IPAddress.Loopback,0);listener.Start(1);
            int port=((IPEndPoint)listener.LocalEndpoint).Port;
            Thread receive=new Thread(ReceiveLoop);receive.IsBackground=true;receive.Start();
            string exe=ExtractRenderer();string project=Value("--project=");
            string arguments="--position -32000,-32000 --resolution 32x32 --disable-vsync";
            if(project!=null)arguments+=" --path \""+project+"\"";
            arguments+=" -- --native-port="+port;
            if(Has("--helios-only"))arguments+=" --helios-only";
            if(Has("--collection-qa"))arguments+=" --collection-qa=\""+diagnosticDir+"\"";
            if(Has("--profile"))arguments+=" --profile=\""+diagnosticDir+"\"";
            if(Has("--legacy-alpha-crop"))arguments+=" --legacy-alpha-crop";
            var start=new ProcessStartInfo(exe,arguments);start.WorkingDirectory=Path.GetDirectoryName(exe);start.UseShellExecute=false;start.CreateNoWindow=true;start.WindowStyle=ProcessWindowStyle.Hidden;start.RedirectStandardError=true;start.RedirectStandardOutput=true;
            renderer=new Process();renderer.StartInfo=start;renderer.EnableRaisingEvents=true;
            renderer.OutputDataReceived+=delegate(object s,DataReceivedEventArgs e){if(e.Data!=null){
                Log("renderer: "+e.Data);
                if(e.Data.StartsWith("HELIOS_WORKER_HWND ",StringComparison.Ordinal)){
                    long value;if(Int64.TryParse(e.Data.Substring(19).Trim(),out value)&&value!=0){
                        BeginInvoke((Action)delegate{workerWindow=(IntPtr)value;HideWorkerWindow();});
                    }
                }
            }};
            renderer.ErrorDataReceived+=delegate(object s,DataReceivedEventArgs e){if(e.Data!=null)Log("renderer error: "+e.Data);};
            renderer.Exited+=delegate{if(!closing)BeginInvoke((Action)delegate{Log("renderer exit code="+renderer.ExitCode);forceClose=true;Close();});};
            renderer.Start();renderer.BeginOutputReadLine();renderer.BeginErrorReadLine();
            Log("native compositor started; renderer="+renderer.Id+" port="+port);
        }catch(Exception e){Log(e.ToString());MessageBox.Show("孵日器启动失败："+e.Message,"HELIOS");Close();}
    }
    private static void ReadAll(Stream input,byte[] data){int offset=0;while(offset<data.Length){int n=input.Read(data,offset,data.Length-offset);if(n<=0)throw new EndOfStreamException();offset+=n;}}
    private void ReceiveLoop(){
        try{
            client=listener.AcceptTcpClient();client.NoDelay=true;stream=client.GetStream();byte[] header=new byte[96];byte[] rawFrame=null;
            while(!closing){
                ReadAll(stream,header);int[] h=new int[24];Buffer.BlockCopy(header,0,h,0,96);
                if((h[0]!=0x484C5333&&h[0]!=0x484C5334&&h[0]!=0x484C5335)||h[1]<1||h[2]<1||h[1]>4096||h[2]>4096||h[5]<h[1]||h[6]<h[2]||h[5]>4096||h[6]>4096)throw new InvalidDataException("Invalid frame header");
                Rectangle[] regions=new Rectangle[0];
                if(h[0]==0x484C5335){
                    byte[] countBytes=new byte[4];ReadAll(stream,countBytes);int count=BitConverter.ToInt32(countBytes,0);
                    if(count<0||count>32)throw new InvalidDataException("Invalid interaction region count");
                    byte[] regionBytes=new byte[count*16];ReadAll(stream,regionBytes);regions=new Rectangle[count];
                    for(int i=0;i<count;i++)regions[i]=new Rectangle(BitConverter.ToInt32(regionBytes,i*16),BitConverter.ToInt32(regionBytes,i*16+4),BitConverter.ToInt32(regionBytes,i*16+8),BitConverter.ToInt32(regionBytes,i*16+12));
                }
                Frame f;
                if(h[0]==0x484C5334||h[0]==0x484C5335){
                    int length=checked(h[1]*h[2]*4);
                    if(rawFrame==null||rawFrame.Length!=length)rawFrame=new byte[length];
                    ReadAll(stream,rawFrame);f=CropRawFrame(h,rawFrame);
                    if(f==null)continue;
                }else{
                    f=new Frame{W=h[1],H=h[2],X=h[3],Y=h[4],CanvasW=h[5],CanvasH=h[6],BaseY=h[7],Sequence=h[8],Fade=h[9],RGBA=new byte[checked(h[1]*h[2]*4)]};Array.Copy(h,10,f.Buttons,0,14);ReadAll(stream,f.RGBA);
                }
                f.InteractiveRegions=regions;
                lock(frameLock){if(pending!=null)pending.Release();pending=f;}
                Interlocked.Increment(ref receivedPackets);
                // Present when a real rendered frame arrives. Polling it on a 15 ms
                // WinForms timer otherwise introduces 15/30/45 ms cadence jitter.
                if(Interlocked.CompareExchange(ref presentQueued,1,0)==0){
                    BeginInvoke((Action)delegate{Interlocked.Exchange(ref presentQueued,0);if(!closing)OnTick(null,EventArgs.Empty);});
                }
            }
        }catch(Exception e){if(!closing)Log("frame transport: "+e.Message);}
    }
    private static unsafe Frame CropRawFrame(int[] h,byte[] rgba){
        long started=Stopwatch.GetTimestamp();int width=h[1],height=h[2];
        int left=width,right=-1,top=height,bottom=-1;
        fixed(byte* bytes=rgba){uint* pixels=(uint*)bytes;
            for(int y=0;y<height;y++){
                int rowLeft=width,rowRight=-1,offset=y*width;
                for(int x=0;x<width;x++)if((pixels[offset+x]&0xFF000000U)!=0){rowLeft=x;break;}
                if(rowLeft==width)continue;
                for(int x=width-1;x>=rowLeft;x--)if((pixels[offset+x]&0xFF000000U)!=0){rowRight=x;break;}
                if(rowLeft<left)left=rowLeft;if(rowRight>right)right=rowRight;
                if(y<top)top=y;bottom=y;
            }
        }
        if(right<left||bottom<top)return null;
        left=Math.Max(0,left-2);top=Math.Max(0,top-2);right=Math.Min(width-1,right+2);bottom=Math.Min(height-1,bottom+2);
        Frame f=new Frame{W=right-left+1,H=bottom-top+1,X=h[3]+left,Y=h[4]+top,CanvasW=h[5],CanvasH=h[6],BaseY=h[7],Sequence=h[8],Fade=h[9]};
        f.RGBA=FrameBuffers.Rent(checked(f.W*f.H*4));f.Pooled=true;Array.Copy(h,10,f.Buttons,0,14);
        for(int y=0;y<f.H;y++)Buffer.BlockCopy(rgba,((top+y)*width+left)*4,f.RGBA,y*f.W*4,f.W*4);
        f.CropMilliseconds=(Stopwatch.GetTimestamp()-started)*1000.0/Stopwatch.Frequency;
        return f;
    }
    private void EnsureDib(int width,int height){
        if(memoryDC!=IntPtr.Zero&&width<=dibWidth&&height<=dibHeight)return;
        width=Math.Max(dibWidth,((width+127)/128)*128);height=Math.Max(dibHeight,((height+127)/128)*128);
        FreeDib();IntPtr screen=Native.GetDC(IntPtr.Zero);memoryDC=Native.CreateCompatibleDC(screen);
        Native.INFO info=new Native.INFO();info.Header.Size=(uint)Marshal.SizeOf(typeof(Native.INFOHEADER));info.Header.Width=width;info.Header.Height=-height;info.Header.Planes=1;info.Header.BitCount=32;info.Header.Compression=0;
        bitmap=Native.CreateDIBSection(screen,ref info,0,out bits,IntPtr.Zero,0);Native.ReleaseDC(IntPtr.Zero,screen);
        if(bitmap==IntPtr.Zero)throw new System.ComponentModel.Win32Exception(Marshal.GetLastWin32Error());
        oldBitmap=Native.SelectObject(memoryDC,bitmap);dibWidth=width;dibHeight=height;
        bitmapAllocations++;
    }
    private void FreeDib(){if(memoryDC==IntPtr.Zero)return;Native.SelectObject(memoryDC,oldBitmap);Native.DeleteObject(bitmap);Native.DeleteDC(memoryDC);memoryDC=IntPtr.Zero;}
    private unsafe void CopyPixels(Frame f){
        byte* target=(byte*)bits.ToPointer();fixed(byte* source=f.RGBA){
            for(int y=0;y<f.H;y++)for(int x=0;x<f.W;x++){
                int i=(y*f.W+x)*4,j=(y*dibWidth+x)*4;int a=source[i+3];
                if(a==0){*(uint*)(target+j)=0;continue;}
                if(a==255&&f.Fade==255){uint pixel=*(uint*)(source+i);*(uint*)(target+j)=(pixel&0xFF00FF00U)|((pixel&0xFFU)<<16)|((pixel>>16)&0xFFU);continue;}
                a=(a*f.Fade+127)/255;target[j]=(byte)((source[i+2]*a+127)/255);target[j+1]=(byte)((source[i+1]*a+127)/255);target[j+2]=(byte)((source[i]*a+127)/255);target[j+3]=(byte)a;
            }
        }
    }
    private void InitializeTransparentPixel(){EnsureDib(1,1);Marshal.WriteInt32(bits,0);Present(-32000,-32000,1,1);}
    private void HideWorkerWindow(){
        if(workerWindow==IntPtr.Zero)return;
        long style=Native.GetWindowLongPtr(workerWindow,-20).ToInt64();
        style=(style&~0x00040000L)|0x00000080L; // TOOLWINDOW, never a second taskbar application.
        Native.SetWindowLongPtr(workerWindow,-20,(IntPtr)style);
        Native.SetWindowLongPtr(workerWindow,-8,Handle); // Owned by the single desktop presentation.
        Native.SetWindowPos(workerWindow,IntPtr.Zero,-32000,-32000,32,32,0x0074);
    }
    private bool WorkerConcealed(){
        if(workerWindow==IntPtr.Zero)return false;
        if(!Native.IsWindowVisible(workerWindow))return true;
        Native.RECT r;if(!Native.GetWindowRect(workerWindow,out r))return true;
        var rectangle=Rectangle.FromLTRB(r.Left,r.Top,r.Right,r.Bottom);
        foreach(var screen in Screen.AllScreens)if(screen.Bounds.IntersectsWith(rectangle))return false;
        return (Native.GetWindowLongPtr(workerWindow,-20).ToInt64()&0x80)!=0;
    }
    private void Present(int x,int y,int w,int h){
        Native.POINT pos=new Native.POINT(x,y),origin=new Native.POINT(0,0);Native.SIZE sz=new Native.SIZE(w,h);Native.BLEND blend=new Native.BLEND{Op=0,Flags=0,Alpha=255,Format=1};
        if(!Native.UpdateLayeredWindow(Handle,IntPtr.Zero,ref pos,ref sz,memoryDC,ref origin,0,ref blend,2)){updateErrors++;Log("UpdateLayeredWindow error="+Marshal.GetLastWin32Error());}
    }
    private void ResetAnchor(){
        if(current==null)return;Rectangle area=Screen.FromPoint(Cursor.Position).WorkingArea;
        anchor=new Point(area.X+area.Width/2-current.CanvasW/2,area.Y+area.Height/2-current.CanvasH/2);
        if(current!=null&&dibWidth>=current.W&&dibHeight>=current.H)Present(anchor.X+current.X,anchor.Y+current.Y,current.W,current.H);
    }
    private void OnTick(object sender,EventArgs e){
        if(activateEvent!=null&&activateEvent.WaitOne(0)){ResetAnchor();Native.ShowWindow(Handle,4);Log("existing instance activated");}
        if(workerWindow!=IntPtr.Zero&&!WorkerConcealed())HideWorkerWindow();
        Frame frame=null;lock(frameLock){frame=pending;pending=null;}
        if(frame!=null){
            if(firstFrame){current=frame;ResetAnchor();firstFrame=false;testStart=lifetime.Elapsed.TotalSeconds;Log("first frame "+frame.W+"x"+frame.H+" at "+anchor);}
            // Reserve the canonical backing once; the visible window still uses
            // only the alpha crop. Opening petals and wide VFX must not allocate GDI memory.
            EnsureDib(frame.CanvasW,frame.CanvasH);CopyPixels(frame);Frame previous=current;current=frame;if(previous!=null&&!Object.ReferenceEquals(previous,frame))previous.Release();Present(anchor.X+frame.X,anchor.Y+frame.Y,frame.W,frame.H);
            if(movie!=null){
                if(!movieStarted){movie.Start(moviePath,ffmpegPath,frame.CanvasW,frame.CanvasH);movieStarted=true;}
                movie.Submit(frame);
            }
            drawn++;lastSequence=frame.Sequence;
            double now=lifetime.Elapsed.TotalSeconds;
            if(firstFrameTime==0)firstFrameTime=now;
            if(lastFrameTime>0&&now-firstFrameTime>1){double gap=now-lastFrameTime;frameGaps.Add(gap);maxPresentationGap=Math.Max(maxPresentationGap,gap);if(testRun||Has("--frame-trace"))frameTrace.Add(String.Format(System.Globalization.CultureInfo.InvariantCulture,"{0:F4},{1:F3},{2},{3},{4},{5},{6:F3},{7}",now-firstFrameTime,gap*1000,frame.Sequence,frame.W,frame.H,bitmapAllocations,frame.CropMilliseconds,GC.CollectionCount(2)));}
            lastFrameTime=now;
            if(testRun)Measure(frame);
            if(workerWindow==IntPtr.Zero&&renderer!=null&&drawn%60==1){try{renderer.Refresh();if(renderer.MainWindowHandle!=IntPtr.Zero){workerWindow=renderer.MainWindowHandle;HideWorkerWindow();}}catch{}}
        }
        if(!String.IsNullOrEmpty(controlFile))ReadControl();
        if(movieFinishing&&movie.IsCompleted){Log("movie complete: "+movie.FramesWritten+" frames; "+(movie.LastError??"OK"));forceClose=true;Close();return;}
        if(testRun)TestTick();
        if(shutdownRequested&&lifetime.Elapsed.TotalSeconds-shutdownStarted>14){forceClose=true;Close();}
        if(firstFrame&&lifetime.Elapsed.TotalSeconds>45){Log("No rendered frame after 45s");Close();}
    }
    private void Send(string json){try{lock(sendLock){if(stream==null)return;byte[] data=Encoding.UTF8.GetBytes(json+"\n");stream.Write(data,0,data.Length);}}catch(Exception e){Log("input: "+e.Message);}}
    private void SendAction(int index){if(shutdownRequested)return;if(index==6){shutdownRequested=true;shutdownStarted=lifetime.Elapsed.TotalSeconds;}Send("{\"type\":\"action\",\"index\":"+index+"}");Log("action "+index);}
    private Point Canonical(Point p){return current==null?p:new Point(p.X+current.X,p.Y+current.Y);}
    private Point PointerCanonical(){Point screen=Cursor.Position;return new Point(screen.X-anchor.X,screen.Y-anchor.Y);}
    private void SendMouse(string type,Point p,bool upper){Send("{\"type\":\""+type+"\",\"x\":"+p.X+",\"y\":"+p.Y+",\"upper\":"+(upper?"true":"false")+"}");}
    protected override void OnMouseDown(MouseEventArgs e){
        base.OnMouseDown(e);if(e.Button==MouseButtons.Right){context.Show(Cursor.Position);return;}if(e.Button!=MouseButtons.Left||current==null)return;
        mouseDown=true;Capture=true;Point p=syntheticClickPoint??PointerCanonical();baseDrag=p.Y>=current.BaseY;
        // Every physical button is forwarded through the same raycast as normal 3D input.
        for(int i=0;i<7;i++){int dx=p.X-current.Buttons[i*2],dy=p.Y-current.Buttons[i*2+1];if(dx*dx+dy*dy<31*31){baseDrag=false;break;}}
        foreach(Rectangle region in current.InteractiveRegions)if(region.Contains(p)){baseDrag=false;break;}
        mouseOrigin=Cursor.Position;anchorOrigin=anchor;SendMouse("down",p,!baseDrag);
    }
    protected override void OnMouseMove(MouseEventArgs e){
        base.OnMouseMove(e);if(current==null)return;
        if(mouseDown&&baseDrag){Point now=Cursor.Position;anchor=new Point(anchorOrigin.X+now.X-mouseOrigin.X,anchorOrigin.Y+now.Y-mouseOrigin.Y);Present(anchor.X+current.X,anchor.Y+current.Y,current.W,current.H);}
        if(!syntheticClickPoint.HasValue)SendMouse("move",PointerCanonical(),!baseDrag);
    }
    protected override void OnMouseUp(MouseEventArgs e){base.OnMouseUp(e);if(e.Button==MouseButtons.Left){bool synthetic=syntheticClickPoint.HasValue;SendMouse("up",syntheticClickPoint??PointerCanonical(),false);syntheticClickPoint=null;mouseDown=false;baseDrag=false;Capture=false;if(synthetic)Send("{\"type\":\"leave\"}");}}
    protected override void OnMouseLeave(EventArgs e){base.OnMouseLeave(e);if(!mouseDown&&!syntheticClickPoint.HasValue)Send("{\"type\":\"leave\"}");}
    protected override void OnMouseCaptureChanged(EventArgs e){
        base.OnMouseCaptureChanged(e);
        if(!Capture&&mouseDown){SendMouse("up",syntheticClickPoint??PointerCanonical(),false);mouseDown=false;baseDrag=false;syntheticClickPoint=null;}
    }
    protected override void OnMouseWheel(MouseEventArgs e){base.OnMouseWheel(e);Point p=syntheticClickPoint??PointerCanonical();Send("{\"type\":\"wheel\",\"delta\":"+e.Delta+",\"x\":"+p.X+",\"y\":"+p.Y+",\"shift\":"+(((Native.GetAsyncKeyState(0x10)&0x8000)!=0)?"true":"false")+"}");}
    protected override void OnKeyDown(KeyEventArgs e){base.OnKeyDown(e);if(e.KeyCode>=Keys.D1&&e.KeyCode<=Keys.D7&&(Has("--helios-only")||e.KeyCode==Keys.D1||e.KeyCode==Keys.D7)){SendAction((int)e.KeyCode-(int)Keys.D1);e.Handled=true;}if(e.KeyCode==Keys.Space){Send("{\"type\":\"rotation\"}");e.Handled=true;}if(e.KeyCode==Keys.Tab){Send("{\"type\":\"selector\"}");e.Handled=true;}if(e.KeyCode==Keys.Escape)context.Show(Cursor.Position);}
    protected override void WndProc(ref Message m){
        if(m.Msg==WM_ERASEBKGND){m.Result=(IntPtr)1;return;}
        if(m.Msg==WM_NCHITTEST&&current!=null&&!Capture){
            long l=m.LParam.ToInt64();int sx=(short)(l&65535),sy=(short)((l>>16)&65535);int x=sx-(anchor.X+current.X),y=sy-(anchor.Y+current.Y);
            if(x<0||y<0||x>=current.W||y>=current.H||current.RGBA[(y*current.W+x)*4+3]*current.Fade/255==0){m.Result=(IntPtr)(-1);return;}
            m.Result=(IntPtr)1;return;
        }
        base.WndProc(ref m);
    }
    protected override void OnPaintBackground(PaintEventArgs e){}
    protected override void OnPaint(PaintEventArgs e){}

    private void SaveFrame(string name){
        if(performanceOnly)return;
        if(current==null)return;Frame f=current;f.Retain();Point snapshotAnchor=anchor;long snapshotHandle=Handle.ToInt64();
        ThreadPool.QueueUserWorkItem(delegate{try{SaveFrameData(name,f,snapshotAnchor,snapshotHandle);}catch(Exception e){Log("snapshot: "+e.Message);}finally{f.Release();}});
    }
    private void SaveFrameData(string name,Frame f,Point snapshotAnchor,long snapshotHandle){
        using(Bitmap image=new Bitmap(f.W,f.H,PixelFormat.Format32bppArgb)){
            BitmapData data=image.LockBits(new Rectangle(0,0,f.W,f.H),ImageLockMode.WriteOnly,PixelFormat.Format32bppArgb);byte[] bgra=new byte[f.W*f.H*4];
            for(int i=0;i<bgra.Length;i+=4){bgra[i]=f.RGBA[i+2];bgra[i+1]=f.RGBA[i+1];bgra[i+2]=f.RGBA[i];bgra[i+3]=f.RGBA[i+3];}
            Marshal.Copy(bgra,0,data.Scan0,bgra.Length);image.UnlockBits(data);image.Save(Path.Combine(diagnosticDir,name+".png"),ImageFormat.Png);
        }
        File.WriteAllText(Path.Combine(diagnosticDir,name+".json"),"{\"width\":"+f.W+",\"height\":"+f.H+",\"crop_x\":"+f.X+",\"crop_y\":"+f.Y+",\"desktop_x\":"+(snapshotAnchor.X+f.X)+",\"desktop_y\":"+(snapshotAnchor.Y+f.Y)+",\"anchor_x\":"+snapshotAnchor.X+",\"anchor_y\":"+snapshotAnchor.Y+",\"sequence\":"+f.Sequence+",\"window_handle\":"+snapshotHandle+",\"region_count\":"+f.InteractiveRegions.Length+",\"buttons\":["+String.Join(",",f.Buttons)+"]}");
    }
    private void ReadControl(){
        try{if(!File.Exists(controlFile))return;string text=File.ReadAllText(controlFile).Trim();if(text==lastControl)return;lastControl=text;
            string[] command=text.Split(' ');if(command[0]=="action")SendAction(Int32.Parse(command[1]));
            else if(command[0]=="capture")SaveFrame(command[1]);
            else if(Has("--collection-qa")&&command[0]=="probe")Send("{\"type\":\"probe\"}");
            else if(Has("--collection-qa")&&command[0]=="wheel")Send("{\"type\":\"wheel\",\"delta\":"+Int32.Parse(command[1])+",\"x\":0,\"y\":0}");
            else if(Has("--collection-qa")&&command[0]=="scroll"){
                Point p=new Point(Int32.Parse(command[2]),Int32.Parse(command[3]));syntheticClickPoint=p;
                OnMouseWheel(new MouseEventArgs(MouseButtons.None,0,p.X-current.X,p.Y-current.Y,Int32.Parse(command[1])));syntheticClickPoint=null;
            }
            else if(Has("--collection-qa")&&command[0]=="rotation")Send("{\"type\":\"rotation\"}");
            else if(Has("--collection-qa")&&command[0]=="point"){
                // Test-owned input follows the production form handlers and the
                // same bridge/raycast. It never moves the user's mouse cursor.
                Point p=new Point(Int32.Parse(command[2]),Int32.Parse(command[3]));
                syntheticClickPoint=p;
                var e=new MouseEventArgs(MouseButtons.Left,1,p.X-current.X,p.Y-current.Y,0);
                if(command[1]=="down"){OnMouseDown(e);Log("qa pointer down base_drag="+baseDrag);}
                else if(command[1]=="move"){SendMouse("move",p,!baseDrag);Log("qa pointer move base_drag="+baseDrag);}
                else if(command[1]=="up")OnMouseUp(e);
            }
            else if(command[0]=="reset"){ResetAnchor();Send("{\"type\":\"reset\"}");}
            else if(command[0]=="test"){testRun=true;testStart=lifetime.Elapsed.TotalSeconds;drawn=0;blankFrames=0;nonblank=0;testEvents.Clear();events.Clear();}
            else if(command[0]=="quit")Close();
        }catch(Exception ex){Log("control: "+ex.Message);}
    }
    private void Measure(Frame f){if(performanceOnly)return;int visible=0;for(int i=3;i<f.W*f.H*4;i+=4)if(f.RGBA[i]>16)visible++;if(visible<4000)blankFrames++;else nonblank++;}
    private bool Once(string key,double seconds){if(current==null||lifetime.Elapsed.TotalSeconds-testStart<seconds||testEvents.ContainsKey(key))return false;testEvents[key]=true;return true;}
    private void TestTick(){
        if(current==null)return;
        if(assemblyTest){
            if(Once("pause",1))ClickTestButton(5);
            if(Once("open",2))ClickTestButton(1);
            if(Once("assemble_open",6.5)){ClickTestButton(4);events.Add("assemble_from_full_open_dispatched");}
            if(Once("alive_closed",10)){SaveFrame("after_open_assembly");events.Add("alive_after_open_assembly=True");}
            if(Once("reopen",11))ClickTestButton(1);
            if(Once("assemble_mid_open",12.3))ClickTestButton(4);
            if(Once("alive_mid",16)){SaveFrame("after_mid_open_assembly");events.Add("alive_after_mid_open_assembly=True");}
            if(Once("explode",18))ClickTestButton(3);
            if(Once("assemble_mid_explode",18.8))ClickTestButton(4);
            if(Once("alive_explode",22)){SaveFrame("after_mid_explode_assembly");events.Add("alive_after_mid_explode_assembly=True");}
            if(Once("open_again",24))ClickTestButton(1);
            if(Once("overload",28))ClickTestButton(2);
            if(Once("assemble_overload",31))ClickTestButton(4);
            if(Once("alive_overload",35)){SaveFrame("after_overload_assembly");events.Add("alive_after_overload_assembly=True");}
            if(Once("shutdown",37)){ClickTestButton(6);shutdownStarted=lifetime.Elapsed.TotalSeconds;shutdownRequested=true;}
            return;
        }
        if(steamTest){
            if(Once("pause",1))ClickTestButton(5);
            if(Once("open_first",3))ClickTestButton(1);
            if(Once("close_first",10))ClickTestButton(1);
            if(Once("open_second",14))ClickTestButton(1);
            if(Once("close_second",21))ClickTestButton(1);
            if(Once("open_third",25))ClickTestButton(1);
            if(Once("close_third",32))ClickTestButton(1);
            if(Once("shutdown",36)){ClickTestButton(6);shutdownStarted=lifetime.Elapsed.TotalSeconds;shutdownRequested=true;}
            return;
        }
        if(Once("closed",3)){SaveFrame("native_closed");testBefore=current;TestAlphaHit();testButtonDesktop=new Point[6];for(int i=0;i<6;i++)testButtonDesktop[i]=new Point(anchor.X+current.Buttons[i*2],anchor.Y+current.Buttons[i*2+1]);ClickTestButton(5);}
        if(Once("bloom",8))ClickTestButton(1);
        if(Once("purge",8.7))SaveFrame("native_pressure");
        if(Once("reveal",10.6))SaveFrame("native_reveal");
        if(Once("open",12)){SaveFrame("native_open");TestFixedBase();TestAlphaHit();}
        if(Once("overload",13))ClickTestButton(2);
        if(Once("fx",14.5))SaveFrame("native_overload");
        if(Once("fx_peak",16.5))SaveFrame("native_overload_peak");
        if(Once("explode",21))ClickTestButton(3);
        if(Once("exploded",25)){SaveFrame("native_exploded");TestAlphaHit();TestFixedBase();}
        if(Once("assemble",27))ClickTestButton(4);
        if(Once("assembled",32)){SaveFrame("native_assembled");ClickTestButton(0);}
        if(Once("sleep",35)){SaveFrame("native_sleep");ClickTestButton(0);}
        if(Once("shutdown",39)){ClickTestButton(6);shutdownStarted=lifetime.Elapsed.TotalSeconds;shutdownRequested=true;}
        if(Once("shutdown_stage",41.4))SaveFrame("native_shutdown");
        if(Once("timeout",48)){forceClose=true;events.Add("shutdown_timeout=True");Close();}
    }
    private void ClickTestButton(int i){
        if(current==null)return;Point p=new Point(current.Buttons[i*2]-current.X,current.Buttons[i*2+1]-current.Y);int packed=(p.Y<<16)|(p.X&65535);
        syntheticClickPoint=new Point(current.Buttons[i*2],current.Buttons[i*2+1]);
        Native.PostMessage(Handle,0x201,(IntPtr)1,(IntPtr)packed);Native.PostMessage(Handle,0x202,IntPtr.Zero,(IntPtr)packed);
        events.Add("native_click_button="+(i+1));Log("test native click "+i);
    }
    private void TestAlphaHit(){
        if(performanceOnly)return;
        if(current==null)return;Frame f=current;int transparent=0,opaque=0,pass=0,own=0;
        for(int y=8;y<f.H-8;y+=29)for(int x=8;x<f.W-8;x+=29){int a=f.RGBA[(y*f.W+x)*4+3];if(a!=0&&a<250)continue;
            var p=new Native.POINT(anchor.X+f.X+x,anchor.Y+f.Y+y);IntPtr hit=Native.WindowFromPoint(p);
            if(a==0){transparent++;if(hit!=Handle)pass++;}else{opaque++;if(hit==Handle)own++;}
        }
        hitTransparentFailures+=transparent-pass;hitOpaqueFailures+=opaque-own;
        events.Add("transparent_pixel_hits_pass="+pass+"/"+transparent);events.Add("opaque_pixel_hits_model="+own+"/"+opaque);
    }
    private void TestFixedBase(){if(testButtonDesktop==null)return;int max=0;for(int i=0;i<6;i++){int dx=Math.Abs(anchor.X+current.Buttons[i*2]-testButtonDesktop[i].X),dy=Math.Abs(anchor.Y+current.Buttons[i*2+1]-testButtonDesktop[i].Y);max=Math.Max(max,Math.Max(dx,dy));}events.Add("base_button_pixel_drift="+max);}
    protected override void OnFormClosing(FormClosingEventArgs e){
        if(!forceClose&&renderer!=null&&!renderer.HasExited&&!firstFrame){e.Cancel=true;if(!shutdownRequested)SendAction(6);return;}
        if(movie!=null&&!movie.IsCompleted){if(!movieFinishing){movieFinishing=true;movie.Stop();Log("finalizing movie");}e.Cancel=true;return;}
        if(testRun&&!performanceOnly&&!verificationWritten){
            verificationWritten=true;events.Add("same_window_handle="+(expectedHandle==Handle));events.Add("blank_frames="+blankFrames);events.Add("UpdateLayeredWindow_errors="+updateErrors);events.Add("presented_frames="+drawn);events.Add("all_received_frames_have_model="+(blankFrames==0));events.Add("transparent_hit_failures="+hitTransparentFailures);events.Add("opaque_hit_failures="+hitOpaqueFailures);events.Add("shutdown_completed="+(renderer!=null&&renderer.HasExited));
            events.Add("worker_window_concealed="+WorkerConcealed());events.Add("shutdown_seconds="+(lifetime.Elapsed.TotalSeconds-shutdownStarted).ToString("F2",System.Globalization.CultureInfo.InvariantCulture));File.WriteAllLines(Path.Combine(diagnosticDir,"native_verification.txt"),events.ToArray());
        }
        if(drawn>1){
            frameGaps.Sort();double median=frameGaps.Count==0?0:frameGaps[frameGaps.Count/2],p95=frameGaps.Count==0?0:frameGaps[(int)((frameGaps.Count-1)*.95)];
            var ci=System.Globalization.CultureInfo.InvariantCulture;
            string metrics="{\"presented_frames\":"+drawn+",\"received_frames\":"+receivedPackets+",\"average_fps\":"+(drawn/Math.Max(.01,lastFrameTime-firstFrameTime)).ToString("F2",ci)+",\"median_frame_ms\":"+(median*1000).ToString("F2",ci)+",\"p95_frame_ms\":"+(p95*1000).ToString("F2",ci)+",\"max_gap_ms\":"+(maxPresentationGap*1000).ToString("F2",ci)+"}";
            File.WriteAllText(Path.Combine(diagnosticDir,"performance.json"),metrics);
            if(testRun||Has("--frame-trace")){frameTrace.Insert(0,"elapsed_seconds,present_gap_ms,frame_id,width,height,bitmap_allocations,native_crop_ms,generation2_collections");File.WriteAllLines(Path.Combine(diagnosticDir,"frame_trace.csv"),frameTrace.ToArray());}
        }
        if(!closing){Send("{\"type\":\"quit\"}");closing=true;timer.Stop();tray.Visible=false;tray.Dispose();try{if(client!=null)client.Close();listener.Stop();}catch{}
            if(renderer!=null){try{if(!renderer.WaitForExit(1500))renderer.Kill();}catch{}}lock(frameLock){if(pending!=null){pending.Release();pending=null;}}if(current!=null){current.Release();current=null;}FreeDib();Log("closed; presented="+drawn+" errors="+updateErrors);log.Dispose();}
        base.OnFormClosing(e);
    }
}

internal static class Program {
    [STAThread] private static void Main(string[] args){
        bool first;
        using(var mutex=new Mutex(true,"Local\\HeliosIncubator.Desktop.Singleton",out first)){
        if(!first){try{using(var active=EventWaitHandle.OpenExisting("Local\\HeliosIncubator.Desktop.Activate"))active.Set();}catch{}return;}
        using(var active=new EventWaitHandle(false,EventResetMode.AutoReset,"Local\\HeliosIncubator.Desktop.Activate")){
        try{Native.SetProcessDpiAwarenessContext((IntPtr)(-4));}catch{Native.SetProcessDPIAware();}
        Native.timeBeginPeriod(1);
        try{Application.EnableVisualStyles();Application.SetCompatibleTextRenderingDefault(false);Application.Run(new HeliosForm(args,active));}
        finally{Native.timeEndPeriod(1);}
        }
        mutex.ReleaseMutex();
        }
    }
}
