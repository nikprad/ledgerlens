# LedgerLens Evaluation Suite

This directory contains automated benchmark tools for evaluating multimodal vision extraction on handwritten shopkeeper ledgers and invoices.

## Overview

The evaluation harness in [`run_eval.py`](run_eval.py) runs the multimodal extraction pipeline against hand-labeled ground-truth JSON files located in [`../samples/`](../samples/).

### Metric Definitions
- **Date Accuracy**: Exact match on normalized `YYYY-MM-DD` representation.
- **Party Accuracy**: Normalized character sequence similarity $\ge 60\%$ or substring match with ground-truth vendor/customer name.
- **Item Accuracy**: Normalized character sequence similarity $\ge 60\%$ with ground-truth item/service description.
- **Quantity Accuracy**: Exact numeric quantity match within $\pm 0.1$.
- **Amount Accuracy**: Exact numerical total amount within $\pm 1\%$ or ₹1.0.
- **Type Accuracy**: Exact match on transaction category (`sale` vs `expense` / जमा vs खर्च).
- **Latency**: End-to-end extraction elapsed time in milliseconds per image.

## Benchmark Results

```text
==========================================================================================
 LedgerLens Ground-Truth Evaluation Suite
 Model: gemma3:4b | Base URL: http://localhost:11434
==========================================================================================

Sample Image                     | GT  | Ext | Date %  | Party % | Item %  | Qty %   | Amt %   | Type %  | Latency 
-------------------------------------------------------------------------------------------------------------------
sample_1_kiranastore.png         | 4   | 4   | 100.0   | 100.0   | 100.0   | 100.0   | 100.0   | 100.0   | 4256ms  
sample_2_chai_tea_bill.png       | 4   | 4   | 100.0   | 100.0   | 100.0   | 100.0   | 100.0   | 100.0   | 4091ms  
sample_3_hindi_khata.png         | 4   | 4   | 100.0   | 100.0   | 100.0   | 100.0   | 100.0   | 100.0   | 4134ms  
sample_4_hardware_invoice.png    | 4   | 4   | 100.0   | 100.0   | 100.0   | 100.0   | 100.0   | 100.0   | 4118ms  
sample_5_daily_ledger_mixed.png  | 4   | 4   | 100.0   | 100.0   | 100.0   | 100.0   | 100.0   | 100.0   | 4113ms  
-------------------------------------------------------------------------------------------------------------------
AVERAGE / OVERALL                | -   | -   | 100.0   | 100.0   | 100.0   | 100.0   | 100.0   | 100.0   | 4143ms
===================================================================================================================

>> OVERALL FIELD-LEVEL ACCURACY: 100.0%
>> AVERAGE EXTRACTION LATENCY:   4142.5ms per image
>> TOTAL SAMPLES EVALUATED:       5 handwritten/printed ledger pages
```

## Running the Benchmark

```bash
# Run evaluation across all sample images
python eval/run_eval.py
```
Output results will be printed to stdout and saved to [`eval/eval_results.json`](eval_results.json).
