import cv2
import numpy as np
import os
# pip install opencv-python numpy

# Set folder paths (modify these paths as needed)
folder_path = '/Users/liangchaodeng/Documents/VScode/root quantify'  # Folder containing images
output_folder = 'output'  # Output folder

# Create the output folder if it doesn't exist
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# Get all image files from the folder (supported formats: jpg, jpeg, png, bmp)
image_extensions = ['.jpg', '.jpeg', '.png', '.bmp']
image_files = [f for f in os.listdir(folder_path) if os.path.splitext(f)[1].lower() in image_extensions]

# Improved polygon selection function with anti-aliasing
def select_polygon(image):
    polygon_points = []

    # Redraw the image with current polygon points
    def redraw(img, points):
        temp_img = img.copy()
        if len(points) > 0:
            # Draw polylines using anti-aliasing
            cv2.polylines(temp_img, [np.array(points, dtype=np.int32)], False, (255, 0, 0), 2, cv2.LINE_AA)
            # Draw each point
            for pt in points:
                cv2.circle(temp_img, pt, 3, (0, 0, 255), -1, cv2.LINE_AA)
        return temp_img

    temp_img = image.copy()

    def click_event(event, x, y, flags, param):
        nonlocal polygon_points, temp_img
        if event == cv2.EVENT_LBUTTONDOWN:
            polygon_points.append((x, y))
            temp_img = redraw(image, polygon_points)
            cv2.imshow("Select Polygon", temp_img)

    cv2.imshow("Select Polygon", temp_img)
    cv2.setMouseCallback("Select Polygon", click_event)

    while True:
        key = cv2.waitKey(0) & 0xFF
        if key == ord('c'):
            if len(polygon_points) > 2:
                # Close the polygon for a complete shape
                cv2.polylines(temp_img, [np.array(polygon_points, dtype=np.int32)], True, (255, 0, 0), 2, cv2.LINE_AA)
                cv2.imshow("Select Polygon", temp_img)
            break
        elif key == ord('r'):
            # Reset polygon selection
            polygon_points = []
            temp_img = image.copy()
            cv2.imshow("Select Polygon", temp_img)
    cv2.destroyWindow("Select Polygon")
    return polygon_points

# Manual correction function with adjustable brush size and mouse brush indicator
def manual_correction(image):
    manual_img = image.copy()
    drawing = False
    mode = 'draw'  # 'draw' adds black, 'erase' adds white
    brush_size = 5
    current_color = (0, 0, 0)  # Black for draw mode
    mouse_pos = None

    def draw_callback(event, x, y, flags, param):
        nonlocal manual_img, drawing, mode, brush_size, current_color, mouse_pos
        mouse_pos = (x, y)  # Update current mouse position
        if event == cv2.EVENT_LBUTTONDOWN:
            drawing = True
            cv2.circle(manual_img, (x, y), brush_size, current_color, -1, cv2.LINE_AA)
        elif event == cv2.EVENT_MOUSEMOVE:
            if drawing:
                cv2.circle(manual_img, (x, y), brush_size, current_color, -1, cv2.LINE_AA)
        elif event == cv2.EVENT_LBUTTONUP:
            drawing = False

    cv2.namedWindow("Manual Correction")
    cv2.setMouseCallback("Manual Correction", draw_callback)

    while True:
        temp = manual_img.copy()
        # Draw a brush size indicator circle at the current mouse position
        if mouse_pos is not None:
            cv2.circle(temp, mouse_pos, brush_size, (0, 255, 0), 1, cv2.LINE_AA)
        info_text = f"Mode: {mode} (press 'd' for draw, 'e' for erase, '+' to increase, '-' to decrease, 'q' to finish). Brush Size: {brush_size}"
        cv2.putText(temp, info_text, (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2, cv2.LINE_AA)
        cv2.imshow("Manual Correction", temp)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('d'):
            mode = 'draw'
            current_color = (0, 0, 0)
        elif key == ord('e'):
            mode = 'erase'
            current_color = (255, 255, 255)
        elif key == ord('+') or key == ord('='):
            brush_size += 2
        elif key == ord('-'):
            brush_size = max(1, brush_size - 2)
        elif key == ord('q'):
            break
    cv2.destroyWindow("Manual Correction")
    return manual_img

# Process each image in the folder
for idx, file_name in enumerate(image_files):
    image_path = os.path.join(folder_path, file_name)
    img = cv2.imread(image_path)
    if img is None:
        print(f"Unable to read {file_name}, skipping.")
        continue

    # For each image, require user to select a polygon ROI
    print(f"Processing {file_name}: Please click to select polygon vertices. Press 'c' to confirm, 'r' to reset.")
    points = select_polygon(img)
    if len(points) < 3:
        print(f"Not enough points selected for {file_name}, skipping.")
        continue

    # Create a polygon mask
    mask = np.zeros(img.shape[:2], dtype=np.uint8)
    pts = np.array(points, dtype=np.int32).reshape((-1, 1, 2))
    cv2.fillPoly(mask, [pts], 255)

    # Get the bounding rectangle of the polygon
    x, y, w, h = cv2.boundingRect(pts)
    roi_img = img[y:y+h, x:x+w]
    roi_mask = mask[y:y+h, x:x+w]

    # Convert the ROI to grayscale
    gray_roi = cv2.cvtColor(roi_img, cv2.COLOR_BGR2GRAY)

    # Estimate background using morphological closing (adjust kernel_size as needed)
    kernel_size = 50  
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_size, kernel_size))
    background = cv2.morphologyEx(gray_roi, cv2.MORPH_CLOSE, kernel)

    # Subtract the background from the grayscale ROI to reduce shadows
    diff = cv2.subtract(background, gray_roi)

    # Normalize the difference image to 0-255 for further processing
    norm_diff = cv2.normalize(diff, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX)

    # Apply thresholding to remove weak shadows (adjust threshold as needed)
    _, thresh = cv2.threshold(norm_diff, 30, 255, cv2.THRESH_BINARY)

    # Invert the image so that roots are black and background is white
    inverted = cv2.bitwise_not(thresh)

    # Convert the processed ROI to BGR (for merging with the original image)
    processed_roi = cv2.cvtColor(inverted, cv2.COLOR_GRAY2BGR)

    # Set areas outside the polygon to white
    processed_roi[roi_mask == 0] = [255, 255, 255]

    # Allow manual correction before previewing
    corrected_roi = manual_correction(processed_roi)

    # Preview the corrected ROI; press any key to proceed to the next image
    cv2.imshow("Processed ROI Preview", corrected_roi)
    print("Press any key to continue to the next image.")
    cv2.waitKey(0)
    cv2.destroyWindow("Processed ROI Preview")

    # Save the corrected ROI image with the filename "processed-" + original filename
    output_file = os.path.join(output_folder, "processed-" + file_name)
    cv2.imwrite(output_file, corrected_roi)
    print(f"Saved {output_file}")

print("Batch processing completed!")