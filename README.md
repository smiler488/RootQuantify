# RootQuantify

English | [中文](README.zh-CN.md)

A small OpenCV tool for washed-root scans. For each image you outline the roots, the region is segmented automatically, you touch up the mask with a brush, and the tool saves the clean binary image and measures total root length, projected area, mean diameter and number of tips.

I wrote it because the automatic thresholds in commercial root software kept picking up soil particles, tray edges and labels in my scans, and fixing those afterwards took longer than drawing the region by hand. The semi-automatic route turned out faster for a few hundred images.

## Installation

```bash
git clone https://github.com/smiler488/RootQuantify.git
cd RootQuantify
pip install -r requirements.txt
```

Python 3.9 or newer, on Windows, macOS or Linux.

## Usage

```bash
python RootImager.py path/to/scans --dpi 600
```

Without a folder argument a folder dialog opens. Two windows appear: the original on the left, the working view on the right.

**1. Outline.** Click the vertices of a polygon around the roots in the right window.
`c` confirms, `r` starts again, `s` skips the image, `Esc` stops the run.

**2. Automatic segmentation.** A grey-level closing estimates the background, which is subtracted from the image. The difference is stretched to 0–255 and thresholded, so roots end up black on white.

**3. Touch-up.** `d` draws roots, `e` erases, `+`/`-` changes the brush (green circle), `u` undoes the last stroke, `q` finishes.

**4. Save and measure.** The mask goes to `output/processed-<name>`, one line of traits is appended to `output/root_traits.csv`, and the original moves to `processed_original/` so an interrupted run can be resumed. Use `--keep-originals` to leave the originals in place.

| Option | Default | Notes |
|---|---|---|
| `--dpi` | none | scan resolution; traits in mm / mm² instead of pixels |
| `--kernel` | 50 | background kernel (px), must be wider than the thickest root |
| `--threshold` | 30 | threshold on the normalised difference image (0–255); lower picks up fine laterals and more noise |
| `-o` | `<folder>/output` | output folder |
| `--keep-originals` | off | do not move finished images |

## Traits

| Column | How it is computed |
|---|---|
| `length` | skeleton of the mask, length after Kimura et al. (1999): √(Nd² + (Nd + No/2)²) + No/2, where No and Nd are orthogonal and diagonal neighbour pairs |
| `area` | number of root pixels |
| `mean_diameter` | area / length |
| `tips` | skeleton end points |
| `objects` | connected root pieces (pieces under 20 px are dropped as dust) |

On synthetic test images the length is within 2–4 % of the true value for straight, oblique and curved roots. Diameter from area/length is a mean over the whole system and is pulled down by many fine laterals. Overlapping roots are counted once where they cross, as in any 2-D method, so spread the roots in the tray before scanning.

## Changes in this revision

- The folder was hard-coded to a path on my laptop, although the README promised a folder dialog. There is now a dialog and a command line argument.
- Added the measurements; the earlier version only produced the binary images.
- Output goes next to the images, not to the current working directory.
- Screen size is read through Tk instead of a Windows-only call.
- `s` skips an image and `Esc` quits.
- Requirements no longer pin 2022 versions that have no wheels for Python 3.12.

## Citation

```bibtex
@software{deng_rootquantify,
  author = {Deng, Liangchao},
  title  = {RootQuantify: semi-automatic segmentation and measurement of root scans},
  year   = {2025},
  url    = {https://github.com/smiler488/RootQuantify}
}
```

Kimura, K., Kikuchi, S. & Yamasaki, S. (1999). Accurate root length measurement by image analysis. *Plant and Soil*, 216, 117–127.

## License

MIT, see [LICENSE](LICENSE). Liangchao Deng (邓良超).
