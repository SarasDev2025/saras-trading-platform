// Authentication helper for tests
const API_BASE_URL = 'http://localhost:8000';

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

export { API_BASE_URL };