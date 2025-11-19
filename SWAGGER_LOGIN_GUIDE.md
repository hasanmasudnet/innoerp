# FastAPI Swagger UI - Login Guide

## Quick Start

### 1. Start Services

```bash
python start_services.py
```

Wait for all services to start (you'll see "All services are running!").

### 2. Access Swagger UI

Open your browser and go to:
- **Auth Service Swagger**: http://localhost:8002/docs
- **API Gateway Swagger**: http://localhost:8000/docs (routes to auth-service)

### 3. Get Organization ID

First, make sure you have the UnlockLive organization created:

```bash
python infrastructure/create_unlocklive_org.py
```

This will print the Organization ID. Save it! (Example: `3c4e6fab-2df4-4951-93c0-5553a50fe57e`)

### 4. Create Admin User (if not done)

```bash
python infrastructure/create_initial_admin.py
```

This creates:
- Email: `admin@unlocklive.com`
- Username: `admin`
- Password: `Admin@123`

### 5. Login via Swagger UI

1. Open http://localhost:8002/docs
2. Find the **POST /api/v1/auth/login** endpoint
3. Click "Try it out"
4. Enter the request body:

```json
{
  "email": "admin@unlocklive.com",
  "password": "Admin@123",
  "organization_id": "3c4e6fab-2df4-4951-93c0-5553a50fe57e"
}
```

**Note**: Replace `organization_id` with your actual organization ID from step 3.

5. Click "Execute"
6. You'll get a response with:
   - `access_token` - Use this for authenticated requests
   - `refresh_token` - Use this to refresh the access token
   - `token_type` - "bearer"
   - `expires_in` - Token expiration time in seconds

### 6. Use the Token

After login, you can:
1. Copy the `access_token` from the response
2. Click "Authorize" button at the top of Swagger UI
3. Enter: `Bearer <your_access_token>`
4. Now all authenticated endpoints will use this token automatically

## Other Endpoints

### Register New User
- **POST /api/v1/auth/register**
- Requires: email, username, password, organization_id, first_name (optional), last_name (optional)

### Refresh Token
- **POST /api/v1/auth/refresh**
- Requires: refresh_token from login response

### Get Current User
- **GET /api/v1/auth/me**
- Requires: Authorization header with Bearer token

### Verify Token
- **GET /api/v1/auth/verify**
- Requires: Authorization header with Bearer token

## Troubleshooting

### "User not found" or "Invalid credentials"
- Make sure you ran `create_initial_admin.py` first
- Check that the email and password are correct
- Verify the organization_id matches your organization

### "Organization ID is required"
- Make sure you're including `organization_id` in the login request
- Get the organization ID from `create_unlocklive_org.py`

### Service not running
- Check that `start_services.py` is running
- Verify the service is listening on port 8002: http://localhost:8002/health

