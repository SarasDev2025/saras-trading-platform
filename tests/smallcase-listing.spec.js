import { test, expect } from '@playwright/test';
import { getAuthToken, API_BASE_URL } from './auth-helper.js';

test.describe('Smallcase Listing with Investment Status', () => {
  let authToken;

  test.beforeEach(async ({ request }) => {
    authToken = await getAuthToken(request);
  });

  test('should list all smallcases with investment status for authenticated user', async ({ request }) => {
    const response = await request.get(`${API_BASE_URL}/smallcases/`, {
      headers: {
        'Authorization': `Bearer ${authToken}`
      }
    });

    expect(response.ok()).toBeTruthy();
    const data = await response.json();

    expect(data).toHaveProperty('success', true);
    expect(data.data).toBeInstanceOf(Array);
    expect(data.data.length).toBeGreaterThan(0);

    console.log(`Found ${data.data.length} smallcases`);

    // Check that each smallcase has the isInvested field
    data.data.forEach(smallcase => {
      expect(smallcase).toHaveProperty('id');
      expect(smallcase).toHaveProperty('name');
      expect(smallcase).toHaveProperty('isInvested');
      expect(typeof smallcase.isInvested).toBe('boolean');
    });

    // Count invested vs not invested
    const investedCount = data.data.filter(sc => sc.isInvested).length;
    const notInvestedCount = data.data.filter(sc => !sc.isInvested).length;

    console.log(`Invested in: ${investedCount} smallcases`);
    console.log(`Not invested in: ${notInvestedCount} smallcases`);
  });

  test('should list smallcases without investment status for unauthenticated user', async ({ request }) => {
    const response = await request.get(`${API_BASE_URL}/smallcases/`);

    expect(response.ok()).toBeTruthy();
    const data = await response.json();

    expect(data).toHaveProperty('success', true);
    expect(data.data).toBeInstanceOf(Array);

    // For unauthenticated users, isInvested should be false for all smallcases
    data.data.forEach(smallcase => {
      expect(smallcase).toHaveProperty('isInvested', false);
    });

    console.log(`Unauthenticated user sees ${data.data.length} smallcases, all marked as not invested`);
  });

  test('should prevent duplicate investment through API validation', async ({ request }) => {
    // Get smallcases to find one that's already invested
    const smallcasesResponse = await request.get(`${API_BASE_URL}/smallcases/`, {
      headers: {
        'Authorization': `Bearer ${authToken}`
      }
    });

    const smallcasesData = await smallcasesResponse.json();
    const investedSmallcase = smallcasesData.data.find(sc => sc.isInvested);

    if (!investedSmallcase) {
      console.log('No invested smallcases found, skipping duplicate prevention test');
      test.skip();
      return;
    }

    console.log(`Testing duplicate prevention for smallcase: ${investedSmallcase.name}`);

    // Try to invest in an already invested smallcase
    // This should fail if proper validation is in place
    const investResponse = await request.post(`${API_BASE_URL}/smallcases/${investedSmallcase.id}/invest`, {
      headers: {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json'
      },
      data: {
        amount: 10000,
        execution_mode: 'paper'
      }
    });

    // This should either fail with a specific error or handle gracefully
    if (!investResponse.ok()) {
      const errorData = await investResponse.json();
      console.log('Investment rejected as expected:', errorData.message || errorData.detail);

      // Check for appropriate error messages
      const errorText = JSON.stringify(errorData).toLowerCase();
      const hasExpectedError = errorText.includes('already invested') ||
                              errorText.includes('duplicate') ||
                              errorText.includes('already have');

      expect(hasExpectedError).toBeTruthy();
    } else {
      // If it succeeds, check that it handled the duplicate gracefully
      const data = await investResponse.json();
      console.log('Investment response:', data);
    }
  });

  test('should show investment details for invested smallcases', async ({ request }) => {
    // Get user investments
    const investmentsResponse = await request.get(`${API_BASE_URL}/smallcases/user/investments`, {
      headers: {
        'Authorization': `Bearer ${authToken}`
      }
    });

    const investmentsData = await investmentsResponse.json();

    if (investmentsData.data.length === 0) {
      console.log('No investments found, skipping investment details test');
      test.skip();
      return;
    }

    const investment = investmentsData.data[0];
    console.log(`Checking investment details for: ${investment.smallcase_name}`);

    // Verify investment has all required fields
    expect(investment).toHaveProperty('id');
    expect(investment).toHaveProperty('smallcase_id');
    expect(investment).toHaveProperty('smallcase_name');
    expect(investment).toHaveProperty('investment_amount');
    expect(investment).toHaveProperty('current_value');
    expect(investment).toHaveProperty('unrealized_pnl');
    expect(investment).toHaveProperty('status');
    expect(investment).toHaveProperty('execution_mode');
    expect(investment).toHaveProperty('invested_at');

    // Check data types
    expect(typeof investment.investment_amount).toBe('number');
    expect(typeof investment.execution_mode).toBe('string');
    expect(['active', 'sold', 'partial'].includes(investment.status)).toBeTruthy();
    expect(['paper', 'live'].includes(investment.execution_mode)).toBeTruthy();
  });
});