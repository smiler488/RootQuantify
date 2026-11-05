"""
RootQuantify - semi-automatic segmentation and measurement of root scans.

For each image in a folder:
1. outline the root region with a polygon (right window, original on the left);
2. the region is segmented automatically: background estimated by a
   morphological closing, subtracted, normalised and thresholded, so roots
   come out black on white;
3. fix the mask by hand with a brush (draw / erase / undo);
4. the mask is saved and root traits are measured: projected area, total
   length (skeleton, Kimura et al. 1999), mean diameter and tip count.

All traits go to ``root_traits.csv`` in the output folder. Give ``--dpi`` to
get millimetres instead of pixels.

Keys
----
ROI window:        left click = add vertex, c = confirm, r = reset, s = skip image, Esc = quit
Correction window: d = draw (root), e = erase, + / - = brush size, u = undo, q = finish

Author: Liangchao Deng (邓良超)
License: MIT
"""

import argparse
import csv
import shutil
import sys
from pathlib import Path

import cv2
import numpy as np

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}
WIN_ORIG = "Original image"
WIN_ROI = "ROI operations"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def screen_size():
    """Screen size in pixels via Tk (works on Windows, macOS and Linux)."""
    try:
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        size = root.winfo_screenwidth(), root.winfo_screenheight()
        root.destroy()
        return size
    except Exception:
        return 1920, 1080


def ask_folder():
    """Folder picker; returns None when cancelled or Tk is unavailable."""
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        path = filedialog.askdirectory(title="Select the folder with root images")
        root.destroy()
        return Path(path) if path else None
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Image processing (no GUI, can be imported and tested)
# ---------------------------------------------------------------------------

def segment_roots(roi_bgr, roi_mask=None, kernel_size=50, threshold=30):
    """Binary root image of a region: roots 0 (black), background 255 (white).

    The background is estimated with a grey-level closing (roots are darker
    than the background and thinner than ``kernel_size``), subtracted from
    the image, stretched to 0-255 and thresholded at ``threshold``.
    Pixels outside ``roi_mask`` are set to background.
    """
    gray = cv2.cvtColor(roi_bgr, cv2.COLOR_BGR2GRAY)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_size, kernel_size))
    background = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)
    diff = cv2.subtract(background, gray)
    norm = cv2.normalize(diff, None, 0, 255, cv2.NORM_MINMAX)
    _, roots = cv2.threshold(norm, threshold, 255, cv2.THRESH_BINARY)
    binary = cv2.bitwise_not(roots)
    if roi_mask is not None:
        binary[roi_mask == 0] = 255
    return binary


def skeletonize(mask):
    """Morphological skeleton of a boolean mask (OpenCV only, no extra deps)."""
    if hasattr(cv2, "ximgproc"):
        return cv2.ximgproc.thinning(mask.astype(np.uint8) * 255) > 0
    img = mask.astype(np.uint8) * 255
    skel = np.zeros_like(img)
    element = cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3))
    while cv2.countNonZero(img):
        eroded = cv2.erode(img, element)
        opened = cv2.dilate(eroded, element)
        skel |= cv2.subtract(img, opened)
        img = eroded
    return skel > 0


def skeleton_length(skel):
    """Root length in pixels from a one-pixel skeleton (Kimura et al., 1999).

    No = number of horizontal / vertical neighbour pairs, Nd = number of
    diagonal pairs. A diagonal pair is only counted when neither pixel that
    would join it orthogonally is set, so staircase corners are not counted
    twice. Length = sqrt(Nd^2 + (Nd + No/2)^2) + No/2, which is exact for
    0 and 45 degree lines and within a few per cent for curved roots.

    Kimura, K., Kikuchi, S. & Yamasaki, S. (1999). Accurate root length
    measurement by image analysis. Plant and Soil, 216, 117-127.
    """
    s = np.pad(skel.astype(bool), 1)
    n_o = np.count_nonzero(s[:, :-1] & s[:, 1:]) + np.count_nonzero(s[:-1, :] & s[1:, :])
    a, b = s[:-1, :-1], s[1:, 1:]        # down-right pair
    c, d = s[:-1, 1:], s[1:, :-1]        # down-left pair
    n_d = (np.count_nonzero(a & b & ~c & ~d) +
           np.count_nonzero(c & d & ~a & ~b))
    return float(np.sqrt(n_d ** 2 + (n_d + n_o / 2.0) ** 2) + n_o / 2.0)


