# Multi-Tenant UI Architecture

This document outlines the architecture for supporting organization-specific UI themes, branding, and routing in innoERP.

## Overview

Different organizations (Hospital, School, IT Company, etc.) will have:

- **Different UI themes** (colors, fonts, layouts)
- **Different branding** (logos, company names)
- **Different URLs** (subdomain-based or path-based routing)
- **Customizable components** (dashboards, forms, etc.)

## Architecture Approach

### 1. URL Routing Strategy

#### Option A: Subdomain-Based (Recommended)

```
hospital.innoerp.com     → Hospital organization
school.innoerp.com       → School organization
itcompany.innoerp.com    → IT Company organization
admin.innoerp.com        → Super admin panel
```

#### Option B: Path-Based

```
innoerp.com/hospital     → Hospital organization
innoerp.com/school       → School organization
innoerp.com/it-company   → IT Company organization
```

**Recommendation:** Use **Subdomain-Based** for better isolation and SEO.

### 2. Theme System Architecture

```
Frontend Structure:
├── themes/
│   ├── base/              # Base theme (default)
│   │   ├── colors.ts      # Color palette
│   │   ├── typography.ts  # Font settings
│   │   ├── components.ts  # Component overrides
│   │   └── layout.ts      # Layout configurations
│   ├── hospital/          # Hospital-specific theme
│   ├── school/            # School-specific theme
│   ├── it-company/        # IT Company theme
│   └── index.ts           # Theme loader
├── components/
│   ├── tenant/            # Tenant-aware components
│   │   ├── TenantProvider.tsx
│   │   ├── ThemeProvider.tsx
│   │   └── BrandingProvider.tsx
│   └── ...
└── lib/
    ├── tenant/             # Tenant utilities
    │   ├── getTenant.ts   # Get tenant from URL
    │   ├── getTheme.ts    # Load tenant theme
    │   └── getBranding.ts # Load tenant branding
    └── ...
```

## Implementation Plan

### Phase 1: Backend - Theme Configuration

#### 1.1 Database Schema

Add to `tenant-service`:

```sql
-- Organization branding and theme settings
CREATE TABLE organization_branding (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id),

    -- Branding
    logo_url VARCHAR(500),
    favicon_url VARCHAR(500),
    company_name VARCHAR(255),
    primary_color VARCHAR(7),        -- Hex color
    secondary_color VARCHAR(7),
    accent_color VARCHAR(7),

    -- Typography
    font_family VARCHAR(100),
    heading_font VARCHAR(100),

    -- Layout
    sidebar_style VARCHAR(50),      -- 'default', 'compact', 'minimal'
    header_style VARCHAR(50),       -- 'default', 'transparent', 'solid'
    dashboard_layout VARCHAR(50),   -- 'grid', 'list', 'card'

    -- Custom CSS
    custom_css TEXT,

    -- Theme preset
    theme_preset VARCHAR(50),        -- 'hospital', 'school', 'it-company', 'custom'

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(organization_id)
);

-- Organization subdomain mapping
ALTER TABLE organizations ADD COLUMN subdomain VARCHAR(100) UNIQUE;
ALTER TABLE organizations ADD COLUMN custom_domain VARCHAR(255);
```

#### 1.2 API Endpoints

**Tenant Service - Branding API:**

```typescript
// GET /api/v1/organizations/{org_id}/branding
// Returns: Organization branding configuration

// PUT /api/v1/organizations/{org_id}/branding
// Updates: Organization branding

// GET /api/v1/organizations/by-subdomain/{subdomain}
// Returns: Organization by subdomain
```

### Phase 2: Frontend - Theme System

#### 2.1 Theme Configuration Structure

```typescript
// themes/base/colors.ts
export const baseColors = {
  primary: {
    50: "#f0f9ff",
    100: "#e0f2fe",
    // ... full palette
    900: "#0c4a6e",
  },
  secondary: {
    /* ... */
  },
  accent: {
    /* ... */
  },
  // ... other colors
};

// themes/hospital/colors.ts
export const hospitalColors = {
  ...baseColors,
  primary: {
    50: "#f0fdf4", // Medical green
    100: "#dcfce7",
    // ... medical-themed palette
  },
};

// themes/school/colors.ts
export const schoolColors = {
  ...baseColors,
  primary: {
    50: "#fef3c7", // Educational yellow
    100: "#fde68a",
    // ... education-themed palette
  },
};
```

#### 2.2 Theme Provider

