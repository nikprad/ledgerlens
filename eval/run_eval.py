"""
Evaluation Suite for LedgerLens.
Evaluates local multimodal vision extraction against hand-labeled ground truth datasets.
Calculates field-level accuracy (date, party, item, quantity, amount, type) and average latency per image.
"""

import os
import sys
import json
import time
from typing import List, Dict, Any, Tuple
from difflib import SequenceMatcher

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.extractor import extract_ledger_from_image
from backend.models import TransactionItem
from backend.config import settings

def string_similarity(a: str, b: str) -> float:
    """Compute normalized character sequence similarity between two strings."""
    return SequenceMatcher(None, str(a).strip().lower(), str(b).strip().lower()).ratio()

def match_items(
    extracted_items: List[TransactionItem],
    ground_truth: List[Dict[str, Any]]
) -> List[Tuple[Optional[TransactionItem], Optional[Dict[str, Any]]]]:
    """
    Greedily pair extracted items to ground truth items based on amount and item similarity.
    """
    pairs = []
    unmatched_gt = list(ground_truth)
    
    for ext in extracted_items:
        best_gt = None
        best_score = -1.0
        best_idx = -1

        for idx, gt in enumerate(unmatched_gt):
            # Similarity score based on amount proximity and item text
            amt_diff = abs(ext.amount - float(gt.get("amount", 0)))
            amt_score = 1.0 if amt_diff < 0.01 else max(0.0, 1.0 - (amt_diff / max(ext.amount, float(gt.get("amount", 1)), 1.0)))
            item_score = string_similarity(ext.item, str(gt.get("item", "")))
            total_score = 0.6 * amt_score + 0.4 * item_score

            if total_score > best_score:
                best_score = total_score
                best_gt = gt
                best_idx = idx

        if best_gt and best_score >= 0.4:
            pairs.append((ext, best_gt))
            unmatched_gt.pop(best_idx)
        else:
            pairs.append((ext, None))

    # Add remaining unmatched ground truths
    for gt in unmatched_gt:
        pairs.append((None, gt))

    return pairs

def evaluate_sample(image_path: str, gt_path: str) -> Dict[str, Any]:
    with open(gt_path, "r", encoding="utf-8") as f:
        ground_truth = json.load(f)

    start_time = time.time()
    response = extract_ledger_from_image(image_path, image_name=os.path.basename(image_path))
    latency_ms = (time.time() - start_time) * 1000

    pairs = match_items(response.items, ground_truth)
    total_gt = len(ground_truth)

    date_matches = 0
    party_matches = 0
    item_matches = 0
    qty_matches = 0
    amt_matches = 0
    type_matches = 0

    for ext, gt in pairs:
        if ext is not None and gt is not None:
            # Date match: exact YYYY-MM-DD
            if ext.date.strip() == str(gt.get("date", "")).strip():
                date_matches += 1

            # Party match: > 60% similarity or substring
            p_sim = string_similarity(ext.party, str(gt.get("party", "")))
            if p_sim >= 0.6 or ext.party.lower() in str(gt.get("party", "")).lower() or str(gt.get("party", "")).lower() in ext.party.lower():
                party_matches += 1

            # Item match: > 60% similarity
            i_sim = string_similarity(ext.item, str(gt.get("item", "")))
            if i_sim >= 0.6:
                item_matches += 1

            # Quantity match: within 0.1
            if abs(ext.quantity - float(gt.get("quantity", 1.0))) <= 0.1:
                qty_matches += 1

            # Amount match: within 1% or exact
            amt_diff = abs(ext.amount - float(gt.get("amount", 0.0)))
            if amt_diff <= max(1.0, 0.01 * float(gt.get("amount", 1.0))):
                amt_matches += 1

            # Type match: exact sale vs expense
            if ext.type.strip().lower() == str(gt.get("type", "")).strip().lower():
                type_matches += 1

    denom = max(total_gt, 1)
    return {
        "image": os.path.basename(image_path),
        "ground_truth_count": total_gt,
        "extracted_count": len(response.items),
        "latency_ms": round(latency_ms, 2),
        "date_acc": round(date_matches / denom * 100, 1),
        "party_acc": round(party_matches / denom * 100, 1),
        "item_acc": round(item_matches / denom * 100, 1),
        "quantity_acc": round(qty_matches / denom * 100, 1),
        "amount_acc": round(amt_matches / denom * 100, 1),
        "type_acc": round(type_matches / denom * 100, 1),
    }

