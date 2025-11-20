"""
Comprehensive script to set up the complete module management system
This script:
1. Creates all necessary database tables (migration)
2. Seeds the module registry with all available modules
3. Seeds industry templates with their module assignments

Run this script once to set up the entire module management system.
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import time
from sqlalchemy import text
from shared.database.base import engine

sys.stdout.reconfigure(line_buffering=True)


def print_section(title: str):
    """Print a formatted section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_step(step_num: int, total: int, description: str):
    """Print a formatted step"""
    print(f"\n[{step_num}/{total}] {description}")
    print("-" * 70)


def check_table_exists(conn, table_name: str) -> bool:
    """Check if table exists"""
    result = conn.execute(
        text(
            """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = :table_name
            )
        """
        ),
        {"table_name": table_name},
    )
    return result.scalar()


def check_column_exists(conn, table_name: str, column_name: str) -> bool:
    """Check if column exists"""
    result = conn.execute(
        text(
            """
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_schema = 'public' 
                AND table_name = :table_name
                AND column_name = :column_name
            )
        """
        ),
        {"table_name": table_name, "column_name": column_name},
    )
    return result.scalar()


def run_migration(conn):
    """Step 1: Run database migration"""
    print_step(1, 3, "Creating Database Tables")
    
    # Update organizations table
    if check_table_exists(conn, "organizations"):
        if not check_column_exists(conn, "organizations", "industry_code"):
            conn.execute(text("ALTER TABLE organizations ADD COLUMN industry_code VARCHAR(100)"))
            conn.execute(
                text("CREATE INDEX IF NOT EXISTS ix_organizations_industry_code ON organizations(industry_code)")
            )
            print("  [OK] Added industry_code column to organizations")
        else:
            print("  [OK] industry_code column already exists")
        
        if not check_column_exists(conn, "organizations", "industry_name"):
            conn.execute(text("ALTER TABLE organizations ADD COLUMN industry_name VARCHAR(255)"))
            print("  [OK] Added industry_name column to organizations")
        else:
            print("  [OK] industry_name column already exists")
    else:
        print("  [SKIP] organizations table does not exist - skipping")
    
    # Create module_registry table
    if not check_table_exists(conn, "module_registry"):
        conn.execute(
            text(
                """
                CREATE TABLE module_registry (
                    module_id VARCHAR(100) PRIMARY KEY,
                    module_name VARCHAR(255) NOT NULL,
                    description TEXT,
                    category VARCHAR(100),
                    is_active BOOLEAN NOT NULL DEFAULT TRUE,
                    service_name VARCHAR(100),
                    api_endpoint VARCHAR(255),
                    version VARCHAR(50),
                    metadata JSONB NOT NULL DEFAULT '{}',
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """
            )
        )
        print("  [OK] Created module_registry table")
    else:
        print("  [OK] module_registry table already exists")
    
    # Create industry_templates table
    if not check_table_exists(conn, "industry_templates"):
        conn.execute(
            text(
                """
                CREATE TABLE industry_templates (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    industry_name VARCHAR(255) NOT NULL UNIQUE,
                    industry_code VARCHAR(100) NOT NULL UNIQUE,
                    description TEXT,
                    is_active BOOLEAN NOT NULL DEFAULT TRUE,
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """
            )
        )
        conn.execute(
            text("CREATE INDEX IF NOT EXISTS ix_industry_templates_code ON industry_templates(industry_code)")
        )
        print("  [OK] Created industry_templates table")
    else:
        print("  [OK] industry_templates table already exists")
    
    # Create industry_module_templates table
    if not check_table_exists(conn, "industry_module_templates"):
        conn.execute(
            text(
                """
                CREATE TABLE industry_module_templates (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    template_id UUID NOT NULL REFERENCES industry_templates(id) ON DELETE CASCADE,
                    module_id VARCHAR(100) NOT NULL REFERENCES module_registry(module_id),
                    is_required BOOLEAN NOT NULL DEFAULT FALSE,
                    default_config JSONB NOT NULL DEFAULT '{}',
                    display_order INTEGER NOT NULL DEFAULT 0,
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """
            )
        )
        conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_industry_module_templates_template_id ON industry_module_templates(template_id)"
            )
        )
        conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_industry_module_templates_module_id ON industry_module_templates(module_id)"
            )
        )
        print("  [OK] Created industry_module_templates table")
    else:
        print("  [OK] industry_module_templates table already exists")
    
    conn.commit()
    print("\n  [SUCCESS] Database migration completed successfully!")


