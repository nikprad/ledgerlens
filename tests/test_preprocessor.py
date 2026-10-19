"""
Unit tests for image preprocessor.
"""

import os
from PIL import Image
from backend.preprocessor import preprocess_ledger_image

def test_preprocessor_resizing_and_enhancement():
    # Create large dummy test image
    img = Image.new("RGB", (2000, 1500), color=(250, 240, 230))
    processed_img, b64_str = preprocess_ledger_image(img, max_dimension=1000)
    
    w, h = processed_img.size
    assert max(w, h) <= 1000
    assert len(b64_str) > 0
    assert processed_img.mode == "RGB"