def count_tips(skel):
    """Skeleton end points (pixels with exactly one 8-neighbour)."""
    s = skel.astype(np.uint8)
    neighbours = cv2.filter2D(s, -1, np.ones((3, 3), np.float32), borderType=cv2.BORDER_CONSTANT) - s
    return int(np.count_nonzero((s == 1) & (neighbours == 1)))


def measure_roots(binary, dpi=None, min_object_px=20):
    """Root traits from a binary image (roots black).

    Objects smaller than ``min_object_px`` pixels are ignored as dust.
    With ``dpi`` the lengths are in mm and the area in mm^2, otherwise in pixels.
    """
    roots = (binary < 128).astype(np.uint8)
    n, labels, stats, _ = cv2.connectedComponentsWithStats(roots, connectivity=8)
    keep = np.zeros(n, bool)
    keep[1:] = stats[1:, cv2.CC_STAT_AREA] >= min_object_px
    roots = keep[labels]

    area_px = int(roots.sum())
    skel = skeletonize(roots)
    length_px = float(skeleton_length(skel))
    tips = count_tips(skel)
    # mean diameter = area / length (cylinder seen from the side)
    diameter_px = area_px / length_px if length_px > 0 else 0.0

    scale = 25.4 / dpi if dpi else 1.0
    unit = "mm" if dpi else "px"
    return {
        f"area_{unit}2": area_px * scale ** 2,
        f"length_{unit}": length_px * scale,
        f"mean_diameter_{unit}": diameter_px * scale,
        "tips": tips,
        "objects": int(keep.sum()),
    }


# ---------------------------------------------------------------------------
# Interactive steps
# ---------------------------------------------------------------------------