def seed_module_registry(conn):
    """Step 2: Seed module registry"""
    print_step(2, 3, "Seeding Module Registry")
    
    modules = [
        {
            "module_id": "projects",
            "module_name": "Project Management",
            "description": "Manage projects, tasks, and teams",
            "category": "Core",
            "service_name": "project-service",
            "api_endpoint": "/api/v1/projects",
            "version": "1.0.0",
            "metadata": {"icon": "project", "color": "#1976d2"},
        },
        {
            "module_id": "hr",
            "module_name": "HR Management",
            "description": "Employee management, attendance, leave",
            "category": "Core",
            "service_name": "employee-service",
            "api_endpoint": "/api/v1/hr",
            "version": "1.0.0",
            "metadata": {"icon": "people", "color": "#dc004e"},
        },
        {
            "module_id": "finance",
            "module_name": "Finance",
            "description": "Accounting, invoicing, expenses",
            "category": "Core",
            "service_name": "finance-service",
            "api_endpoint": "/api/v1/finance",
            "version": "1.0.0",
            "metadata": {"icon": "account_balance", "color": "#00a86b"},
        },
        {
            "module_id": "crm",
            "module_name": "CRM",
            "description": "Customer relationship management",
            "category": "Core",
            "service_name": "crm-service",
            "api_endpoint": "/api/v1/crm",
            "version": "1.0.0",
            "metadata": {"icon": "contacts", "color": "#ff9800"},
        },
        {
            "module_id": "inventory",
            "module_name": "Inventory",
            "description": "Stock management and tracking",
            "category": "Industry-Specific",
            "service_name": "inventory-service",
            "api_endpoint": "/api/v1/inventory",
            "version": "1.0.0",
            "metadata": {"icon": "inventory", "color": "#9c27b0"},
        },
        {
            "module_id": "products",
            "module_name": "Products",
            "description": "Product catalog and management",
            "category": "Industry-Specific",
            "service_name": "product-service",
            "api_endpoint": "/api/v1/products",
            "version": "1.0.0",
            "metadata": {"icon": "shopping_cart", "color": "#f44336"},
        },
        {
            "module_id": "contact",
            "module_name": "Contact Management",
            "description": "Manage contacts and communications",
            "category": "Core",
            "service_name": "contact-service",
            "api_endpoint": "/api/v1/contacts",
            "version": "1.0.0",
            "metadata": {"icon": "contact_mail", "color": "#2196f3"},
        },
        {
            "module_id": "career",
            "module_name": "Career Management",
            "description": "Job postings and recruitment",
            "category": "Industry-Specific",
            "service_name": "career-service",
            "api_endpoint": "/api/v1/career",
            "version": "1.0.0",
            "metadata": {"icon": "work", "color": "#4caf50"},
        },
        {
            "module_id": "portfolio",
            "module_name": "Portfolio",
            "description": "Portfolio and project showcase",
            "category": "Industry-Specific",
            "service_name": "portfolio-service",
            "api_endpoint": "/api/v1/portfolio",
            "version": "1.0.0",
            "metadata": {"icon": "folder", "color": "#ff5722"},
        },
        {
            "module_id": "attendance",
            "module_name": "Attendance",
            "description": "Employee attendance tracking",
            "category": "Core",
            "service_name": "attendance-service",
            "api_endpoint": "/api/v1/attendance",
            "version": "1.0.0",
            "metadata": {"icon": "event", "color": "#009688"},
        },
        {
            "module_id": "leave",
            "module_name": "Leave Management",
            "description": "Employee leave requests and management",
            "category": "Core",
            "service_name": "leave-service",
            "api_endpoint": "/api/v1/leave",
            "version": "1.0.0",
            "metadata": {"icon": "calendar_today", "color": "#795548"},
        },
    ]
    
    inserted = 0
    updated = 0
    
    for module in modules:
        # Check if module exists
        result = conn.execute(
            text("SELECT EXISTS (SELECT 1 FROM module_registry WHERE module_id = :module_id)"),
            {"module_id": module["module_id"]},
        )
        exists = result.scalar()
        
        metadata_json = str(module["metadata"]).replace("'", '"')
        
        if exists:
            # Update existing
            conn.execute(
                text("""
                    UPDATE module_registry
                    SET module_name = :module_name,
                        description = :description,
                        category = :category,
                        service_name = :service_name,
                        api_endpoint = :api_endpoint,
                        version = :version,
                        metadata = CAST(:metadata AS JSONB),
                        is_active = TRUE,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE module_id = :module_id
                """),
                {
                    "module_id": module["module_id"],
                    "module_name": module["module_name"],
                    "description": module["description"],
                    "category": module["category"],
                    "service_name": module["service_name"],
                    "api_endpoint": module["api_endpoint"],
                    "version": module["version"],
                    "metadata": metadata_json,
                },
            )
            updated += 1
            print(f"  [UPDATE] {module['module_name']} ({module['module_id']})")
        else:
            # Insert new
            conn.execute(
                text("""
                    INSERT INTO module_registry (
                        module_id, module_name, description, category,
                        service_name, api_endpoint, version, metadata, is_active
                    ) VALUES (
                        :module_id, :module_name, :description, :category,
                        :service_name, :api_endpoint, :version, CAST(:metadata AS JSONB), TRUE
                    )
                """),
                {
                    "module_id": module["module_id"],
                    "module_name": module["module_name"],
                    "description": module["description"],
                    "category": module["category"],
                    "service_name": module["service_name"],
                    "api_endpoint": module["api_endpoint"],
                    "version": module["version"],
                    "metadata": metadata_json,
                },
            )
            inserted += 1
            print(f"  [INSERT] {module['module_name']} ({module['module_id']})")
    
    conn.commit()
    print(f"\n  [SUCCESS] Module registry seeded: {inserted} inserted, {updated} updated")


