# Frontend Setup Guide

This guide helps you set up the innoERP frontend in a separate repository.

## Frontend Repository

**GitHub:** https://github.com/hasanmasudnet/innoerp-frontend.git

## Technology Stack

- **Framework:** Next.js 14+ (App Router)
- **Language:** TypeScript
- **Styling:** Tailwind CSS
- **UI Framework:** shadcn/ui (Recommended) or Mantine
- **State Management:** React Context / Zustand (optional)
- **HTTP Client:** Axios or Fetch API
- **Authentication:** JWT tokens stored in httpOnly cookies or localStorage
- **Form Handling:** React Hook Form + Zod validation
- **Icons:** Lucide React or React Icons
- **Data Tables:** TanStack Table (React Table)
- **Charts:** Recharts or Chart.js

## Project Structure

```
innoerp-frontend/
├── .env.local                 # Environment variables
├── .env.example              # Example env file
├── next.config.js            # Next.js configuration
├── tailwind.config.js        # Tailwind configuration
├── tsconfig.json             # TypeScript configuration
├── package.json              # Dependencies
├── public/                   # Static assets
├── src/
│   ├── app/                  # Next.js App Router
│   │   ├── (auth)/           # Auth routes (login, register)
│   │   ├── (dashboard)/      # Protected dashboard routes
│   │   ├── layout.tsx        # Root layout
│   │   └── page.tsx          # Home page
│   ├── components/            # React components
│   │   ├── auth/             # Auth components
│   │   ├── dashboard/        # Dashboard components
│   │   ├── users/            # User management components
│   │   ├── common/           # Shared components
│   │   └── ui/               # UI primitives (buttons, inputs, etc.)
│   ├── lib/                  # Utilities
│   │   ├── api/              # API client
│   │   │   ├── auth.ts       # Auth API calls
│   │   │   ├── users.ts      # User API calls
│   │   │   └── client.ts     # Axios instance
│   │   ├── auth/             # Auth utilities
│   │   │   ├── context.tsx   # Auth context
│   │   │   └── middleware.ts # Auth middleware
│   │   └── utils/            # Helper functions
│   ├── types/                # TypeScript types
│   │   ├── auth.ts           # Auth types
│   │   ├── user.ts           # User types
│   │   └── api.ts            # API response types
│   └── hooks/                # Custom React hooks
│       ├── useAuth.ts        # Auth hook
│       └── useApi.ts         # API hook
└── README.md
```

## Environment Variables

Create `.env.local`:

```env
# API Gateway URL
NEXT_PUBLIC_API_URL=http://localhost:8000

# Direct service URLs (for development)
NEXT_PUBLIC_AUTH_SERVICE_URL=http://localhost:8002
NEXT_PUBLIC_USER_SERVICE_URL=http://localhost:8003
NEXT_PUBLIC_TENANT_SERVICE_URL=http://localhost:8001

# Organization ID (default for development)
NEXT_PUBLIC_DEFAULT_ORG_ID=3c4e6fab-2df4-4951-93c0-5553a50fe57e
```

## UI Framework Recommendations

### 🏆 Option 1: shadcn/ui (RECOMMENDED)

**Why shadcn/ui?**

- ✅ Modern, beautiful components built on Radix UI
- ✅ Fully customizable (copy-paste components, not a dependency)
- ✅ Built with Tailwind CSS
- ✅ Accessible by default
- ✅ Perfect for ERP/dashboard applications
- ✅ Great TypeScript support
- ✅ No runtime overhead (components are in your codebase)

**Installation:**

```bash
npx shadcn-ui@latest init
npx shadcn-ui@latest add button input card form label select table dialog
```

**Components to add:**

```bash
# Essential components
npx shadcn-ui@latest add button
npx shadcn-ui@latest add input
npx shadcn-ui@latest add card
npx shadcn-ui@latest add form
npx shadcn-ui@latest add label
npx shadcn-ui@latest add select
npx shadcn-ui@latest add table
npx shadcn-ui@latest add dialog
npx shadcn-ui@latest add dropdown-menu
npx shadcn-ui@latest add toast
npx shadcn-ui@latest add avatar
npx shadcn-ui@latest add badge
npx shadcn-ui@latest add tabs
npx shadcn-ui@latest add sidebar
npx shadcn-ui@latest add sheet
npx shadcn-ui@latest add calendar
npx shadcn-ui@latest add date-picker
```

