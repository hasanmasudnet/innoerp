# Frontend Multi-Tenant UI Setup Guide

This guide shows how to implement organization-specific UI themes, branding, and routing in the Next.js frontend.

## Overview

Each organization can have:
- **Unique subdomain** (hospital.innoerp.com, school.innoerp.com)
- **Custom branding** (logo, colors, fonts)
- **Theme preset** (hospital, school, it-company)
- **Custom CSS** (additional styling)

## Quick Start

### 1. Install Dependencies

```bash
npm install next@latest react@latest react-dom@latest
npm install axios react-hook-form zod @hookform/resolvers
npm install js-cookie lucide-react date-fns
npm install @tanstack/react-table recharts

# UI Framework
npx shadcn-ui@latest init
npx shadcn-ui@latest add button input card form table dialog
```

### 2. Project Structure

```
innoerp-frontend/
├── src/
│   ├── app/
│   │   ├── layout.tsx              # Root layout with TenantProvider
│   │   ├── page.tsx                # Home page
│   │   └── (dashboard)/            # Protected routes
│   ├── components/
│   │   ├── tenant/                 # Tenant-aware components
│   │   │   ├── TenantProvider.tsx  # Subdomain detection
│   │   │   ├── ThemeProvider.tsx   # Theme loading
│   │   │   └── BrandingProvider.tsx # Branding context
│   │   ├── layout/
│   │   │   ├── DashboardLayout.tsx # Themed layout
│   │   │   ├── Header.tsx          # Branded header
│   │   │   └── Sidebar.tsx         # Themed sidebar
│   │   └── ui/                     # shadcn/ui components
│   ├── themes/                     # Theme presets
│   │   ├── base/
│   │   │   ├── colors.ts
│   │   │   ├── typography.ts
│   │   │   └── index.ts
│   │   ├── hospital/
│   │   │   └── index.ts
│   │   ├── school/
│   │   │   └── index.ts
│   │   └── it-company/
│   │       └── index.ts
│   └── lib/
│       ├── api/
│       │   ├── tenant.ts           # Tenant API calls
│       │   └── client.ts
│       └── tenant/
│           ├── getTenant.ts        # Get tenant from URL
│           └── getTheme.ts         # Load theme
```

## Implementation

### Step 1: Tenant Provider

Create `src/components/tenant/TenantProvider.tsx`:

```typescript
'use client';

import { createContext, useContext, useEffect, useState } from 'react';
import { tenantApi } from '@/lib/api/tenant';

interface Tenant {
  id: string;
  name: string;
  subdomain: string;
  customDomain?: string;
  branding: {
    logoUrl?: string;
    faviconUrl?: string;
    companyName: string;
    primaryColor: string;
    secondaryColor: string;
    accentColor: string;
    fontFamily: string;
    headingFont: string;
    themePreset: string;
    sidebarStyle: string;
    headerStyle: string;
    dashboardLayout: string;
    customCss?: string;
  };
}

const TenantContext = createContext<{
  tenant: Tenant | null;
  loading: boolean;
}>({ tenant: null, loading: true });

export function TenantProvider({ children }: { children: React.ReactNode }) {
  const [tenant, setTenant] = useState<Tenant | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadTenant();
  }, []);

  const loadTenant = async () => {
    try {
      const subdomain = getSubdomain();
      if (!subdomain) {
        setLoading(false);
        return;
      }

      // Fetch organization by subdomain
      const org = await tenantApi.getBySubdomain(subdomain);
      
      // Fetch branding
      const branding = await tenantApi.getBranding(org.id);

      setTenant({
        id: org.id,
        name: org.name,
        subdomain: org.subdomain,
        customDomain: org.custom_domain,
        branding: {
          logoUrl: branding.logo_url,
          faviconUrl: branding.favicon_url,
          companyName: branding.company_name || org.name,
          primaryColor: branding.primary_color || '#3b82f6',
          secondaryColor: branding.secondary_color || '#8b5cf6',
          accentColor: branding.accent_color || '#f59e0b',
          fontFamily: branding.font_family || 'Inter',
          headingFont: branding.heading_font || 'Inter',
          themePreset: branding.theme_preset || 'base',
          sidebarStyle: branding.sidebar_style || 'default',
          headerStyle: branding.header_style || 'default',
          dashboardLayout: branding.dashboard_layout || 'grid',
          customCss: branding.custom_css,
        },
      });
    } catch (error) {
      console.error('Failed to load tenant:', error);
    } finally {
      setLoading(false);
    }
  };

  const getSubdomain = (): string | null => {
    if (typeof window === 'undefined') return null;
    
    const hostname = window.location.hostname;
    
    // Development: localhost:3000/hospital
    if (hostname === 'localhost') {
      const path = window.location.pathname.split('/')[1];
      return path || null;
    }
    
    // Production: hospital.innoerp.com
    const parts = hostname.split('.');
    if (parts.length >= 3) {
      return parts[0];
    }
    
    return null;
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <TenantContext.Provider value={{ tenant, loading }}>
      {children}
    </TenantContext.Provider>
  );
}

export function useTenant() {
  return useContext(TenantContext);
}
```

