"""
Image Preprocessing Pipeline for LedgerLens.
Optimizes handwritten bills and ledger photos for small multimodal vision models
via resizing, grayscale conversion, and contrast/sharpness enhancement.
"""

import io
import base64
from PIL import Image, ImageOps, ImageEnhance
from typing import Tuple

def preprocess_ledger_image(
    image_input,
    max_dimension: int = 1280,
    contrast_factor: float = 1.8,
    sharpness_factor: float = 1.4,
    as_base64: bool = True
) -> Tuple[Image.Image, str]:
    """
    Preprocess image:
    1. Load image (from bytes, file path, or PIL Image)
    2. Resize preserving aspect ratio (max dimension 1280)
    3. Grayscale conversion for text/ink clarity
    4. Contrast enhancement to separate ink from paper texture
    5. Sharpness enhancement to improve stroke boundaries
    
    Returns:
        (PIL Image, base64_string)
    """
    if isinstance(image_input, str):
        img = Image.open(image_input)
    elif isinstance(image_input, bytes):
        img = Image.open(io.BytesIO(image_input))
    elif isinstance(image_input, Image.Image):
        img = image_input.copy()
    else:
        raise ValueError("Unsupported image input format")

    # Convert RGBA or CMYK to RGB
    if img.mode != "RGB":
        img = img.convert("RGB")

    # Resize preserving aspect ratio
    w, h = img.size
    if max(w, h) > max_dimension:
        scale = max_dimension / max(w, h)
        new_w = int(w * scale)
        new_h = int(h * scale)
        img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

    # Convert to Grayscale
    gray = ImageOps.grayscale(img)

    # Contrast enhancement
    enhancer = ImageEnhance.Contrast(gray)
    enhanced = enhancer.enhance(contrast_factor)

    # Sharpness enhancement
    sharp_enhancer = ImageEnhance.Sharpness(enhanced)
    final_img = sharp_enhancer.enhance(sharpness_factor)

    # Convert back to RGB for multimodal model compatibility
    final_rgb = final_img.convert("RGB")

    base64_str = ""
    if as_base64:
        buffered = io.BytesIO()
        final_rgb.save(buffered, format="JPEG", quality=92)
        base64_str = base64.b64encode(buffered.getvalue()).decode("utf-8")

    return final_rgb, base64_str
