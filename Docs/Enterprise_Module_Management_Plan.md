# Enterprise Module Management System with Kafka & Redis Integration

## Overview
Build a scalable, enterprise-grade module management system that supports industry-based module templates, super admin module assignment, automatic signup assignment, Kafka-driven transactions, and Redis caching. **All modules are fully manageable from admin interface - nothing is hardcoded.**

## Architecture Decisions

### Kafka Transaction Pattern (Enterprise Standard)
- **Event-Driven Architecture**: All critical database writes (CREATE, UPDATE, DELETE) publish events to Kafka
- **Module-Wise Decoupling**: Each module's operations are independent Kafka topics/events
- **CQRS Pattern**: Writes go through Kafka → Event Handlers → Database; Reads from Redis cache or DB
- **Event Sourcing**: Maintain event log for audit trail and eventual consistency
- **High Volume Support**: Async processing, batch operations, and consumer groups for scalability

### Redis Caching Strategy
- Cache all read-heavy queries: organization data, module configs, industry templates, module lists
- TTL-based invalidation with cache-aside pattern
- Cache keys: `org:{org_id}:modules`, `industry:{industry}:modules`, `module:{module_id}:config`

### No Hardcoding Policy
- **All modules must be in database** (ModuleRegistry table)
- **All module lists come from database queries**, not hardcoded arrays
- **Super admin can add/edit/remove modules** from the system
- **Industry templates reference modules from registry**, not hardcoded IDs
- **Frontend dynamically loads** all module data from API

## Phase 1: Database Schema & Models

### 1.1 Industry Template Schema
**File**: `innoERP/services/tenant-service/app/schemas.py`
- Add `IndustryTemplate` model with fields:
  - `id` (UUID, primary key)
  - `industry_name` (String, unique) - e.g., "Technology", "Manufacturing"
  - `industry_code` (String, unique) - e.g., "tech", "manufacturing"
  - `description` (Text)
  - `is_active` (Boolean)
  - `created_at`, `updated_at` (DateTime)
- Add `IndustryModuleTemplate` model (many-to-many):
  - `template_id` (FK to IndustryTemplate)
  - `module_id` (String) - references ModuleRegistry.module_id
  - `is_required` (Boolean) - required vs optional
  - `default_config` (JSON) - default module configuration
  - `display_order` (Integer)

### 1.2 Module Registry Schema
**File**: `innoERP/services/tenant-service/app/schemas.py`
- Add `ModuleRegistry` model:
  - `module_id` (String, primary key) - e.g., "projects", "hr", "crm"
  - `module_name` (String)
  - `description` (Text)
  - `category` (String) - e.g., "Core", "Industry-Specific"
  - `is_active` (Boolean) - can be disabled system-wide
  - `service_name` (String) - microservice that handles this module
  - `api_endpoint` (String) - base endpoint for module
  - `version` (String)
  - `metadata` (JSON) - additional config (icon, color, permissions, etc.)
  - `created_at`, `updated_at` (DateTime)

### 1.3 Update Organization Schema
**File**: `innoERP/services/tenant-service/app/schemas.py`
- Add to `Organization` model:
  - `industry_code` (String, nullable, indexed) - references IndustryTemplate
  - `industry_name` (String, nullable) - denormalized for quick access

### 1.4 Migration Script
**File**: `innoERP/infrastructure/migrations/add_industry_module_system.py`
- Create `industry_templates` table
- Create `industry_module_templates` table
- Create `module_registry` table
- Add `industry_code` and `industry_name` to `organizations` table
- Seed initial data: 8 industries with their module templates

## Phase 2: Kafka Event System

