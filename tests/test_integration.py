"""
Integration tests — equivalent to WebApplicationFactory<Program> integration tests in C#.

In .NET:
    public class OrdersControllerTests : IClassFixture<WebApplicationFactory<Program>> {
        private readonly HttpClient _client;
        public OrdersControllerTests(WebApplicationFactory<Program> factory) {
            _client = factory.CreateClient();
        }

        [Fact]
        public async Task CreateOrder_ReturnsCreated() {
            var response = await _client.PostAsJsonAsync("/api/orders", new { ... });
            response.EnsureSuccessStatusCode();
            Assert.Equal(HttpStatusCode.Created, response.StatusCode);
        }
    }

In Python we use httpx.AsyncClient with FastAPI's TestClient.
These tests use an in-memory SQLite database (no PostgreSQL needed).
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from dependency_injector import providers

from infrastructure.persistence.models import Base
from infrastructure.repositories.unit_of_work import UnitOfWork
from infrastructure.container import create_mediator
from main import create_app


# ── Test fixtures (like IClassFixture<WebApplicationFactory> in C#) ──────

@pytest_asyncio.fixture
async def test_app():
    """
    Create a test application with an in-memory SQLite database.
    Equivalent to WebApplicationFactory<Program> with custom configuration.
    """
    # Use in-memory SQLite for tests (no PostgreSQL required)
    test_engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )
    test_session_factory = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    # Create tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Build the app and override the DI container
    app = create_app()

    # Override the container's session_factory and unit_of_work using proper providers
    app.state.container.session_factory.override(providers.Object(test_session_factory))
    app.state.container.unit_of_work.override(
        providers.Factory(UnitOfWork, session_factory=test_session_factory)
    )

    # Re-create mediator with overridden container
    app.state.mediator = create_mediator(app.state.container)

    yield app

    # Cleanup
    app.state.container.session_factory.reset_override()
    app.state.container.unit_of_work.reset_override()
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()


@pytest_asyncio.fixture
async def client(test_app):
    """
    HTTP client for testing — like HttpClient from WebApplicationFactory.
    """
    transport = ASGITransport(app=test_app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        follow_redirects=True,  # Like .NET HttpClient — follow 307 trailing-slash redirects
    ) as ac:
        yield ac


# ── Health Check Tests ───────────────────────────────────────────────────

class TestHealthEndpoint:
    @pytest.mark.asyncio
    async def test_health_check_returns_healthy(self, client: AsyncClient):
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


# ── Create Order Tests ───────────────────────────────────────────────────

class TestCreateOrder:
    """Like OrdersControllerTests in C# integration tests."""

    @pytest.mark.asyncio
    async def test_create_order_returns_201(self, client: AsyncClient):
        """
        Equivalent to:
            [Fact]
            public async Task CreateOrder_ReturnsCreated() {
                var response = await _client.PostAsJsonAsync("/api/orders", payload);
                Assert.Equal(HttpStatusCode.Created, response.StatusCode);
            }
        """
        payload = {
            "customer_name": "John Doe",
            "shipping_address": "123 Main St, Springfield, IL 62701",
            "items": [
                {"product_name": "Widget Pro", "quantity": 2, "unit_price": 29.99},
                {"product_name": "Gadget Lite", "quantity": 1, "unit_price": 14.99},
            ],
        }
        response = await client.post("/api/orders", json=payload)
        assert response.status_code == 201

        data = response.json()
        assert data["customer_name"] == "John Doe"
        assert data["status"] == "pending"
        assert data["item_count"] == 2
        assert data["total"] == pytest.approx(74.97)
        assert data["id"] is not None

    @pytest.mark.asyncio
    async def test_create_order_validation_fails_empty_items(self, client: AsyncClient):
        """FluentValidation equivalent: empty items list should fail."""
        payload = {
            "customer_name": "John Doe",
            "shipping_address": "123 Main St, Springfield, IL 62701",
            "items": [],
        }
        response = await client.post("/api/orders", json=payload)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_order_validation_fails_short_name(self, client: AsyncClient):
        payload = {
            "customer_name": "J",
            "shipping_address": "123 Main St, Springfield, IL 62701",
            "items": [{"product_name": "Widget", "quantity": 1, "unit_price": 9.99}],
        }
        response = await client.post("/api/orders", json=payload)
        assert response.status_code == 422


# ── Get Orders Tests ─────────────────────────────────────────────────────

class TestGetOrders:

    @pytest.mark.asyncio
    async def test_get_all_orders_empty(self, client: AsyncClient):
        response = await client.get("/api/orders")
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_get_all_orders_after_create(self, client: AsyncClient):
        # Create an order first
        payload = {
            "customer_name": "John Doe",
            "shipping_address": "123 Main St, Springfield, IL 62701",
            "items": [{"product_name": "Widget", "quantity": 1, "unit_price": 9.99}],
        }
        await client.post("/api/orders", json=payload)

        response = await client.get("/api/orders")
        assert response.status_code == 200
        orders = response.json()
        assert len(orders) == 1
        assert orders[0]["customer_name"] == "John Doe"

    @pytest.mark.asyncio
    async def test_get_order_by_id(self, client: AsyncClient):
        # Create
        payload = {
            "customer_name": "Jane Doe",
            "shipping_address": "456 Oak Ave, Portland, OR 97201",
            "items": [{"product_name": "Gadget", "quantity": 3, "unit_price": 14.99}],
        }
        create_response = await client.post("/api/orders", json=payload)
        order_id = create_response.json()["id"]

        # Get by ID
        response = await client.get(f"/api/orders/{order_id}")
        assert response.status_code == 200
        assert response.json()["customer_name"] == "Jane Doe"

    @pytest.mark.asyncio
    async def test_get_nonexistent_order_returns_404(self, client: AsyncClient):
        response = await client.get("/api/orders/99999")
        assert response.status_code == 404