### 🎨 Option 2: Mantine

**Why Mantine?**

- ✅ Comprehensive component library
- ✅ Built-in hooks and utilities
- ✅ Great form handling
- ✅ Data tables, charts, and more
- ✅ Dark mode support
- ✅ Perfect for complex dashboards

**Installation:**

```bash
npm install @mantine/core @mantine/hooks @mantine/form @mantine/dates @mantine/notifications
npm install dayjs
```

### 🎯 Option 3: Ant Design

**Why Ant Design?**

- ✅ Enterprise-grade components
- ✅ Extensive component library
- ✅ Great for admin panels
- ✅ Built-in form validation
- ✅ Data tables and charts included

**Installation:**

```bash
npm install antd @ant-design/icons
```

### 📦 Additional Libraries

**Icons:**

```bash
npm install lucide-react  # For shadcn/ui
# or
npm install react-icons   # More icon sets
```

**Data Tables:**

```bash
npm install @tanstack/react-table  # Powerful table library
```

**Charts:**

```bash
npm install recharts  # React charts library
# or
npm install chart.js react-chartjs-2
```

**Date Handling:**

```bash
npm install date-fns  # Date utilities
```

## Initial Setup Steps

### 1. Clone/Create Frontend Repository

```bash
# If repository doesn't exist, create it
git clone https://github.com/hasanmasudnet/innoerp-frontend.git
cd innoerp-frontend

# Or initialize new repo
mkdir innoerp-frontend
cd innoerp-frontend
git init
git remote add origin https://github.com/hasanmasudnet/innoerp-frontend.git
```

### 2. Initialize Next.js Project

```bash
npx create-next-app@latest . --typescript --tailwind --app --no-src-dir=false
```

### 3. Install Core Dependencies

```bash
# HTTP Client & Auth
npm install axios react-hook-form zod @hookform/resolvers
npm install js-cookie
npm install -D @types/js-cookie

# UI Framework (Choose one)
# Option A: shadcn/ui (Recommended)
npx shadcn-ui@latest init
npx shadcn-ui@latest add button input card form label select table dialog dropdown-menu toast avatar badge tabs

# Option B: Mantine
npm install @mantine/core @mantine/hooks @mantine/form @mantine/dates @mantine/notifications dayjs

# Option C: Ant Design
npm install antd @ant-design/icons

# Icons
npm install lucide-react  # For shadcn/ui
# or
npm install react-icons

# Data Tables
npm install @tanstack/react-table

# Charts
npm install recharts
# or
npm install chart.js react-chartjs-2

# Date Utilities
npm install date-fns

# State Management (Optional)
npm install zustand
```

### 4. Configure Tailwind CSS

```bash
npx tailwindcss init -p
```

Update `tailwind.config.js`:

```javascript
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
};
```

### 5. Configure shadcn/ui (if using)

After running `npx shadcn-ui@latest init`, you'll have:

- `components/ui/` - All shadcn components
- `lib/utils.ts` - Utility functions (cn helper)
- `components.json` - Configuration

Update `tailwind.config.js` to include shadcn paths:

```javascript
module.exports = {
  darkMode: ["class"],
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      // shadcn/ui theme configuration
    },
  },
  plugins: [require("tailwindcss-animate")],
};
```

### 6. Create API Client

Create `src/lib/api/client.ts`:

```typescript
import axios from "axios";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const AUTH_SERVICE_URL =
  process.env.NEXT_PUBLIC_AUTH_SERVICE_URL || "http://localhost:8002";

// Create axios instance
export const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Add auth token to requests
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle token refresh on 401
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Try to refresh token
      const refreshToken = localStorage.getItem("refresh_token");
      if (refreshToken) {
        try {
          const response = await axios.post(
            `${AUTH_SERVICE_URL}/api/v1/auth/refresh`,
            {
              refresh_token: refreshToken,
            }
          );
          const { access_token } = response.data;
          localStorage.setItem("access_token", access_token);
          // Retry original request
          error.config.headers.Authorization = `Bearer ${access_token}`;
          return apiClient.request(error.config);
        } catch (refreshError) {
          // Refresh failed, redirect to login
          localStorage.removeItem("access_token");
          localStorage.removeItem("refresh_token");
          window.location.href = "/login";
        }
      }
    }
    return Promise.reject(error);
  }
);

// Direct service clients (bypass API Gateway if needed)
export const authClient = axios.create({
  baseURL: AUTH_SERVICE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});
```

