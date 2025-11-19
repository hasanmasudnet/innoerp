"""
Migration to add organization branding and theme support
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
    print("Organization Branding & Theme Migration")
    print("=" * 60)

    with engine.connect() as conn:
        try:
            # Step 1: Add custom_domain to organizations table
            print("\n[1/3] Updating organizations table...")
            if table_exists(conn, "organizations"):
                if not column_exists(conn, "organizations", "custom_domain"):
                    conn.execute(
                        text(
                            "ALTER TABLE organizations ADD COLUMN custom_domain VARCHAR(255)"
                        )
                    )
                    conn.commit()
                    print("[OK] Added custom_domain column")
                else:
                    print("[SKIP] custom_domain column already exists")

                # Ensure subdomain is indexed (should already exist)
                print("[OK] subdomain column verified")
            else:
                print("[SKIP] organizations table does not exist")

            # Step 2: Create organization_branding table
            print("\n[2/3] Creating organization_branding table...")
            if not table_exists(conn, "organization_branding"):
                conn.execute(
                    text(
                        """
                        CREATE TABLE organization_branding (
                            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                            organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
                            
                            -- Branding
                            logo_url VARCHAR(500),
                            favicon_url VARCHAR(500),
                            company_name VARCHAR(255),
                            primary_color VARCHAR(7),
                            secondary_color VARCHAR(7),
                            accent_color VARCHAR(7),
                            
                            -- Typography
                            font_family VARCHAR(100) DEFAULT 'Inter',
                            heading_font VARCHAR(100) DEFAULT 'Inter',
                            
                            -- Layout
                            sidebar_style VARCHAR(50) DEFAULT 'default',
                            header_style VARCHAR(50) DEFAULT 'default',
                            dashboard_layout VARCHAR(50) DEFAULT 'grid',
                            
                            -- Custom CSS
                            custom_css TEXT,
                            
                            -- Theme preset
                            theme_preset VARCHAR(50) DEFAULT 'base',
                            
                            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
                            
                            CONSTRAINT uq_org_branding_org_id UNIQUE (organization_id)
                        )
                    """
                    )
                )
                conn.execute(
                    text(
                        "CREATE INDEX IF NOT EXISTS ix_org_branding_org_id ON organization_branding(organization_id)"
                    )
                )
                conn.commit()
                print("[OK] organization_branding table created")
            else:
                print("[SKIP] organization_branding table already exists")

            # Step 3: Create default branding for existing organizations
            print("\n[3/3] Creating default branding for existing organizations...")
            result = conn.execute(
                text(
                    """
                    INSERT INTO organization_branding (organization_id, company_name, theme_preset)
                    SELECT id, name, 'base'
                    FROM organizations
                    WHERE id NOT IN (SELECT organization_id FROM organization_branding)
                    ON CONFLICT (organization_id) DO NOTHING
                """
                )
            )
            conn.commit()
            print(f"[OK] Created default branding for {result.rowcount} organization(s)")

            print("\n" + "=" * 60)
            print("[OK] Migration completed successfully!")
            print("=" * 60)

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

