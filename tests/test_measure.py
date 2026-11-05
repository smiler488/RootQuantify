"""Accuracy tests for segmentation and root measurements on synthetic scans."""
import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import RootImager as R  # noqa: E402


def blank(h=300, w=300):
    return np.full((h, w), 255, np.uint8)


def length_of(img):
    return R.measure_roots(img)["length_px"]


def test_straight_root():
    img = blank()
    cv2.line(img, (20, 150), (280, 150), 0, 3)
    assert abs(length_of(img) - 260) / 260 < 0.04


def test_oblique_root():
    img = blank()
    cv2.line(img, (20, 250), (280, 100), 0, 3)
    true = np.hypot(260, 150)
    assert abs(length_of(img) - true) / true < 0.04


def test_ring_root():
    img = blank()
    cv2.circle(img, (150, 150), 80, 0, 3)
    true = 2 * np.pi * 80
    assert abs(length_of(img) - true) / true < 0.05


def test_dpi_scaling_and_tips():
    img = blank()
    cv2.line(img, (20, 150), (280, 150), 0, 3)
    px = R.measure_roots(img)
    mm = R.measure_roots(img, dpi=600)
    assert abs(mm["length_mm"] - px["length_px"] * 25.4 / 600) < 1e-9
    assert px["tips"] == 2 and px["objects"] == 1


def test_segmentation_with_uneven_background():
    gray = np.full((300, 600), 200, np.uint8) - np.linspace(0, 40, 600)[None, :].astype(np.uint8)
    cv2.line(gray, (100, 100), (500, 100), 60, 6)
    binary = R.segment_roots(cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR))
    traits = R.measure_roots(binary)
    assert traits["objects"] == 1
    assert abs(traits["length_px"] - 400) / 400 < 0.05


def test_dust_is_ignored():
    img = blank()
    cv2.line(img, (20, 150), (280, 150), 0, 3)
    cv2.circle(img, (50, 50), 1, 0, -1)
    assert R.measure_roots(img)["objects"] == 1