### 7. Create Auth API

Create `src/lib/api/auth.ts`:

```typescript
import { authClient } from "./client";

export interface LoginRequest {
  email: string;
  password: string;
  organization_id: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface RegisterRequest {
  email: string;
  username: string;
  password: string;
  first_name?: string;
  last_name?: string;
  organization_id: string;
}

export const authApi = {
  login: async (data: LoginRequest): Promise<LoginResponse> => {
    const response = await authClient.post("/api/v1/auth/login", data);
    return response.data;
  },

  register: async (data: RegisterRequest): Promise<LoginResponse> => {
    const response = await authClient.post("/api/v1/auth/register", data);
    return response.data;
  },

  refreshToken: async (refreshToken: string): Promise<LoginResponse> => {
    const response = await authClient.post("/api/v1/auth/refresh", {
      refresh_token: refreshToken,
    });
    return response.data;
  },

  getCurrentUser: async () => {
    const response = await authClient.get("/api/v1/auth/me");
    return response.data;
  },

  logout: async (refreshToken: string) => {
    await authClient.post("/api/v1/auth/logout", {
      refresh_token: refreshToken,
    });
  },
};
```

### 8. Create Auth Context

Create `src/lib/auth/context.tsx`:

```typescript
"use client";

import React, { createContext, useContext, useState, useEffect } from "react";
import { authApi, LoginRequest, RegisterRequest } from "@/lib/api/auth";

interface User {
  id: string;
  email: string;
  username: string;
  first_name?: string;
  last_name?: string;
  is_superuser: boolean;
  current_organization_id?: string;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (data: LoginRequest) => Promise<void>;
  register: (data: RegisterRequest) => Promise<void>;
  logout: () => Promise<void>;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check if user is logged in on mount
    const token = localStorage.getItem("access_token");
    if (token) {
      loadUser();
    } else {
      setLoading(false);
    }
  }, []);

  const loadUser = async () => {
    try {
      const userData = await authApi.getCurrentUser();
      setUser(userData);
    } catch (error) {
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
    } finally {
      setLoading(false);
    }
  };

  const login = async (data: LoginRequest) => {
    const response = await authApi.login(data);
    localStorage.setItem("access_token", response.access_token);
    localStorage.setItem("refresh_token", response.refresh_token);
    await loadUser();
  };

  const register = async (data: RegisterRequest) => {
    const response = await authApi.register(data);
    localStorage.setItem("access_token", response.access_token);
    localStorage.setItem("refresh_token", response.refresh_token);
    await loadUser();
  };

  const logout = async () => {
    const refreshToken = localStorage.getItem("refresh_token");
    if (refreshToken) {
      try {
        await authApi.logout(refreshToken);
      } catch (error) {
        // Ignore logout errors
      }
    }
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        login,
        register,
        logout,
        isAuthenticated: !!user,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
```

### 9. Create Login Page with shadcn/ui

Here's an example using shadcn/ui components:

Create `src/app/(auth)/login/page.tsx` with shadcn/ui:

