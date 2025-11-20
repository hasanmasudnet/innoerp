"""
Migration to add industry-based module management system
Creates: module_registry, industry_templates, industry_module_templates tables
Updates: organizations table with industry_code and industry_name
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from shared.database.base import engine

sys.stdout.reconfigure(line_buffering=True)


def table_exists(conn, table_name):
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


def column_exists(conn, table_name, column_name):
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


def run_migration():
    """Run the migration"""
    print("=" * 60)
    print("Industry Module Management System Migration")
    print("=" * 60)

    with engine.connect() as conn:
        try:
            # Step 1: Update organizations table
            print("\n[1/4] Updating organizations table...")
            if table_exists(conn, "organizations"):
                if not column_exists(conn, "organizations", "industry_code"):
                    conn.execute(
                        text(
                            "ALTER TABLE organizations ADD COLUMN industry_code VARCHAR(100)"
                        )
                    )
                    conn.execute(
                        text(
                            "CREATE INDEX IF NOT EXISTS ix_organizations_industry_code ON organizations(industry_code)"
                        )
                    )
                    conn.commit()
                    print("[OK] Added industry_code column and index")
                else:
                    print("[SKIP] industry_code column already exists")

                if not column_exists(conn, "organizations", "industry_name"):
                    conn.execute(
                        text(
                            "ALTER TABLE organizations ADD COLUMN industry_name VARCHAR(255)"
                        )
                    )
                    conn.commit()
                    print("[OK] Added industry_name column")
                else:
                    print("[SKIP] industry_name column already exists")
            else:
                print("[SKIP] organizations table does not exist")

            # Step 2: Create module_registry table
            print("\n[2/4] Creating module_registry table...")
            if not table_exists(conn, "module_registry"):
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
                conn.commit()
                print("[OK] module_registry table created")
            else:
                print("[SKIP] module_registry table already exists")

            # Step 3: Create industry_templates table
            print("\n[3/4] Creating industry_templates table...")
            if not table_exists(conn, "industry_templates"):
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
                    text(
                        "CREATE INDEX IF NOT EXISTS ix_industry_templates_code ON industry_templates(industry_code)"
                    )
                )
                conn.commit()
                print("[OK] industry_templates table created")
            else:
                print("[SKIP] industry_templates table already exists")

            # Step 4: Create industry_module_templates table
            print("\n[4/4] Creating industry_module_templates table...")
            if not table_exists(conn, "industry_module_templates"):
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
                conn.commit()
                print("[OK] industry_module_templates table created")
            else:
                print("[SKIP] industry_module_templates table already exists")

            print("\n" + "=" * 60)
            print("[OK] Migration completed successfully!")
            print("=" * 60)
            print("\nNext steps:")
            print("1. Run seed_module_registry.py to register all modules")
            print("2. Run seed_industry_templates.py to create industry templates")

        except Exception as e:
            conn.rollback()
            print(f"\n[FAIL] Migration failed: {e}")
            import traceback

            traceback.print_exc()
            raise


if __name__ == "__main__":
    try:
        run_migration()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