### 2.1 New Kafka Event Schemas
**File**: `innoERP/shared/kafka/schemas.py`
- Add `ModuleAssignedEvent` - when module assigned to org
- Add `ModuleUnassignedEvent` - when module removed
- Add `ModulesBulkAssignedEvent` - bulk assignment operations
- Add `IndustryTemplateAppliedEvent` - when industry template applied
- Add `ModuleConfigUpdatedEvent` - when module config changes
- Add `ModuleRegisteredEvent` - when new module registered in system
- Add `ModuleUpdatedEvent` - when module metadata updated
- All events include: `organization_id`, `module_id`, `user_id` (who performed action), `payload`

### 2.2 Kafka Producer Service
**File**: `innoERP/services/tenant-service/app/kafka/producer.py`
- Extend existing producer to support:
  - `publish_module_event(event_type, event_data)` - generic module event publisher
  - Topic naming: `tenant.module.{action}` (e.g., `tenant.module.assigned`, `tenant.module.unassigned`)
  - Partition key: `organization_id` for ordering

### 2.3 Kafka Consumer Service
**File**: `innoERP/services/tenant-service/app/kafka/consumer.py` (NEW)
- Create consumer that listens to module events
- Event handlers:
  - `handle_module_assigned` - update database, invalidate Redis cache
  - `handle_module_unassigned` - update database, invalidate Redis cache
  - `handle_bulk_assigned` - batch update database
  - `handle_module_registered` - update module registry cache
- Use consumer groups for scalability
- Implement idempotency checks (prevent duplicate processing)

### 2.4 Database Transaction Wrapper
**File**: `innoERP/shared/database/kafka_transaction.py` (NEW)
- Create decorator/context manager `@kafka_transaction`
- Wraps DB operations: commit DB → publish Kafka event → handle failures
- Ensures atomicity: if Kafka publish fails, rollback DB (or use outbox pattern)
- Support for batch operations

## Phase 3: Redis Caching Layer

### 3.1 Redis Client Wrapper
**File**: `innoERP/shared/cache/redis_client.py` (NEW)
- Create Redis connection pool
- Methods:
  - `get(key)` - get cached value
  - `set(key, value, ttl)` - set with TTL
  - `delete(key)` - delete cache
  - `delete_pattern(pattern)` - bulk delete (e.g., `org:{org_id}:*`)
  - `exists(key)` - check existence

### 3.2 Cache Service
**File**: `innoERP/services/tenant-service/app/services/cache_service.py` (NEW)
- Cache decorator `@cache_result(ttl=300, key_pattern="...")`
- Cache keys:
  - `org:{org_id}:modules` - organization's modules (TTL: 5 min)
  - `industry:{code}:modules` - industry template modules (TTL: 1 hour)
  - `module:{module_id}:config` - module configuration (TTL: 10 min)
  - `org:{org_id}:info` - organization basic info (TTL: 5 min)
  - `modules:registry:all` - all registered modules (TTL: 10 min)
- Cache invalidation on writes

### 3.3 Update Services to Use Cache
**File**: `innoERP/services/tenant-service/app/services.py`
- Update `ModuleService.list_modules()` - check cache first
- **Replace `ModuleService.get_available_modules()`** - query ModuleRegistry from DB (cached)
- Update `OrganizationService.get_organization()` - cache org data
- Invalidate cache on module assignment/unassignment

## Phase 4: Backend API & Services

### 4.1 Industry Template Service
**File**: `innoERP/services/tenant-service/app/services.py`
- Add `IndustryTemplateService`:
  - `list_all()` - get all industry templates
  - `get_by_code(code)` - get template by code
  - `get_modules(industry_code)` - get modules for industry (cached, validates modules exist in registry)
  - `create_template()` - create new template (super admin)
  - `update_template()` - update template
  - `delete_template()` - soft delete template
  - `apply_to_organization(org_id, industry_code)` - apply template to org (via Kafka, validates all modules exist)

