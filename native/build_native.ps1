param([switch]$Embed,[string]$OutputPath,[string]$RendererPath)
$ErrorActionPreference='Stop'
$heliosRoot=Split-Path -Parent $PSScriptRoot
$heliosCsc=Join-Path $env:WINDIR 'Microsoft.NET\Framework64\v4.0.30319\csc.exe'
if (-not (Test-Path -LiteralPath $heliosCsc -PathType Leaf)) { throw 'The .NET Framework 4.x x64 compiler is required.' }
$heliosArguments=@('/nologo','/target:winexe','/platform:x64','/unsafe','/optimize+','/r:System.dll','/r:System.Core.dll','/r:System.Drawing.dll','/r:System.Windows.Forms.dll','/r:System.IO.Compression.dll',('/win32icon:'+(Join-Path $heliosRoot 'app\assets\icon.ico')))
if($Embed){
 if(-not $RendererPath){$RendererPath=Join-Path $heliosRoot 'native\HeliosRenderer.exe'}
 $heliosArguments+=('/resource:'+$RendererPath+',Helios.Renderer')
 if(-not $OutputPath){$OutputPath=Join-Path $heliosRoot 'dist\HELIOS.exe'}
}elseif(-not $OutputPath){$OutputPath=Join-Path $heliosRoot 'native\HeliosDesktop.exe'}
$OutputPath=[IO.Path]::GetFullPath($OutputPath)
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $OutputPath) | Out-Null
$heliosArguments+=('/out:'+$OutputPath)
$heliosArguments+=(Join-Path $PSScriptRoot 'HeliosDesktop.cs')
$heliosArguments+=(Join-Path $PSScriptRoot 'NativeMovieRecorder.cs')
& $heliosCsc $heliosArguments
if($LASTEXITCODE -ne 0){throw 'Native desktop build failed.'}
