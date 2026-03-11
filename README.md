# 🏗️ Clean Architecture in Python — A .NET Developer's Guide

> **Yes, Python supports Clean Architecture AND full OOP.** This project proves it by implementing
> the same patterns you know from .NET Core microservices — using Python's best-in-class libraries.

This project is specifically designed for **staff-level .NET/C# engineers** learning Python.
Every file has C# equivalent comments so you can map your existing knowledge.

---

## 📐 Architecture Layers

```
src/
├── domain/                              # 🟢 Domain Layer (innermost — ZERO dependencies)
│   ├── entities/                        #     Entities, Value Objects, Enums
│   │   ├── base_entity.py              #     BaseEntity with domain events (like Entity<TId>)
│   │   ├── order.py                    #     Order aggregate root with state machine
│   │   └── order_item.py              #     OrderItem child entity
│   ├── interfaces/                     #     Repository abstractions (like IRepository<T>)
│   │   ├── i_order_repository.py      #     IOrderRepository (ABC = interface)
│   │   └── i_unit_of_work.py          #     IUnitOfWork
│   ├── events.py                       #     Domain Events (like INotification in MediatR)
│   └── exceptions.py                   #     Custom exceptions (NotFoundException, etc.)
│
├── application/                         # 🔵 Application Layer (use cases, CQRS)
│   ├── dtos/                           #     DTOs with Pydantic validation
│   │   └── order_dtos.py              #     Request/Response DTOs (FluentValidation + AutoMapper)
│   ├── use_cases/orders/              #     MediatR Command/Query Handlers
│   │   ├── create_order.py            #     CreateOrderCommand + Handler
│   │   ├── get_orders.py              #     GetOrderByIdQuery, GetAllOrdersQuery + Handlers
│   │   ├── update_order.py            #     UpdateOrderCommand + Handler
│   │   ├── change_order_status.py     #     ChangeOrderStatusCommand + Handler (state machine)
│   │   └── delete_order.py            #     DeleteOrderCommand + Handler
│   ├── behaviors.py                    #     MediatR Pipeline Behaviors (logging, perf)
│   └── mappers.py                      #     AutoMapper-style centralized mapping service
│
├── infrastructure/                      # 🟠 Infrastructure Layer (persistence, DI, logging)
│   ├── config.py                       #     Settings (appsettings.json equivalent)
│   ├── container.py                    #     DI Container (IServiceCollection equivalent)
│   ├── logging.py                      #     Structlog config (Serilog equivalent)
│   ├── persistence/
│   │   ├── database.py                #     SQLAlchemy engine (DbContext configuration)
│   │   └── models.py                  #     ORM models (EF Core entity configurations)
│   └── repositories/
│       ├── mappers.py                  #     Entity ↔ ORM Model mapping (AutoMapper profiles)
│       ├── order_repository.py        #     OrderRepository implementation
│       └── unit_of_work.py            #     UnitOfWork implementation
│
├── presentation/                        # 🔴 Presentation Layer (API)
│   ├── api/
│   │   ├── order_routes.py            #     OrdersController (FastAPI router)
│   │   └── health_routes.py           #     Health check endpoint
│   └── middleware/
│       ├── exception_handlers.py      #     Global exception handling (ProblemDetails)
│       └── correlation_id.py          #     X-Correlation-ID middleware
│
└── main.py                             #     Program.cs equivalent — app startup

tests/
├── test_domain.py                       #     Domain entity unit tests (25 tests)
├── test_validation.py                   #     FluentValidation-style DTO tests
├── test_mappers.py                      #     AutoMapper mapping tests
├── test_exceptions.py                   #     Domain exception hierarchy tests
└── test_integration.py                  #     Full HTTP API integration tests (17 tests)
```

---

## 🔄 .NET ↔ Python Mapping (Complete Reference)

### Core Architecture

| .NET Core Concept | Python Equivalent | File |
|---|---|---|
| `Program.cs` | `main.py` (app factory) | `src/main.py` |
| `IServiceCollection` / DI | `dependency-injector` Container | `src/infrastructure/container.py` |
| `DbContext` / EF Core | SQLAlchemy 2.0 async engine | `src/infrastructure/persistence/` |
| EF Core Migrations | Alembic | `alembic/` |
| `appsettings.json` | `.env` + Pydantic Settings | `src/infrastructure/config.py` |

### MediatR / CQRS

| .NET Core Concept | Python Equivalent | File |
|---|---|---|
| `IRequest<T>` | `@dataclass` command/query | `src/application/use_cases/` |
| `IRequestHandler<T,R>` | `@Mediator.handler` class | `src/application/use_cases/` |
| `IPipelineBehavior<T,R>` | Custom behavior classes | `src/application/behaviors.py` |
| `INotification` | Domain event dataclasses | `src/domain/events.py` |

### Validation & Mapping

| .NET Core Concept | Python Equivalent | File |
|---|---|---|
| FluentValidation | Pydantic `Field(...)` + `@field_validator` | `src/application/dtos/order_dtos.py` |
| AutoMapper `IMapper` | `OrderMapper` + `model_validate()` | `src/application/mappers.py` |
| AutoMapper Profiles | Infra `mappers.py` (Entity ↔ ORM) | `src/infrastructure/repositories/mappers.py` |

### Domain-Driven Design

| .NET Core Concept | Python Equivalent | File |
|---|---|---|
| `abstract class` / `interface` | `ABC` (Abstract Base Class) | `src/domain/interfaces/` |
| `AggregateRoot` | `BaseEntity` with domain events | `src/domain/entities/base_entity.py` |
| Domain Events | `DomainEvent` dataclasses | `src/domain/events.py` |
| Custom Exceptions | `DomainException` hierarchy | `src/domain/exceptions.py` |