def seed_industry_templates(conn):
    """Step 3: Seed industry templates"""
    print_step(3, 3, "Seeding Industry Templates")
    
    industries = [
        {
            "code": "tech",
            "name": "Technology",
            "description": "Software development, IT services, technology companies",
            "modules": [
                {"module_id": "projects", "is_required": True, "order": 1},
                {"module_id": "crm", "is_required": True, "order": 2},
                {"module_id": "hr", "is_required": True, "order": 3},
                {"module_id": "finance", "is_required": True, "order": 4},
                {"module_id": "products", "is_required": False, "order": 5},
            ],
        },
        {
            "code": "manufacturing",
            "name": "Manufacturing",
            "description": "Manufacturing and production companies",
            "modules": [
                {"module_id": "projects", "is_required": True, "order": 1},
                {"module_id": "inventory", "is_required": True, "order": 2},
                {"module_id": "finance", "is_required": True, "order": 3},
                {"module_id": "hr", "is_required": True, "order": 4},
                {"module_id": "crm", "is_required": False, "order": 5},
            ],
        },
        {
            "code": "retail",
            "name": "Retail",
            "description": "Retail stores and e-commerce",
            "modules": [
                {"module_id": "inventory", "is_required": True, "order": 1},
                {"module_id": "crm", "is_required": True, "order": 2},
                {"module_id": "finance", "is_required": True, "order": 3},
                {"module_id": "products", "is_required": True, "order": 4},
                {"module_id": "contact", "is_required": False, "order": 5},
            ],
        },
        {
            "code": "healthcare",
            "name": "Healthcare",
            "description": "Healthcare providers and medical facilities",
            "modules": [
                {"module_id": "hr", "is_required": True, "order": 1},
                {"module_id": "finance", "is_required": True, "order": 2},
                {"module_id": "crm", "is_required": True, "order": 3},
                {"module_id": "projects", "is_required": False, "order": 4},
                {"module_id": "contact", "is_required": False, "order": 5},
            ],
        },
        {
            "code": "finance",
            "name": "Finance",
            "description": "Financial services and banking",
            "modules": [
                {"module_id": "finance", "is_required": True, "order": 1},
                {"module_id": "crm", "is_required": True, "order": 2},
                {"module_id": "hr", "is_required": True, "order": 3},
                {"module_id": "projects", "is_required": False, "order": 4},
            ],
        },
        {
            "code": "construction",
            "name": "Construction",
            "description": "Construction and engineering companies",
            "modules": [
                {"module_id": "projects", "is_required": True, "order": 1},
                {"module_id": "finance", "is_required": True, "order": 2},
                {"module_id": "hr", "is_required": True, "order": 3},
                {"module_id": "inventory", "is_required": True, "order": 4},
                {"module_id": "crm", "is_required": False, "order": 5},
            ],
        },
        {
            "code": "professional-services",
            "name": "Professional Services",
            "description": "Consulting, legal, and professional services",
            "modules": [
                {"module_id": "projects", "is_required": True, "order": 1},
                {"module_id": "crm", "is_required": True, "order": 2},
                {"module_id": "finance", "is_required": True, "order": 3},
                {"module_id": "hr", "is_required": True, "order": 4},
                {"module_id": "career", "is_required": False, "order": 5},
            ],
        },
        {
            "code": "education",
            "name": "Education",
            "description": "Educational institutions and training centers",
            "modules": [
                {"module_id": "hr", "is_required": True, "order": 1},
                {"module_id": "finance", "is_required": True, "order": 2},
                {"module_id": "projects", "is_required": True, "order": 3},
                {"module_id": "crm", "is_required": False, "order": 4},
                {"module_id": "career", "is_required": False, "order": 5},
            ],
        },
    ]
    
    industries_created = 0
    industries_updated = 0
    total_modules_assigned = 0
    
    for industry in industries:
        industry_code = industry["code"]
        
        # Check if industry exists
        result = conn.execute(
            text("SELECT id FROM industry_templates WHERE industry_code = :code"),
            {"code": industry_code},
        )
        row = result.fetchone()
        
        if row:
            template_id = row[0]
            # Update existing
            conn.execute(
                text("""
                    UPDATE industry_templates
                    SET industry_name = :name,
                        description = :description,
                        is_active = TRUE,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE industry_code = :code
                """),
                {
                    "code": industry_code,
                    "name": industry["name"],
                    "description": industry["description"],
                },
            )
            industries_updated += 1
            print(f"  [UPDATE] {industry['name']} ({industry_code})")
        else:
            # Insert new
            result = conn.execute(
                text("""
                    INSERT INTO industry_templates (
                        industry_name, industry_code, description, is_active
                    ) VALUES (
                        :name, :code, :description, TRUE
                    ) RETURNING id
                """),
                {
                    "name": industry["name"],
                    "code": industry_code,
                    "description": industry["description"],
                },
            )
            template_id = result.fetchone()[0]
            industries_created += 1
            print(f"  [CREATE] {industry['name']} ({industry_code})")
        
        # Clear existing module assignments
        conn.execute(
            text("DELETE FROM industry_module_templates WHERE template_id = :template_id"),
            {"template_id": template_id},
        )
        
        # Add modules
        modules_added = 0
        for module in industry["modules"]:
            module_id = module["module_id"]
            
            # Validate module exists in registry
            result = conn.execute(
                text(
                    "SELECT EXISTS (SELECT 1 FROM module_registry WHERE module_id = :module_id AND is_active = TRUE)"
                ),
                {"module_id": module_id},
            )
            if not result.scalar():
                print(f"    [WARN] Module {module_id} not found in registry, skipping")
                continue
            
            # Insert module assignment
            conn.execute(
                text("""
                    INSERT INTO industry_module_templates (
                        template_id, module_id, is_required, default_config, display_order
                    ) VALUES (
                        :template_id, :module_id, :is_required, '{}'::jsonb, :display_order
                    )
                """),
                {
                    "template_id": template_id,
                    "module_id": module_id,
                    "is_required": module["is_required"],
                    "display_order": module["order"],
                },
            )
            modules_added += 1
            status = "required" if module["is_required"] else "optional"
            print(f"    [ADD] {module_id} ({status})")
        
        total_modules_assigned += modules_added
        print(f"    -> Total modules assigned: {modules_added}\n")
    
    conn.commit()
    print(
        f"  [SUCCESS] Industry templates seeded: {industries_created} created, {industries_updated} updated, {total_modules_assigned} module assignments"
    )


