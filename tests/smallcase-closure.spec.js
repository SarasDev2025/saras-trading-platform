import { test, expect } from '@playwright/test';
import { getAuthToken, API_BASE_URL } from './auth-helper.js';

test.describe('Smallcase Closure API', () => {
  let authToken;

  test.beforeEach(async ({ request }) => {
    authToken = await getAuthToken(request);
  });

  test('should get user investments', async ({ request }) => {
    const response = await request.get(`${API_BASE_URL}/smallcases/user/investments`, {
      headers: {
        'Authorization': `Bearer ${authToken}`
      }
    });

    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(data).toHaveProperty('success', true);
    expect(data.data).toBeInstanceOf(Array);
    expect(data.data.length).toBeGreaterThan(0);

    console.log(`Found ${data.data.length} active investments for testing`);
  });

  test('should preview closure for an investment', async ({ request }) => {
    // First get user investments
    const investmentsResponse = await request.get(`${API_BASE_URL}/smallcases/user/investments`, {
      headers: {
        'Authorization': `Bearer ${authToken}`
      }
    });

    const investmentsData = await investmentsResponse.json();
    expect(investmentsData.data.length).toBeGreaterThan(0);

    const investment = investmentsData.data[0];
    console.log(`Testing closure preview for investment: ${investment.id}`);

    // Test closure preview
    const previewResponse = await request.get(`${API_BASE_URL}/smallcases/investments/${investment.id}/closure-preview`, {
      headers: {
        'Authorization': `Bearer ${authToken}`
      }
    });

    expect(previewResponse.ok()).toBeTruthy();
    const previewData = await previewResponse.json();

    expect(previewData).toHaveProperty('success', true);
    expect(previewData.data).toHaveProperty('investment_amount');
    expect(previewData.data).toHaveProperty('current_value');
    expect(previewData.data).toHaveProperty('unrealized_pnl');
    expect(previewData.data).toHaveProperty('roi_percentage');
    expect(previewData.data).toHaveProperty('holding_period_days');
    expect(previewData.data).toHaveProperty('execution_mode');

    console.log('Closure preview:', previewData.data);
  });

  test('should close an investment in paper mode', async ({ request }) => {
    // Get user investments
    const investmentsResponse = await request.get(`${API_BASE_URL}/smallcases/user/investments`, {
      headers: {
        'Authorization': `Bearer ${authToken}`
      }
    });

    const investmentsData = await investmentsResponse.json();
    expect(investmentsData.data.length).toBeGreaterThan(0);

    // Find a paper mode investment to close
    const paperInvestment = investmentsData.data.find(inv => inv.execution_mode === 'paper');

    if (!paperInvestment) {
      console.log('No paper mode investments found, skipping closure test');
      test.skip();
      return;
    }

    console.log(`Closing paper investment: ${paperInvestment.id}`);

    // Close the investment
    const closeResponse = await request.post(`${API_BASE_URL}/smallcases/investments/${paperInvestment.id}/close`, {
      headers: {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json'
      },
      data: {
        closure_reason: 'test_closure'
      }
    });

    expect(closeResponse.ok()).toBeTruthy();
    const closeData = await closeResponse.json();

    expect(closeData).toHaveProperty('success', true);
    expect(closeData.data).toHaveProperty('position_closed', true);
    expect(closeData.data).toHaveProperty('realized_pnl');
    expect(closeData.data).toHaveProperty('exit_value');
    expect(closeData.data).toHaveProperty('holding_period_days');

    console.log('Investment closed successfully:', closeData.data);

    // Verify investment status changed
    const updatedInvestmentsResponse = await request.get(`${API_BASE_URL}/smallcases/user/investments`, {
      headers: {
        'Authorization': `Bearer ${authToken}`
      }
    });

    const updatedInvestmentsData = await updatedInvestmentsResponse.json();
    const closedInvestment = updatedInvestmentsData.data.find(inv => inv.id === paperInvestment.id);

    // The investment should either be marked as 'sold' or not appear in active investments
    if (closedInvestment) {
      expect(closedInvestment.status).toBe('sold');
    }
  });

  test('should get position history', async ({ request }) => {
    const response = await request.get(`${API_BASE_URL}/smallcases/user/positions/history`, {
      headers: {
        'Authorization': `Bearer ${authToken}`
      }
    });

    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(data).toHaveProperty('success', true);
    expect(data.data).toBeInstanceOf(Array);

    console.log(`Found ${data.data.length} historical positions`);

    if (data.data.length > 0) {
      const historyItem = data.data[0];
      expect(historyItem).toHaveProperty('investment_amount');
      expect(historyItem).toHaveProperty('exit_value');
      expect(historyItem).toHaveProperty('realized_pnl');
      expect(historyItem).toHaveProperty('roi_percentage');
      expect(historyItem).toHaveProperty('holding_period_days');
      expect(historyItem).toHaveProperty('closed_at');
    }
  });

  test('should get closed positions', async ({ request }) => {
    const response = await request.get(`${API_BASE_URL}/smallcases/user/positions/closed`, {
      headers: {
        'Authorization': `Bearer ${authToken}`
      }
    });

    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(data).toHaveProperty('success', true);
    expect(data.data).toBeInstanceOf(Array);

    console.log(`Found ${data.data.length} closed positions`);

    if (data.data.length > 0) {
      const closedPosition = data.data[0];
      expect(closedPosition).toHaveProperty('investment_amount');
      expect(closedPosition).toHaveProperty('closed_at');
      expect(closedPosition).toHaveProperty('exit_value');
      expect(closedPosition).toHaveProperty('realized_pnl');
    }
  });

  test('should get enhanced transaction history', async ({ request }) => {
    const response = await request.get(`${API_BASE_URL}/trading/transactions?limit=10`, {
      headers: {
        'Authorization': `Bearer ${authToken}`
      }
    });

    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(data).toHaveProperty('success', true);
    expect(data.data).toHaveProperty('transactions');
    expect(data.data).toHaveProperty('pagination');

    console.log(`Found ${data.data.transactions.length} transactions`);

    if (data.data.transactions.length > 0) {
      const transaction = data.data.transactions[0];
      expect(transaction).toHaveProperty('transaction_type');
      expect(transaction).toHaveProperty('amount');
      expect(transaction).toHaveProperty('transaction_date');
    }
  });

  test('should filter transaction history by type', async ({ request }) => {
    const response = await request.get(`${API_BASE_URL}/trading/transactions?transaction_type=close_position&limit=5`, {
      headers: {
        'Authorization': `Bearer ${authToken}`
      }
    });

    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(data).toHaveProperty('success', true);

    // All returned transactions should be of type 'close_position'
    if (data.data.transactions.length > 0) {
      data.data.transactions.forEach(transaction => {
        expect(transaction.transaction_type).toBe('close_position');
      });
    }

    console.log(`Found ${data.data.transactions.length} close_position transactions`);
  });
});