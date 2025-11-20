"""
Seed script for 8 industry templates with their module assignments
Each references modules from ModuleRegistry (not hardcoded IDs)
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from shared.database.base import engine
import uuid

sys.stdout.reconfigure(line_buffering=True)


def industry_exists(conn, industry_code):
    """Check if industry exists"""
    result = conn.execute(
        text("SELECT EXISTS (SELECT 1 FROM industry_templates WHERE industry_code = :code)"),
        {"code": industry_code}
    )
    return result.scalar()


def module_exists(conn, module_id):
    """Check if module exists in registry"""
    result = conn.execute(
        text("SELECT EXISTS (SELECT 1 FROM module_registry WHERE module_id = :module_id AND is_active = TRUE)"),
        {"module_id": module_id}
    )
    return result.scalar()


def get_industry_id(conn, industry_code):
    """Get industry template ID"""
    result = conn.execute(
        text("SELECT id FROM industry_templates WHERE industry_code = :code"),
        {"code": industry_code}
    )
    row = result.fetchone()
    return row[0] if row else None


def run_seed():
    """Seed industry templates"""
    print("=" * 60)
    print("Industry Templates Seed")
    print("=" * 60)

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
            ]
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
            ]
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
            ]
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
            ]
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
            ]
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
            ]
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
            ]
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
            ]
        },
    ]

    with engine.connect() as conn:
        try:
            print(f"\nSeeding {len(industries)} industry templates...")
            
            for industry in industries:
                industry_code = industry["code"]
                
                # Check if industry exists
                if industry_exists(conn, industry_code):
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
                            "description": industry["description"]
                        }
                    )
                    print(f"  [UPDATE] {industry['name']} ({industry_code})")
                else:
                    # Insert new
                    industry_id = uuid.uuid4()
                    conn.execute(
                        text("""
                            INSERT INTO industry_templates (
                                id, industry_name, industry_code, description, is_active
                            ) VALUES (
                                :id, :name, :code, :description, TRUE
                            )
                        """),
                        {
                            "id": industry_id,
                            "name": industry["name"],
                            "code": industry_code,
                            "description": industry["description"]
                        }
                    )
                    print(f"  [INSERT] {industry['name']} ({industry_code})")
                
                # Get industry template ID
                template_id = get_industry_id(conn, industry_code)
                
                # Clear existing module assignments
                conn.execute(
                    text("DELETE FROM industry_module_templates WHERE template_id = :template_id"),
                    {"template_id": template_id}
                )
                
                # Add modules
                for module in industry["modules"]:
                    module_id = module["module_id"]
                    
                    # Validate module exists in registry
                    if not module_exists(conn, module_id):
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
                            "display_order": module["order"]
                        }
                    )
                    print(f"    [ADD] {module_id} ({'required' if module['is_required'] else 'optional'})")
            
            conn.commit()
            
            print("\n" + "=" * 60)
            print("[OK] Industry templates seed completed!")
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

