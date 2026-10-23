# LegacyLens AI — 5-Minute Hackathon Demonstration Script

This script guides presenters and judges through the working demonstration of LegacyLens AI.

---

## Act 1: The Problem & One-Click Ingestion (Minute 0:00 - 1:00)

1. Open the Web UI: `http://localhost:8000` (or `http://localhost:5173` if running Vite dev server).
2. Point out the enterprise workspace interface:
   - Highlight: *"Enterprise modernization teams spend months reading undocumented legacy code to understand business rules. LegacyLens AI automates this with zero hallucinated requirements."*
3. Click the primary button: **"Analyze LegacyOrders Sample"** (or upload `samples/LegacyOrders.zip`).
4. Watch the transition to the **Agent Pipeline** tab.

---

## Act 2: Deterministic LangGraph Pipeline (Minute 1:00 - 2:00)

1. Observe the **11 Explicit LangGraph Stages**:
   - `validate_repository` → `scan_source_code` → `build_evidence_index` → `extract_business_capabilities` → `extract_business_rules` → `generate_functional_requirements` → `validate_evidence` → `identify_gaps_and_questions` → `generate_brd` → `await_human_review` → `export_approved_document`.
2. Note the **Evidence Citation Score: 100.0%**.
3. Point out that every requirement was verified by pure Python deterministic code against disk before reaching the reviewer.

---

## Act 3: Central Business Analyst Interaction (Minute 2:00 - 3:15)

1. Navigate to **Requirements (BRD)** tab.
2. Select **FR-002: Dynamic Tier-Based Customer Discount Calculation**:
   - Read the plain-English functional description.
   - Show the Gherkin Acceptance Criteria (`Given`, `When`, `Then`).
   - Click one of the supporting evidence IDs (e.g. `ev_...`).
3. Notice the seamless transition to the **Source Evidence** tab:
   - The exact C# lines in `Services/DiscountRuleEngine.cs` are highlighted:
     `private const decimal MaxDiscountPercentageCap = 0.25m;`
     `if (customer.Tier == CustomerTier.VIP && order.Subtotal >= VipSubtotalThreshold)`
   - Show that no imaginary logic was added.

---

## Act 4: The Innovation — Business Rule Impact Explorer (Minute 3:15 - 4:15)

1. Navigate to the **Impact Explorer** tab.
2. Demonstrate the interactive React Flow visual graph:
   - Show the flow: **Business Rule → Source Method → Related Service → Functional Requirement → Acceptance Criteria**.
3. Click on **BR-001** (VIP Tier Discount):
   - The side inspector shows:
     - Rule threshold: `>= 500.00m`
     - Exact implementing service: `DiscountRuleEngine.cs`
     - Connected functional requirement: `FR-002`
     - Validation test scenarios.
4. Highlight: *"If product management asks to change the VIP threshold from $500 to $400, this graph shows every affected method, requirement, and test scenario in seconds."*

---

## Act 5: Governance, Editing & Corporate DOCX Export (Minute 4:15 - 5:00)

1. Navigate to **Review & Sign-Off** tab.
2. Click the edit icon on **FR-001**:
   - Add an analyst note: *"Approved for Q1 Modernization SOW."*
   - Save the edit; observe the BRD version increments to `v2.0`.
3. Submit the human review decision: Click **"Approve & Sign Off"**.
4. Click **"Export Corporate DOCX"**:
   - A verified Word document (`BRD_....docx`) downloads instantly with cover page, executive summary, requirement tables, evidence citations, and sign-off blocks.
5. Conclude: *"A complete, verified, audit-ready BRD produced in seconds from raw C# source code."*