def select_polygon(image):
    """Collect polygon vertices in the ROI window.

    Returns the list of points, [] to skip this image, or None to quit.
    """
    points = []
    view = image.copy()

    def redraw():
        nonlocal view
        view = image.copy()
        if points:
            cv2.polylines(view, [np.array(points, np.int32)], False, (255, 0, 0), 2, cv2.LINE_AA)
            for pt in points:
                cv2.circle(view, pt, 3, (0, 0, 255), -1, cv2.LINE_AA)
        cv2.imshow(WIN_ROI, view)

    def on_click(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            points.append((x, y))
            redraw()

    cv2.imshow(WIN_ROI, view)
    cv2.setMouseCallback(WIN_ROI, on_click)
    try:
        while True:
            key = cv2.waitKey(0) & 0xFF
            if key == ord("c"):
                if len(points) >= 3:
                    return points
                print("  need at least 3 vertices")
            elif key == ord("r"):
                points.clear()
                redraw()
            elif key == ord("s"):
                return []
            elif key == 27:  # Esc
                return None
    finally:
        cv2.setMouseCallback(WIN_ROI, lambda *a: None)


def manual_correction(image, brush_size=5):
    """Brush editing of the binary image. d = draw roots, e = erase, u = undo, q = done."""
    canvas = image.copy()
    state = {"drawing": False, "color": (0, 0, 0), "mode": "draw", "brush": brush_size, "pos": None}
    undo = [canvas.copy()]

    def on_mouse(event, x, y, flags, param):
        state["pos"] = (x, y)
        if event == cv2.EVENT_LBUTTONDOWN:
            state["drawing"] = True
        if state["drawing"] and event in (cv2.EVENT_LBUTTONDOWN, cv2.EVENT_MOUSEMOVE):
            cv2.circle(canvas, (x, y), state["brush"], state["color"], -1, cv2.LINE_AA)
        elif event == cv2.EVENT_LBUTTONUP and state["drawing"]:
            state["drawing"] = False
            undo.append(canvas.copy())

    cv2.setMouseCallback(WIN_ROI, on_mouse)
    while True:
        view = canvas.copy()
        if state["pos"] is not None:
            cv2.circle(view, state["pos"], state["brush"], (0, 255, 0), 1, cv2.LINE_AA)
        cv2.putText(view, f"{state['mode']} | brush {state['brush']} | d/e/+/-/u, q = done",
                    (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2, cv2.LINE_AA)
        cv2.imshow(WIN_ROI, view)
        key = cv2.waitKey(15) & 0xFF
        if key == ord("d"):
            state.update(mode="draw", color=(0, 0, 0))
        elif key == ord("e"):
            state.update(mode="erase", color=(255, 255, 255))
        elif key in (ord("+"), ord("=")):
            state["brush"] += 2
        elif key == ord("-"):
            state["brush"] = max(1, state["brush"] - 2)
        elif key == ord("u") and len(undo) > 1:
            undo.pop()
            canvas = undo[-1].copy()
        elif key == ord("q"):
            break
    cv2.setMouseCallback(WIN_ROI, lambda *a: None)
    return canvas


# ---------------------------------------------------------------------------
# Batch loop
# ---------------------------------------------------------------------------

def append_row(csv_path, row):
    new = not csv_path.exists()
    with open(csv_path, "a", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(row.keys()))
        if new:
            writer.writeheader()
        writer.writerow(row)


def process_folder(folder, out_dir=None, dpi=None, kernel_size=50, threshold=30,
                   move_originals=True):
    folder = Path(folder)
    out_dir = Path(out_dir) if out_dir else folder / "output"
    done_dir = folder / "processed_original"
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / "root_traits.csv"

    files = sorted(p for p in folder.iterdir() if p.suffix.lower() in IMAGE_EXTENSIONS)
    if not files:
        print(f"No images found in {folder}")
        return

    sw, sh = screen_size()
    win_w, win_h = sw // 2 - 100, sh - 100

    for i, path in enumerate(files, 1):
        img = cv2.imread(str(path))
        if img is None:
            print(f"Cannot read {path.name}, skipped.")
            continue
        print(f"[{i}/{len(files)}] {path.name}: click the outline, c = confirm, r = reset, s = skip, Esc = quit")

        preview = img.copy()
        cv2.putText(preview, path.name, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
        for name, x in ((WIN_ORIG, 50), (WIN_ROI, sw // 2 + 50)):
            cv2.namedWindow(name, cv2.WINDOW_NORMAL)
            cv2.resizeWindow(name, win_w, win_h)
            cv2.moveWindow(name, x, 10)
        cv2.imshow(WIN_ORIG, preview)

        points = select_polygon(img)
        if points is None:
            print("Stopped by user.")
            break
        if not points:
            print("  skipped")
            continue

        poly = np.array(points, np.int32).reshape(-1, 1, 2)
        mask = np.zeros(img.shape[:2], np.uint8)
        cv2.fillPoly(mask, [poly], 255)
        x, y, w, h = cv2.boundingRect(poly)
        binary = segment_roots(img[y:y + h, x:x + w], mask[y:y + h, x:x + w], kernel_size, threshold)

        print("  correct the mask: d = draw, e = erase, +/- = brush, u = undo, q = done")
        corrected = manual_correction(cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR))
        corrected_gray = cv2.cvtColor(corrected, cv2.COLOR_BGR2GRAY)

        out_file = out_dir / f"processed-{path.name}"
        cv2.imwrite(str(out_file), corrected_gray)
        traits = measure_roots(corrected_gray, dpi=dpi)
        append_row(csv_path, {"image": path.name, **traits})
        print(f"  saved {out_file.name}; " + ", ".join(f"{k}={v:.2f}" if isinstance(v, float) else f"{k}={v}"
                                                     for k, v in traits.items()))

        if move_originals:
            done_dir.mkdir(exist_ok=True)
            shutil.move(str(path), str(done_dir / path.name))

    cv2.destroyAllWindows()
    print(f"Done. Traits in {csv_path}")


def main(argv=None):
    ap = argparse.ArgumentParser(description="Segment and measure root images, one folder at a time.")
    ap.add_argument("folder", nargs="?", help="folder with images (a dialog opens if omitted)")
    ap.add_argument("-o", "--out", help="output folder (default: <folder>/output)")
    ap.add_argument("--dpi", type=float, help="scan resolution; report mm instead of pixels")
    ap.add_argument("--kernel", type=int, default=50,
                    help="background kernel size in px, larger than the thickest root (default: 50)")
    ap.add_argument("--threshold", type=int, default=30,
                    help="threshold on the normalised difference image, 0-255 (default: 30)")
    ap.add_argument("--keep-originals", action="store_true",
                    help="do not move finished images to processed_original/")
    args = ap.parse_args(argv)

    folder = Path(args.folder) if args.folder else ask_folder()
    if folder is None or not folder.is_dir():
        sys.exit("No valid image folder given.")
    process_folder(folder, args.out, args.dpi, args.kernel, args.threshold,
                   move_originals=not args.keep_originals)


if __name__ == "__main__":
    main()