def main():
    """Main execution function"""
    print_section("Module Management System Setup")
    print("\nThis script will:")
    print("  1. Create database tables (module_registry, industry_templates, etc.)")
    print("  2. Seed module registry with 11 modules")
    print("  3. Seed 8 industry templates with module assignments")
    print("\n[!] Make sure your database is running and accessible!")
    print("\nStarting setup in 2 seconds...")
    time.sleep(2)
    
    start_time = time.time()
    
    try:
        with engine.connect() as conn:
            # Step 1: Migration
            run_migration(conn)
            time.sleep(0.5)  # Small delay for readability
            
            # Step 2: Seed modules
            seed_module_registry(conn)
            time.sleep(0.5)
            
            # Step 3: Seed industries
            seed_industry_templates(conn)
        
        elapsed_time = time.time() - start_time
        
        print_section("Setup Complete!")
        print(f"\n[SUCCESS] All steps completed successfully in {elapsed_time:.2f} seconds")
        print("\nSummary:")
        print("  - Database tables created/verified")
        print("  - 11 modules registered in module registry")
        print("  - 8 industry templates created with module assignments")
        print("\n[INFO] Your module management system is ready to use!")
        print("\nNext steps:")
        print("  1. Start your backend services")
        print("  2. Access super admin dashboard at /super-admin/modules")
        print("  3. Manage modules and industries from the admin panel")
        
    except Exception as e:
        print(f"\n[ERROR] Error during setup: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[INFO] Setup cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERROR] Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

