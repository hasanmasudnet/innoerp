# Tenant Service

Manages organizations/tenants and subscriptions for innoERP.

## Features

- Organization CRUD operations
- Subscription management
- Module enable/disable
- Stripe integration (subscription management)

## API Endpoints

- `POST /api/v1/organizations` - Create organization
- `GET /api/v1/organizations/{id}` - Get organization
- `GET /api/v1/organizations/slug/{slug}` - Get by slug
- `GET /api/v1/organizations/subdomain/{subdomain}` - Get by subdomain
- `PATCH /api/v1/organizations/{id}` - Update organization
- `GET /api/v1/subscriptions/organization/{id}` - Get subscription
- `POST /api/v1/modules/organization/{id}` - Enable module
- `GET /api/v1/modules/organization/{id}` - List modules

## Environment Variables

- `DATABASE_URL` - PostgreSQL connection string
- `KAFKA_BOOTSTRAP_SERVERS` - Kafka brokers
- `STRIPE_SECRET_KEY` - Stripe secret key
- `DEBUG` - Enable debug mode

## Running

```bash
# Install dependencies
pip install -r requirements.txt

# Run with uvicorn
uvicorn app.main:app --reload --port 8001
```

