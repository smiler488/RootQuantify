# Root Quantify

## Overview
**Root Quantify** is a Python-based tool designed for processing root system images. It supports:

- **Batch Processing:** Automatically iterates through all images in a selected folder.
- **Interactive ROI Selection:** In the right window, users click to select polygon vertices to define the region of interest (ROI). Press `c` to confirm or `r` to reset the selection.
- **Digital Image Processing:** The tool performs background estimation, shadow removal, binarization, and inversion on the selected ROI so that the roots appear black on a white background.
- **Manual Correction:** In the right window, users can manually correct the processed ROI by drawing or erasing. The brush size is adjustable (using `+`/`-`), and you can undo the last operation by pressing `u`. Press `q` when finished.
- **Dual-Window Preview:** The left window displays the original image along with its filename, while the right window handles ROI selection, image processing, and manual correction.
- **Automatic Archiving:** Processed images are saved in an `output` folder, and the original images are moved to a `processed_original` folder to prevent reprocessing.

## System Requirements
- Python 3.12 (or another compatible version)
- [OpenCV](https://opencv.org/) (opencv-python)
- [NumPy](https://numpy.org/)
- Tkinter (usually included with Python)
- macOS or Windows

## Installation
1.**Clone the Repository**
   Open your terminal and run:
   ```bash
   git clone https://github.com/smiler488/RootQuantify.git
   cd RootQuantify
   ```
2.**Install Dependencies**
   Use the provided requirements.txt file to install necessary libraries, Open your terminal and run:
   ```bash
   pip install -r requirements.txt
   ```

## How to Use
1.**Run the Application**
   Launch the script from your command line:
   ```bash
   python RootImager.py      
   ```
2.**Select the Image Folder**

When the program starts, a folder selection dialog will appear. Choose the folder containing the images you want to process. Supported image formats include JPG, JPEG, PNG, BMP, TIF, and TIFF.
   
3.**Dual-Window Workflow**

- Left Window (“Original Image”):Displays the original image along with its filename.
- ROI Selection:Click in the right window to select polygon vertices that define your ROI.Press `c` to confirm the selection, or press `r` to reset.
- Automatic Processing:Once confirmed, the selected ROI is processed (background estimation, shadow removal, thresholding, inversion) so that roots appear black on a white background.
- Manual Correction:The right window then enters manual correction mode. You can:Press `d` to switch to draw mode (black).Press `e `to switch to erase mode (white).Use `+` or `-` to adjust the brush size (a green circle indicates the current brush size at the mouse pointer).Press `u` to undo the last operation.Press `q` to finish manual correction.
- 5Once manual correction is complete, press any key to proceed to the next image.

4.**Output and Archiving**

- The corrected ROI is automatically saved in the output folder with a filename prefixed by processed-.
- The original image is moved to a processed_original folder to avoid processing it again.
  
5.**Completion**

When all images have been processed, the terminal will display “Batch processing completed!” You can then close the application.


