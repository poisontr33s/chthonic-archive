# Nautical ASCII Algorithms

@SID: DOC_NAUTICAL_ASCII_ALGORITHMS
@Type: Reference
@Context: Image / ASCII / Nautical Charts

## Verdict

The local converter is useful for deterministic image-to-symbol work, but the
PowerShell built-in engine is a correctness/prototyping lane, not the final
high-performance implementation. If this becomes a primary art tool, move the
algorithm core to Rust and keep the PowerShell script as a thin CLI surface.

Current rating:

- Deterministic local conversion: 8/10
- Speed at large dimensions: 5/10
- Nautical chart line extraction: 7/10 with `Sobel` or `Mixed`
- Photographic tonal ASCII: 7/10 with `Luma`, `Bayer`, or `FloydSteinberg`
- Diffusion/stable-image generation: not the same problem

## Algorithms

`Luma`

- Uses Rec. 601 luminance: `0.299 R + 0.587 G + 0.114 B`.
- Best for icons, screenshots, and simple tonal previews.

`Sobel`

- Applies Sobel convolution over the downsampled luminance matrix.
- Best for linework, coastlines, chart contours, silhouettes, glyph-like output.

`Mixed`

- Blends luminance with Sobel edge strength.
- Best default for nautical image work when both tone and structure matter.

`Bayer`

- Ordered dithering with a 4x4 Bayer threshold matrix.
- Best for stable, patterned tone that keeps the same result every run.

`FloydSteinberg`

- Error diffusion dithering.
- Best for richer tonal distribution in low-width output.

## Stable Diffusion Note

Euler and Euler a in Stable Diffusion are sampler names, not image-to-ASCII
conversion algorithms. They matter when generating images from noise. For
image-to-ASCII, the relevant math is sampling, luminance, convolution, quantized
symbol ramps, and dithering.

ASCII-to-image is plausible through diffusion prompting or ControlNet-style
conditioning, but that is a generative pipeline. It should not be mixed with the
deterministic converter unless the explicit goal is image generation.

## CLI Examples

```powershell
bun run ascii:nautical -- assets\meta-extension.png -Width 80 -Algorithm Mixed
bun run ascii:nautical -- assets\meta-extension.png -Width 80 -Algorithm Sobel
bun run ascii:nautical -- assets\meta-extension.png -Width 80 -Algorithm FloydSteinberg
bun run ascii:nautical -- assets\meta-extension.png -Width 80 -Algorithm Mixed -Invert
```

## Next Better Implementation

Rust core shape:

- Use `image` crate for decoding.
- Use `rayon` for parallel cell sampling.
- Use `imageproc` or local convolution for Sobel/Canny-style edge maps.
- Emit plain text, Markdown fenced text, or SVG text layers.
- Keep URL/stdin disabled by default for this repo.
