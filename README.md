# innoERP - Innovative ERP Solutions

A modern, multi-tenant ERP system built with microservices architecture.

## Quick Start

### 1. Setup

```bash
python3 setup.py
```

This creates virtual environment and installs all dependencies.

### 2. Start Infrastructure

```bash
cd infrastructure
docker-compose -f docker-compose.dev.yml up -d
cd ..
```

### 3. Initialize Database

```bash
source venv/bin/activate
export PYTHONPATH=$(pwd)
python infrastructure/init_db.py
```

### 4. Start All Services

```bash
python start_services.py
```

Press `Ctrl+C` to stop all services.

## Architecture

- **Backend**: FastAPI microservices
- **Message Queue**: Apache Kafka
- **Logging**: EFK Stack (Elasticsearch, Fluentd, Kibana)
- **Database**: PostgreSQL
- **Deployment**: Docker Compose / Kubernetes

## Services

1. **API Gateway** (port 8000) - Main entry point
2. **Tenant Service** (port 8001) - Organizations and subscriptions
3. **Auth Service** (port 8002) - Authentication
4. **User Service** (port 8003) - User management
5. **Project Service** - To be implemented
6. **Employee Service** - To be implemented
7. **Attendance Service** - To be implemented
8. **Leave Service** - To be implemented
9. **Finance Service** - To be implemented
10. **CRM Service** - To be implemented
11. **Career Service** - To be implemented
12. **Portfolio Service** - To be implemented
13. **Products Service** - To be implemented
14. **Contact Service** - To be implemented
15. **Notification Service** - To be implemented

## API Documentation

- http://localhost:8000/docs (API Gateway)
- http://localhost:8001/docs (Tenant Service)
- http://localhost:8002/docs (Auth Service)
- http://localhost:8003/docs (User Service)

## Environment Variables

Create `.env` file in project root:

```env
DATABASE_URL=postgresql://user:password@host:port/database
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
REDIS_URL=redis://localhost:6379
SECRET_KEY=your-secret-key
```

## Project Structure

```
innoERP/
├── setup.py              # Setup script
├── start_services.py     # Start all services
├── services/             # Microservices
├── shared/               # Shared libraries
├── infrastructure/       # Docker configs
└── monitoring/           # EFK stack configs
```
