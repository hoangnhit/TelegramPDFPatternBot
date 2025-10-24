import cv2
import numpy as np
import svgwrite
from pdf2image import convert_from_path
from PIL import Image
import cairosvg

def _pil_to_bgr(pil_img):
    return cv2.cvtColor(np.array(pil_img.convert("RGB")), cv2.COLOR_RGB2BGR)

def render_pdf_to_images(pdf_path: str, dpi: int = 400):
    pages = convert_from_path(pdf_path, dpi=dpi)
    return [_pil_to_bgr(p) for p in pages]

def preprocess(bgr: np.ndarray, invert: bool = True):
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    gray = cv2.bilateralFilter(gray, 7, 50, 50)
    mode = cv2.THRESH_BINARY_INV if invert else cv2.THRESH_BINARY
    bw = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, mode, 51, 8)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3,3))
    bw = cv2.morphologyEx(bw, cv2.MORPH_CLOSE, kernel, iterations=2)
    edges = cv2.Canny(bw, 50, 150)
    return edges

def extract_contours(edges: np.ndarray, min_len: int = 100):
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    return [c for c in contours if len(c) >= min_len]

def simplify_contour(cnt: np.ndarray, eps_ratio: float = 0.002):
    eps = eps_ratio * cv2.arcLength(cnt, True)
    return cv2.approxPolyDP(cnt, eps, True)

def contours_to_svg(contours, size_wh, stroke_width: float = 2.0):
    w, h = size_wh
    dwg = svgwrite.Drawing(size=(w, h))
    for c in contours:
        pts = c.reshape(-1, 2)
        d = [f"M {pts[0][0]} {pts[0][1]}"] + [f"L {x} {y}" for (x, y) in pts[1:]] + ["Z"]
        path_cmd = " ".join(d)
        dwg.add(dwg.path(d=path_cmd, fill="none", stroke="black", stroke_width=stroke_width))
    return dwg.tostring()

def svg_to_pdf_bytes(svg_str: str):
    return cairosvg.svg2pdf(bytestring=svg_str.encode("utf-8"))

def process_image_to_pdf_page(bgr: np.ndarray, invert: bool = True, stroke: float = 2.0):
    h, w = bgr.shape[:2]
    edges = preprocess(bgr, invert)
    contours = extract_contours(edges)
    simp = [simplify_contour(c) for c in contours]
    svg_str = contours_to_svg(simp, (w, h), stroke_width=stroke)
    return svg_to_pdf_bytes(svg_str)

def process_pdf_to_pdf(in_path: str, out_path: str, invert: bool = True, stroke: float = 2.0, dpi: int = 400):
    pages_bgr = render_pdf_to_images(in_path, dpi=dpi)
    pdf_pages = [process_image_to_pdf_page(bgr, invert, stroke) for bgr in pages_bgr]
    with open(out_path, "wb") as f:
        for p in pdf_pages:
            f.write(p)
    return out_path

def process_imagefile_to_pdf(img_path: str, out_path: str, invert: bool = True, stroke: float = 2.0):
    bgr = cv2.imread(img_path)
    pdf_bytes = process_image_to_pdf_page(bgr, invert, stroke)
    with open(out_path, "wb") as f:
        f.write(pdf_bytes)
    return out_path