```typescript
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth/context";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Loader2 } from "lucide-react";

const loginSchema = z.object({
  email: z.string().email("Invalid email address"),
  password: z.string().min(8, "Password must be at least 8 characters"),
  organization_id: z.string().uuid("Invalid organization ID"),
});

type LoginForm = z.infer<typeof loginSchema>;

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuth();
  const [error, setError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginForm>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      organization_id: process.env.NEXT_PUBLIC_DEFAULT_ORG_ID || "",
    },
  });

  const onSubmit = async (data: LoginForm) => {
    try {
      setError(null);
      await login(data);
      router.push("/dashboard");
    } catch (err: any) {
      setError(err.response?.data?.detail?.message || "Login failed");
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-50 to-gray-100 p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1">
          <CardTitle className="text-2xl font-bold text-center">
            Sign in to innoERP
          </CardTitle>
          <CardDescription className="text-center">
            Enter your credentials to access your account
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            {error && (
              <Alert variant="destructive">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="admin@unlocklive.com"
                {...register("email")}
                disabled={isSubmitting}
              />
              {errors.email && (
                <p className="text-sm text-red-600">{errors.email.message}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                placeholder="••••••••"
                {...register("password")}
                disabled={isSubmitting}
              />
              {errors.password && (
                <p className="text-sm text-red-600">
                  {errors.password.message}
                </p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="organization_id">Organization ID</Label>
              <Input
                id="organization_id"
                type="text"
                placeholder="3c4e6fab-2df4-4951-93c0-5553a50fe57e"
                {...register("organization_id")}
                disabled={isSubmitting}
              />
              {errors.organization_id && (
                <p className="text-sm text-red-600">
                  {errors.organization_id.message}
                </p>
              )}
            </div>

            <Button type="submit" className="w-full" disabled={isSubmitting}>
              {isSubmitting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Signing in...
                </>
              ) : (
                "Sign in"
              )}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
```

### Alternative: Login Page with Mantine

```typescript
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth/context";
import { Button, TextInput, Card, Title, Text, Alert } from "@mantine/core";
import { useForm } from "@mantine/form";
import { z } from "zod";
import { zodResolver } from "@mantine/form/zod-resolvers";

const loginSchema = z.object({
  email: z.string().email("Invalid email address"),
  password: z.string().min(8, "Password must be at least 8 characters"),
  organization_id: z.string().uuid("Invalid organization ID"),
});

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuth();
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const form = useForm({
    initialValues: {
      email: "",
      password: "",
      organization_id: process.env.NEXT_PUBLIC_DEFAULT_ORG_ID || "",
    },
    validate: zodResolver(loginSchema),
  });

  const handleSubmit = async (values: typeof form.values) => {
    try {
      setError(null);
      setLoading(true);
      await login(values);
      router.push("/dashboard");
    } catch (err: any) {
      setError(err.response?.data?.detail?.message || "Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 p-4">
      <Card
        shadow="sm"
        padding="lg"
        radius="md"
        withBorder
        className="w-full max-w-md"
      >
        <Title order={2} ta="center" mb="md">
          Sign in to innoERP
        </Title>
        <Text c="dimmed" size="sm" ta="center" mb="xl">
          Enter your credentials to access your account
        </Text>

        {error && (
          <Alert color="red" mb="md">
            {error}
          </Alert>
        )}

        <form onSubmit={form.onSubmit(handleSubmit)}>
          <TextInput
            label="Email"
            placeholder="admin@unlocklive.com"
            required
            {...form.getInputProps("email")}
            mb="md"
          />

          <TextInput
            label="Password"
            type="password"
            placeholder="••••••••"
            required
            {...form.getInputProps("password")}
            mb="md"
          />

          <TextInput
            label="Organization ID"
            placeholder="3c4e6fab-2df4-4951-93c0-5553a50fe57e"
            required
            {...form.getInputProps("organization_id")}
            mb="xl"
          />

          <Button type="submit" fullWidth loading={loading}>
            Sign in
          </Button>
        </form>
      </Card>
    </div>
  );
}
```

## Next Steps

1. **Set up the repository structure** as outlined above
2. **Install dependencies** and configure Next.js
3. **Create the API client** and auth system
4. **Build the login/register pages**
5. **Create protected dashboard routes**
6. **Implement user management UI**
7. **Add invitation management UI**

## Integration Points

- **Authentication:** JWT tokens stored in localStorage
- **API Gateway:** http://localhost:8000 (or direct service URLs)
- **Organization ID:** Use default from env or allow selection
- **Error Handling:** Centralized error handling in API client
- **Token Refresh:** Automatic token refresh on 401 errors

## Development Workflow

1. Start backend services: `python start_services.py`
2. Start frontend: `npm run dev`
3. Frontend runs on: http://localhost:3000
4. Backend API Gateway: http://localhost:8000

## Git Repository Setup

```bash
# Initialize and push to GitHub
git init
git add .
git commit -m "Initial Next.js frontend setup for innoERP"
git branch -M main
git remote add origin https://github.com/hasanmasudnet/innoerp-frontend.git
git push -u origin main
```
