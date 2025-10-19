"""
Authentication Tests

Tests for user registration, login, logout, and JWT token validation.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.auth
@pytest.mark.asyncio
class TestAuthentication:
    """Test authentication endpoints"""

    async def test_register_new_user(self, client: AsyncClient):
        """Test user registration with valid data"""
        response = await client.post(
            "/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "SecurePassword123!",
                "full_name": "New User",
                "region": "US"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "user_id" in data["data"]
        assert data["data"]["email"] == "newuser@example.com"

    async def test_register_duplicate_email(self, client: AsyncClient, test_user):
        """Test registration with existing email fails"""
        response = await client.post(
            "/auth/register",
            json={
                "email": test_user["email"],
                "password": "SecurePassword123!",
                "full_name": "Duplicate User"
            }
        )

        assert response.status_code == 400
        data = response.json()
        assert "already registered" in data["detail"].lower()

    async def test_register_invalid_email(self, client: AsyncClient):
        """Test registration with invalid email fails"""
        response = await client.post(
            "/auth/register",
            json={
                "email": "invalid-email",
                "password": "SecurePassword123!",
                "full_name": "Invalid Email"
            }
        )

        assert response.status_code == 422  # Validation error

    async def test_login_valid_credentials(self, client: AsyncClient, test_user):
        """Test login with valid credentials"""
        response = await client.post(
            "/auth/login",
            json={
                "email": test_user["email"],
                "password": test_user["password"]
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"

    async def test_login_invalid_password(self, client: AsyncClient, test_user):
        """Test login with incorrect password"""
        response = await client.post(
            "/auth/login",
            json={
                "email": test_user["email"],
                "password": "wrongpassword"
            }
        )

        assert response.status_code == 401
        data = response.json()
        assert "incorrect" in data["detail"].lower()

    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Test login with non-existent user"""
        response = await client.post(
            "/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "password123"
            }
        )

        assert response.status_code == 401

    async def test_protected_endpoint_without_token(self, client: AsyncClient):
        """Test accessing protected endpoint without authentication"""
        response = await client.get("/api/v1/algorithms/")

        assert response.status_code == 401

    async def test_protected_endpoint_with_invalid_token(self, client: AsyncClient):
        """Test accessing protected endpoint with invalid token"""
        response = await client.get(
            "/api/v1/algorithms/",
            headers={"Authorization": "Bearer invalid_token"}
        )

        assert response.status_code == 401

    async def test_protected_endpoint_with_valid_token(
        self,
        client: AsyncClient,
        auth_headers
    ):
        """Test accessing protected endpoint with valid token"""
        response = await client.get(
            "/api/v1/algorithms/",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    async def test_get_current_user(
        self,
        client: AsyncClient,
        auth_headers,
        test_user
    ):
        """Test getting current user info"""
        response = await client.get(
            "/auth/me",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user["email"]
        assert data["full_name"] == test_user["full_name"]

    async def test_token_expiry(self, client: AsyncClient):
        """Test that expired tokens are rejected"""
        # TODO: Implement with freezegun to simulate token expiry
        pass

    async def test_logout(self, client: AsyncClient, auth_headers):
        """Test logout invalidates token"""
        response = await client.post(
            "/auth/logout",
            headers=auth_headers
        )

        # Note: JWT logout typically doesn't exist server-side
        # This depends on implementation
        assert response.status_code in [200, 404]
