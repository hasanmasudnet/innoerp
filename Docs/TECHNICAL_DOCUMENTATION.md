# innoERP - Complete Technical Documentation

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [Technology Stack](#technology-stack)
4. [Microservices Architecture](#microservices-architecture)
5. [Infrastructure Components](#infrastructure-components)
6. [Database Architecture](#database-architecture)
7. [Logging and Monitoring](#logging-and-monitoring)
8. [Module Management System](#module-management-system)
9. [Authentication and Authorization](#authentication-and-authorization)
10. [API Gateway](#api-gateway)
11. [Frontend Architecture](#frontend-architecture)
12. [Deployment Architecture](#deployment-architecture)
13. [Development Workflow](#development-workflow)
14. [Security Considerations](#security-considerations)

---

## System Overview

**innoERP** is a modern, enterprise-grade, multi-tenant ERP (Enterprise Resource Planning) system built with a microservices architecture. The system is designed to support high-volume users, transaction data, and provides a module-wise approach where each business module operates as an independent microservice.

### Key Features

- **Multi-Tenancy**: Complete tenant isolation with subdomain-based routing
- **Module-Based Architecture**: Plug-and-play modules that can be enabled/disabled per tenant
- **Industry Templates**: Pre-configured module sets for different industries
- **Super Admin Dashboard**: Centralized management for system administration
- **Real-time Monitoring**: Comprehensive logging and metrics collection
- **Scalable Infrastructure**: Built for horizontal scaling and high availability

---

## Architecture

### High-Level Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                         Frontend (Next.js)                   │
│                    http://{tenant}.innoerp.io                │
│                    http://admin.innoerp.io                   │
└────────────────────────────┬─────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────┐
│                        API Gateway (8000)                    │
│              - Request Routing                               │
│              - Authentication                                │
│              - Rate Limiting                                 │
│              - Request Logging                               │
└──────────────┬─────────────┬─────────────┬───────────────────┘
               │             │             │
       ┌───────┴───┐  ┌──────┴────┐  ┌─────┴──────┐
       │  Tenant   │  │   Auth    │  │    User    │
       │  Service  │  │  Service  │  │  Service   │
       │   (8001)  │  │   (8002)  │  │   (8003)   │
       └───────┬───┘  └──────┬────┘  └─────┬──────┘
               │             │             │
               └─────────────┴─────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  PostgreSQL  │    │    Kafka     │    │    Redis     │
│  (Database)  │    │  (Messaging) │    │   (Cache)    │
└──────────────┘    └──────────────┘    └──────────────┘
        │                    │                    │
        └────────────────────┼────────────────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │   EFK Stack     │
                    │  Elasticsearch  │
                    │    Fluentd      │
                    │     Kibana      │
                    └─────────────────┘
```

### Architecture Principles

1. **Microservices**: Each business module is an independent service
2. **API Gateway Pattern**: Single entry point for all client requests
3. **Event-Driven**: Asynchronous communication via Kafka
4. **Caching Strategy**: Redis for read-heavy operations
5. **Centralized Logging**: EFK stack for log aggregation
6. **Multi-Tenancy**: Subdomain-based tenant isolation

---

## Technology Stack

### Backend

| Component            | Technology      | Version  | Purpose                              |
| -------------------- | --------------- | -------- | ------------------------------------ |
| **Framework**        | FastAPI         | ≥0.104.1 | RESTful API framework                |
| **ASGI Server**      | Uvicorn         | ≥0.24.0  | ASGI server with standard extensions |
| **ORM**              | SQLAlchemy      | ≥2.0.23  | Database ORM                         |
| **Database Driver**  | psycopg2-binary | ≥2.9.9   | PostgreSQL adapter                   |
| **Validation**       | Pydantic        | ≥2.5.0   | Data validation and serialization    |
| **Authentication**   | python-jose     | ≥3.3.0   | JWT token handling                   |
| **Password Hashing** | passlib[bcrypt] | ≥1.7.4   | Secure password hashing              |
| **Message Queue**    | kafka-python    | ≥2.0.2   | Kafka client for Python              |
| **Logging**          | EALogger        | ≥0.1.0   | Structured logging library           |
| **HTTP Client**      | httpx           | ≥0.25.0  | Async HTTP client                    |

### Frontend

| Component            | Technology        | Version  | Purpose                  |
| -------------------- | ----------------- | -------- | ------------------------ |
| **Framework**        | Next.js           | 16.x     | React framework with SSR |
| **UI Library**       | Material-UI (MUI) | v7       | Component library        |
| **HTTP Client**      | Axios             | Latest   | API communication        |
| **State Management** | React Context     | Built-in | Global state management  |
| **Charts**           | Recharts          | Latest   | Data visualization       |
| **Build Tool**       | Turbopack         | Built-in | Next.js bundler          |

### Infrastructure

| Component            | Technology          | Version   | Purpose                       |
| -------------------- | ------------------- | --------- | ----------------------------- |
| **Database**         | PostgreSQL          | Latest    | Primary database              |
| **Cache**            | Redis               | 7-alpine  | In-memory cache               |
| **Message Broker**   | Apache Kafka        | 7.4.0     | Event streaming               |
| **Zookeeper**        | Confluent Zookeeper | Latest    | Kafka coordination            |
| **Search Engine**    | Elasticsearch       | 8.11.0    | Log indexing and search       |
| **Log Collector**    | Fluentd             | v1-debian | Log aggregation               |
| **Visualization**    | Kibana              | 8.11.0    | Log and metrics visualization |
| **Containerization** | Docker              | Latest    | Container runtime             |
| **Orchestration**    | Docker Compose      | Latest    | Multi-container orchestration |

### Development Tools

| Tool                    | Purpose                     |
| ----------------------- | --------------------------- |
| **Python 3.11+**        | Backend runtime             |
| **Node.js 18+**         | Frontend runtime            |
| **Git**                 | Version control             |
| **Virtual Environment** | Python dependency isolation |

---

## Microservices Architecture

### Service Overview

The system consists of multiple independent microservices, each handling a specific business domain:

#### 1. API Gateway (Port 8000)

**Purpose**: Single entry point for all client requests

**Responsibilities**:

- Request routing to appropriate services
- Authentication and authorization
- Rate limiting
- Request/response logging
- CORS handling
- Request validation

**Key Features**:

- JWT token validation
- Tenant context extraction from subdomain
- Service discovery and routing
- Request logging middleware

**Endpoints**:

- `/api/v1/*` - Proxies to backend services
- `/health` - Health check
- `/docs` - OpenAPI documentation

#### 2. Tenant Service (Port 8001)

**Purpose**: Organization and subscription management

**Responsibilities**:

- Organization (tenant) CRUD operations
- Subscription plan management
- Module assignment to organizations
- Industry template management
- Module registry management
- Branding and theme customization

**Key Features**:

- Multi-tenant organization management
- Industry-based module auto-assignment
- Subscription lifecycle management
- Module enable/disable per tenant
- Branding API (logos, favicons, themes)

**Database Tables**:

- `organizations` - Tenant organizations
- `subscription_plans` - Available subscription plans
- `organization_subscriptions` - Active subscriptions
- `module_registry` - System-wide module definitions
- `organization_modules` - Module assignments per organization
- `industry_templates` - Industry definitions
- `industry_module_templates` - Industry-module mappings

**API Endpoints**:

- `/api/v1/organizations/*` - Organization management
- `/api/v1/subscriptions/*` - Subscription management
- `/api/v1/modules/*` - Module management
- `/api/v1/industries/*` - Industry template management
- `/api/v1/module-registry/*` - Module registry management

#### 3. Auth Service (Port 8002)

**Purpose**: Authentication and authorization

**Responsibilities**:

- User authentication (login/logout)
- JWT token generation and validation
- Refresh token management
- Password management
- User session management

**Key Features**:

- JWT-based authentication
- Refresh token rotation
- Password hashing with bcrypt
- Multi-tenant user isolation
- Super admin authentication

**Database Tables**:

- `users` - User accounts (tenant-scoped)
- `refresh_tokens` - Refresh token storage
- `user_organizations` - User-organization relationships

**API Endpoints**:

- `/api/v1/auth/login` - User login
- `/api/v1/auth/logout` - User logout
- `/api/v1/auth/refresh` - Refresh access token
- `/api/v1/auth/me` - Get current user
- `/api/v1/auth/register` - User registration

#### 4. User Service (Port 8003)

**Purpose**: User profile and relationship management

**Responsibilities**:

- User profile management
- User-organization relationships
- User invitations
- Profile updates
- User search and listing

**Key Features**:

- User profile CRUD operations
- Multi-organization user support
- User invitation system
- Profile image management

**Database Tables**:

- `users` - User accounts
- `user_organizations` - User-organization relationships
- `user_profiles` - Extended user profile data

**API Endpoints**:

- `/api/v1/users/*` - User management
- `/api/v1/users/{id}/profile` - Profile management
- `/api/v1/users/invitations/*` - Invitation management

#### 5. Monitoring Service (Port 8006)

**Purpose**: System monitoring and observability

**Responsibilities**:

- Log aggregation and search
- Service health monitoring
- Kafka topic and consumer group monitoring
- Redis statistics and monitoring
- Metrics collection
- Kibana dashboard integration

**Key Features**:

- Elasticsearch log search
- Real-time service health checks
- Kafka broker and topic monitoring
- Redis memory and key pattern monitoring
- Response time metrics

**API Endpoints**:

- `/api/v1/monitor/logs/search` - Search application logs
- `/api/v1/monitor/metrics/health` - Service health status
- `/api/v1/monitor/metrics/response-time` - Response time metrics
- `/api/v1/monitor/kafka/*` - Kafka monitoring
- `/api/v1/monitor/redis/*` - Redis monitoring
- `/api/v1/monitor/kibana/dashboard-url` - Kibana dashboard URL

### Service Communication

#### Synchronous Communication

- **HTTP/REST**: All external requests go through API Gateway
- **Service-to-Service**: Direct HTTP calls between services for internal communication
- **Service URLs**: Configured via environment variables

#### Asynchronous Communication

- **Kafka Topics**: Event-driven architecture for decoupled communication
- **Event Types**:
  - `tenant.created` - New tenant organization created
  - `user.created` - New user account created
  - `module.assigned` - Module assigned to organization
  - `subscription.updated` - Subscription status changed

#### Caching Strategy

- **Redis**: Shared cache for all services
- **Use Cases**:
  - Session storage
  - Rate limiting
  - Module registry cache
  - Industry template cache
  - Organization data cache
  - Read-heavy query results

---

## Infrastructure Components

### PostgreSQL Database

**Purpose**: Primary data store for all services

**Configuration**:

- Connection pooling: 10 connections, max overflow 20
- Connection health checks: `pool_pre_ping=True`
- Database URL: Configured via `DATABASE_URL` environment variable

**Schema**:

- Shared database with schema separation by service
- UUID primary keys for all entities
- Timestamps: `created_at`, `updated_at` on all tables
- Multi-tenant isolation via `organization_id` foreign keys

### Redis Cache

**Purpose**: In-memory cache and session storage

**Configuration**:

- Port: 6380 (external), 6379 (internal)
- Image: `redis:7-alpine`
- Persistence: Volume-mounted data directory

**Use Cases**:

- Module registry caching (TTL: 600 seconds)
- Industry template caching
- Organization module assignments cache
- Session storage
- Rate limiting counters
- Temporary data storage

**Cache Keys Pattern**:

- `modules:registry:all` - All modules
- `modules:registry:active` - Active modules only
- `industries:all` - All industry templates
- `organizations:{org_id}:modules` - Organization modules
- `ratelimit:{user_id}:{endpoint}` - Rate limit counters

### Apache Kafka

**Purpose**: Event streaming and asynchronous messaging

**Configuration**:

- Broker: `localhost:9092`
- Zookeeper: `localhost:2181`
- Auto-create topics: Enabled
- Replication factor: 1 (development)

**Topics**:

- `tenant.created` - Tenant creation events
- `user.created` - User creation events
- `module.assigned` - Module assignment events
- `subscription.updated` - Subscription update events

**Event Structure**:

```json
{
  "event_type": "tenant.created",
  "timestamp": "2025-11-20T15:30:00Z",
  "data": {
    "organization_id": "uuid",
    "name": "Organization Name",
    "subdomain": "org-subdomain"
  }
}
```

### Elasticsearch

**Purpose**: Log indexing and search

**Configuration**:

- Port: 9200
- Version: 8.11.0
- Security: Disabled (development)
- Memory: 512MB heap

**Index Pattern**:

- `innoerp-YYYY.MM.DD` - Daily log indices (Logstash format)

**Data Structure**:

```json
{
  "timestamp": "2025-11-20T15:30:00Z",
  "level": "INFO",
  "service": "auth-service",
  "message": "User logged in",
  "module": "auth-service",
  "action": "login",
  "user_id": "uuid",
  "organization_id": "uuid",
  "request_id": "uuid"
}
```

### Fluentd

**Purpose**: Log collection and forwarding

**Configuration**:

- Image: `fluent/fluentd-kubernetes-daemonset:v1-debian-elasticsearch`
- Port: 24224 (forward protocol)
- Config: `/monitoring/efk/fluentd.conf`

**Sources**:

1. **Forward Protocol**: Receives logs from services via TCP/UDP
2. **File Tailing**: Tails EALogger JSON log files from service directories

**Log File Paths**:

- `/var/log/innoerp/services/{service}/logs/{module}/{YYYY-MM}/{module}-{YYYY-MM-DD}.log`

**Processing**:

- JSON parsing for EALogger logs
- Service name enrichment from file paths
- Timestamp extraction and normalization
- Forwarding to Elasticsearch

### Kibana

**Purpose**: Log visualization and dashboarding

**Configuration**:

- Port: 5601
- Version: 8.11.0
- Elasticsearch: `http://elasticsearch:9200`

**Features**:

- Log search and filtering
- Service-based log filtering
- Time-range queries
- Dashboard creation
- Embedded dashboards in monitoring UI

---

## Database Architecture

### Schema Design

#### Multi-Tenancy Pattern

All tenant-scoped tables include `organization_id`:

- Ensures data isolation between tenants
- Enables efficient querying with indexes
- Supports cross-tenant queries for super admins

#### Common Patterns

1. **UUID Primary Keys**: All tables use UUID for primary keys
2. **Timestamps**: `created_at`, `updated_at` on all tables
3. **Soft Deletes**: `is_active` flag for soft deletion
4. **Audit Fields**: Track creation and modification times

### Key Tables

#### Organizations (Tenant Service)

```sql
organizations
├── id (UUID, PK)
├── name (VARCHAR)
├── slug (VARCHAR, UNIQUE)
├── subdomain (VARCHAR, UNIQUE)
├── owner_email (VARCHAR)
├── owner_name (VARCHAR)
├── industry_code (VARCHAR)
├── industry_name (VARCHAR)
├── is_active (BOOLEAN)
├── trial_ends_at (TIMESTAMP)
├── stripe_customer_id (VARCHAR)
├── stripe_subscription_id (VARCHAR)
├── created_at (TIMESTAMP)
└── updated_at (TIMESTAMP)
```

#### Users (Auth/User Service)

```sql
users
├── id (UUID, PK)
├── organization_id (UUID, FK → organizations.id)
├── email (VARCHAR, INDEX)
├── username (VARCHAR, INDEX)
├── password_hash (VARCHAR)
├── user_type (VARCHAR) -- admin, manager, employee, client, supplier
├── is_active (BOOLEAN)
├── is_superuser (BOOLEAN)
├── first_name (VARCHAR)
├── last_name (VARCHAR)
├── created_at (TIMESTAMP)
└── updated_at (TIMESTAMP)

UNIQUE (organization_id, email)
UNIQUE (organization_id, username)
```

#### Module Registry (Tenant Service)

```sql
module_registry
├── module_id (VARCHAR, PK) -- e.g., "projects", "hr", "crm"
├── module_name (VARCHAR)
├── description (TEXT)
├── category (VARCHAR) -- "Core", "Industry-Specific"
├── is_active (BOOLEAN)
├── service_name (VARCHAR) -- microservice name
├── api_endpoint (VARCHAR) -- base endpoint
├── version (VARCHAR)
├── metadata (JSONB) -- icon, color, permissions, etc.
├── created_at (TIMESTAMP)
└── updated_at (TIMESTAMP)
```

#### Organization Modules (Tenant Service)

```sql
organization_modules
├── id (UUID, PK)
├── organization_id (UUID, FK → organizations.id)
├── module_id (VARCHAR, FK → module_registry.module_id)
├── is_enabled (BOOLEAN)
├── config (JSONB) -- module-specific configuration
├── assigned_at (TIMESTAMP)
├── created_at (TIMESTAMP)
└── updated_at (TIMESTAMP)

UNIQUE (organization_id, module_id)
```

#### Industry Templates (Tenant Service)

```sql
industry_templates
├── industry_code (VARCHAR, PK) -- e.g., "technology", "manufacturing"
├── industry_name (VARCHAR)
├── description (TEXT)
├── is_active (BOOLEAN)
├── created_at (TIMESTAMP)
└── updated_at (TIMESTAMP)

industry_module_templates
├── id (UUID, PK)
├── industry_code (VARCHAR, FK → industry_templates.industry_code)
├── module_id (VARCHAR, FK → module_registry.module_id)
├── is_required (BOOLEAN)
├── default_config (JSONB)
├── display_order (INTEGER)
├── created_at (TIMESTAMP)
└── updated_at (TIMESTAMP)

UNIQUE (industry_code, module_id)
```

#### Subscriptions (Tenant Service)

```sql
subscription_plans
├── id (UUID, PK)
├── name (VARCHAR)
├── description (TEXT)
├── price_monthly (DECIMAL)
├── price_yearly (DECIMAL)
├── features (JSONB)
├── is_active (BOOLEAN)
├── created_at (TIMESTAMP)
└── updated_at (TIMESTAMP)

organization_subscriptions
├── id (UUID, PK)
├── organization_id (UUID, FK → organizations.id)
├── plan_id (UUID, FK → subscription_plans.id)
├── status (VARCHAR) -- active, cancelled, expired
├── current_period_start (TIMESTAMP)
├── current_period_end (TIMESTAMP)
├── stripe_subscription_id (VARCHAR)
├── created_at (TIMESTAMP)
└── updated_at (TIMESTAMP)
```

#### Refresh Tokens (Auth Service)

```sql
refresh_tokens
├── id (UUID, PK)
├── user_id (UUID, FK → users.id)
├── token (VARCHAR, UNIQUE)
├── expires_at (TIMESTAMP)
├── is_revoked (BOOLEAN)
├── created_at (TIMESTAMP)
└── updated_at (TIMESTAMP)
```

### Indexes

**Performance Optimizations**:

- `organization_id` indexed on all tenant-scoped tables
- `email` and `username` indexed on users table
- `subdomain` indexed on organizations table
- Composite indexes for common query patterns

---

## Logging and Monitoring

### Logging Architecture

#### EALogger Integration

**Purpose**: Structured logging with entry/exit decorators

**Features**:

- Structured JSON log format
- Automatic entry/exit logging for functions
- Request ID tracking
- Organization and user context
- File-based logging with rotation

**Log Format**:

```json
{
  "timestamp": "2025-11-20T15:30:00.123456Z",
  "level": "INFO",
  "module": "auth-service",
  "action": "login",
  "method": "POST",
  "username": "user@example.com",
  "message": "User logged in successfully",
  "organization_id": "uuid",
  "user_id": "uuid",
  "request_id": "uuid",
  "duration_ms": 45.23
}
```

**Log File Structure**:

```
services/{service}/logs/{module}/{YYYY-MM}/{module}-{YYYY-MM-DD}.log
```

**Example**:

```
services/auth-service/logs/auth-service/2025-11/auth-service-2025-11-20.log
services/tenant-service/logs/middleware/2025-11/middleware-2025-11-20.log
```

#### Log Flow

```
Service Code
    ↓
EALogger (Structured JSON)
    ↓
Local Log Files
    ↓
Fluentd (Tail + Parse)
    ↓
Elasticsearch (Index)
    ↓
Kibana (Visualize)
```

#### Fluentd Configuration

**Sources**:

1. **Forward Protocol** (Port 24224): Receives logs via TCP/UDP
2. **File Tailing**: Monitors EALogger log files

**Processing**:

- JSON parsing for EALogger logs
- Service name extraction from file paths
- Timestamp normalization
- Service enrichment

**Output**:

- Elasticsearch index: `innoerp-YYYY.MM.DD`
- Logstash format with daily rotation

### Monitoring Components

#### Service Health Monitoring

**Endpoint**: `/api/v1/monitor/metrics/health`

**Checks**:

- API Gateway health
- Tenant Service health
- Auth Service health
- User Service health
- Monitoring Service health

**Response**:

```json
[
  {
    "service": "api-gateway",
    "status": "healthy",
    "details": { "status": "healthy" },
    "timestamp": "2025-11-20T15:30:00Z"
  }
]
```

#### Kafka Monitoring

**Endpoints**:

- `/api/v1/monitor/kafka/info` - Broker information
- `/api/v1/monitor/kafka/topics` - List all topics
- `/api/v1/monitor/kafka/consumer-groups` - Consumer groups

**Metrics**:

- Broker connectivity
- Topic partitions
- Consumer lag
- Consumer group state

#### Redis Monitoring

**Endpoints**:

- `/api/v1/monitor/redis/stats` - Server statistics
- `/api/v1/monitor/redis/memory` - Memory usage
- `/api/v1/monitor/redis/keys` - Key patterns

**Metrics**:

- Memory usage (used, peak)
- Total keys
- Connected clients
- Command statistics
- Hit/miss ratios

#### Log Search

**Endpoint**: `/api/v1/monitor/logs/search`

**Parameters**:

- `service` - Filter by service name
- `level` - Filter by log level (INFO, WARNING, ERROR, DEBUG)
- `start_time` - Start timestamp
- `end_time` - End timestamp
- `query` - Full-text search
- `size` - Results per page
- `from` - Pagination offset

**Response**:

```json
{
  "hits": [
    {
      "id": "elasticsearch-doc-id",
      "timestamp": "2025-11-20T15:30:00Z",
      "level": "INFO",
      "service": "auth-service",
      "message": "User logged in",
      "metadata": {},
      "organization_id": "uuid",
      "user_id": "uuid",
      "request_id": "uuid"
    }
  ],
  "total": 100
}
```

---

## Module Management System

### Overview

The module management system allows super admins to:

- Define system-wide modules in the module registry
- Create industry templates with default module assignments
- Assign modules to organizations manually or via industry templates
- Enable/disable modules per organization

### Module Registry

**Purpose**: Central repository for all available modules

**Key Fields**:

- `module_id`: Unique identifier (e.g., "projects", "hr", "crm")
- `module_name`: Display name
- `category`: Module category (Core, Industry-Specific)
- `service_name`: Microservice handling this module
- `api_endpoint`: Base API endpoint
- `metadata`: JSON configuration (icon, color, permissions)

**Predefined Modules**:

- `projects` - Project Management
- `users` - Users & Teams
- `finance` - Finance & Accounting
- `hr` - HR Management
- `crm` - Customer Relationship Management
- `inventory` - Inventory Management
- `settings` - Settings (always enabled)

### Industry Templates

**Purpose**: Pre-configured module sets for different industries

**Supported Industries**:

- Technology
- Manufacturing
- Retail
- Healthcare
- Finance
- Construction
- Professional Services
- Education

**Template Structure**:

- Industry code and name
- List of modules (required/optional)
- Default configuration per module
- Display order

### Module Assignment Flow

#### Automatic Assignment (Signup)

1. User selects industry during signup
2. System retrieves industry template
3. All required modules are assigned
4. Optional modules can be assigned based on plan
5. Modules are enabled by default

#### Manual Assignment (Super Admin)

1. Super admin selects organization
2. Views current module assignments
3. Can assign/unassign individual modules
4. Can apply industry template (replaces existing)
5. Can enable/disable modules without unassigning

### Module Enable/Disable

**Purpose**: Control module visibility without removing assignment

**Behavior**:

- Disabled modules are not shown in navigation
- API endpoints remain accessible (for flexibility)
- Module data is preserved
- Can be re-enabled without re-assignment

**Use Cases**:

- Temporary module suspension
- Plan-based feature gating
- A/B testing
- Gradual rollout

---

## Authentication and Authorization

### Authentication Flow

#### Login Process

1. User submits credentials to `/api/v1/auth/login`
2. Auth Service validates credentials
3. Generates JWT access token (short-lived, 15 minutes)
4. Generates refresh token (long-lived, 7 days)
5. Returns tokens to client
6. Client stores tokens (access token in memory, refresh token in httpOnly cookie)

#### Token Structure

**Access Token (JWT)**:

```json
{
  "sub": "user-uuid",
  "email": "user@example.com",
  "is_superuser": false,
  "organization_id": "org-uuid",
  "type": "access",
  "exp": 1734723000
}
```

**Refresh Token**:

- Stored in database (`refresh_tokens` table)
- UUID-based token string
- Expires after 7 days
- Can be revoked

#### Token Refresh

1. Client sends refresh token to `/api/v1/auth/refresh`
2. Auth Service validates refresh token
3. Checks if token is revoked or expired
4. Generates new access token
5. Optionally rotates refresh token

### Authorization

#### User Types

- **Super Admin**: System-wide access, can manage all tenants
- **Admin**: Organization admin, full access within tenant
- **Manager**: Limited admin access within tenant
- **Employee**: Standard user access
- **Client**: External client access
- **Supplier**: Supplier access

#### Permission Model

**Current Implementation**:

- Role-based via `user_type` field
- Organization-scoped permissions
- Super admin bypass for admin subdomain

**Future Enhancement**:

- Fine-grained permission system
- Module-specific permissions
- Resource-level access control

### Multi-Tenancy Security

#### Tenant Isolation

- All queries filtered by `organization_id`
- Subdomain-based tenant identification
- JWT token includes `organization_id`
- API Gateway extracts tenant from subdomain

#### Super Admin Access

- Separate subdomain: `admin.innoerp.io`
- Bypasses tenant context
- Can access all organizations
- Dedicated dashboard and routes

---

## API Gateway

### Purpose

Single entry point for all client requests, providing:

- Request routing
- Authentication
- Rate limiting
- Request logging
- CORS handling

### Routing Strategy

#### Subdomain-Based Routing

- **Tenant Subdomains**: `{tenant}.innoerp.io`

  - Routes to tenant-specific services
  - Extracts tenant context
  - Applies tenant-scoped filters

- **Admin Subdomain**: `admin.innoerp.io`
  - Routes to super admin endpoints
  - Bypasses tenant context
  - Full system access

#### Path-Based Routing

```
/api/v1/organizations/* → Tenant Service (8001)
/api/v1/auth/* → Auth Service (8002)
/api/v1/users/* → User Service (8003)
/api/v1/monitor/* → Monitoring Service (8006)
```

### Middleware Stack

1. **CORS Middleware**: Handles cross-origin requests
2. **Request Logging Middleware**: Logs all requests with EALogger
3. **Authentication Middleware**: Validates JWT tokens
4. **Rate Limiting Middleware**: Enforces rate limits per user/endpoint
5. **Tenant Context Middleware**: Extracts and sets tenant context

### Request Flow

```
Client Request
    ↓
API Gateway (8000)
    ↓
CORS Check
    ↓
Request Logging
    ↓
Authentication (if required)
    ↓
Rate Limiting
    ↓
Tenant Context Extraction
    ↓
Service Routing
    ↓
Backend Service
    ↓
Response
    ↓
API Gateway
    ↓
Client
```

---

## Frontend Architecture

### Technology Stack

- **Framework**: Next.js 16 with Turbopack
- **UI Library**: Material-UI (MUI) v7
- **State Management**: React Context API
- **HTTP Client**: Axios with interceptors
- **Charts**: Recharts for data visualization

### Project Structure

```
innoerp-frontend/
├── src/
│   ├── app/                    # Next.js app router
│   │   ├── (routes)/           # Route groups
│   │   ├── super-admin/         # Super admin routes
│   │   ├── tenant-admin/        # Tenant admin routes
│   │   └── middleware.ts        # Next.js middleware
│   ├── components/              # React components
│   │   ├── layout/              # Layout components
│   │   ├── settings/            # Settings components
│   │   └── ...
│   ├── lib/                     # Utilities
│   │   ├── api/                 # API clients
│   │   └── hooks/               # Custom hooks
│   └── styles/                  # Global styles
└── public/                      # Static assets
```

### Routing

#### Subdomain-Based Routing

**Middleware** (`src/app/middleware.ts`):

- Detects subdomain from request
- Routes admin subdomain to `/super-admin/*`
- Routes tenant subdomains to `/tenant-admin/*`
- Handles authentication redirects

#### Route Structure

**Super Admin Routes**:

- `/super-admin` - Dashboard
- `/super-admin/tenants` - Tenant management
- `/super-admin/modules` - Module registry
- `/super-admin/industries` - Industry templates
- `/super-admin/monitor/*` - Monitoring pages

**Tenant Admin Routes**:

- `/tenant-admin` - Dashboard
- `/tenant-admin/projects/*` - Project management
- `/tenant-admin/users/*` - User management
- `/tenant-admin/settings/*` - Settings

### State Management

#### Tenant Context

**Provider**: `TenantProvider`

- Loads organization data
- Loads branding (logo, favicon, theme)
- Provides context to all components
- Skips loading on admin subdomain

#### Authentication Context

**Provider**: `AuthProvider`

- Manages user authentication state
- Handles login/logout
- Token refresh
- User profile data

### API Integration

#### API Clients

- `tenant.ts` - Tenant service API
- `auth.ts` - Auth service API
- `user.ts` - User service API
- `monitoring.ts` - Monitoring service API

#### Axios Configuration

- Base URL: `process.env.NEXT_PUBLIC_API_GATEWAY_URL`
- Request interceptors: Add JWT token
- Response interceptors: Handle errors, token refresh
- File upload support: Multipart form data

### Dynamic Module Rendering

**Navigation**: Dynamically renders based on assigned modules

**Flow**:

1. Fetch assigned modules for organization
2. Filter menu items based on `module_id`
3. Render only enabled modules
4. Always show Dashboard and Settings

---

## Deployment Architecture

### Development Environment

#### Infrastructure Services (Docker)

```yaml
Services:
  - Redis (Port 6380)
  - Zookeeper (Port 2181)
  - Kafka (Port 9092)
  - Elasticsearch (Port 9200)
  - Kibana (Port 5601)
  - Fluentd (Port 24224)
```

#### Application Services (Local)

- API Gateway: `localhost:8000`
- Tenant Service: `localhost:8001`
- Auth Service: `localhost:8002`
- User Service: `localhost:8003`
- Monitoring Service: `localhost:8006`

#### Frontend (Local)

- Next.js Dev Server: `localhost:3000`
- Subdomain routing via hosts file or DNS

### Production Architecture (Planned)

#### Container Orchestration

- **Kubernetes**: For production deployment
- **Docker Compose**: For staging/single-server deployment

#### Service Deployment

- Each microservice in separate container
- Horizontal scaling per service
- Load balancing via API Gateway
- Database connection pooling
- Redis cluster for high availability

#### High Availability

- Multiple instances per service
- Database replication (master-slave)
- Redis sentinel for failover
- Kafka cluster for message durability
- Elasticsearch cluster for log storage

---

## Development Workflow

### Setup

1. **Clone Repository**

   ```bash
   git clone <repository-url>
   cd innoERP
   ```

2. **Setup Python Environment**

   ```bash
   python setup.py  # Creates venv and installs dependencies
   ```

3. **Start Infrastructure**

   ```bash
   cd infrastructure
   docker-compose -f docker-compose.dev.yml up -d
   cd ..
   ```

4. **Initialize Database**

   ```bash
   source venv/bin/activate  # Linux/Mac
   # or
   venv\Scripts\activate  # Windows
   python infrastructure/init_db.py
   ```

5. **Start Services**

   ```bash
   python start_services.py
   ```

6. **Start Frontend**
   ```bash
   cd innoerp-frontend
   npm install
   npm run dev
   ```

### Service Development

#### Adding a New Service

1. Create service directory: `services/{service-name}/`
2. Copy structure from existing service
3. Update `start_services.py` with new service
4. Add service to API Gateway routing
5. Create database migrations
6. Add to monitoring service health checks

#### Database Migrations

**Using Alembic**:

```bash
cd services/{service-name}
alembic revision --autogenerate -m "Description"
alembic upgrade head
```

### Testing

#### Unit Tests

- Location: `services/{service}/tests/`
- Framework: pytest
- Run: `pytest services/{service}/tests/`

#### Integration Tests

- Test service-to-service communication
- Test Kafka event handling
- Test database operations
- Test authentication flows

### Logging

#### Adding Logs

```python
from shared.common.logging import get_logger, log_entry_exit

logger = get_logger(__name__, app_name="service-name")

@log_entry_exit(app_name="service-name")
def my_function():
    logger.info("Operation started", "my_function", "POST", "user-id", "service-name")
    # ... code ...
    logger.info("Operation completed", "my_function", "POST", "user-id", "service-name")
```

---

## Security Considerations

### Authentication Security

- **Password Hashing**: bcrypt with salt rounds
- **JWT Tokens**: Short-lived access tokens (15 min)
- **Refresh Tokens**: Long-lived with rotation
- **Token Storage**: Access token in memory, refresh token in httpOnly cookie

### Data Security

- **Encryption**: HTTPS in production
- **Database**: Encrypted connections
- **Secrets**: Environment variables, never in code
- **API Keys**: Stored securely, rotated regularly

### Multi-Tenancy Security

- **Data Isolation**: Strict `organization_id` filtering
- **Subdomain Validation**: Verified subdomain-organization mapping
- **Super Admin**: Separate authentication and authorization
- **Cross-Tenant Access**: Prevented by design

### API Security

- **Rate Limiting**: Per user, per endpoint
- **CORS**: Configured allowed origins
- **Input Validation**: Pydantic models for all inputs
- **SQL Injection**: Prevented by SQLAlchemy ORM
- **XSS Protection**: React's built-in escaping

### Infrastructure Security

- **Container Security**: Regular image updates
- **Network Security**: Internal service communication
- **Logging**: No sensitive data in logs
- **Monitoring**: Alert on suspicious activity

---

## Conclusion

This technical documentation provides a comprehensive overview of the innoERP system architecture, technology stack, and implementation details. The system is designed for scalability, maintainability, and enterprise-grade reliability.

For specific implementation details, refer to:

- Service-specific README files
- API documentation at `/docs` endpoints
- Code comments and docstrings
- Architecture decision records (if available)

---

**Document Version**: 1.0  
**Last Updated**: November 2025  
**Maintained By**: innoERP Development Team
