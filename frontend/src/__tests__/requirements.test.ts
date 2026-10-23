import { describe, it, expect } from 'vitest';
import { FunctionalRequirement, BusinessRule, ConfidenceCategory, ClassificationType } from '../types';

describe('LegacyLens Domain Schemas & Validation Logic', () => {
  it('instantiates functional requirement with zero hallucination constraints', () => {
    const req: FunctionalRequirement = {
      id: 'FR-002',
      title: 'Dynamic Tier-Based Customer Discount Calculation',
      description: 'Calculates discounts based on customer tier and order subtotal.',
      category: 'Pricing & Discounts',
      supporting_evidence_ids: ['ev_c4a8b9f1d2e3'],
      acceptance_criteria: [
        {
          id: 'AC-002-A',
          scenario: 'VIP discount qualification',
          given: 'A VIP customer places an order with subtotal $600.00',
          when: 'CalculateDiscount executes',
          then: 'System applies 15% discount subject to 25% global cap'
        }
      ],
      confidence: 'HIGH' as ConfidenceCategory,
      classification: 'OBSERVED' as ClassificationType,
      assumptions: [],
      open_questions: [],
      review_status: 'PENDING',
      implemented_by_symbols: ['DiscountRuleEngine.CalculateDiscount']
    };

    expect(req.id).toBe('FR-002');
    expect(req.classification).toBe('OBSERVED');
    expect(req.supporting_evidence_ids.length).toBeGreaterThan(0);
    expect(req.acceptance_criteria[0].then).toContain('15% discount');
  });

  it('verifies business rule comparison threshold operators', () => {
    const rule: BusinessRule = {
      id: 'BR-001',
      title: 'VIP Customer Tier Discount',
      description: 'VIP customers with order subtotal >= $500 get 15% discount',
      supporting_evidence_ids: ['ev_vip_threshold'],
      threshold_operator: '>=',
      threshold_value: '500.00m',
      source_symbol: 'DiscountRuleEngine',
      source_file: 'Services/DiscountRuleEngine.cs',
      impacted_requirements: ['FR-002'],
      confidence: 'HIGH' as ConfidenceCategory,
      classification: 'OBSERVED' as ClassificationType
    };

    expect(rule.threshold_operator).toBe('>=');
    expect(rule.threshold_value).toBe('500.00m');
    expect(rule.confidence).toBe('HIGH');
  });
});
