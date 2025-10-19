"""
Algorithm Management Tests

Tests for algorithm CRUD operations, execution, and validation.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.algorithms
@pytest.mark.asyncio
class TestAlgorithms:
    """Test algorithm management endpoints"""

    async def test_create_algorithm_code_mode(
        self,
        client: AsyncClient,
        auth_headers
    ):
        """Test creating algorithm in code mode"""
        response = await client.post(
            "/api/v1/algorithms/",
            headers=auth_headers,
            json={
                "name": "Test Strategy",
                "description": "A test trading strategy",
                "builder_type": "code",
                "strategy_code": "def execute(context):\n    return None",
                "stock_universe": {
                    "type": "specific",
                    "symbols": ["AAPL", "GOOGL"]
                },
                "execution_interval": "1day",
                "max_positions": 5,
                "risk_per_trade": 2.0
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "id" in data["data"]
        assert data["data"]["name"] == "Test Strategy"

    async def test_list_algorithms(
        self,
        client: AsyncClient,
        auth_headers,
        test_algorithm
    ):
        """Test listing user's algorithms"""
        response = await client.get(
            "/api/v1/algorithms/",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) >= 1
        assert any(algo["id"] == test_algorithm["id"] for algo in data["data"])

    async def test_get_algorithm_by_id(
        self,
        client: AsyncClient,
        auth_headers,
        test_algorithm
    ):
        """Test getting algorithm details"""
        response = await client.get(
            f"/api/v1/algorithms/{test_algorithm['id']}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["id"] == test_algorithm["id"]
        assert data["data"]["name"] == test_algorithm["name"]

    async def test_update_algorithm(
        self,
        client: AsyncClient,
        auth_headers,
        test_algorithm
    ):
        """Test updating algorithm"""
        response = await client.put(
            f"/api/v1/algorithms/{test_algorithm['id']}",
            headers=auth_headers,
            json={
                "name": "Updated Strategy",
                "description": "Updated description"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    async def test_delete_algorithm(
        self,
        client: AsyncClient,
        auth_headers,
        test_algorithm
    ):
        """Test deleting algorithm"""
        response = await client.delete(
            f"/api/v1/algorithms/{test_algorithm['id']}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    async def test_toggle_algorithm_status(
        self,
        client: AsyncClient,
        auth_headers,
        test_algorithm
    ):
        """Test toggling algorithm active/inactive"""
        response = await client.post(
            f"/api/v1/algorithms/{test_algorithm['id']}/toggle",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["status"] in ["active", "inactive"]

    async def test_validate_algorithm_code(
        self,
        client: AsyncClient,
        auth_headers
    ):
        """Test code validation"""
        response = await client.post(
            "/api/v1/algorithms/validate",
            headers=auth_headers,
            json={
                "code": "def execute(context):\n    return {'action': 'buy'}"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    async def test_get_algorithm_performance(
        self,
        client: AsyncClient,
        auth_headers,
        test_algorithm
    ):
        """Test getting algorithm performance metrics"""
        response = await client.get(
            f"/api/v1/algorithms/{test_algorithm['id']}/performance",
            headers=auth_headers
        )

        # May return 200 with no data or specific error if no performance data
        assert response.status_code in [200, 404]

    async def test_unauthorized_access_other_user_algorithm(
        self,
        client: AsyncClient,
        test_algorithm
    ):
        """Test that users can't access other users' algorithms"""
        # Create a different user and get their token
        response = await client.post(
            "/auth/register",
            json={
                "email": "other@example.com",
                "password": "password123",
                "full_name": "Other User"
            }
        )

        login_response = await client.post(
            "/auth/login",
            json={
                "email": "other@example.com",
                "password": "password123"
            }
        )

        other_token = login_response.json()["access_token"]
        other_headers = {"Authorization": f"Bearer {other_token}"}

        # Try to access first user's algorithm
        response = await client.get(
            f"/api/v1/algorithms/{test_algorithm['id']}",
            headers=other_headers
        )

        assert response.status_code == 404  # Not found (not authorized)
