# innoERP Architecture

## Technology Stack

### Backend

- **FastAPI** - Modern Python web framework for building APIs
- **SQLAlchemy** - ORM for database operations
- **Pydantic** - Data validation and settings management
- **Uvicorn** - ASGI server for running FastAPI applications

### Messaging & Caching

- **Apache Kafka** - Distributed streaming platform for event-driven architecture
- **Redis** - In-memory data store for caching and sessions

### Database

- **PostgreSQL** - Relational database with multi-tenancy support

### Logging & Monitoring

- **EFK Stack**:
  - **Elasticsearch** - Search and analytics engine
  - **Fluentd** - Log collection and forwarding
  - **Kibana** - Visualization and dashboards

### Authentication

- **JWT** (JSON Web Tokens) - Stateless authentication
- **bcrypt** - Password hashing

### Frontend (Planned)

- **Next.js** - React framework for frontend development

## Service Architecture Decision

### Approach: One Service Per Module (True Microservices)

Each business module is a **separate, independent service** for true plug-and-play capability.

### Service List

#### ✅ **Implemented Services** (Phase 1 - Currently Working)

1. **api-gateway** (Port 8000) - Main entry point, routes to all services

   - Service registry and routing
   - Authentication middleware
   - Tenant identification middleware
   - CORS configuration
   - Health check endpoint

2. **tenant-service** (Port 8001) - Organization and subscription management

   - Organization CRUD operations
   - Subscription plans management
   - Organization subscriptions
   - Module enable/disable management
   - Stripe integration (planned)

3. **auth-service** (Port 8002) - Authentication and authorization

   - User registration
   - Login/logout
   - JWT token generation and validation
   - Token refresh
   - Password hashing (bcrypt)

4. **user-service** (Port 8003) - User profile management
   - User profiles
   - User-organization relationships
   - Profile updates

#### 📋 **Planned Services** (Future Phases)

5. **project-service** - Project and task management
6. **employee-service** - Employee management
7. **attendance-service** - Attendance tracking
8. **leave-service** - Leave management
9. **finance-service** - Financial/accounting (Account module)
   - Chart of accounts
   - Expenses
   - Revenue
   - Invoices
   - Bank accounts
   - Vendors
   - Reimbursements
10. **crm-service** - CRM (leads, contacts)
11. **career-service** - Career (job postings, applications)
12. **portfolio-service** - Portfolio management
13. **products-service** - Products & Services
14. **contact-service** - Contact management
15. **notification-service** - Notifications (email, in-app)

**Total: 15 services** (4 implemented, 11 planned)

### Benefits of This Approach

✅ **True Plug-and-Play**: Each module can be enabled/disabled independently
✅ **Independent Scaling**: Scale only the services that need it
✅ **Technology Flexibility**: Each service can use different tech if needed
✅ **Team Autonomy**: Different teams can work on different services
✅ **Fault Isolation**: If one service fails, others continue working

### Service Communication

- **Synchronous**: HTTP/REST via API Gateway
  - All external requests go through API Gateway
  - Services can call each other directly for internal communication
  - Service-to-service calls use service URLs from config
- **Asynchronous**: Kafka events for decoupled communication
  - Event-driven architecture for non-critical operations
  - Events: UserCreated, OrganizationCreated, etc.
  - Services publish events to Kafka topics
- **Caching**: Redis for shared cache
  - Session storage
  - Rate limiting
  - Temporary data storage

### Infrastructure Services (Docker)

All infrastructure services run in Docker containers:

- **Kafka** (Port 9092) - Message queue for asynchronous communication
- **Zookeeper** (Port 2181) - Kafka coordination and metadata management
- **Redis** (Port 6380) - Caching and session storage
- **Elasticsearch** (Port 9200) - Log storage and search
- **Kibana** (Port 5601) - Log visualization and dashboards
- **Fluentd** (Port 24224) - Log collection and forwarding

**Note**: Redis uses port 6380 (instead of default 6379) to avoid conflicts with existing Redis instances.

### Database (PostgreSQL)

