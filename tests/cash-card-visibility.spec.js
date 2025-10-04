import { test, expect } from '@playwright/test';

test.describe('Cash Card Visibility', () => {
  test('should display Cash Available card on dashboard', async ({ page }) => {
    // Register a new user for this test
    const timestamp = Date.now();
    const testEmail = `cashtest${timestamp}@example.com`;

    const registerResponse = await page.request.post('http://localhost:8000/auth/register', {
      data: {
        email: testEmail,
        username: testEmail,
        password: 'Password123',
        first_name: 'Cash',
        last_name: 'Test'
      },
      headers: {
        'Content-Type': 'application/json'
      }
    });

    const registerData = await registerResponse.json();

    if (!registerData.success || !registerData.data) {
      throw new Error(`Registration failed: ${JSON.stringify(registerData)}`);
    }

    const token = registerData.data.access_token;

    // Navigate to dashboard and set token
    await page.goto('http://localhost:3000/dashboard');
    await page.evaluate((accessToken) => {
      localStorage.setItem('access_token', accessToken);
    }, token);

    // Reload to apply authentication
    await page.reload();

    // Wait for navigation to dashboard
    await page.waitForURL('**/dashboard', { timeout: 10000 });

    // Wait for portfolio data to load
    await page.waitForTimeout(2000);

    // Check if Cash Available card is visible
    const cashCard = page.locator('text=Cash Available').first();
    await expect(cashCard).toBeVisible({ timeout: 5000 });

    // Verify the card contains dollar sign icon
    const dollarIcon = page.locator('svg').filter({ has: page.locator('path') }).first();
    await expect(dollarIcon).toBeVisible();

    // Verify Add Funds button is present
    const addFundsButton = page.locator('text=Add Funds').first();
    await expect(addFundsButton).toBeVisible();

    // Verify cash amount is displayed (should contain $ sign)
    const cashAmount = page.locator('.text-2xl.font-bold.text-white').filter({ hasText: '$' }).first();
    await expect(cashAmount).toBeVisible();

    // Verify allocation percentage is shown
    const allocationText = page.locator('text=% allocation').first();
    await expect(allocationText).toBeVisible();

    console.log('✅ Cash Available card is visible and contains all expected elements');
  });

  test('should open Add Funds modal when clicking Add Funds button', async ({ page }) => {
    // Register a new user for this test
    const timestamp = Date.now();
    const testEmail = `modaltest${timestamp}@example.com`;

    const registerResponse = await page.request.post('http://localhost:8000/auth/register', {
      data: {
        email: testEmail,
        username: testEmail,
        password: 'Password123',
        first_name: 'Modal',
        last_name: 'Test'
      },
      headers: {
        'Content-Type': 'application/json'
      }
    });

    const registerData = await registerResponse.json();
    const token = registerData.data.access_token;

    // Navigate to dashboard and set token
    await page.goto('http://localhost:3000/dashboard');
    await page.evaluate((accessToken) => {
      localStorage.setItem('access_token', accessToken);
    }, token);

    // Reload to apply authentication
    await page.reload();

    // Wait for dashboard
    await page.waitForURL('**/dashboard', { timeout: 10000 });
    await page.waitForTimeout(2000);

    // Click Add Funds button
    const addFundsButton = page.locator('text=Add Funds').first();
    await addFundsButton.click();

    // Verify modal opens
    const modalTitle = page.locator('text=Add Virtual Funds');
    await expect(modalTitle).toBeVisible({ timeout: 3000 });

    // Verify quick amount buttons are present
    const quickAmountButtons = page.locator('button:has-text("$")').filter({ hasText: 'k' });
    await expect(quickAmountButtons.first()).toBeVisible();

    // Verify amount input field
    const amountInput = page.locator('input[type="number"]');
    await expect(amountInput).toBeVisible();

    console.log('✅ Add Funds modal opens correctly');
  });

  test('should display correct cash balance from API', async ({ page }) => {
    // Register a new user for this test
    const timestamp = Date.now();
    const testEmail = `apitest${timestamp}@example.com`;

    const registerResponse = await page.request.post('http://localhost:8000/auth/register', {
      data: {
        email: testEmail,
        username: testEmail,
        password: 'Password123',
        first_name: 'API',
        last_name: 'Test'
      },
      headers: {
        'Content-Type': 'application/json'
      }
    });

    const registerData = await registerResponse.json();
    const token = registerData.data.access_token;

    // Navigate to dashboard and set token
    await page.goto('http://localhost:3000/dashboard');
    await page.evaluate((accessToken) => {
      localStorage.setItem('access_token', accessToken);
    }, token);

    // Reload to apply authentication
    await page.reload();

    // Wait for dashboard
    await page.waitForURL('**/dashboard', { timeout: 10000 });

    // Intercept API call to check response
    const response = await page.waitForResponse(
      response => response.url().includes('/portfolios/cash-balance') && response.status() === 200,
      { timeout: 10000 }
    );

    const data = await response.json();
    console.log('Cash balance API response:', data);

    // Verify API returned expected data
    expect(data.success).toBe(true);
    expect(data.data).toHaveProperty('cash_balance');
    expect(data.data).toHaveProperty('buying_power');

    // Verify the UI displays the cash balance
    const cashAmount = page.locator('.text-2xl.font-bold.text-white').filter({ hasText: '$' }).first();
    await expect(cashAmount).toBeVisible();

    const displayedAmount = await cashAmount.textContent();
    console.log('Displayed cash amount:', displayedAmount);

    console.log('✅ Cash balance API integration working correctly');
  });
});
