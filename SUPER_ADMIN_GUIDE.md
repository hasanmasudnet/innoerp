# Super Admin Dashboard - User Guide

This guide will help you access and use the new Super Admin Dashboard for managing all tenants, subscriptions, orders, and system settings.

## Prerequisites

1. **Python 3.9+** installed
2. **Node.js 18+** installed
3. **PostgreSQL** database running
4. **Docker** (for Kafka, Redis, Zookeeper - optional for now)

## Step 1: Start Backend Services

### Option A: Using the Start Script (Recommended)

Open a terminal in the `innoERP` directory and run:

```bash
# Windows (PowerShell)
python start_services.py

# Linux/Mac
python3 start_services.py
```

This will start all 4 services:

- **API Gateway**: http://localhost:8000
- **Tenant Service**: http://localhost:8001
- **Auth Service**: http://localhost:8002
- **User Service**: http://localhost:8003

**Note**: The script will keep services running. Press `Ctrl+C` to stop all services.

### Option B: Start Services Individually

If you prefer to start services separately:

```bash
# Terminal 1 - API Gateway
cd services/api-gateway
python -m uvicorn app.main:app --port 8000 --reload

# Terminal 2 - Tenant Service
cd services/tenant-service
python -m uvicorn app.main:app --port 8001 --reload

# Terminal 3 - Auth Service
cd services/auth-service
python -m uvicorn app.main:app --port 8002 --reload

# Terminal 4 - User Service
cd services/user-service
python -m uvicorn app.main:app --port 8003 --reload
```

## Step 2: Verify Backend Services

Check that services are running by visiting:

- API Gateway Docs: http://localhost:8000/docs
- Tenant Service Docs: http://localhost:8001/docs
- Auth Service Docs: http://localhost:8002/docs
- User Service Docs: http://localhost:8003/docs

## Step 3: Start Frontend

Open a **new terminal** and navigate to the frontend directory:

```bash
cd innoerp-frontend
```

### Install Dependencies (if not already done)

```bash
npm install
```

### Configure Environment Variables