```typescript
// components/tenant/ThemeProvider.tsx
"use client";

import { createContext, useContext, useEffect, useState } from "react";
import { useTenant } from "./TenantProvider";

interface ThemeConfig {
  colors: Record<string, any>;
  typography: {
    fontFamily: string;
    headingFont: string;
  };
  layout: {
    sidebarStyle: string;
    headerStyle: string;
    dashboardLayout: string;
  };
  branding: {
    logoUrl?: string;
    faviconUrl?: string;
    companyName: string;
  };
}

const ThemeContext = createContext<ThemeConfig | null>(null);

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const { tenant } = useTenant();
  const [theme, setTheme] = useState<ThemeConfig | null>(null);

  useEffect(() => {
    if (tenant) {
      loadTheme(tenant.themePreset || "base", tenant.branding);
    }
  }, [tenant]);

  const loadTheme = async (preset: string, branding: any) => {
    // Load theme preset
    const themeModule = await import(`@/themes/${preset}/index`);
    const themeConfig = themeModule.default;

    // Merge with organization branding
    const mergedTheme = {
      ...themeConfig,
      branding: {
        ...themeConfig.branding,
        ...branding,
      },
      colors: {
        ...themeConfig.colors,
        primary: branding.primaryColor || themeConfig.colors.primary,
        secondary: branding.secondaryColor || themeConfig.colors.secondary,
      },
    };

    setTheme(mergedTheme);
    applyTheme(mergedTheme);
  };

  const applyTheme = (theme: ThemeConfig) => {
    // Apply CSS variables
    const root = document.documentElement;
    root.style.setProperty("--color-primary", theme.colors.primary[600]);
    root.style.setProperty("--color-secondary", theme.colors.secondary[600]);
    root.style.setProperty("--font-family", theme.typography.fontFamily);
    root.style.setProperty("--font-heading", theme.typography.headingFont);

    // Apply custom CSS if provided
    if (theme.branding.customCss) {
      // Inject custom CSS
    }
  };

  return (
    <ThemeContext.Provider value={theme}>{children}</ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error("useTheme must be used within ThemeProvider");
  }
  return context;
}
```

#### 2.3 Tenant Provider (Subdomain Detection)

```typescript
// components/tenant/TenantProvider.tsx
"use client";

import { createContext, useContext, useEffect, useState } from "react";
import { usePathname } from "next/navigation";

interface Tenant {
  id: string;
  name: string;
  subdomain: string;
  themePreset: string;
  branding: {
    logoUrl?: string;
    faviconUrl?: string;
    companyName: string;
    primaryColor: string;
    secondaryColor: string;
  };
}

const TenantContext = createContext<Tenant | null>(null);

export function TenantProvider({ children }: { children: React.ReactNode }) {
  const [tenant, setTenant] = useState<Tenant | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadTenant();
  }, []);

  const loadTenant = async () => {
    try {
      // Get subdomain from URL
      const subdomain = getSubdomain();

      if (subdomain) {
        // Fetch organization by subdomain
        const response = await fetch(
          `${process.env.NEXT_PUBLIC_TENANT_SERVICE_URL}/api/v1/organizations/by-subdomain/${subdomain}`
        );
        const org = await response.json();

        // Fetch branding
        const brandingResponse = await fetch(
          `${process.env.NEXT_PUBLIC_TENANT_SERVICE_URL}/api/v1/organizations/${org.id}/branding`
        );
        const branding = await brandingResponse.json();

        setTenant({
          id: org.id,
          name: org.name,
          subdomain: org.subdomain,
          themePreset: branding.theme_preset || "base",
          branding: {
            logoUrl: branding.logo_url,
            faviconUrl: branding.favicon_url,
            companyName: branding.company_name || org.name,
            primaryColor: branding.primary_color,
            secondaryColor: branding.secondary_color,
          },
        });
      }
    } catch (error) {
      console.error("Failed to load tenant:", error);
    } finally {
      setLoading(false);
    }
  };

  const getSubdomain = (): string | null => {
    if (typeof window === "undefined") return null;

    const hostname = window.location.hostname;

    // Development: localhost:3000
    if (hostname === "localhost") {
      // Use path-based: localhost:3000/hospital
      const path = window.location.pathname.split("/")[1];
      return path || null;
    }

    // Production: hospital.innoerp.com
    const parts = hostname.split(".");
    if (parts.length >= 3) {
      return parts[0]; // 'hospital'
    }

    return null;
  };

  if (loading) {
    return <div>Loading...</div>;
  }

  return (
    <TenantContext.Provider value={tenant}>{children}</TenantContext.Provider>
  );
}

export function useTenant() {
  const context = useContext(TenantContext);
  return { tenant: context };
}
```

#### 2.4 Dynamic Component Theming

```typescript
// components/ui/Button.tsx (shadcn/ui with theme support)
import { Button as ShadcnButton } from "@/components/ui/button";
import { useTheme } from "@/components/tenant/ThemeProvider";
import { cn } from "@/lib/utils";

export function Button({ className, ...props }) {
  const theme = useTheme();

  return (
    <ShadcnButton
      className={cn(
        // Apply theme colors
        `bg-[var(--color-primary)] hover:bg-[var(--color-primary-dark)]`,
        className
      )}
      style={
        {
          // Dynamic styles from theme
          "--color-primary": theme?.colors.primary[600],
          "--color-primary-dark": theme?.colors.primary[700],
        } as React.CSSProperties
      }
      {...props}
    />
  );
}
```

#### 2.5 Layout with Branding