### Web / API

| .NET Core Concept | Python Equivalent | File |
|---|---|---|
| `[ApiController]` | FastAPI `APIRouter` | `src/presentation/api/` |
| `app.UseExceptionHandler()` | Exception handler functions | `src/presentation/middleware/` |
| `app.UseCorrelationId()` | `CorrelationIdMiddleware` | `src/presentation/middleware/correlation_id.py` |
| Serilog | Structlog | `src/infrastructure/logging.py` |
| Swagger / Swashbuckle | FastAPI built-in `/swagger` | Built-in |
| xUnit / NUnit | pytest | `tests/` |

---

## 🧠 Python OOP for .NET Developers

Python **fully supports OOP**. Here's the mapping:

```python
# C#: public interface IOrderRepository { Task<Order?> GetByIdAsync(int id); }
# Python:
class IOrderRepository(ABC):
    @abstractmethod
    async def get_by_id(self, order_id: int) -> Order | None: ...

# C#: public class Order : AggregateRoot { private readonly List<OrderItem> _items; }
# Python:
class Order(BaseEntity):
    def __init__(self, customer_name: str, shipping_address: str):
        super().__init__()
        self.customer_name = customer_name
        self.items: list[OrderItem] = []

# C#: public class OrderRepository : IOrderRepository { }
# Python:
class OrderRepository(IOrderRepository):
    def __init__(self, session: AsyncSession):
        self._session = session
    async def get_by_id(self, order_id: int) -> Order | None: ...

# C#: public enum OrderStatus { Pending, Confirmed, Shipped }
# Python:
class OrderStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    SHIPPED = "shipped"

# C#: throw new NotFoundException(nameof(Order), orderId);
# Python:
raise NotFoundException("Order", order_id)

# C#: var dto = _mapper.Map<OrderResponseDto>(order);
# Python:
dto = OrderMapper.to_response_dto(order)
# or: dto = OrderResponseDto.model_validate(order)
```

---

## 🚀 Quick Start

### 1. Start PostgreSQL
```bash
docker-compose up -d
```

### 2. Install dependencies
```bash
pip install -e ".[dev]"
```

### 3. Run the application
```bash
cd src
uvicorn main:app --reload
```

### 4. Open Swagger UI
Navigate to: **http://localhost:8000/swagger**

### 5. Run tests (60 tests!)
```bash
pytest tests/ -v
```

---

## 📡 API Endpoints

| Method | Endpoint | Description | C# Equivalent |
|---|---|---|---|
| `GET` | `/health` | Health check | `[HttpGet("/health")]` |
| `POST` | `/api/orders` | Create a new order | `[HttpPost]` |
| `GET` | `/api/orders` | Get all orders | `[HttpGet]` |
| `GET` | `/api/orders/{id}` | Get order by ID | `[HttpGet("{id}")]` |
| `PUT` | `/api/orders/{id}` | Update an order | `[HttpPut("{id}")]` |
| `POST` | `/api/orders/{id}/status` | Change order status | `[HttpPost("{id}/status")]` |
| `DELETE` | `/api/orders/{id}` | Delete an order | `[HttpDelete("{id}")]` |

### Example: Create Order
```json
POST /api/orders
{
  "customer_name": "John Doe",
  "shipping_address": "123 Main St, Springfield, IL 62701",
  "items": [
    { "product_name": "Widget Pro", "quantity": 2, "unit_price": 29.99 },
    { "product_name": "Gadget Lite", "quantity": 1, "unit_price": 14.99 }
  ]
}
```

### Example: Change Order Status (State Machine)
```json
POST /api/orders/1/status
{ "action": "confirm" }

POST /api/orders/1/status
{ "action": "ship" }

POST /api/orders/1/status
{ "action": "deliver" }

POST /api/orders/1/status
{ "action": "cancel", "reason": "Customer changed their mind" }
```

### Example: Update Order
```json
PUT /api/orders/1
{
  "customer_name": "Jane Doe",
  "shipping_address": "456 Oak Avenue, Portland, OR 97201"
}
```

---

## 🧪 Running Migrations (like `dotnet ef migrations add`)

```bash
# Generate a migration
alembic revision --autogenerate -m "initial"

# Apply migrations
alembic upgrade head
```

---

## 🔧 Key Libraries → .NET Equivalents

| Python Library | .NET Equivalent | Purpose |
|---|---|---|
| `FastAPI` | ASP.NET Core | Web framework |
| `SQLAlchemy 2.0` | Entity Framework Core | ORM / data access |
| `Pydantic` | FluentValidation + AutoMapper | Validation + mapping |
| `mediatr-py` | MediatR | CQRS / mediator pattern |
| `dependency-injector` | `IServiceCollection` | Dependency injection |
| `Structlog` | Serilog | Structured logging |
| `Alembic` | EF Core Migrations | Database migrations |
| `pytest` | xUnit / NUnit | Testing framework |
| `asyncpg` | Npgsql | PostgreSQL async driver |

---

## ✅ Test Coverage (60 tests)

- **Domain Entity Tests** — Order state machine, business rules, computed properties
- **Domain Event Tests** — Events raised on confirm, cancel, create
- **Exception Tests** — Custom exception hierarchy
- **Validation Tests** — Pydantic/FluentValidation field constraints
- **Mapper Tests** — AutoMapper-style Entity ↔ DTO mapping
- **Integration Tests** — Full HTTP API tests using in-memory SQLite (like WebApplicationFactory in C#)