### 4.2 Module Registry Service
**File**: `innoERP/services/tenant-service/app/services.py`
- Add `ModuleRegistryService`:
  - `register_module()` - register new module in system (super admin, publishes ModuleRegisteredEvent)
  - `list_all()` - get all registered modules (cached, replaces ALL hardcoded lists)
  - `get_by_id(module_id)` - get module details (cached)
  - `update_module()` - update module metadata (super admin, publishes ModuleUpdatedEvent)
  - `delete_module()` - soft delete module (super admin)
  - `activate_module(module_id)` - enable module system-wide
  - `deactivate_module(module_id)` - disable module system-wide
  - `validate_modules_exist(module_ids)` - helper to check modules are registered and active
- **CRITICAL**: This service replaces ALL hardcoded module references

### 4.3 Enhanced Module Service
**File**: `innoERP/services/tenant-service/app/services.py`
- **Remove hardcoded `get_available_modules()` method completely**
- Replace with `ModuleRegistryService.list_all()` everywhere
- Update `ModuleService`:
  - `assign_module(org_id, module_id, config)` - assign via Kafka (validates module exists in registry)
  - `unassign_module(org_id, module_id)` - unassign via Kafka
  - `bulk_assign_modules(org_id, module_ids, industry_code)` - bulk assign via Kafka (validates all modules exist)
  - `assign_from_industry(org_id, industry_code)` - auto-assign from template (validates all modules in registry)
  - `validate_modules_exist(module_ids)` - helper to check modules are registered and active
  - All methods: validate against ModuleRegistry → check cache → if miss, query DB → cache result → return

### 4.4 API Routes
**File**: `innoERP/services/tenant-service/app/routers/modules.py`
- Update existing routes to use ModuleRegistry:
  - `GET /modules/available` - get all available modules from ModuleRegistry (cached, replaces hardcoded list)
- Add new routes:
  - `POST /modules/assign/{organization_id}` - assign module (super admin, validates module exists)
  - `POST /modules/unassign/{organization_id}/{module_id}` - unassign
  - `POST /modules/bulk-assign/{organization_id}` - bulk assign (validates all modules)
  - `POST /modules/apply-industry/{organization_id}` - apply industry template (validates all modules)

**File**: `innoERP/services/tenant-service/app/routers/industries.py` (NEW)
- `GET /industries` - list all industries
- `GET /industries/{code}` - get industry details
- `GET /industries/{code}/modules` - get modules for industry (validates modules exist)
- `POST /industries` - create industry template (super admin)
- `PATCH /industries/{code}` - update template
- `DELETE /industries/{code}` - delete template

**File**: `innoERP/services/tenant-service/app/routers/module-registry.py` (NEW)
- `GET /module-registry` - list all registered modules (super admin, cached)
- `GET /module-registry/{module_id}` - get module details
- `POST /module-registry` - register new module (super admin)
- `PATCH /module-registry/{module_id}` - update module (super admin)
- `DELETE /module-registry/{module_id}` - delete module (super admin)
- `POST /module-registry/{module_id}/activate` - activate module
- `POST /module-registry/{module_id}/deactivate` - deactivate module

### 4.5 Update Tenant Signup
**File**: `innoERP/services/tenant-service/app/routers/organizations.py`
- Update `TenantSignupRequest` model to include `industry_code` (optional)
- Update `tenant_signup()`:
  - Accept `industry_code` in request
  - After org creation, if industry_code provided:
    - Validate industry exists
    - Get modules from industry template
    - Validate all modules exist in ModuleRegistry
    - Auto-assign modules from template via Kafka
  - Publish `IndustryTemplateAppliedEvent` to Kafka

## Phase 5: Frontend - Super Admin Module Management

### 5.1 Module Registry Management Page
**File**: `innoerp-frontend/src/app/super-admin/modules/page.tsx` (NEW)
- List all registered modules from API (no hardcoding)
- Module details: name, description, category, service, endpoint, version, status
- Actions:
  - Add new module (form with all fields)
  - Edit module metadata
  - Activate/Deactivate module
  - Delete module (with confirmation)
- Search and filter capabilities
- Shows which organizations use each module

