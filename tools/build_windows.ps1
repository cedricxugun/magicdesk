param([string]$GodotPath,[string]$OutputPath)
$ErrorActionPreference='Stop'
$magicRoot=Split-Path -Parent $PSScriptRoot
if(-not $GodotPath){
    $magicCommand=Get-Command godot -ErrorAction SilentlyContinue
    if(-not $magicCommand){throw 'Pass -GodotPath with the Godot 4.7.1 executable.'}
    $GodotPath=$magicCommand.Source
}
if(-not $OutputPath){$OutputPath=Join-Path $magicRoot 'dist\MagicDesk.exe'}
$magicRenderer=Join-Path $magicRoot 'native\MagicDeskRenderer.exe'
& $GodotPath --headless --editor --path (Join-Path $magicRoot 'app') --import
if($LASTEXITCODE -ne 0){throw 'Godot import failed.'}
& $GodotPath --headless --path (Join-Path $magicRoot 'app') --export-release 'Windows Desktop' $magicRenderer
if($LASTEXITCODE -ne 0){throw 'Godot export failed.'}
& (Join-Path $magicRoot 'native\build_native.ps1') -Embed -RendererPath $magicRenderer -OutputPath $OutputPath
Get-FileHash -LiteralPath $OutputPath -Algorithm SHA256
