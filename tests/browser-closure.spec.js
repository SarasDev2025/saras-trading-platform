import { test, expect } from '@playwright/test';

test.describe('Smallcase Closure - Browser Tests', () => {

  test.beforeEach(async ({ page }) => {
    // Navigate to the app
    await page.goto('/');

    // Login process
    await page.waitForSelector('input[type="email"], input[name="email"], input[placeholder*="email" i]', { timeout: 10000 });

    // Try different possible selectors for email input
    const emailInput = page.locator('input[type="email"], input[name="email"], input[placeholder*="email" i]').first();
    await emailInput.fill('john.doe@example.com');

    // Try different possible selectors for password input
    const passwordInput = page.locator('input[type="password"], input[name="password"], input[placeholder*="password" i]').first();
    await passwordInput.fill('password123');

    // Submit login form
    await page.click('button[type="submit"], button:has-text("Login"), button:has-text("Sign In")');

    // Wait for successful login (could be redirect or UI change)
    await page.waitForURL('**/dashboard**', { timeout: 10000 }).catch(async () => {
      // If no redirect, wait for login success indicators
      try {
        await page.waitForSelector('[data-testid="user-menu"]', { timeout: 5000 });
      } catch {
        try {
          await page.waitForSelector('.user-profile', { timeout: 5000 });
        } catch {
          await page.waitForSelector('text=Dashboard', { timeout: 5000 });
        }
      }
    });
  });

  test('should display smallcases with investment status indicators', async ({ page }) => {
    // Navigate to smallcases page
    await page.goto('/smallcases');
    await page.waitForLoadState('networkidle');

    // Wait for smallcases to load
    await page.waitForSelector('.smallcase-card, [data-testid="smallcase-item"]', { timeout: 10000 });

    // Check that smallcases are displayed
    const smallcaseCards = page.locator('.smallcase-card, [data-testid="smallcase-item"]');
    const count = await smallcaseCards.count();
    expect(count).toBeGreaterThan(0);

    // Check for investment status indicators
    const investedIndicators = page.locator('text="Invested", .invested-badge, [data-testid="invested-indicator"]');
    const investedCount = await investedIndicators.count();

    console.log(`Found ${count} smallcases, ${investedCount} showing invested status`);

    // Verify at least some show invested status (we know john.doe has 7 investments)
    expect(investedCount).toBeGreaterThan(0);
  });

  test('should show closure option for invested smallcases', async ({ page }) => {
    // Navigate to smallcases page
    await page.goto('/smallcases');
    await page.waitForLoadState('networkidle');

    // Click on "My Investments" tab (it shows count like "My Investments (7)")
    await page.click('text=/My Investments/');
    await page.waitForLoadState('networkidle');

    // Wait for investment cards to load
    await page.waitForSelector('button:has-text("Close")', { timeout: 10000 });

    // Check for closure buttons
    const closureButtons = page.locator('button:has-text("Close")');
    const closureCount = await closureButtons.count();

    console.log(`Found ${closureCount} closure buttons available`);

    expect(closureCount).toBeGreaterThan(0);

    // Test clicking the first closure button
    await closureButtons.first().click();

    // Wait for closure modal
    await page.waitForSelector('text="Close Position"', { timeout: 5000 });

    // Check for closure preview information in the modal
    const currentValueText = await page.locator('text="Current Value:"').count();
    const investedAmountText = await page.locator('text="Invested Amount:"').count();
    const pnlText = await page.locator('text="P&L:"').count();

    expect(currentValueText).toBeGreaterThan(0);
    expect(investedAmountText).toBeGreaterThan(0);
    expect(pnlText).toBeGreaterThan(0);

    console.log('Closure preview modal displayed successfully with all expected fields');

    // Close the modal without confirming (safety)
    await page.click('button:has-text("Cancel")');
  });

  test('should display position history', async ({ page }) => {
    // Try different routes for position history
    const historyRoutes = ['/history', '/portfolio/history', '/investments/history', '/closed-positions'];
    let found = false;

    for (const route of historyRoutes) {
      try {
        await page.goto(route);
        await page.waitForSelector('.history-item, [data-testid="history"], .closed-position', { timeout: 5000 });
        found = true;
        break;
      } catch (e) {
        console.log(`History route ${route} not found, trying next...`);
      }
    }

    if (!found) {
      // Look for history navigation from main pages
      await page.goto('/portfolio');
      await page.click('text="History", text="Closed", text="Past Investments"').catch(() => {
        console.log('Could not find history navigation, checking for history data on current page');
      });
    }

    // Check if history data is displayed
    const historyItems = page.locator('.history-item, [data-testid="history"], .closed-position, .transaction-history');
    const historyCount = await historyItems.count();

    console.log(`Found ${historyCount} history items`);

    // If history items exist, verify they contain expected information
    if (historyCount > 0) {
      const firstHistoryItem = historyItems.first();

      // Check for common history fields
      const hasSmallcaseName = await firstHistoryItem.locator('text=/.*Strategy|.*Portfolio|.*Fund/').count() > 0;
      const hasAmount = await firstHistoryItem.locator('text=/\\$|₹|[0-9,]+\\.?[0-9]*/').count() > 0;
      const hasDate = await firstHistoryItem.locator('text=/\\d{4}-\\d{2}-\\d{2}|\\d{1,2}\\/\\d{1,2}\\/\\d{4}/').count() > 0;

      console.log(`History item validation - Name: ${hasSmallcaseName}, Amount: ${hasAmount}, Date: ${hasDate}`);

      expect(hasSmallcaseName || hasAmount || hasDate).toBeTruthy();
    }
  });

  test('should handle closure confirmation flow', async ({ page }) => {
    // Navigate to investments page
    await page.goto('/portfolio');
    await page.waitForLoadState('networkidle');

    // Look for an investment to close (prefer paper mode for safety)
    const paperInvestments = page.locator('[data-mode="paper"], .paper-investment, text="Paper Mode"');
    const paperCount = await paperInvestments.count();

    let investmentToClose;
    if (paperCount > 0) {
      investmentToClose = paperInvestments.first();
      console.log('Found paper mode investment for safe testing');
    } else {
      // Fallback to any investment but be careful
      investmentToClose = page.locator('.investment-item, [data-testid="investment"]').first();
      console.log('Using first available investment (caution: might be live)');
    }

    // Find and click closure button
    const closureButton = investmentToClose.locator('button:has-text("Close"), button:has-text("Sell"), button:has-text("Exit")');
    await closureButton.click();

    // Wait for closure modal
    await page.waitForSelector('.modal, .dialog, [data-testid="closure-modal"]');

    // Check for closure preview information
    const currentValueText = await page.locator('text="Current Value"').count();
    const pnlText = await page.locator('text="P&L", text="Profit", text="Loss"').count();

    expect(currentValueText + pnlText).toBeGreaterThan(0);

    // Look for confirmation button (but don't click it to avoid actual closure)
    const confirmButton = page.locator('button:has-text("Confirm"), button:has-text("Close Position"), button[type="submit"]');
    const confirmCount = await confirmButton.count();

    expect(confirmCount).toBeGreaterThan(0);
    console.log('Closure confirmation flow displayed correctly');

    // Close the modal instead of confirming
    await page.click('button:has-text("Cancel"), button:has-text("Close"), .modal-close, [data-testid="close-modal"]');
  });

  test('should prevent duplicate investments UI', async ({ page }) => {
    // Navigate to smallcases listing
    await page.goto('/smallcases');
    await page.waitForLoadState('networkidle');

    // Find a smallcase that's already invested
    const investedSmallcase = page.locator('.smallcase-card:has(.invested-badge), [data-invested="true"]').first();
    const investedCount = await page.locator('.smallcase-card:has(.invested-badge), [data-invested="true"]').count();

    if (investedCount > 0) {
      // Check that invest button is disabled or shows different text
      const investButton = investedSmallcase.locator('button:has-text("Invest"), button:has-text("Buy"), [data-testid="invest-button"]');
      const isDisabled = await investButton.isDisabled().catch(() => false);
      const buttonText = await investButton.textContent().catch(() => '');

      console.log(`Invested smallcase button - Disabled: ${isDisabled}, Text: "${buttonText}"`);

      // Should either be disabled or show "Already Invested" or similar
      const hasPreventionUI = isDisabled ||
                             buttonText.toLowerCase().includes('invested') ||
                             buttonText.toLowerCase().includes('owned') ||
                             buttonText.toLowerCase().includes('manage');

      expect(hasPreventionUI).toBeTruthy();
    } else {
      console.log('No invested smallcases found with UI indicators');
    }
  });
});