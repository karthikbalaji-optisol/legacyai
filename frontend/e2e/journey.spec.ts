import { test, expect } from '@playwright/test';

test.describe('LegacyLens AI — End-to-End User Journey', () => {
  test('Upload sample -> Timeline -> Requirements -> Evidence -> Impact -> DOCX Export', async ({ page }) => {
    // 1. Visit the application
    await page.goto('/');
    await expect(page).toHaveTitle(/LegacyLens AI/);

    // 2. Click Analyze LegacyOrders Sample
    const sampleBtn = page.getByRole('button', { name: /Analyze LegacyOrders Sample/i });
    await expect(sampleBtn).toBeVisible();
    await sampleBtn.click();

    // 3. Confirm transition to Agent Pipeline timeline
    await expect(page.getByText(/LangGraph Deterministic Orchestration Pipeline/i)).toBeVisible({ timeout: 10000 });
    await expect(page.getByText(/11 Explicit Stages/i)).toBeVisible();

    // 4. Navigate to Requirements Explorer
    await page.getByRole('button', { name: /Requirements \(BRD\)/i }).click();
    await expect(page.getByText(/Functional Requirements Explorer/i)).toBeVisible();

    // 5. Select FR-002
    const fr002 = page.getByText(/Dynamic Tier-Based Customer Discount Calculation/i);
    await expect(fr002).toBeVisible();
    await fr002.click();

    // 6. Trace citation to Source Evidence Viewer
    const citationBtn = page.getByRole('button', { name: /ev_/i }).first();
    await expect(citationBtn).toBeVisible();
    await citationBtn.click();

    // 7. Verify Source Code viewer displays exact C# excerpt
    await expect(page.getByText(/Source Code Evidence Viewer/i)).toBeVisible();
    await expect(page.getByText(/C# Source Code Excerpt/i)).toBeVisible();

    // 8. Open Impact Explorer
    await page.getByRole('button', { name: /Impact Explorer/i }).click();
    await expect(page.getByText(/Business Rule Impact Explorer/i)).toBeVisible();

    // 9. Open Review & Sign-Off Workspace
    await page.getByRole('button', { name: /Review & Sign-Off/i }).click();
    await expect(page.getByText(/Human Stakeholder Governance/i)).toBeVisible();

    // 10. Verify Corporate DOCX Export Button is active
    const exportBtn = page.getByRole('button', { name: /Export Corporate DOCX/i });
    await expect(exportBtn).toBeVisible();
    await expect(exportBtn).toBeEnabled();
  });
});
