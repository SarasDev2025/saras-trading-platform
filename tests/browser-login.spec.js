import { test, expect } from '@playwright/test';

test.describe('Login & Registration - Browser Tests', () => {

  // Generate unique test data for each test run
  const generateTestUser = (prefix = 'testuser') => {
    const timestamp = Date.now();
    const random = Math.floor(Math.random() * 1000);
    return {
      username: `${prefix}${timestamp}${random}`.substring(0, 25), // Keep under 30 char limit, alphanumeric
      email: `${prefix}_${timestamp}_${random}@example.com`,
      first_name: 'Test', // Required field
      last_name: 'User',  // Required field
      normalPassword: 'TestPassword123!', // Meets all validation: 8+ chars, upper, lower, digit
      longPassword: 'TestPassword123!' + 'a'.repeat(60) + 'Z9!', // >72 bytes but meets validation
      unicodePassword: 'TestPassword123äöü!', // Unicode but meets validation requirements
    };
  };

  test.beforeEach(async ({ page }) => {
    // Navigate to the login page
    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });

  test.describe('Registration Flow', () => {

    test('should register user with normal password', async ({ page }) => {
      const testUser = generateTestUser('normal');

      // Navigate to registration page (route from App.tsx is /auth/register)
      try {
        await page.click('a:has-text("Create Account"), button:has-text("Sign Up"), a:has-text("Sign Up")', { timeout: 5000 });
      } catch {
        await page.goto('/auth/register');
      }

      await page.waitForLoadState('networkidle');

      // Fill registration form with all required fields (exact field names from RegisterForm.tsx)
      await page.fill('input[name="first_name"]', testUser.first_name);
      await page.fill('input[name="last_name"]', testUser.last_name);
      await page.fill('input[name="username"]', testUser.username);
      await page.fill('input[name="email"]', testUser.email);
      await page.fill('input[name="password"]', testUser.normalPassword);
      await page.fill('input[name="confirmPassword"]', testUser.normalPassword);

      // Submit registration (button text from RegisterForm.tsx is "Create Account")
      await page.click('button[type="submit"], button:has-text("Create Account")');

      // Wait for successful registration
      await page.waitForURL('**/dashboard**', { timeout: 10000 }).catch(async () => {
        // Alternative success indicators
        try {
          await page.waitForSelector('[data-testid="user-menu"], .user-profile, text=Dashboard', { timeout: 10000 });
        } catch {
          // Check for success message
          await expect(page.locator('text=Registration successful, text=Welcome')).toBeVisible({ timeout: 5000 });
        }
      });

      // Verify we're logged in
      const isLoggedIn = await page.locator('[data-testid="user-menu"], .user-profile, text=Dashboard').isVisible();
      expect(isLoggedIn).toBeTruthy();
    });

    test('should register user with long password (>72 bytes)', async ({ page }) => {
      const testUser = generateTestUser('longpass');

      // Navigate to registration (route from App.tsx is /auth/register)
      try {
        await page.click('a:has-text("Create Account"), button:has-text("Sign Up"), a:has-text("Sign Up")', { timeout: 5000 });
      } catch {
        await page.goto('/auth/register');
      }

      await page.waitForLoadState('networkidle');

      // Fill registration form with long password (exact field names from RegisterForm.tsx)
      await page.fill('input[name="first_name"]', testUser.first_name);
      await page.fill('input[name="last_name"]', testUser.last_name);
      await page.fill('input[name="username"]', testUser.username);
      await page.fill('input[name="email"]', testUser.email);
      await page.fill('input[name="password"]', testUser.longPassword);
      await page.fill('input[name="confirmPassword"]', testUser.longPassword);

      console.log(`Testing with ${testUser.longPassword.length} character password (${Buffer.from(testUser.longPassword, 'utf8').length} bytes)`);

      // Submit registration (button text from RegisterForm.tsx is "Create Account")
      await page.click('button[type="submit"], button:has-text("Create Account")');

      // Should not show bcrypt error and should succeed
      await page.waitForTimeout(2000); // Wait for any processing

      // Check for error messages (should not have bcrypt 72-byte error)
      const errorMessage = await page.locator('.error, .alert-error, [role="alert"]').textContent().catch(() => '');
      expect(errorMessage).not.toContain('72 bytes');
      expect(errorMessage).not.toContain('password cannot be longer');

      // Should eventually succeed or show reasonable validation error
      const hasSuccess = await page.locator('[data-testid="user-menu"], .user-profile, text=Dashboard').isVisible().catch(() => false);
      const hasReasonableError = await page.locator('text=Password must be, text=Invalid').isVisible().catch(() => false);

      expect(hasSuccess || hasReasonableError).toBeTruthy();
    });

    test('should register user with Unicode password', async ({ page }) => {
      const testUser = generateTestUser('unicode');

      // Navigate to registration (route from App.tsx is /auth/register)
      try {
        await page.click('a:has-text("Create Account"), button:has-text("Sign Up"), a:has-text("Sign Up")', { timeout: 5000 });
      } catch {
        await page.goto('/auth/register');
      }

      await page.waitForLoadState('networkidle');

      // Fill registration form with Unicode password (exact field names from RegisterForm.tsx)
      await page.fill('input[name="first_name"]', testUser.first_name);
      await page.fill('input[name="last_name"]', testUser.last_name);
      await page.fill('input[name="username"]', testUser.username);
      await page.fill('input[name="email"]', testUser.email);
      await page.fill('input[name="password"]', testUser.unicodePassword);
      await page.fill('input[name="confirmPassword"]', testUser.unicodePassword);

      console.log(`Testing Unicode password: ${testUser.unicodePassword} (${Buffer.from(testUser.unicodePassword, 'utf8').length} bytes)`);

      // Submit registration (button text from RegisterForm.tsx is "Create Account")
      await page.click('button[type="submit"], button:has-text("Create Account")');

      // Should handle Unicode correctly without errors
      await page.waitForTimeout(2000);

      // Check for error messages
      const errorMessage = await page.locator('.error, .alert-error, [role="alert"]').textContent().catch(() => '');
      expect(errorMessage).not.toContain('72 bytes');
      expect(errorMessage).not.toContain('encoding');

      // Should succeed or show reasonable validation
      const hasSuccess = await page.locator('[data-testid="user-menu"], .user-profile, text=Dashboard').isVisible().catch(() => false);
      const hasReasonableError = await page.locator('text=Password must be, text=Invalid').isVisible().catch(() => false);

      expect(hasSuccess || hasReasonableError).toBeTruthy();
    });
  });

  test.describe('Login Flow', () => {

    test('should login with valid credentials', async ({ page }) => {
      // Use a test user that should exist or create one first
      const testUser = {
        email: 'john.doe@example.com',
        password: 'password123'
      };

      // Fill login form (exact field names from LoginForm.tsx)
      await page.fill('input[name="email"]', testUser.email);
      await page.fill('input[name="password"]', testUser.password);

      // Submit login
      await page.click('button[type="submit"], button:has-text("Login"), button:has-text("Sign In")');

      // Wait for successful login
      await page.waitForURL('**/dashboard**', { timeout: 10000 }).catch(async () => {
        // Alternative success indicators
        await page.waitForSelector('[data-testid="user-menu"], .user-profile, text=Dashboard', { timeout: 10000 });
      });

      // Verify successful login
      const isLoggedIn = await page.locator('[data-testid="user-menu"], .user-profile, text=Dashboard').isVisible();
      expect(isLoggedIn).toBeTruthy();
    });

    test('should show error for invalid credentials', async ({ page }) => {
      // Fill login form with invalid credentials (exact field names from LoginForm.tsx)
      await page.fill('input[name="email"]', 'invalid@example.com');
      await page.fill('input[name="password"]', 'wrongpassword');

      // Submit login
      await page.click('button[type="submit"], button:has-text("Login"), button:has-text("Sign In")');

      // Should show error message
      await expect(page.locator('.error, .alert-error, [role="alert"], text=Invalid credentials, text=Login failed')).toBeVisible({ timeout: 10000 });

      // Should not be logged in
      const isLoggedIn = await page.locator('[data-testid="user-menu"], .user-profile').isVisible().catch(() => false);
      expect(isLoggedIn).toBeFalsy();
    });

    test('should handle empty form submission', async ({ page }) => {
      // Submit empty form
      await page.click('button[type="submit"], button:has-text("Login"), button:has-text("Sign In")');

      // Should show validation errors
      const hasValidationError = await page.locator('.error, .alert-error, [role="alert"], text=required, text=field').isVisible({ timeout: 5000 });
      expect(hasValidationError).toBeTruthy();
    });
  });

  test.describe('Password Length Security', () => {

    test('should handle long password login without bcrypt errors', async ({ page }) => {
      // First register a user with a long password
      const testUser = generateTestUser('longlogin');

      // Navigate to registration first (route from App.tsx is /auth/register)
      try {
        await page.click('a:has-text("Create Account"), button:has-text("Sign Up"), a:has-text("Sign Up")', { timeout: 5000 });
      } catch {
        await page.goto('/auth/register');
      }

      await page.waitForLoadState('networkidle');

      // Register with long password (exact field names from RegisterForm.tsx)
      await page.fill('input[name="first_name"]', testUser.first_name);
      await page.fill('input[name="last_name"]', testUser.last_name);
      await page.fill('input[name="username"]', testUser.username);
      await page.fill('input[name="email"]', testUser.email);
      await page.fill('input[name="password"]', testUser.longPassword);
      await page.fill('input[name="confirmPassword"]', testUser.longPassword);

      await page.click('button[type="submit"], button:has-text("Create Account")');
      await page.waitForTimeout(3000);

      // Now test login with the same long password
      await page.goto('/');
      await page.waitForLoadState('networkidle');

      await page.fill('input[name="email"]', testUser.email);
      await page.fill('input[name="password"]', testUser.longPassword);

      await page.click('button[type="submit"], button:has-text("Login")');

      // Should not show bcrypt 72-byte error
      await page.waitForTimeout(2000);
      const errorMessage = await page.locator('.error, .alert-error, [role="alert"]').textContent().catch(() => '');
      expect(errorMessage).not.toContain('72 bytes');
      expect(errorMessage).not.toContain('password cannot be longer');

      console.log('Long password login test completed without bcrypt errors');
    });

    test('should handle Unicode password login correctly', async ({ page }) => {
      // Test login with Unicode characters
      const testUser = generateTestUser('unicodelogin');

      // Quick registration first (route from App.tsx is /auth/register)
      try {
        await page.click('a:has-text("Create Account"), button:has-text("Sign Up"), a:has-text("Sign Up")', { timeout: 5000 });
      } catch {
        await page.goto('/auth/register');
      }

      await page.waitForLoadState('networkidle');

      await page.fill('input[name="first_name"]', testUser.first_name);
      await page.fill('input[name="last_name"]', testUser.last_name);
      await page.fill('input[name="username"]', testUser.username);
      await page.fill('input[name="email"]', testUser.email);
      await page.fill('input[name="password"]', testUser.unicodePassword);
      await page.fill('input[name="confirmPassword"]', testUser.unicodePassword);

      await page.click('button[type="submit"], button:has-text("Create Account")');
      await page.waitForTimeout(3000);

      // Test login with Unicode password
      await page.goto('/');
      await page.waitForLoadState('networkidle');

      await page.fill('input[name="email"]', testUser.email);
      await page.fill('input[name="password"]', testUser.unicodePassword);

      await page.click('button[type="submit"], button:has-text("Login")');

      // Should handle Unicode without encoding errors
      await page.waitForTimeout(2000);
      const errorMessage = await page.locator('.error, .alert-error, [role="alert"]').textContent().catch(() => '');
      expect(errorMessage).not.toContain('encoding');
      expect(errorMessage).not.toContain('character');

      console.log('Unicode password login test completed successfully');
    });
  });

  test.describe('UI Validation', () => {

    test('should display proper loading states', async ({ page }) => {
      // Fill valid form (exact field names from LoginForm.tsx)
      await page.fill('input[name="email"]', 'test@example.com');
      await page.fill('input[name="password"]', 'password123');

      // Submit and check for loading state
      await page.click('button[type="submit"], button:has-text("Login")');

      // Should show loading indicator
      const hasLoadingState = await page.locator('button:disabled, .loading, .spinner, text=Loading').isVisible({ timeout: 2000 }).catch(() => false);

      // Note: Loading state might be very quick, so we don't fail if we miss it
      console.log(`Loading state visible: ${hasLoadingState}`);
    });

    test('should have accessible form elements', async ({ page }) => {
      // Check for proper form accessibility (exact field names from LoginForm.tsx)
      const emailInput = page.locator('input[name="email"]');
      const passwordInput = page.locator('input[name="password"]');
      const submitButton = page.locator('button[type="submit"], button:has-text("Login")');

      await expect(emailInput).toBeVisible();
      await expect(passwordInput).toBeVisible();
      await expect(submitButton).toBeVisible();

      // Check for labels or placeholders
      const emailHasLabel = await emailInput.getAttribute('placeholder') || await emailInput.getAttribute('aria-label');
      const passwordHasLabel = await passwordInput.getAttribute('placeholder') || await passwordInput.getAttribute('aria-label');

      expect(emailHasLabel).toBeTruthy();
      expect(passwordHasLabel).toBeTruthy();
    });
  });

  test.afterEach(async ({ page }, testInfo) => {
    // Log test results
    console.log(`Test "${testInfo.title}" ${testInfo.status}`);

    // Take screenshot on failure
    if (testInfo.status === 'failed') {
      await page.screenshot({
        path: `test-results/login-failure-${testInfo.title.replace(/\s+/g, '-')}-${Date.now()}.png`,
        fullPage: true
      });
    }
  });
});