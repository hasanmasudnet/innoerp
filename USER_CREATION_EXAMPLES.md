# User Creation JSON Examples

This document provides JSON examples for creating users with different roles in innoERP.

## User Types Available

- `admin` - Organization administrator
- `manager` - Manager role
- `employee` - Regular employee
- `client` - External client
- `supplier` - External supplier

## Method 1: Registration (Direct User Creation)

**Endpoint:** `POST /api/v1/auth/register`

### Admin User

```json
{
  "email": "admin@example.com",
  "username": "admin_user",
  "password": "SecurePass123!",
  "first_name": "Admin",
  "last_name": "User",
  "organization_id": "3c4e6fab-2df4-4951-93c0-5553a50fe57e"
}
```

### Manager User

```json
{
  "email": "manager@example.com",
  "username": "manager_user",
  "password": "SecurePass123!",
  "first_name": "Manager",
  "last_name": "User",
  "organization_id": "3c4e6fab-2df4-4951-93c0-5553a50fe57e"
}
```

### Employee User

```json
{
  "email": "employee@example.com",
  "username": "employee_user",
  "password": "SecurePass123!",
  "first_name": "Employee",
  "last_name": "User",
  "organization_id": "3c4e6fab-2df4-4951-93c0-5553a50fe57e"
}
```

### Client User

```json
{
  "email": "client@example.com",
  "username": "client_user",
  "password": "SecurePass123!",
  "first_name": "Client",
  "last_name": "User",
  "organization_id": "3c4e6fab-2df4-4951-93c0-5553a50fe57e"
}
```

### Supplier User

```json
{
  "email": "supplier@example.com",
  "username": "supplier_user",
  "password": "SecurePass123!",
  "first_name": "Supplier",
  "last_name": "User",
  "organization_id": "3c4e6fab-2df4-4951-93c0-5553a50fe57e"
}
```

**Note:** Registration creates users with default `user_type: "employee"`. To set a different user type, you need to use the invitation system or update the user type after creation.

## Method 2: Invitation System (Recommended)

**Endpoint:** `POST /api/v1/users/invitations`

The invitation system allows you to specify the exact user type and module relationships.

### Admin Invitation

```json
{
  "email": "newadmin@example.com",
  "user_type": "admin",
  "module_type": null,
  "invitation_metadata": {
    "note": "Organization administrator",
    "department": "Management"
  }
}
```

### Manager Invitation

```json
{
  "email": "newmanager@example.com",
  "user_type": "manager",
  "module_type": "project",
  "invitation_metadata": {
    "note": "Project manager",
    "department": "Project Management"
  }
}
```

### Employee Invitation

```json
{
  "email": "newemployee@example.com",
  "user_type": "employee",
  "module_type": "project",
  "invitation_metadata": {
    "note": "Software developer",
    "department": "Engineering",
    "skills": ["Python", "FastAPI"]
  }
}
```

### Client Invitation

```json
{
  "email": "client@clientcompany.com",
  "user_type": "client",
  "module_type": "project",
  "invitation_metadata": {
    "note": "External client for Project X",
    "company": "Client Company Inc.",
    "project_id": "project-uuid-here"
  }
}
```

### Supplier Invitation

```json
{
  "email": "supplier@suppliercompany.com",
  "user_type": "supplier",
  "module_type": "finance",
  "invitation_metadata": {
    "note": "Vendor for office supplies",
    "company": "Supply Co.",
    "category": "Office Supplies"
  }
}
```

## Method 3: Update User Type After Creation

**Endpoint:** `PATCH /api/v1/users/{user_id}/type`

If you created a user via registration and want to change their type:

```json
{
  "user_type": "manager"
}
```

## Module Types

When creating invitations, you can specify `module_type`:

- `project` - For project module relationships
- `finance` - For finance module relationships
- `null` - For organization-wide access (no specific module)

## Complete Workflow Example

### Step 1: Send Invitation

```bash
POST /api/v1/users/invitations
Authorization: Bearer <your_access_token>

{
  "email": "newuser@example.com",
  "user_type": "employee",
  "module_type": "project",
  "invitation_metadata": {
    "department": "Engineering"
  }
}
```

**Response:**

```json
{
  "id": "invitation-uuid",
  "organization_id": "3c4e6fab-2df4-4951-93c0-5553a50fe57e",
  "email": "newuser@example.com",
  "user_type": "employee",
  "module_type": "project",
  "invitation_token": "token-here",
  "status": "pending",
  "expires_at": "2025-11-26T09:14:50.672159Z",
  "accepted_at": null,
  "created_at": "2025-11-19T09:14:50.672159Z"
}
```

### Step 2: User Accepts Invitation

```bash
POST /api/v1/users/invitations/{token}/accept

{
  "password": "SecurePass123!",
  "username": "newuser",
  "first_name": "New",
  "last_name": "User"
}
```

**Response:**

```json
{
  "id": "user-uuid",
  "email": "newuser@example.com",
  "username": "newuser",
  "first_name": "New",
  "last_name": "User",
  "is_active": true,
  "is_superuser": false,
  "created_at": "2025-11-19T09:15:00.000000Z",
  "updated_at": "2025-11-19T09:15:00.000000Z"
}
```

## cURL Examples

### Create Admin via Registration

```bash
curl -X 'POST' \
  'http://localhost:8002/api/v1/auth/register' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
    "email": "admin2@example.com",
    "username": "admin2",
    "password": "Admin@123",
    "first_name": "Admin",
    "last_name": "Two",
    "organization_id": "3c4e6fab-2df4-4951-93c0-5553a50fe57e"
  }'
```

### Send Employee Invitation

```bash
curl -X 'POST' \
  'http://localhost:8003/api/v1/users/invitations' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer <your_access_token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "email": "employee@example.com",
    "user_type": "employee",
    "module_type": "project",
    "invitation_metadata": {
      "department": "Engineering"
    }
  }'
```

### Send Client Invitation

```bash
curl -X 'POST' \
  'http://localhost:8003/api/v1/users/invitations' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer <your_access_token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "email": "client@clientcompany.com",
    "user_type": "client",
    "module_type": "project",
    "invitation_metadata": {
      "company": "Client Company Inc.",
      "project_id": "project-uuid"
    }
  }'
```

### Send Supplier Invitation

```bash
curl -X 'POST' \
  'http://localhost:8003/api/v1/users/invitations' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer <your_access_token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "email": "supplier@suppliercompany.com",
    "user_type": "supplier",
    "module_type": "finance",
    "invitation_metadata": {
      "company": "Supply Co.",
      "category": "Office Supplies"
    }
  }'
```

## Notes

1. **Registration** creates users immediately but defaults to `employee` type
2. **Invitation** allows you to specify user type and module relationships upfront
3. **User Type** can be changed later using `PATCH /api/v1/users/{user_id}/type`
4. **Module Type** is optional and can be `project`, `finance`, or `null`
5. **Invitation Metadata** is optional and can store any additional context (JSON object)

## Required Fields

### Registration

- `email` (required)
- `username` (required, min 3 chars)
- `password` (required, min 8 chars)
- `organization_id` (required, UUID)

### Invitation

- `email` (required)
- `user_type` (required: admin, manager, employee, client, supplier)
- `module_type` (optional: project, finance, or null)
- `invitation_metadata` (optional: any JSON object)
