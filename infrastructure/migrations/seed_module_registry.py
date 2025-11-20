"""
Seed script to register all existing modules in the system
This is the source of truth - no hardcoding after this
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from shared.database.base import engine

sys.stdout.reconfigure(line_buffering=True)


def module_exists(conn, module_id):
    """Check if module exists"""
    result = conn.execute(
        text("SELECT EXISTS (SELECT 1 FROM module_registry WHERE module_id = :module_id)"),
        {"module_id": module_id}
    )
    return result.scalar()


def run_seed():
    """Seed module registry"""
    print("=" * 60)
    print("Module Registry Seed")
    print("=" * 60)

    modules = [
        {
            "module_id": "projects",
            "module_name": "Project Management",
            "description": "Manage projects, tasks, and teams",
            "category": "Core",
            "service_name": "project-service",
            "api_endpoint": "/api/v1/projects",
            "version": "1.0.0",
            "metadata": {"icon": "project", "color": "#1976d2"}
        },
        {
            "module_id": "hr",
            "module_name": "HR Management",
            "description": "Employee management, attendance, leave",
            "category": "Core",
            "service_name": "employee-service",
            "api_endpoint": "/api/v1/hr",
            "version": "1.0.0",
            "metadata": {"icon": "people", "color": "#dc004e"}
        },
        {
            "module_id": "finance",
            "module_name": "Finance",
            "description": "Accounting, invoicing, expenses",
            "category": "Core",
            "service_name": "finance-service",
            "api_endpoint": "/api/v1/finance",
            "version": "1.0.0",
            "metadata": {"icon": "account_balance", "color": "#00a86b"}
        },
        {
            "module_id": "crm",
            "module_name": "CRM",
            "description": "Customer relationship management",
            "category": "Core",
            "service_name": "crm-service",
            "api_endpoint": "/api/v1/crm",
            "version": "1.0.0",
            "metadata": {"icon": "contacts", "color": "#ff9800"}
        },
        {
            "module_id": "inventory",
            "module_name": "Inventory",
            "description": "Stock management and tracking",
            "category": "Industry-Specific",
            "service_name": "inventory-service",
            "api_endpoint": "/api/v1/inventory",
            "version": "1.0.0",
            "metadata": {"icon": "inventory", "color": "#9c27b0"}
        },
        {
            "module_id": "products",
            "module_name": "Products",
            "description": "Product catalog and management",
            "category": "Industry-Specific",
            "service_name": "product-service",
            "api_endpoint": "/api/v1/products",
            "version": "1.0.0",
            "metadata": {"icon": "shopping_cart", "color": "#f44336"}
        },
        {
            "module_id": "contact",
            "module_name": "Contact Management",
            "description": "Manage contacts and communications",
            "category": "Core",
            "service_name": "contact-service",
            "api_endpoint": "/api/v1/contacts",
            "version": "1.0.0",
            "metadata": {"icon": "contact_mail", "color": "#2196f3"}
        },
        {
            "module_id": "career",
            "module_name": "Career Management",
            "description": "Job postings and recruitment",
            "category": "Industry-Specific",
            "service_name": "career-service",
            "api_endpoint": "/api/v1/career",
            "version": "1.0.0",
            "metadata": {"icon": "work", "color": "#4caf50"}
        },
        {
            "module_id": "portfolio",
            "module_name": "Portfolio",
            "description": "Portfolio and project showcase",
            "category": "Industry-Specific",
            "service_name": "portfolio-service",
            "api_endpoint": "/api/v1/portfolio",
            "version": "1.0.0",
            "metadata": {"icon": "folder", "color": "#ff5722"}
        },
        {
            "module_id": "attendance",
            "module_name": "Attendance",
            "description": "Employee attendance tracking",
            "category": "Core",
            "service_name": "attendance-service",
            "api_endpoint": "/api/v1/attendance",
            "version": "1.0.0",
            "metadata": {"icon": "event", "color": "#009688"}
        },
        {
            "module_id": "leave",
            "module_name": "Leave Management",
            "description": "Employee leave requests and management",
            "category": "Core",
            "service_name": "leave-service",
            "api_endpoint": "/api/v1/leave",
            "version": "1.0.0",
            "metadata": {"icon": "calendar_today", "color": "#795548"}
        },
    ]

    with engine.connect() as conn:
        try:
            print(f"\nSeeding {len(modules)} modules...")
            inserted = 0
            updated = 0
            
            for module in modules:
                if module_exists(conn, module["module_id"]):
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
                                metadata = :metadata::jsonb,
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
                            "metadata": str(module["metadata"]).replace("'", '"')
                        }
                    )
                    updated += 1
                    print(f"  [UPDATE] {module['module_id']}")
                else:
                    # Insert new
                    conn.execute(
                        text("""
                            INSERT INTO module_registry (
                                module_id, module_name, description, category,
                                service_name, api_endpoint, version, metadata, is_active
                            ) VALUES (
                                :module_id, :module_name, :description, :category,
                                :service_name, :api_endpoint, :version, :metadata::jsonb, TRUE
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
                            "metadata": str(module["metadata"]).replace("'", '"')
                        }
                    )
                    inserted += 1
                    print(f"  [INSERT] {module['module_id']}")
            
            conn.commit()
            
            print("\n" + "=" * 60)
            print(f"[OK] Seed completed! Inserted: {inserted}, Updated: {updated}")
            print("=" * 60)
            
        except Exception as e:
            conn.rollback()
            print(f"\n[FAIL] Seed failed: {e}")
            import traceback
            traceback.print_exc()
            raise


if __name__ == "__main__":
    try:
        run_seed()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