### Step 2: Theme Provider

Create `src/components/tenant/ThemeProvider.tsx`:

```typescript
'use client';

import { createContext, useContext, useEffect, useState } from 'react';
import { useTenant } from './TenantProvider';

interface ThemeConfig {
  colors: {
    primary: Record<string, string>;
    secondary: Record<string, string>;
    accent: Record<string, string>;
    background: Record<string, string>;
    text: Record<string, string>;
  };
  typography: {
    fontFamily: string;
    headingFont: string;
  };
  layout: {
    sidebarStyle: string;
    headerStyle: string;
    dashboardLayout: string;
  };
}

const ThemeContext = createContext<ThemeConfig | null>(null);

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const { tenant } = useTenant();
  const [theme, setTheme] = useState<ThemeConfig | null>(null);

  useEffect(() => {
    if (tenant) {
      loadTheme(tenant.branding.themePreset, tenant.branding);
    }
  }, [tenant]);

  const loadTheme = async (preset: string, branding: any) => {
    try {
      // Dynamic import of theme preset
      const themeModule = await import(`@/themes/${preset}/index`);
      const themeConfig = themeModule.default;
      
      // Merge with organization branding
      const mergedTheme: ThemeConfig = {
        colors: {
          ...themeConfig.colors,
          primary: {
            ...themeConfig.colors.primary,
            600: branding.primaryColor || themeConfig.colors.primary[600],
          },
          secondary: {
            ...themeConfig.colors.secondary,
            600: branding.secondaryColor || themeConfig.colors.secondary[600],
          },
        },
        typography: {
          fontFamily: branding.fontFamily || themeConfig.typography.fontFamily,
          headingFont: branding.headingFont || themeConfig.typography.headingFont,
        },
        layout: {
          sidebarStyle: branding.sidebarStyle || themeConfig.layout.sidebarStyle,
          headerStyle: branding.headerStyle || themeConfig.layout.headerStyle,
          dashboardLayout: branding.dashboardLayout || themeConfig.layout.dashboardLayout,
        },
      };
      
      setTheme(mergedTheme);
      applyTheme(mergedTheme, branding);
    } catch (error) {
      console.error('Failed to load theme:', error);
      // Fallback to base theme
      const baseTheme = await import('@/themes/base/index');
      setTheme(baseTheme.default);
      applyTheme(baseTheme.default, branding);
    }
  };

  const applyTheme = (theme: ThemeConfig, branding: any) => {
    const root = document.documentElement;
    
    // Apply CSS variables
    root.style.setProperty('--color-primary', theme.colors.primary[600]);
    root.style.setProperty('--color-secondary', theme.colors.secondary[600]);
    root.style.setProperty('--color-accent', branding.accentColor || theme.colors.accent[600]);
    root.style.setProperty('--font-family', theme.typography.fontFamily);
    root.style.setProperty('--font-heading', theme.typography.headingFont);
    
    // Apply custom CSS if provided
    if (branding.customCss) {
      let styleElement = document.getElementById('tenant-custom-css');
      if (!styleElement) {
        styleElement = document.createElement('style');
        styleElement.id = 'tenant-custom-css';
        document.head.appendChild(styleElement);
      }
      styleElement.textContent = branding.customCss;
    }
    
    // Apply favicon
    if (branding.faviconUrl) {
      let link = document.querySelector("link[rel~='icon']") as HTMLLinkElement;
      if (!link) {
        link = document.createElement('link');
        link.rel = 'icon';
        document.head.appendChild(link);
      }
      link.href = branding.faviconUrl;
    }
  };

  return (
    <ThemeContext.Provider value={theme}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within ThemeProvider');
  }
  return context;
}
```

### Step 3: Root Layout

Update `src/app/layout.tsx`:

