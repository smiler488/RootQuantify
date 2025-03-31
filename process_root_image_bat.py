import cv2
import numpy as np
import os
import shutil
import ctypes

# Function to get screen resolution on Windows
def get_screen_resolution():
    try:
        user32 = ctypes.windll.user32
        user32.SetProcessDPIAware()  # For Windows 10/8/7
        width = user32.GetSystemMetrics(0)
        height = user32.GetSystemMetrics(1)
        return width, height
    except Exception as e:
        return 1920, 1080  # Fallback resolution

# Set folder paths (modify these paths as needed)
folder_path = '/Users/liangchaodeng/Documents/VScode/root quantify'  # Folder containing images
output_folder = 'output'  # Folder to save processed ROI images
processed_folder = os.path.join(folder_path, 'processed_original')  # Folder to move original images after processing

# Create output folders if they don't exist
if not os.path.exists(output_folder):
    os.makedirs(output_folder)
if not os.path.exists(processed_folder):
    os.makedirs(processed_folder)

# Get all image files from the folder (supported formats: jpg, jpeg, png, bmp, tif, tiff)
image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff']
image_files = [f for f in os.listdir(folder_path) if os.path.splitext(f)[1].lower() in image_extensions]

# Get screen resolution and define window sizes/positions
screen_width, screen_height = get_screen_resolution()
left_win_width = screen_width // 2 - 100
right_win_width = screen_width // 2 - 100
win_height = screen_height - 100
# 将窗口上移，将 y 坐标设置为 10，避免靠近屏幕下部
left_win_pos = (50, 10)
right_win_pos = (screen_width // 2 + 50, 10)
# --- ROI Selection Function (Polygon) ---
def select_polygon(image):
    polygon_points = []

    def redraw(img, points):
        temp_img = img.copy()
        if len(points) > 0:
            cv2.polylines(temp_img, [np.array(points, dtype=np.int32)], False, (255, 0, 0), 2, cv2.LINE_AA)
            for pt in points:
                cv2.circle(temp_img, pt, 3, (0, 0, 255), -1, cv2.LINE_AA)
        return temp_img

    temp_img = image.copy()

    def click_event(event, x, y, flags, param):
        nonlocal polygon_points, temp_img
        if event == cv2.EVENT_LBUTTONDOWN:
            polygon_points.append((x, y))
            temp_img = redraw(image, polygon_points)
            cv2.imshow("ROI Operations", temp_img)

    cv2.imshow("ROI Operations", temp_img)
    cv2.setMouseCallback("ROI Operations", click_event)

    while True:
        key = cv2.waitKey(0) & 0xFF
        if key == ord('c'):
            if len(polygon_points) > 2:
                cv2.polylines(temp_img, [np.array(polygon_points, dtype=np.int32)], True, (255, 0, 0), 2, cv2.LINE_AA)
                cv2.imshow("ROI Operations", temp_img)
            break
        elif key == ord('r'):
            polygon_points = []
            temp_img = image.copy()
            cv2.imshow("ROI Operations", temp_img)
    cv2.setMouseCallback("ROI Operations", lambda *args: None)
    return polygon_points

# --- Manual Correction Function with Drag and Undo ---
def manual_correction(image):
    manual_img = image.copy()
    drawing = False
    mode = 'draw'  # 'draw' for black, 'erase' for white
    brush_size = 5
    current_color = (0, 0, 0)
    mouse_pos = None
    # Undo stack to store history for undo
    undo_stack = [manual_img.copy()]

    def draw_callback(event, x, y, flags, param):
        nonlocal manual_img, drawing, mode, brush_size, current_color, mouse_pos, undo_stack
        mouse_pos = (x, y)
        if event == cv2.EVENT_LBUTTONDOWN:
            drawing = True
            cv2.circle(manual_img, (x, y), brush_size, current_color, -1, cv2.LINE_AA)
        elif event == cv2.EVENT_MOUSEMOVE:
            if drawing:
                cv2.circle(manual_img, (x, y), brush_size, current_color, -1, cv2.LINE_AA)
        elif event == cv2.EVENT_LBUTTONUP:
            drawing = False
            undo_stack.append(manual_img.copy())

    cv2.namedWindow("ROI Operations", cv2.WINDOW_NORMAL)
    cv2.setMouseCallback("ROI Operations", draw_callback)

    while True:
        temp = manual_img.copy()
        if mouse_pos is not None:
            cv2.circle(temp, mouse_pos, brush_size, (0, 255, 0), 1, cv2.LINE_AA)
        info_text = (f"Mode: {mode} (d: draw, e: erase, +: increase, -: decrease, u: undo, q: finish). "
                     f"Brush Size: {brush_size}")
        cv2.putText(temp, info_text, (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2, cv2.LINE_AA)
        cv2.imshow("ROI Operations", temp)
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
        elif key == ord('u'):
            if len(undo_stack) > 1:
                undo_stack.pop()
                manual_img = undo_stack[-1].copy()
        elif key == ord('q'):
            break
    cv2.setMouseCallback("ROI Operations", lambda *args: None)
    return manual_img

# --- Main Processing Loop ---
for idx, file_name in enumerate(image_files):
    image_path = os.path.join(folder_path, file_name)
    img = cv2.imread(image_path)
    if img is None:
        print(f"Unable to read {file_name}, skipping.")
        continue

    # --- Left Window: Display Original Image with Name ---
    original_preview = img.copy()
    cv2.putText(original_preview, f"Image: {file_name}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
    cv2.namedWindow("Original Image", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Original Image", left_win_width, win_height)
    cv2.imshow("Original Image", original_preview)
    cv2.moveWindow("Original Image", left_win_pos[0], left_win_pos[1])

    # --- Right Window: ROI Operations ---
    cv2.namedWindow("ROI Operations", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("ROI Operations", right_win_width, win_height)
    cv2.moveWindow("ROI Operations", right_win_pos[0], right_win_pos[1])

    print(f"Processing image: {file_name}")
    print("Right window: Please click to select polygon vertices. Press 'c' to confirm, 'r' to reset.")
    points = select_polygon(img)
    if len(points) < 3:
        print(f"Not enough points selected for {file_name}, skipping.")
        cv2.destroyWindow("ROI Operations")
        cv2.destroyWindow("Original Image")
        continue

    # Create polygon mask
    mask = np.zeros(img.shape[:2], dtype=np.uint8)
    pts = np.array(points, dtype=np.int32).reshape((-1, 1, 2))
    cv2.fillPoly(mask, [pts], 255)

    # Extract ROI from bounding rectangle of polygon
    x, y, w, h = cv2.boundingRect(pts)
    roi_img = img[y:y+h, x:x+w]
    roi_mask = mask[y:y+h, x:x+w]

    # Digital image processing on ROI
    gray_roi = cv2.cvtColor(roi_img, cv2.COLOR_BGR2GRAY)
    kernel_size = 50  # Adjust as needed
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_size, kernel_size))
    background = cv2.morphologyEx(gray_roi, cv2.MORPH_CLOSE, kernel)
    diff = cv2.subtract(background, gray_roi)
    norm_diff = cv2.normalize(diff, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX)
    _, thresh = cv2.threshold(norm_diff, 30, 255, cv2.THRESH_BINARY)
    inverted = cv2.bitwise_not(thresh)
    processed_roi = cv2.cvtColor(inverted, cv2.COLOR_GRAY2BGR)
    processed_roi[roi_mask == 0] = [255, 255, 255]

    # Briefly display processed ROI in right window before manual correction
    cv2.imshow("ROI Operations", processed_roi)
    cv2.waitKey(500)

    print("Right window: Now perform manual correction (d: draw, e: erase, + / -: adjust, u: undo, q: finish).")
    corrected_roi = manual_correction(processed_roi)

    # Final preview in right window
    cv2.imshow("ROI Operations", corrected_roi)
    print("Press any key to continue to the next image.")
    cv2.waitKey(0)

    # Save processed ROI image
    output_file = os.path.join(output_folder, "processed-" + file_name)
    cv2.imwrite(output_file, corrected_roi)
    print(f"Saved processed image to {output_file}")

    # Move original image to processed_folder
    shutil.move(image_path, os.path.join(processed_folder, file_name))
    print(f"Moved original image {file_name} to {processed_folder}")

    cv2.destroyWindow("ROI Operations")
    cv2.destroyWindow("Original Image")

print("Batch processing completed!")