$ErrorActionPreference = 'Stop'
$magicdeskRoot = Split-Path -Parent $PSScriptRoot
$magicdeskAssembly = [Reflection.Assembly]::LoadFrom((Join-Path $magicdeskRoot 'native\HeliosDesktop.exe'))
$magicdeskMethod = $magicdeskAssembly.GetType('HeliosForm').GetMethod('CropRawFrame', [Reflection.BindingFlags]'NonPublic,Static')
$magicdeskCases = @(
    @{ Name='empty'; Points=@(); Rect=$null },
    @{ Name='faint alpha at corner'; Points=@(,@(0,0,1)); Rect=@(0,0,3,3) },
    @{ Name='opposite edges'; Points=@(@(0,47,255),@(63,0,1)); Rect=@(0,0,64,48) },
    @{ Name='disjoint islands and transparent gap'; Points=@(@(11,14,255),@(39,31,37)); Rect=@(9,12,33,22) },
    @{ Name='single bottom right pixel'; Points=@(,@(63,47,1)); Rect=@(61,45,3,3) }
)
foreach ($magicdeskCase in $magicdeskCases) {
    $magicdeskHeader = [int[]]::new(24)
    $magicdeskHeader[0]=0x484C5334; $magicdeskHeader[1]=64; $magicdeskHeader[2]=48
    $magicdeskHeader[5]=64; $magicdeskHeader[6]=48; $magicdeskHeader[9]=255
    $magicdeskRgba=[byte[]]::new(64*48*4)
    foreach ($magicdeskPoint in $magicdeskCase.Points) {
        $magicdeskIndex=([int]$magicdeskPoint[1]*64+[int]$magicdeskPoint[0])*4
        $magicdeskRgba[$magicdeskIndex]=17; $magicdeskRgba[$magicdeskIndex+1]=86; $magicdeskRgba[$magicdeskIndex+2]=203
        $magicdeskRgba[$magicdeskIndex+3]=[byte]$magicdeskPoint[2]
    }
    $magicdeskFrame=$magicdeskMethod.Invoke($null, [object[]]@($magicdeskHeader,$magicdeskRgba))
    if ($null -eq $magicdeskCase.Rect) {
        if ($null -ne $magicdeskFrame) { throw 'Empty frame was presented' }
    } else {
        $magicdeskRect=$magicdeskCase.Rect
        if ($magicdeskFrame.X -ne $magicdeskRect[0] -or $magicdeskFrame.Y -ne $magicdeskRect[1] -or $magicdeskFrame.W -ne $magicdeskRect[2] -or $magicdeskFrame.H -ne $magicdeskRect[3]) { throw ('Wrong bounds: '+$magicdeskCase.Name) }
        for ($magicdeskY=0; $magicdeskY -lt $magicdeskFrame.H; $magicdeskY++) {
            for ($magicdeskX=0; $magicdeskX -lt $magicdeskFrame.W; $magicdeskX++) {
                for ($magicdeskChannel=0; $magicdeskChannel -lt 4; $magicdeskChannel++) {
                    $magicdeskA=($magicdeskY*$magicdeskFrame.W+$magicdeskX)*4+$magicdeskChannel
                    $magicdeskB=(($magicdeskY+$magicdeskFrame.Y)*64+$magicdeskX+$magicdeskFrame.X)*4+$magicdeskChannel
                    if ($magicdeskFrame.RGBA[$magicdeskA] -ne $magicdeskRgba[$magicdeskB]) { throw ('Pixel changed: '+$magicdeskCase.Name) }
                }
            }
        }
        $magicdeskFrame.Release()
    }
    Write-Output ('PASS: '+$magicdeskCase.Name)
}