- **PostgreSQL** - Runs on local or remote server, configured via `.env` file
- All services connect to the same database (shared database multi-tenancy)
- Multi-tenancy via `organization_id` column on all business tables
- Row-level security for additional isolation (planned)
- UUID primary keys for all tables
- Automatic timestamp management (`created_at`, `updated_at`)

## Module Enable/Disable System

Each organization can enable/disable modules via:

- `OrganizationModule` table in tenant-service
- API Gateway checks module availability before routing
- Frontend dynamically shows/hides module UI based on enabled modules

## Project Structure

```
innoERP/
├── setup.py                  # Setup script (creates venv, installs dependencies)
├── start_services.py         # Start all services concurrently
├── .env                      # Environment variables (database, Kafka, Redis, etc.)
├── services/                 # Microservices
│   ├── api-gateway/
│   ├── tenant-service/
│   ├── auth-service/
│   ├── user-service/
│   └── [future services...]
├── shared/                   # Shared libraries
│   ├── common/              # Common utilities (logging, errors, tenant context)
│   ├── database/            # Database base (SQLAlchemy models, session management)
│   └── kafka/               # Kafka client and event schemas
├── infrastructure/          # Infrastructure configuration
│   ├── docker-compose.dev.yml  # Docker Compose for dev infrastructure
│   └── init_db.py           # Database initialization script
├── monitoring/              # Monitoring and logging
│   └── efk/                 # EFK stack configuration
└── frontend/                # Next.js frontend (planned)
```

## Shared Libraries

### `shared/common/`

- **logging.py**: Structured logging with service context
- **errors.py**: Custom exception classes (ResourceNotFoundError, ValidationError)
- **tenant_context.py**: Tenant context management (for multi-tenancy)

### `shared/database/`

- **base.py**: SQLAlchemy base model, engine, session management
- All services use the same database connection
- Automatic `.env` loading for database configuration

### `shared/kafka/`

- **client.py**: Kafka producer client
- **schemas.py**: Pydantic models for Kafka events (UserCreatedEvent, OrganizationCreatedEvent, etc.)

## Multi-Tenancy

- **Shared Database**: All services connect to the same PostgreSQL database
- **Tenant Isolation**: Via `organization_id` column on all business tables
- **Row-Level Security**: Additional isolation layer (planned)
- **Tenant Context**: Middleware automatically extracts tenant from request headers/subdomain

## Database Schema

- **UUID Primary Keys**: All tables use UUID for primary keys
- **Timestamps**: `created_at` and `updated_at` on all tables
- **Soft Deletes**: `deleted_at` for soft deletion (where applicable)
- **Organization ID**: `organization_id` on all business tables for multi-tenancy

## Setup and Development

### Initial Setup

1. **Install Dependencies**:

   ```bash
   python3 setup.py
   ```

2. **Start Infrastructure** (Docker):

   ```bash
   cd infrastructure
   docker-compose -f docker-compose.dev.yml up -d
   cd ..
   ```

3. **Initialize Database**:

   ```bash
   source venv/bin/activate
   export PYTHONPATH=$(pwd)
   python infrastructure/init_db.py
   ```

4. **Start All Services**:
   ```bash
   python start_services.py
   ```

### Environment Configuration

Create `.env` file in project root:

```env
DATABASE_URL=postgresql://user:password@host:port/database
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
REDIS_URL=redis://localhost:6380
SECRET_KEY=your-secret-key-change-in-production
```

## API Documentation

All services provide interactive API documentation via Swagger UI:

- **API Gateway**: http://localhost:8000/docs
- **Tenant Service**: http://localhost:8001/docs
- **Auth Service**: http://localhost:8002/docs
- **User Service**: http://localhost:8003/docs

## Deployment Strategy

### Development

- Services run locally via `uvicorn` (managed by `start_services.py`)
- Infrastructure (Kafka, Zookeeper, Redis, EFK) runs in Docker
- Database runs on local/remote PostgreSQL server (configured via `.env`)
- Hot reload enabled for all services
- Cross-platform Python scripts for setup and service management

### Production

- Services can run in Kubernetes
- Or use Docker Compose for simpler deployments
- Database can be managed PostgreSQL (RDS, etc.)
- Infrastructure services remain in Docker/Kubernetes
- Environment variables managed via secrets/config maps