```typescript
import { TenantProvider } from '@/components/tenant/TenantProvider';
import { ThemeProvider } from '@/components/tenant/ThemeProvider';
import './globals.css';

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <TenantProvider>
          <ThemeProvider>
            {children}
          </ThemeProvider>
        </TenantProvider>
      </body>
    </html>
  );
}
```

### Step 4: Theme Presets

Create `src/themes/base/index.ts`:

```typescript
export default {
  colors: {
    primary: {
      50: '#eff6ff',
      100: '#dbeafe',
      500: '#3b82f6',
      600: '#2563eb',
      700: '#1d4ed8',
    },
    secondary: {
      50: '#faf5ff',
      100: '#f3e8ff',
      500: '#a855f7',
      600: '#9333ea',
      700: '#7e22ce',
    },
    accent: {
      50: '#fffbeb',
      100: '#fef3c7',
      500: '#f59e0b',
      600: '#d97706',
      700: '#b45309',
    },
  },
  typography: {
    fontFamily: 'Inter, sans-serif',
    headingFont: 'Inter, sans-serif',
  },
  layout: {
    sidebarStyle: 'default',
    headerStyle: 'default',
    dashboardLayout: 'grid',
  },
};
```

Create `src/themes/hospital/index.ts`:

```typescript
export default {
  colors: {
    primary: {
      50: '#f0fdf4',
      100: '#dcfce7',
      500: '#22c55e',
      600: '#16a34a',
      700: '#15803d',
    },
    secondary: {
      50: '#ecfdf5',
      100: '#d1fae5',
      500: '#10b981',
      600: '#059669',
      700: '#047857',
    },
    accent: {
      50: '#fef2f2',
      100: '#fee2e2',
      500: '#ef4444',
      600: '#dc2626',
      700: '#b91c1c',
    },
  },
  typography: {
    fontFamily: 'Inter, sans-serif',
    headingFont: 'Inter, sans-serif',
  },
  layout: {
    sidebarStyle: 'default',
    headerStyle: 'solid',
    dashboardLayout: 'grid',
  },
};
```

### Step 5: Tenant API

Create `src/lib/api/tenant.ts`:

```typescript
import { apiClient } from './client';

export const tenantApi = {
  getBySubdomain: async (subdomain: string) => {
    const response = await apiClient.get(
      `/api/v1/tenants/by-subdomain/${subdomain}`
    );
    return response.data;
  },

  getBranding: async (organizationId: string) => {
    const response = await apiClient.get(
      `/api/v1/tenants/${organizationId}/branding`
    );
    return response.data;
  },

  updateBranding: async (organizationId: string, branding: any) => {
    const response = await apiClient.put(
      `/api/v1/tenants/${organizationId}/branding`,
      branding
    );
    return response.data;
  },
};
```

## Usage in Components

### Themed Button

```typescript
import { Button } from '@/components/ui/button';
import { useTheme } from '@/components/tenant/ThemeProvider';

export function ThemedButton({ children, ...props }) {
  const theme = useTheme();
  
  return (
    <Button
      style={{
        backgroundColor: `var(--color-primary)`,
        fontFamily: `var(--font-family)`,
      }}
      {...props}
    >
      {children}
    </Button>
  );
}
```

### Branded Header

```typescript
import { useTenant } from '@/components/tenant/TenantProvider';
import Image from 'next/image';

export function Header() {
  const { tenant } = useTenant();
  
  return (
    <header className="border-b">
      <div className="container mx-auto px-4 py-4">
        {tenant?.branding.logoUrl ? (
          <Image
            src={tenant.branding.logoUrl}
            alt={tenant.branding.companyName}
            width={150}
            height={40}
          />
        ) : (
          <h1 style={{ fontFamily: 'var(--font-heading)' }}>
            {tenant?.branding.companyName}
          </h1>
        )}
      </div>
    </header>
  );
}
```

## Environment Variables

```env
# API URLs
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_TENANT_SERVICE_URL=http://localhost:8001

# Development subdomain handling
NEXT_PUBLIC_DEV_SUBDOMAIN=hospital  # For localhost testing
```

## Testing

### Development (localhost)

Access via path: `http://localhost:3000/hospital`

### Production (subdomain)

Access via subdomain: `http://hospital.innoerp.com`

## Next Steps

1. Run backend migration: `python infrastructure/migrations/add_organization_branding.py`
2. Implement tenant-service branding endpoints
3. Set up frontend theme system
4. Create theme presets
5. Test with multiple organizations