### 5.2 Industry Templates Page
**File**: `innoerp-frontend/src/app/super-admin/industries/page.tsx` (NEW)
- List all industry templates
- Create/edit industry templates
- Assign modules to templates (dropdown populated from ModuleRegistry API)
- Shows modules per industry with required/optional flags
- Module selection validates against ModuleRegistry
- Preview of which modules will be assigned

### 5.3 Module Assignment UI
**File**: `innoerp-frontend/src/app/super-admin/tenants/[id]/modules/page.tsx` (NEW)
- Show current modules for tenant (from API)
- Assign modules (dropdown from ModuleRegistry API, no hardcoding)
- Unassign modules
- Apply industry template (dropdown from industries API)
- Bulk assign from template
- Module configuration editor
- All module lists come from API calls

### 5.4 Update Tenant Detail Page
**File**: `innoerp-frontend/src/app/super-admin/tenants/[id]/page.tsx`
- Add "Modules" tab
- Show assigned modules (from API)
- Quick actions: assign, unassign, apply template
- All module data from API, no hardcoding

### 5.5 API Client Updates
**File**: `innoerp-frontend/src/lib/api/tenant.ts`
- Add methods:
  - `getModuleRegistry()` - get all registered modules
  - `registerModule(moduleData)` - register new module
  - `updateModule(moduleId, moduleData)` - update module
  - `deleteModule(moduleId)` - delete module
  - `activateModule(moduleId)` - activate module
  - `deactivateModule(moduleId)` - deactivate module
  - `assignModule(orgId, moduleId, config)` - assign module
  - `unassignModule(orgId, moduleId)` - unassign module
  - `bulkAssignModules(orgId, moduleIds, industryCode)` - bulk assign
  - `applyIndustryTemplate(orgId, industryCode)` - apply template
  - `getIndustries()` - get all industries
  - `getIndustryModules(industryCode)` - get modules for industry
  - `createIndustry(industryData)` - create industry template
  - `updateIndustry(code, industryData)` - update template
  - `deleteIndustry(code)` - delete template

## Phase 6: Frontend - Tenant Signup Enhancement

### 6.1 Update Signup Form
**File**: `innoerp-frontend/src/components/auth/SignupForm.tsx` (or wherever signup is)
- Add industry selection dropdown (populated from industries API)
- Show preview of modules that will be assigned (from industry modules API)
- Industry description and module list (all from API)
- No hardcoded industry or module lists

### 6.2 Update Signup API
**File**: `innoerp-frontend/src/lib/api/tenant.ts`
- Update `signup()` to include `industry_code` in request

## Phase 7: Initial Data Seeding

### 7.1 Module Registry Seed
**File**: `innoERP/infrastructure/migrations/seed_module_registry.py`
- Register all existing modules in ModuleRegistry:
  - projects, hr, finance, crm, inventory, products, contact, career, portfolio, attendance, leave
- Include service names, endpoints, metadata for each
- This is the source of truth - no hardcoding after this

### 7.2 Industry Templates Seed
**File**: `innoERP/infrastructure/migrations/seed_industry_templates.py`
- Seed 8 industries:
  1. **Technology**: projects, crm, hr, finance, products
  2. **Manufacturing**: projects, inventory, finance, hr, crm
  3. **Retail**: inventory, crm, finance, products, contact
  4. **Healthcare**: hr, finance, crm, projects, contact
  5. **Finance**: finance, crm, hr, projects
  6. **Construction**: projects, finance, hr, inventory, crm
  7. **Professional Services**: projects, crm, finance, hr, career
  8. **Education**: hr, finance, projects, crm, career
- Each references modules from ModuleRegistry (not hardcoded IDs)
- Each with appropriate required/optional flags

## Phase 8: Remove All Hardcoding

### 8.1 Backend Hardcoding Removal
**File**: `innoERP/services/tenant-service/app/services.py`
- Remove `ModuleService.get_available_modules()` hardcoded list
- Replace all references with `ModuleRegistryService.list_all()`
- Remove any enum-based module lists
- Ensure all module validations check ModuleRegistry

