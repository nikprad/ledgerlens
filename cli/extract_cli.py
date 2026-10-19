"""
LedgerLens Extraction CLI.
Extracts handwritten bills and shop ledgers into structured financial transactions.
"""

import sys
import os
import argparse
import json

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Add project root to sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.extractor import extract_ledger_from_image
from backend.config import settings

def main():
    parser = argparse.ArgumentParser(description="LedgerLens Local Vision Extraction CLI")
    parser.add_argument("image", nargs="?", default=os.path.join(BASE_DIR, "samples", "sample_1_kiranastore.png"),
                        help="Path to receipt or ledger image (default: sample_1_kiranastore.png)")
    parser.add_argument("--json", action="store_true", help="Output raw JSON only")
    parser.add_argument("--model", type=str, default=None, help="Override Gemma model tag")
    args = parser.parse_args()

    image_path = args.image
    if not os.path.exists(image_path):
        print(f"Error: Image not found at {image_path}", file=sys.stderr)
        sys.exit(1)

    if args.model:
        settings.GEMMA_VISION_MODEL = args.model

    if not args.json:
        print("=" * 70)
        print(" LedgerLens Local-First Vision Extractor (Gemma Multimodal)")
        print(f" Model: {settings.GEMMA_VISION_MODEL} | Base URL: {settings.OLLAMA_BASE_URL}")
        print(f" Image: {os.path.basename(image_path)}")
        print("=" * 70)

    try:
        response = extract_ledger_from_image(image_path, image_name=os.path.basename(image_path))
    except Exception as e:
        print(f"Extraction failed: {e}", file=sys.stderr)
        sys.exit(1)

    if args.json:
        print(response.model_dump_json(indent=2))
        return

    print(f"\nExtracted {len(response.items)} entries in {response.latency_ms:.1f}ms (Tokens: ~{response.token_count}):\n")
    print(f"{'Date':<12} | {'Party':<22} | {'Item':<28} | {'Qty':<5} | {'Amount':<10} | {'Type':<7} | {'Conf':<6} | Review")
    print("-" * 115)
    
    for item in response.items:
        review_flag = "[REVIEW]" if item.flagged or item.confidence < 0.7 else "OK"
        amount_str = f"Rs {item.amount:,.2f}"
        print(f"{item.date:<12} | {item.party[:20]:<22} | {item.item[:26]:<28} | {item.quantity:<5.1f} | {amount_str:<10} | {item.type:<7} | {item.confidence:<6.2f} | {review_flag}")
        if item.flag_reason:
            print(f"   -> Flag Reason: {item.flag_reason}")

    print("-" * 115)
    print(f"Status: {response.status.upper()} | Model used: {response.model} | Retried: {response.retried}")
    print("Logged to: observability.json\n")

if __name__ == "__main__":
    main()
