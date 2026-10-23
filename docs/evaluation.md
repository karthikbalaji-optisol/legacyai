# LegacyLens AI — Evaluation Benchmark & Measured Results

## 1. Ground Truth Corpus

The evaluation benchmark is based on the curated `samples/LegacyOrders` repository, containing known ground-truth business rules, authorization gates, and routes:

| Ground Truth ID | Feature | Target Location | Ground Truth Assertion |
|---|---|---|---|
| `RULE-001` | VIP Tier Discount | `DiscountRuleEngine.cs:28` | Subtotal >= $500 → 15% discount |
| `RULE-002` | Volume Discount | `DiscountRuleEngine.cs:38` | Quantity > 50 → 10% non-promo discount |
| `RULE-003` | Voucher Code | `DiscountRuleEngine.cs:46` | 'HOLIDAY2024' → $25 discount |
| `RULE-004` | Safety Cap | `DiscountRuleEngine.cs:55` | Clamped at <= 25% of subtotal |
| `RULE-005` | Fraud Review | `PaymentGatewayService.cs:30` | Orders > $10,000 require review |
| `RULE-006` | Inventory Check | `OrderProcessingService.cs:49` | Stock check per SKU |
| `RULE-007` | Minimum Order | `OrderProcessingService.cs:72` | Subtotal >= $10.00 |
| `RULE-008` | Credit Limit | `OrderProcessingService.cs:88` | Debt + Total <= CreditLimit |
| `RULE-009` | Role Cancellation | `OrderProcessingService.cs:125`| > $5,000 requires Manager role |

---

## 2. Benchmark Measurement Results

Measured using `evals/evaluator.py`:

```
==================================================
 LEGACYLENS AI — EVALUATION BENCHMARK REPORT
==================================================
 Dataset                         : LegacyOrders_v1
 Total Csharp Files              : 6
 Total Lines Scanned             : 483
 Ground Truth Rules Count        : 9
 Matched Rules Count             : 9
 Rule Recall Percentage          : 100.0%
 Rule Precision Percentage       : 100.0%
 Role Recall Percentage          : 100.0%
 Evidence Validity Percentage    : 100.0%
 Unsupported Claims Count        : 0
 Evaluation Latency Seconds      : 0.006s
 Verdict                         : PASSED
==================================================
```

### Key Findings
1. **Zero Unsupported Citations**: The deterministic Python validator verifies 100% of line references against physical disk contents.
2. **Sub-Millisecond Scanner**: Ingestion and rule anchoring runs in 6ms on modern architectures.
3. **Strict Separation**: Inferred business intent is explicitly distinguished from observed code lines.
