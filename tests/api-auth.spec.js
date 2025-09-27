import { test, expect } from '@playwright/test';

const API_BASE_URL = 'http://localhost:8000';

// Test authentication endpoints
test.describe('Authentication API', () => {
  test('should login with valid credentials', async ({ request }) => {
    const response = await request.post(`${API_BASE_URL}/auth/login`, {
      form: {
        username: 'john.doe@example.com',
        password: 'password123'
      }
    });

    expect(response.ok()).toBeTruthy();
    const data = await response.json();
    expect(data.success).toBe(true);
    expect(data.data).toHaveProperty('access_token');
    expect(data.data).toHaveProperty('token_type', 'bearer');
  });

  test('should reject invalid credentials', async ({ request }) => {
    const response = await request.post(`${API_BASE_URL}/auth/login`, {
      form: {
        username: 'invalid@example.com',
        password: 'wrongpassword'
      }
    });

    // API might return 400 or 401, both indicate authentication failure
    expect([400, 401]).toContain(response.status());
  });
});

// Export auth helper function
export async function getAuthToken(request) {
  const response = await request.post(`${API_BASE_URL}/auth/login`, {
    form: {
      username: 'john.doe@example.com',
      password: 'password123'
    }
  });

  if (!response.ok()) {
    throw new Error(`Failed to authenticate: ${response.status()}`);
  }

  const data = await response.json();
  return data.data.access_token;
}