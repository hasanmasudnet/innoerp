# API Gateway

Main entry point for all API requests in innoERP. Routes requests to appropriate microservices.

## Features

- Request routing to backend services
- Authentication middleware
- Tenant identification from subdomain
- CORS handling
- Request/response proxying

## Service Routing

- `/api/v1/tenants/*` -> tenant-service
- `/api/v1/auth/*` -> auth-service
- `/api/v1/users/*` -> user-service
- `/api/v1/projects/*` -> project-service
- `/api/v1/employees/*` -> employee-service

## Environment Variables

- `TENANT_SERVICE_URL` - Tenant service URL
- `AUTH_SERVICE_URL` - Auth service URL
- `USER_SERVICE_URL` - User service URL
- `PROJECT_SERVICE_URL` - Project service URL
- `EMPLOYEE_SERVICE_URL` - Employee service URL

## Running

```bash
# Install dependencies
pip install -r requirements.txt

# Run with uvicorn
uvicorn app.main:app --reload --port 8000
```

