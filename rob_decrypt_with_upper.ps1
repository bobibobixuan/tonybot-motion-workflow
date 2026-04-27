param(
    [Parameter(Mandatory = $true)]
    [string]$InputFile,

    [string]$UpperSoftwareDir = 'C:\Bus Servo Control',

    [string]$OutputFile
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-PrivateBlobBytes {
    param(
        [Parameter(Mandatory = $true)]
        [System.Reflection.Assembly]$Assembly
    )

    $privateImpl = $Assembly.GetType('<PrivateImplementationDetails>', $true)
    $blobField = $privateImpl.GetFields([System.Reflection.BindingFlags]'Public,NonPublic,Static,DeclaredOnly') |
        Select-Object -First 1

    if (-not $blobField) {
        throw 'Unable to locate private implementation blob.'
    }

    $blobValue = $blobField.GetValue($null)
    $blobSize = [Runtime.InteropServices.Marshal]::SizeOf($blobValue)
    $blobPtr = [Runtime.InteropServices.Marshal]::AllocHGlobal($blobSize)

    try {
        [Runtime.InteropServices.Marshal]::StructureToPtr($blobValue, $blobPtr, $false)
        $blobBytes = New-Object byte[] $blobSize
        [Runtime.InteropServices.Marshal]::Copy($blobPtr, $blobBytes, 0, $blobSize)
        return $blobBytes
    }
    finally {
        [Runtime.InteropServices.Marshal]::FreeHGlobal($blobPtr)
    }
}

function Get-EncryptArray {
    param(
        [Parameter(Mandatory = $true)]
        [System.Reflection.Assembly]$Assembly
    )

    $blobBytes = Get-PrivateBlobBytes -Assembly $Assembly
    if ($blobBytes.Length -ne 16) {
        throw "Unexpected private blob size: $($blobBytes.Length)"
    }

    $values = New-Object 'UInt32[]' 4
    0..3 | ForEach-Object {
        $values[$_] = [BitConverter]::ToUInt32($blobBytes, $_ * 4)
    }
    return ,$values
}

function Load-UpperSoftwareAssembly {
    param(
        [Parameter(Mandatory = $true)]
        [string]$SoftwareDir
    )

    $dependencies = @(
        'GenericHid.dll',
        'HalfRoundGauge.dll',
        'WpfGauge.dll',
        'MmTimer.dll',
        'Bus Servo Control.exe'
    )

    foreach ($item in $dependencies) {
        $fullPath = Join-Path $SoftwareDir $item
        if (Test-Path $fullPath) {
            [Reflection.Assembly]::LoadFrom($fullPath) | Out-Null
        }
    }

    $exePath = Join-Path $SoftwareDir 'Bus Servo Control.exe'
    if (-not (Test-Path $exePath)) {
        throw "Upper software executable not found: $exePath"
    }

    return [Reflection.Assembly]::LoadFrom($exePath)
}

function Get-PlainRobBytes {
    param(
        [Parameter(Mandatory = $true)]
        [string]$SourceFile,

        [Parameter(Mandatory = $true)]
        [System.Reflection.Assembly]$Assembly
    )

    $mainType = $Assembly.GetType('WpfApplication1.MainWindow', $true)
    $decryptMethod = $mainType.GetMethod('DecryptActionFile', [System.Reflection.BindingFlags]'Public,NonPublic,Instance')
    $encryptField = $mainType.GetField('ENCRYPT_ARRAY', [System.Reflection.BindingFlags]'Public,NonPublic,Instance')

    if (-not $decryptMethod) {
        throw 'DecryptActionFile method not found.'
    }
    if (-not $encryptField) {
        throw 'ENCRYPT_ARRAY field not found.'
    }

    $encryptArray = Get-EncryptArray -Assembly $Assembly
    $instance = [Runtime.Serialization.FormatterServices]::GetUninitializedObject($mainType)
    $encryptField.SetValue($instance, $encryptArray)

    $cipherBytes = [System.IO.File]::ReadAllBytes($SourceFile)
    $args = New-Object object[] 1
    $args[0] = $cipherBytes
    $plainBody = [byte[]]$decryptMethod.Invoke($instance, $args)

    if ($cipherBytes.Length -lt 16) {
        throw 'Input file is too small to be a valid ACT-40 file.'
    }

    $header = New-Object byte[] 16
    [Array]::Copy($cipherBytes, 0, $header, 0, 16)
    for ($index = 8; $index -le 11; $index++) {
        $header[$index] = 0
    }

    $plainFile = New-Object byte[] ($header.Length + $plainBody.Length)
    [Array]::Copy($header, 0, $plainFile, 0, $header.Length)
    [Array]::Copy($plainBody, 0, $plainFile, $header.Length, $plainBody.Length)

    return [PSCustomObject]@{
        EncryptArray = $encryptArray
        PlainBytes    = $plainFile
        PlainBody     = $plainBody
    }
}

if (-not $OutputFile) {
    $directory = [System.IO.Path]::GetDirectoryName($InputFile)
    $baseName = [System.IO.Path]::GetFileNameWithoutExtension($InputFile)
    $OutputFile = Join-Path $directory ($baseName + '.plain.rob')
}

Add-Type -AssemblyName PresentationFramework

$assembly = Load-UpperSoftwareAssembly -SoftwareDir $UpperSoftwareDir
$result = Get-PlainRobBytes -SourceFile $InputFile -Assembly $assembly
[System.IO.File]::WriteAllBytes($OutputFile, $result.PlainBytes)

Write-Output ('INPUT=' + $InputFile)
Write-Output ('OUTPUT=' + $OutputFile)
Write-Output ('ENCRYPT_ARRAY=' + (($result.EncryptArray | ForEach-Object { '0x{0:X8}' -f $_ }) -join ','))
Write-Output ('PLAIN_LENGTH=' + $result.PlainBytes.Length)