# ── Update Order Tests ───────────────────────────────────────────────────

class TestUpdateOrder:

    @pytest.mark.asyncio
    async def test_update_order_customer_name(self, client: AsyncClient):
        # Create
        payload = {
            "customer_name": "John Doe",
            "shipping_address": "123 Main St, Springfield, IL 62701",
            "items": [{"product_name": "Widget", "quantity": 1, "unit_price": 9.99}],
        }
        create_response = await client.post("/api/orders", json=payload)
        order_id = create_response.json()["id"]

        # Update
        update_payload = {"customer_name": "Jane Doe"}
        response = await client.put(f"/api/orders/{order_id}", json=update_payload)
        assert response.status_code == 200
        assert response.json()["customer_name"] == "Jane Doe"

    @pytest.mark.asyncio
    async def test_update_nonexistent_order_returns_404(self, client: AsyncClient):
        response = await client.put("/api/orders/99999", json={"customer_name": "Test"})
        assert response.status_code == 404


# ── Change Order Status Tests ────────────────────────────────────────────

class TestChangeOrderStatus:

    @pytest.mark.asyncio
    async def test_confirm_order(self, client: AsyncClient):
        # Create
        payload = {
            "customer_name": "John Doe",
            "shipping_address": "123 Main St, Springfield, IL 62701",
            "items": [{"product_name": "Widget", "quantity": 1, "unit_price": 9.99}],
        }
        create_response = await client.post("/api/orders", json=payload)
        order_id = create_response.json()["id"]

        # Confirm
        response = await client.post(
            f"/api/orders/{order_id}/status",
            json={"action": "confirm"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "confirmed"

    @pytest.mark.asyncio
    async def test_full_lifecycle(self, client: AsyncClient):
        """Test Pending → Confirmed → Shipped → Delivered."""
        # Create
        payload = {
            "customer_name": "John Doe",
            "shipping_address": "123 Main St, Springfield, IL 62701",
            "items": [{"product_name": "Widget", "quantity": 1, "unit_price": 9.99}],
        }
        create_response = await client.post("/api/orders", json=payload)
        order_id = create_response.json()["id"]

        # Confirm
        r = await client.post(f"/api/orders/{order_id}/status", json={"action": "confirm"})
        assert r.json()["status"] == "confirmed"

        # Ship
        r = await client.post(f"/api/orders/{order_id}/status", json={"action": "ship"})
        assert r.json()["status"] == "shipped"

        # Deliver
        r = await client.post(f"/api/orders/{order_id}/status", json={"action": "deliver"})
        assert r.json()["status"] == "delivered"

    @pytest.mark.asyncio
    async def test_invalid_transition_returns_422(self, client: AsyncClient):
        """Trying to ship a pending order should fail with 422."""
        payload = {
            "customer_name": "John Doe",
            "shipping_address": "123 Main St, Springfield, IL 62701",
            "items": [{"product_name": "Widget", "quantity": 1, "unit_price": 9.99}],
        }
        create_response = await client.post("/api/orders", json=payload)
        order_id = create_response.json()["id"]

        # Try to ship without confirming first
        response = await client.post(
            f"/api/orders/{order_id}/status",
            json={"action": "ship"},
        )
        assert response.status_code == 422


# ── Delete Order Tests ───────────────────────────────────────────────────

class TestDeleteOrder:

    @pytest.mark.asyncio
    async def test_delete_order(self, client: AsyncClient):
        # Create
        payload = {
            "customer_name": "John Doe",
            "shipping_address": "123 Main St, Springfield, IL 62701",
            "items": [{"product_name": "Widget", "quantity": 1, "unit_price": 9.99}],
        }
        create_response = await client.post("/api/orders", json=payload)
        order_id = create_response.json()["id"]

        # Delete
        response = await client.delete(f"/api/orders/{order_id}")
        assert response.status_code == 204

        # Verify it's gone
        get_response = await client.get(f"/api/orders/{order_id}")
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_nonexistent_order_returns_404(self, client: AsyncClient):
        response = await client.delete("/api/orders/99999")
        assert response.status_code == 404


# ── Correlation ID Tests ─────────────────────────────────────────────────

class TestCorrelationId:

    @pytest.mark.asyncio
    async def test_correlation_id_generated(self, client: AsyncClient):
        """Response should include X-Correlation-ID header."""
        response = await client.get("/health")
        assert "x-correlation-id" in response.headers

    @pytest.mark.asyncio
    async def test_correlation_id_forwarded(self, client: AsyncClient):
        """If we send X-Correlation-ID, it should be echoed back."""
        response = await client.get(
            "/health",
            headers={"X-Correlation-ID": "my-custom-id-123"},
        )
        assert response.headers["x-correlation-id"] == "my-custom-id-123"



