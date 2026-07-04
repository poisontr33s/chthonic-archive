#!/usr/bin/env pwsh

<# 
@SID: TOOL_NAUTICAL_ASCII_CONVERTER_V1
@Purpose: Local, token-free image-to-ASCII entrypoint for nautical chart work.

Upstream reviewed:
  github.com/TheZoraiz/ascii-image-converter
  d05a757c5e02ab23e97b6f6fca4e1fbeb10ab559

Install policy:
  This script never installs Go or Go packages. Put a reviewed converter on PATH,
  place it in scripts/bin, or set ASCII_IMAGE_CONVERTER to its exact file path.
  If building the converter from source, use the goup-managed Go toolchain first;
  do not add ad hoc Go bootstrapping to this runtime hook.
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$InputPath,

    [string]$OutPath,

    [ValidateRange(8, 400)]
    [int]$Width = 96,

    [int]$Height = 0,

    [ValidateScript({
        if ($_.Length -lt 2) {
            throw "Map must contain at least two characters."
        }
        $true
    })]
    [string]$Map = " .,:;~-+xX#%@",

    [switch]$Braille,
    [switch]$Dither,
    [ValidateSet("Luma", "Sobel", "Mixed", "Bayer", "FloydSteinberg")]
    [string]$Algorithm = "Luma",
    [switch]$Invert,
    [ValidateSet("Auto", "External", "BuiltIn")]
    [string]$Engine = "Auto",
    [switch]$Mock
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$AllowedExtensions = @(".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff", ".bmp")
$IsWindowsPlatform = [System.Runtime.InteropServices.RuntimeInformation]::IsOSPlatform(
    [System.Runtime.InteropServices.OSPlatform]::Windows
)

function Resolve-StaticImagePath {
    param([string]$Path)

    if ([string]::IsNullOrWhiteSpace($Path)) {
        throw "InputPath is required."
    }

    if ($Path -eq "-") {
        throw "stdin is intentionally disabled for this hook. Pass a local image path."
    }

    if ($Path -match "^[a-zA-Z][a-zA-Z0-9+.-]*://") {
        throw "URLs are intentionally disabled for this hook. Download the image first, then pass the local path."
    }

    $resolved = @(Resolve-Path -LiteralPath $Path)
    if ($resolved.Count -ne 1) {
        throw "InputPath must resolve to exactly one local file."
    }

    $item = Get-Item -LiteralPath $resolved[0].ProviderPath
    if ($item.PSIsContainer) {
        throw "InputPath must be a static image file, not a directory."
    }

    $extension = [System.IO.Path]::GetExtension($item.FullName).ToLowerInvariant()
    if ($AllowedExtensions -notcontains $extension) {
        throw "Unsupported image extension '$extension'. Allowed: $($AllowedExtensions -join ', ')."
    }

    return $item.FullName
}

function Resolve-Converter {
    if (-not [string]::IsNullOrWhiteSpace($env:ASCII_IMAGE_CONVERTER)) {
        $override = Resolve-Path -LiteralPath $env:ASCII_IMAGE_CONVERTER -ErrorAction SilentlyContinue
        if ($override) {
            return $override.ProviderPath
        }
        throw "ASCII_IMAGE_CONVERTER is set but does not point to a file: $env:ASCII_IMAGE_CONVERTER"
    }

    $command = Get-Command ascii-image-converter -CommandType Application -ErrorAction SilentlyContinue
    if ($command) {
        return $command.Source
    }

    $exeNames = if ($IsWindowsPlatform) {
        @("ascii-image-converter.exe", "ascii-image-converter")
    } else {
        @("ascii-image-converter", "ascii-image-converter.exe")
    }

    foreach ($exeName in $exeNames) {
        $localCandidate = Join-Path (Join-Path $PSScriptRoot "bin") $exeName
        if (Test-Path -LiteralPath $localCandidate -PathType Leaf) {
            return (Resolve-Path -LiteralPath $localCandidate).ProviderPath
        }
    }

    return $null
}

function Test-BuiltInEngineAvailable {
    if (-not $IsWindowsPlatform) {
        return $false
    }

    try {
        Add-Type -AssemblyName System.Drawing
        return $true
    } catch {
        return $false
    }
}