```typescript
// components/layout/DashboardLayout.tsx
"use client";

import { useTheme } from "@/components/tenant/ThemeProvider";
import { useTenant } from "@/components/tenant/TenantProvider";
import Image from "next/image";

export function DashboardLayout({ children }: { children: React.ReactNode }) {
  const theme = useTheme();
  const { tenant } = useTenant();

  return (
    <div
      className="min-h-screen"
      style={{ fontFamily: theme?.typography.fontFamily }}
    >
      {/* Header with tenant logo */}
      <header className="border-b">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          {tenant?.branding.logoUrl ? (
            <Image
              src={tenant.branding.logoUrl}
              alt={tenant.branding.companyName}
              width={150}
              height={40}
            />
          ) : (
            <h1
              className="text-2xl font-bold"
              style={{ fontFamily: theme?.typography.headingFont }}
            >
              {tenant?.branding.companyName || "innoERP"}
            </h1>
          )}
          {/* User menu, etc. */}
        </div>
      </header>

      <div className="flex">
        {/* Sidebar with theme styling */}
        <aside
          className="w-64 border-r"
          style={{ backgroundColor: theme?.colors.sidebar.bg }}
        >
          {/* Navigation */}
        </aside>

        {/* Main content */}
        <main className="flex-1 p-6">{children}</main>
      </div>
    </div>
  );
}
```

### Phase 3: Theme Presets

#### 3.1 Hospital Theme

```typescript
// themes/hospital/index.ts
export default {
  colors: {
    primary: {
      50: "#f0fdf4",
      100: "#dcfce7",
      500: "#22c55e",
      600: "#16a34a",
      700: "#15803d",
    },
    // Medical-themed palette
  },
  typography: {
    fontFamily: "Inter, sans-serif",
    headingFont: "Inter, sans-serif",
  },
  layout: {
    sidebarStyle: "default",
    headerStyle: "solid",
    dashboardLayout: "grid",
  },
  branding: {
    companyName: "Hospital Management System",
  },
};
```

#### 3.2 School Theme

```typescript
// themes/school/index.ts
export default {
  colors: {
    primary: {
      50: "#fef3c7",
      100: "#fde68a",
      500: "#f59e0b",
      600: "#d97706",
      700: "#b45309",
    },
    // Education-themed palette
  },
  typography: {
    fontFamily: "Roboto, sans-serif",
    headingFont: "Roboto Slab, serif",
  },
  layout: {
    sidebarStyle: "compact",
    headerStyle: "transparent",
    dashboardLayout: "card",
  },
  branding: {
    companyName: "School Management System",
  },
};
```

#### 3.3 IT Company Theme

```typescript
// themes/it-company/index.ts
export default {
  colors: {
    primary: {
      50: "#eff6ff",
      100: "#dbeafe",
      500: "#3b82f6",
      600: "#2563eb",
      700: "#1d4ed8",
    },
    // Tech-themed palette
  },
  typography: {
    fontFamily: "Inter, sans-serif",
    headingFont: "Inter, sans-serif",
  },
  layout: {
    sidebarStyle: "minimal",
    headerStyle: "solid",
    dashboardLayout: "list",
  },
  branding: {
    companyName: "IT Management System",
  },
};
```

## Implementation Steps

### Step 1: Backend - Add Branding API

1. Create `organization_branding` table
2. Add subdomain to `organizations` table
3. Create branding endpoints in tenant-service
4. Add subdomain lookup endpoint

### Step 2: Frontend - Theme System

1. Create theme directory structure
2. Implement `TenantProvider` for subdomain detection
3. Implement `ThemeProvider` for theme loading
4. Create theme presets (hospital, school, it-company)
5. Update components to use theme context

### Step 3: Dynamic Styling

1. Use CSS variables for dynamic colors
2. Implement component theming
3. Add custom CSS injection
4. Create branding components (logo, favicon)

### Step 4: Testing

1. Test subdomain routing
2. Test theme switching
3. Test branding customization
4. Test custom CSS injection

## Configuration Example

### Organization Setup

```json
{
  "organization": {
    "id": "uuid",
    "name": "City Hospital",
    "subdomain": "hospital",
    "custom_domain": "hospital.city.com"
  },
  "branding": {
    "logo_url": "https://cdn.example.com/hospital-logo.png",
    "favicon_url": "https://cdn.example.com/hospital-favicon.ico",
    "company_name": "City Hospital",
    "primary_color": "#16a34a",
    "secondary_color": "#0ea5e9",
    "accent_color": "#f59e0b",
    "font_family": "Inter",
    "heading_font": "Inter",
    "theme_preset": "hospital",
    "sidebar_style": "default",
    "header_style": "solid",
    "dashboard_layout": "grid",
    "custom_css": ".custom-class { /* ... */ }"
  }
}
```

## Benefits

✅ **White-Label Solution** - Each organization gets their own branded experience
✅ **Flexible Theming** - Easy to add new themes or customize existing ones
✅ **SEO Friendly** - Subdomain-based routing improves SEO
✅ **Scalable** - Easy to add new organizations and themes
✅ **Maintainable** - Theme system is centralized and organized

## Next Steps

1. Implement backend branding API
2. Create frontend theme system
3. Build theme presets
4. Test with multiple organizations
5. Add theme customization UI for admins
