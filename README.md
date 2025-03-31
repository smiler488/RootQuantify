# Root Quantify

## Overview
Root Quantify is a Python-based tool for processing root system images. It supports:
- **Batch Processing:** Automatically iterates over all images in a selected folder.
- **Interactive ROI Selection:** In the right window, users can click to select polygon vertices for the region of interest (ROI), then press `c` to confirm or `r` to reset.
- **Digital Image Processing:** The tool performs background estimation, shadow removal, binarization, and inversion on the selected ROI so that the roots appear black on a white background.
- **Manual Correction:** In the right window, users can perform manual corrections with drag-and-draw functionality. The brush size is adjustable (using `+`/`-`), and you can undo the last operation by pressing `u` before finishing with `q`.
- **Dual Window Preview:** The left window displays the original image along with the image name, while the right window displays the ROI selection, image processing, and manual correction stages.
- **Automatic Archiving:** Processed images are saved in an `output` folder, and the original images are moved to a `processed_original` subfolder to avoid reprocessing.

## System Requirements
- Python 3.12 (or another version)
- [OpenCV](https://opencv.org/) (opencv-python)
- [NumPy](https://numpy.org/)
- [Tkinter](https://docs.python.org/3/library/tkinter.html) (usually included with Python)
- macOS or Windows (this script has been adjusted to run on both)

## Installation
Install the required dependencies using pip:
```bash
pip install opencv-python numpy