function Select-Engine {
    param(
        [string]$RequestedEngine,
    [string]$Converter,
    [string]$ImagePath
    )

    $extension = [System.IO.Path]::GetExtension($ImagePath).ToLowerInvariant()
    $builtInAvailable = (Test-BuiltInEngineAvailable) -and (-not $Braille) -and ($extension -ne ".webp")
    $needsBuiltInAlgorithm = ($Algorithm -ne "Luma") -or $Invert -or ($Dither -and (-not $Braille))

    if ($RequestedEngine -eq "External") {
        if (-not $Converter) {
            throw "External engine requested, but ascii-image-converter is missing."
        }
        if ($needsBuiltInAlgorithm) {
            throw "External engine only supports the basic Luma path from this hook. Use -Engine BuiltIn for -Algorithm, -Invert, or non-braille -Dither."
        }
        return "External"
    }

    if ($RequestedEngine -eq "BuiltIn") {
        if (-not $builtInAvailable) {
            throw "BuiltIn engine is unavailable for this input. It requires Windows System.Drawing, non-braille mode, and a non-WebP image."
        }
        return "BuiltIn"
    }

    if ($needsBuiltInAlgorithm -and $builtInAvailable) {
        return "BuiltIn"
    }

    if ($Converter -and (-not $needsBuiltInAlgorithm)) {
        return "External"
    }

    if ($builtInAvailable) {
        return "BuiltIn"
    }

    throw "No converter engine is available. Place ascii-image-converter on PATH/scripts/bin, set ASCII_IMAGE_CONVERTER, or use a non-WebP static image with the BuiltIn engine."
}

function New-ConverterArgs {
    param([string]$ImagePath)

    if ($Height -lt 0) {
        throw "Height must be 0 or greater."
    }

    $args = @($ImagePath)

    if ($Height -gt 0) {
        $args += @("--dimensions", "$Width,$Height")
    } else {
        $args += @("--width", "$Width")
    }

    if ($Braille) {
        $args += "--braille"
        if ($Dither) {
            $args += "--dither"
        }
    } else {
        $args += @("--map", $Map)
    }

    return $args
}

function Convert-WithExternalEngine {
    param(
        [string]$Converter,
        [string[]]$ConverterArgs
    )

    $output = & $Converter @ConverterArgs 2>&1
    $exitCode = $LASTEXITCODE
    if ($exitCode -ne 0) {
        $output | ForEach-Object { Write-Error $_ }
        exit $exitCode
    }

    return (($output | ForEach-Object { "$_" }) -join [Environment]::NewLine)
}

