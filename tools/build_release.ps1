param([string]$GodotPath = $env:GODOT_EXE)
$ErrorActionPreference = 'Stop'
$heliosRoot = Split-Path -Parent $PSScriptRoot
$heliosGodot = $GodotPath
if ([string]::IsNullOrWhiteSpace($heliosGodot)) {
    $heliosCommand = Get-Command godot -ErrorAction SilentlyContinue
    if ($null -ne $heliosCommand) { $heliosGodot = $heliosCommand.Source }
}
if ([string]::IsNullOrWhiteSpace($heliosGodot) -or -not (Test-Path -LiteralPath $heliosGodot -PathType Leaf)) {
    throw 'Set GODOT_EXE or pass -GodotPath with the full path to the Godot 4.7.1 executable.'
}
New-Item -ItemType Directory -Path (Join-Path $heliosRoot 'dist') -Force | Out-Null
& $heliosGodot --headless --editor --path (Join-Path $heliosRoot 'app') --import
if ($LASTEXITCODE -ne 0) { throw 'Godot import failed.' }
& $heliosGodot --headless --path (Join-Path $heliosRoot 'app') --export-release 'Windows Desktop' (Join-Path $heliosRoot 'native\HeliosRenderer.exe')
if ($LASTEXITCODE -ne 0) { throw 'Windows export failed.' }
& (Join-Path $heliosRoot 'native\build_native.ps1') -Embed
Write-Output (Join-Path $heliosRoot 'dist\HELIOS.exe')