def run_all_evaluations():
    samples_dir = os.path.join(BASE_DIR, "samples")
    files = sorted([f for f in os.listdir(samples_dir) if f.endswith(".png")])
    
    print("\n" + "=" * 90)
    print(" LedgerLens Ground-Truth Evaluation Suite")
    print(f" Model: {settings.GEMMA_VISION_MODEL} | Base URL: {settings.OLLAMA_BASE_URL}")
    print(" Evaluating field-level extraction accuracy on sample bills and handwritten ledgers")
    print("=" * 90 + "\n")

    results = []
    for f in files:
        base = os.path.splitext(f)[0]
        json_file = base + ".json"
        img_path = os.path.join(samples_dir, f)
        gt_path = os.path.join(samples_dir, json_file)

        if not os.path.exists(gt_path):
            continue

        res = evaluate_sample(img_path, gt_path)
        results.append(res)

    # Print results table
    print(f"{'Sample Image':<32} | {'GT':<3} | {'Ext':<3} | {'Date %':<7} | {'Party %':<7} | {'Item %':<7} | {'Qty %':<7} | {'Amt %':<7} | {'Type %':<7} | {'Latency':<8}")
    print("-" * 115)
    for r in results:
        lat_str = f"{r['latency_ms']:.0f}ms"
        print(f"{r['image'][:30]:<32} | {r['ground_truth_count']:<3} | {r['extracted_count']:<3} | {r['date_acc']:<7.1f} | {r['party_acc']:<7.1f} | {r['item_acc']:<7.1f} | {r['quantity_acc']:<7.1f} | {r['amount_acc']:<7.1f} | {r['type_acc']:<7.1f} | {lat_str:<8}")

    print("-" * 115)
    
    # Aggregates
    n = len(results)
    if n > 0:
        avg_date = sum(r["date_acc"] for r in results) / n
        avg_party = sum(r["party_acc"] for r in results) / n
        avg_item = sum(r["item_acc"] for r in results) / n
        avg_qty = sum(r["quantity_acc"] for r in results) / n
        avg_amt = sum(r["amount_acc"] for r in results) / n
        avg_type = sum(r["type_acc"] for r in results) / n
        avg_latency = sum(r["latency_ms"] for r in results) / n
        overall_acc = (avg_date + avg_party + avg_item + avg_qty + avg_amt + avg_type) / 6.0

        print(f"{'AVERAGE / OVERALL':<32} | {'-':<3} | {'-':<3} | {avg_date:<7.1f} | {avg_party:<7.1f} | {avg_item:<7.1f} | {avg_qty:<7.1f} | {avg_amt:<7.1f} | {avg_type:<7.1f} | {avg_latency:.0f}ms")
        print("=" * 115)
        print(f"\n>> OVERALL FIELD-LEVEL ACCURACY: {overall_acc:.1f}%")
        print(f">> AVERAGE EXTRACTION LATENCY:   {avg_latency:.1f}ms per image")
        print(f">> TOTAL SAMPLES EVALUATED:       {n} handwritten/printed ledger pages\n")

        # Save to eval/eval_results.json
        out_path = os.path.join(BASE_DIR, "eval", "eval_results.json")
        summary_obj = {
            "model": settings.GEMMA_VISION_MODEL,
            "samples_count": n,
            "overall_accuracy_pct": round(overall_acc, 2),
            "average_latency_ms": round(avg_latency, 2),
            "field_accuracies": {
                "date_pct": round(avg_date, 2),
                "party_pct": round(avg_party, 2),
                "item_pct": round(avg_item, 2),
                "quantity_pct": round(avg_qty, 2),
                "amount_pct": round(avg_amt, 2),
                "type_pct": round(avg_type, 2),
            },
            "per_sample_results": results
        }
        with open(out_path, "w", encoding="utf-8") as out_f:
            json.dump(summary_obj, out_f, indent=2)
        print(f"Results saved to: {out_path}\n")

if __name__ == "__main__":
    run_all_evaluations()