### 8.2 Frontend Hardcoding Removal
**File**: `innoerp-frontend/src/**/*.tsx`
- Remove any hardcoded module arrays
- Remove any hardcoded industry lists
- Ensure all module/industry data comes from API calls
- Update all components to use API data

### 8.3 Enum Updates
**File**: `innoERP/shared/database/enums.py`
- Keep `ModuleType` enum for type safety, but validate against ModuleRegistry
- Add comment: "Enum for type safety only - actual modules come from ModuleRegistry"

## Phase 9: Testing & Validation

### 9.1 Unit Tests
- Test Kafka event publishing
- Test Redis caching
- Test module assignment logic
- Test industry template application
- Test ModuleRegistry CRUD operations
- Test module validation against registry

### 9.2 Integration Tests
- Test signup with industry selection
- Test super admin module assignment
- Test super admin module registry management
- Test cache invalidation
- Test Kafka consumer processing
- Test all modules come from database, not hardcoded

### 9.3 Performance Tests
- Load test Kafka consumers
- Cache hit rate monitoring
- Database query optimization
- Module registry query performance

## Implementation Order

1. **Database Schema** (Phase 1) - Foundation
2. **Module Registry Seed** (Phase 7.1) - Source of truth for modules
3. **Kafka Infrastructure** (Phase 2) - Event system
4. **Redis Infrastructure** (Phase 3) - Caching
5. **Backend Services** (Phase 4) - Business logic
6. **Remove Hardcoding** (Phase 8) - Critical for maintainability
7. **Industry Templates Seed** (Phase 7.2) - Initial data
8. **Frontend - Super Admin** (Phase 5) - Management UI
9. **Frontend - Signup** (Phase 6) - User experience
10. **Testing** (Phase 9) - Validation

## Key Files to Modify/Create

### Backend
- `innoERP/services/tenant-service/app/schemas.py` - Add models
- `innoERP/services/tenant-service/app/services.py` - Add services, remove hardcoding
- `innoERP/services/tenant-service/app/routers/modules.py` - Update routes
- `innoERP/services/tenant-service/app/routers/industries.py` - New file
- `innoERP/services/tenant-service/app/routers/module-registry.py` - New file
- `innoERP/services/tenant-service/app/kafka/consumer.py` - New file
- `innoERP/shared/kafka/schemas.py` - Add events
- `innoERP/shared/cache/redis_client.py` - New file
- `innoERP/shared/database/kafka_transaction.py` - New file

### Frontend
- `innoerp-frontend/src/app/super-admin/modules/page.tsx` - New (Module Registry)
- `innoerp-frontend/src/app/super-admin/industries/page.tsx` - New
- `innoerp-frontend/src/app/super-admin/tenants/[id]/modules/page.tsx` - New
- `innoerp-frontend/src/lib/api/tenant.ts` - Add methods

### Infrastructure
- `innoERP/infrastructure/migrations/add_industry_module_system.py` - New
- `innoERP/infrastructure/migrations/seed_module_registry.py` - New
- `innoERP/infrastructure/migrations/seed_industry_templates.py` - New

## Critical Requirements

1. **NO HARDCODING**: All modules must be in ModuleRegistry table
2. **Super Admin Control**: All modules, industries, and assignments manageable via UI
3. **Validation**: All module operations validate against ModuleRegistry
4. **Kafka-Driven**: All writes go through Kafka for scalability
5. **Redis Caching**: All reads cached for performance
6. **Database as Source of Truth**: ModuleRegistry is the single source of truth

## Success Criteria

- Super admin can add/edit/delete modules from UI
- Super admin can create/edit industry templates with module assignments
- Super admin can assign/unassign modules to any organization
- Tenant signup can select industry and auto-assign modules
- All module lists come from API, no hardcoding
- All database writes go through Kafka
- All reads are cached in Redis
- System handles high volume transactions efficiently

