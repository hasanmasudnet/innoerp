# Quick Start Guide - Super Admin Dashboard

## 🚀 Quick Start (3 Steps)

### Step 1: Start Backend Services

Open PowerShell/Terminal in `innoERP` folder:

```powershell
python start_services.py
```

Wait for all services to start (you'll see "All services are running!")

**Services:**
- API Gateway: http://localhost:8000
- Tenant Service: http://localhost:8001
- Auth Service: http://localhost:8002
- User Service: http://localhost:8003

### Step 2: Start Frontend

Open a **NEW** PowerShell/Terminal window:

```powershell
cd innoerp-frontend
npm run dev
```

Frontend will start on: **http://localhost:3000**

### Step 3: Access Super Admin Dashboard

1. Open browser: **http://localhost:3000/super-admin/login**

2. Login with:
   - **Email**: `admin@innoerp.io`
   - **Password**: `Admin@123`

3. You'll be redirected to the Super Admin Dashboard!

## 📍 What You'll See

### Main Dashboard (`/super-admin`)
- Statistics cards showing total tenants, active subscriptions, etc.

### Navigation Menu (Left Sidebar)

1. **Dashboard** - Overview and statistics
2. **Tenants** - Manage all tenant organizations
   - Click any tenant to view details
   - Activate/deactivate tenants
   - Extend trial periods
3. **Orders** - View subscription orders and payments
4. **Subscription Plans** - Create and manage pricing plans
5. **System Settings** - Configure modules, features, limits

## 🎯 Quick Actions

### View Tenant Details
1. Go to **Tenants** → Click any tenant row
2. View tabs: Overview, Subscription, Users, Modules, Usage

### Extend Trial
1. Open tenant detail page
2. Click **"Extend Trial"** button
3. Enter days (e.g., 30)
4. Click **"Extend"**

### Create Subscription Plan
1. Go to **Subscription Plans**
2. Click **"Create Plan"**
3. Fill in details and save

## ⚠️ Troubleshooting

### Services won't start?
- Check if ports 8000-8003 are free
- Ensure PostgreSQL is running
- Check `.env` file has correct database URL

### Frontend shows errors?
- Ensure backend services are running
- Check `.env.local` in `innoerp-frontend` folder
- Clear cache: `rm -rf .next` then `npm run dev`

### Can't login?
- Verify super admin exists in database
- Check email: `admin@innoerp.io`
- Default password: `Admin@123`

## 📚 Full Documentation

See `SUPER_ADMIN_GUIDE.md` for detailed documentation.

---

**Need Help?** Check the browser console (F12) for errors!