Create or check `.env.local` file in `innoerp-frontend` directory:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_AUTH_SERVICE_URL=http://localhost:8002
NEXT_PUBLIC_USER_SERVICE_URL=http://localhost:8003
NEXT_PUBLIC_TENANT_SERVICE_URL=http://localhost:8001
```

### Start Frontend Development Server

```bash
npm run dev
```

The frontend will start on: **http://localhost:3000**

## Step 4: Access Super Admin Dashboard

### Login Credentials

The super admin user should already exist. If not, you need to create it first.

**Super Admin Credentials:**

- **Email**: `admin@innoerp.io`
- **Password**: `Admin@123` (or the password you set)

**Note**: If the super admin doesn't exist, you can create it using the database or by running a script.

### Access the Dashboard

1. Open your browser and go to: **http://localhost:3000/super-admin/login**

2. Enter the super admin credentials:

   - Email: `admin@innoerp.io`
   - Password: `Admin@123`

3. After login, you'll be redirected to: **http://localhost:3000/super-admin**

## Step 5: Navigate the Super Admin Dashboard

### Main Navigation (Left Sidebar)

The sidebar contains the following sections:

1. **Dashboard** (`/super-admin`)

   - Overview of all tenants
   - Statistics: Total tenants, Active, Trial, Expired
   - Subscription status overview

2. **Tenants** (`/super-admin/tenants`)

   - **All Tenants**: List of all organizations
   - **New Signups**: Recent tenant registrations
   - **Analytics**: Tenant analytics and reports

3. **Orders** (`/super-admin/orders`)

   - **All Orders**: Subscription orders (new, upgrades, downgrades)
   - **Subscriptions**: Active subscriptions list
   - **Payments**: Payment transaction history
   - **Signup Requests**: New tenant registration requests

4. **Subscription Plans** (`/super-admin/plans`)

   - **All Plans**: List of all subscription plans
   - **Create Plan**: Create new subscription plan

5. **System Settings** (`/super-admin/settings`)
   - **Modules**: Enable/disable system modules
   - **Feature Flags**: Toggle features on/off
   - **Limits**: Set default limits for plans
   - **Integrations**: Configure Stripe, email, etc.
   - **General**: System-wide settings

### Features Overview

#### 1. Dashboard Page

- View key metrics at a glance
- See total tenants, active subscriptions
- Quick access to recent activity

#### 2. Tenants Management

- **List View**: See all tenants in a table
- **Click on a tenant** to view details
- **Tenant Detail Page** includes:
  - **Overview Tab**: Basic information, status, trial dates
  - **Subscription Tab**: Current plan, billing period, status
  - **Users Tab**: List of users in the tenant (placeholder)
  - **Modules Tab**: Enabled/disabled modules
  - **Usage Tab**: Usage statistics (users, projects, etc.)
  - **Actions**: Activate/Deactivate tenant, Extend trial

#### 3. Orders Management

- View subscription orders
- View payment transactions
- Filter and search orders
- See signup requests

#### 4. Subscription Plans

- List all plans (Basic, Pro, Enterprise, etc.)
- Create new plans
- Edit existing plans
- Set pricing, features, limits

#### 5. System Settings

- **Modules**: Enable/disable modules globally
- **Feature Flags**: Toggle features for all tenants
- **Limits**: Set default resource limits
- **Integrations**: Configure third-party services

## Step 6: Common Tasks

### View Tenant Details

1. Go to **Tenants** → **All Tenants**
2. Click on any tenant row
3. View comprehensive information in tabs

### Activate/Deactivate a Tenant

1. Go to tenant detail page
2. Click **"Activate"** or **"Deactivate"** button in the top section

### Extend Trial Period

1. Go to tenant detail page
2. Click **"Extend Trial"** button
3. Enter number of days (1-365)
4. Click **"Extend"**

### Create a Subscription Plan

1. Go to **Subscription Plans** → **All Plans**
2. Click **"Create Plan"** button
3. Fill in:
   - Plan name (e.g., "Basic", "Pro", "Enterprise")
   - Monthly price
   - Max users
   - Max projects
   - Features list
   - Limits (JSON)
4. Click **"Create"**

### View Orders and Payments

1. Go to **Orders**
2. Switch between tabs:
   - **Subscription Orders**: All subscription changes
   - **Payment Transactions**: All payments
   - **Signup Requests**: New tenant registrations

## Troubleshooting

### Backend Services Not Starting

1. **Check if ports are already in use:**

   ```bash
   # Windows
   netstat -ano | findstr :8000
   netstat -ano | findstr :8001

   # Linux/Mac
   lsof -i :8000
   lsof -i :8001
   ```

2. **Check database connection:**

   - Ensure PostgreSQL is running
   - Check `.env` file has correct `DATABASE_URL`

3. **Check Python virtual environment:**
   ```bash
   # Activate venv if using one
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```

### Frontend Not Loading

1. **Check if backend is running:**

   - Visit http://localhost:8000/docs to verify API Gateway

2. **Check environment variables:**

   - Ensure `.env.local` exists in `innoerp-frontend` directory
   - Verify all URLs are correct

3. **Clear Next.js cache:**
   ```bash
   cd innoerp-frontend
   rm -rf .next
   npm run dev
   ```

### Can't Login as Super Admin

1. **Verify super admin exists:**

   - Check database `users` table for `admin@innoerp.io`
   - Ensure `is_superuser = true`

2. **Create super admin if missing:**

   - You may need to create it manually in the database or run a script

3. **Check password:**
   - Default password is `Admin@123`
   - If changed, use the new password

### Pages Show "404" or "Not Found"

1. **Check route exists:**

   - Ensure all page files are in correct directories
   - Check file names match route paths

2. **Restart frontend:**
   ```bash
   # Stop frontend (Ctrl+C)
   # Restart
   npm run dev
   ```

## API Endpoints Reference

### Tenant Management

- `GET /api/v1/tenants` - List all tenants
- `GET /api/v1/tenants/{id}/details` - Get tenant details
- `GET /api/v1/tenants/{id}/subscription` - Get tenant subscription
- `PATCH /api/v1/tenants/{id}/status` - Update tenant status
- `PATCH /api/v1/tenants/{id}/trial` - Extend trial

### Subscriptions

- `GET /api/v1/subscriptions` - List subscriptions
- `GET /api/v1/subscriptions/plans` - List subscription plans
- `POST /api/v1/subscriptions/plans` - Create plan
- `PATCH /api/v1/subscriptions/plans/{id}` - Update plan

### Orders & Payments

- `GET /api/v1/subscriptions/orders` - Get orders
- `GET /api/v1/subscriptions/payments` - Get payments

### Modules

- `GET /api/v1/modules/available` - List available modules

## Next Steps

1. **Explore the dashboard** - Navigate through all sections
2. **View tenant details** - Click on tenants to see full information
3. **Create subscription plans** - Set up pricing tiers
4. **Configure system settings** - Enable/disable modules and features
5. **Monitor orders** - Track subscription changes and payments

## Support

If you encounter any issues:

1. Check the browser console for errors (F12)
2. Check backend service logs
3. Verify database connection
4. Ensure all environment variables are set correctly

---

**Happy Administering! 🚀**