function Convert-WithBuiltInEngine {
    param([string]$ImagePath)

    if ($Braille) {
        throw "BuiltIn engine does not support braille mode."
    }

    Add-Type -AssemblyName System.Drawing

    function Get-ClampedUnit {
        param([double]$Value)

        if ($Value -lt 0.0) {
            return 0.0
        }
        if ($Value -gt 1.0) {
            return 1.0
        }
        return $Value
    }

    function Get-AsciiIndex {
        param(
            [double]$Value,
            [int]$LastIndex
        )

        $clamped = Get-ClampedUnit -Value $Value
        return [Math]::Min([int][Math]::Floor($clamped * ($LastIndex + 1)), $LastIndex)
    }

    function New-DoubleMatrix {
        param(
            [int]$Rows,
            [int]$Columns
        )

        $matrix = New-Object 'double[][]' $Rows
        for ($rowIndex = 0; $rowIndex -lt $Rows; $rowIndex++) {
            $matrix[$rowIndex] = New-Object 'double[]' $Columns
        }
        return $matrix
    }

    function Get-CellLuma {
        param(
            [System.Drawing.Bitmap]$Bitmap,
            [double]$SourceWidth,
            [double]$SourceHeight,
            [int]$TargetWidth,
            [int]$TargetHeight,
            [int]$X,
            [int]$Y
        )

        $offsets = @(0.25, 0.5, 0.75)
        $sum = 0.0
        $samples = 0

        foreach ($offsetY in $offsets) {
            $sourceY = [Math]::Min(
                [int][Math]::Floor((($Y + $offsetY) * $SourceHeight) / $TargetHeight),
                [int]$SourceHeight - 1
            )

            foreach ($offsetX in $offsets) {
                $sourceX = [Math]::Min(
                    [int][Math]::Floor((($X + $offsetX) * $SourceWidth) / $TargetWidth),
                    [int]$SourceWidth - 1
                )

                $pixel = $Bitmap.GetPixel($sourceX, $sourceY)
                $sum += ((0.299 * $pixel.R) + (0.587 * $pixel.G) + (0.114 * $pixel.B)) / 255.0
                $samples++
            }
        }

        return $sum / [double]$samples
    }

    function New-SobelMatrix {
        param(
            [double[][]]$LumaMatrix,
            [int]$Rows,
            [int]$Columns
        )

        $edgeMatrix = New-DoubleMatrix -Rows $Rows -Columns $Columns

        for ($y = 0; $y -lt $Rows; $y++) {
            for ($x = 0; $x -lt $Columns; $x++) {
                if ($x -eq 0 -or $y -eq 0 -or $x -eq ($Columns - 1) -or $y -eq ($Rows - 1)) {
                    $edgeMatrix[$y][$x] = 0.0
                    continue
                }

                $gx =
                    (-1.0 * $LumaMatrix[$y - 1][$x - 1]) + (1.0 * $LumaMatrix[$y - 1][$x + 1]) +
                    (-2.0 * $LumaMatrix[$y][$x - 1])     + (2.0 * $LumaMatrix[$y][$x + 1]) +
                    (-1.0 * $LumaMatrix[$y + 1][$x - 1]) + (1.0 * $LumaMatrix[$y + 1][$x + 1])

                $gy =
                    (-1.0 * $LumaMatrix[$y - 1][$x - 1]) + (-2.0 * $LumaMatrix[$y - 1][$x]) + (-1.0 * $LumaMatrix[$y - 1][$x + 1]) +
                    (1.0 * $LumaMatrix[$y + 1][$x - 1])  + (2.0 * $LumaMatrix[$y + 1][$x])  + (1.0 * $LumaMatrix[$y + 1][$x + 1])

                $edgeMatrix[$y][$x] = Get-ClampedUnit -Value ([Math]::Sqrt(($gx * $gx) + ($gy * $gy)) / 4.0)
            }
        }

        return $edgeMatrix
    }

    function Convert-MatrixToLines {
        param(
            [double[][]]$ValueMatrix,
            [int]$Rows,
            [int]$Columns,
            [char[]]$Chars,
            [string]$Mode
        )

        $lastIndex = $Chars.Length - 1
        $lines = [System.Collections.Generic.List[string]]::new()
        $bayer4 = @(
            @(0, 8, 2, 10),
            @(12, 4, 14, 6),
            @(3, 11, 1, 9),
            @(15, 7, 13, 5)
        )

        if ($Mode -eq "FloydSteinberg") {
            $work = New-DoubleMatrix -Rows $Rows -Columns $Columns
            for ($copyY = 0; $copyY -lt $Rows; $copyY++) {
                for ($copyX = 0; $copyX -lt $Columns; $copyX++) {
                    $work[$copyY][$copyX] = $ValueMatrix[$copyY][$copyX]
                }
            }

            for ($y = 0; $y -lt $Rows; $y++) {
                $builder = [System.Text.StringBuilder]::new()
                for ($x = 0; $x -lt $Columns; $x++) {
                    $oldValue = Get-ClampedUnit -Value $work[$y][$x]
                    $index = [Math]::Min([int][Math]::Round($oldValue * $lastIndex), $lastIndex)
                    $newValue = if ($lastIndex -eq 0) { 0.0 } else { [double]$index / [double]$lastIndex }
                    $error = $oldValue - $newValue

                    [void]$builder.Append($Chars[$index])

                    if (($x + 1) -lt $Columns) {
                        $work[$y][$x + 1] += $error * 7.0 / 16.0
                    }
                    if (($y + 1) -lt $Rows) {
                        if (($x - 1) -ge 0) {
                            $work[$y + 1][$x - 1] += $error * 3.0 / 16.0
                        }
                        $work[$y + 1][$x] += $error * 5.0 / 16.0
                        if (($x + 1) -lt $Columns) {
                            $work[$y + 1][$x + 1] += $error * 1.0 / 16.0
                        }
                    }
                }
                $lines.Add($builder.ToString())
            }

            return ($lines -join [Environment]::NewLine)
        }

        for ($y = 0; $y -lt $Rows; $y++) {
            $builder = [System.Text.StringBuilder]::new()
            for ($x = 0; $x -lt $Columns; $x++) {
                $value = $ValueMatrix[$y][$x]

                if ($Mode -eq "Bayer") {
                    $threshold = (($bayer4[$y % 4][$x % 4] + 0.5) / 16.0) - 0.5
                    $value = Get-ClampedUnit -Value ($value + ($threshold / [Math]::Max($Chars.Length, 2)))
                }

                $index = Get-AsciiIndex -Value $value -LastIndex $lastIndex
                [void]$builder.Append($Chars[$index])
            }
            $lines.Add($builder.ToString())
        }

        return ($lines -join [Environment]::NewLine)
    }

    $image = [System.Drawing.Image]::FromFile($ImagePath)
    try {
        $bitmap = [System.Drawing.Bitmap]::new($image)
        try {
            $sourceWidth = [double]$bitmap.Width
            $sourceHeight = [double]$bitmap.Height
            if ($sourceWidth -le 0 -or $sourceHeight -le 0) {
                throw "Image has invalid dimensions."
            }

            $targetWidth = $Width
            if ($Height -gt 0) {
                $targetHeight = $Height
            } else {
                $aspectRatio = $sourceWidth / $sourceHeight
                $targetHeight = [Math]::Max(1, [int][Math]::Round(($targetWidth / $aspectRatio) * 0.5))
            }

            $lumaMatrix = New-DoubleMatrix -Rows $targetHeight -Columns $targetWidth

            for ($y = 0; $y -lt $targetHeight; $y++) {
                for ($x = 0; $x -lt $targetWidth; $x++) {
                    $lumaMatrix[$y][$x] = Get-CellLuma `
                        -Bitmap $bitmap `
                        -SourceWidth $sourceWidth `
                        -SourceHeight $sourceHeight `
                        -TargetWidth $targetWidth `
                        -TargetHeight $targetHeight `
                        -X $x `
                        -Y $y
                }
            }

            $edgeMatrix = $null
            if ($Algorithm -eq "Sobel" -or $Algorithm -eq "Mixed") {
                $edgeMatrix = New-SobelMatrix -LumaMatrix $lumaMatrix -Rows $targetHeight -Columns $targetWidth
            }

            $valueMatrix = New-DoubleMatrix -Rows $targetHeight -Columns $targetWidth
            for ($y = 0; $y -lt $targetHeight; $y++) {
                for ($x = 0; $x -lt $targetWidth; $x++) {
                    $value = switch ($Algorithm) {
                        "Sobel" { $edgeMatrix[$y][$x]; break }
                        "Mixed" { (0.65 * $lumaMatrix[$y][$x]) + (0.35 * $edgeMatrix[$y][$x]); break }
                        default { $lumaMatrix[$y][$x]; break }
                    }

                    if ($Invert) {
                        $value = 1.0 - $value
                    }

                    $valueMatrix[$y][$x] = Get-ClampedUnit -Value $value
                }
            }

            $renderMode = if ($Dither -and $Algorithm -eq "Luma") { "FloydSteinberg" } else { $Algorithm }
            return Convert-MatrixToLines `
                -ValueMatrix $valueMatrix `
                -Rows $targetHeight `
                -Columns $targetWidth `
                -Chars $Map.ToCharArray() `
                -Mode $renderMode
        } finally {
            $bitmap.Dispose()
        }
    } finally {
        $image.Dispose()
    }
}

$imagePath = Resolve-StaticImagePath -Path $InputPath
$converterArgs = New-ConverterArgs -ImagePath $imagePath
$converter = Resolve-Converter
$selectedEngine = $null
try {
    $selectedEngine = Select-Engine -RequestedEngine $Engine -Converter $converter -ImagePath $imagePath
} catch {
    if (-not $Mock) {
        throw
    }
}

if ($Mock) {
    Write-Host "[mock] input: $imagePath"
    if ($selectedEngine) {
        Write-Host "[mock] engine: $selectedEngine"
    }
    if ($selectedEngine -eq "External" -and $converter) {
        Write-Host "[mock] converter: $converter"
    } elseif (-not $selectedEngine) {
        Write-Host "[mock] converter missing; put ascii-image-converter on PATH, place it in scripts/bin, or set ASCII_IMAGE_CONVERTER."
    }
    if ($selectedEngine -eq "External") {
        Write-Host "[mock] args: $($converterArgs -join ' ')"
    } else {
        Write-Host "[mock] dimensions: width=$Width height=$(if ($Height -gt 0) { $Height } else { 'auto' })"
        Write-Host "[mock] algorithm: $Algorithm"
        Write-Host "[mock] invert: $($Invert.IsPresent)"
        Write-Host "[mock] dither: $($Dither.IsPresent)"
        Write-Host "[mock] map: $Map"
    }
    if (-not [string]::IsNullOrWhiteSpace($OutPath)) {
        try {
            $mockOutput = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($OutPath)
        } catch {
            $mockOutput = $OutPath
        }
        Write-Host "[mock] output: $mockOutput"
    } else {
        Write-Host "[mock] output: stdout"
    }
    exit 0
}

if ($selectedEngine -eq "External") {
    $ascii = Convert-WithExternalEngine -Converter $converter -ConverterArgs $converterArgs
} elseif ($selectedEngine -eq "BuiltIn") {
    $ascii = Convert-WithBuiltInEngine -ImagePath $imagePath
} else {
    throw "No converter engine was selected."
}

if ([string]::IsNullOrWhiteSpace($OutPath)) {
    Write-Output $ascii
    exit 0
}

$outFullPath = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($OutPath)
$outParent = Split-Path -Parent $outFullPath
if (-not [string]::IsNullOrWhiteSpace($outParent) -and -not (Test-Path -LiteralPath $outParent)) {
    New-Item -ItemType Directory -Path $outParent | Out-Null
}

$utf8NoBom = [System.Text.UTF8Encoding]::new($false)
[System.IO.File]::WriteAllText($outFullPath, $ascii + [Environment]::NewLine, $utf8NoBom)
Write-Host "Wrote $outFullPath"
