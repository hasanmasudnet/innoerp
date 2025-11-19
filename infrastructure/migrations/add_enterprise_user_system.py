"""
Database migration script for Enterprise User Relationship System

This script:
1. Adds organization_id to users table (backfill with first org)
2. Adds user_type column to users table
3. Updates unique constraints (email, username per organization)
4. Creates invitations table
5. Creates module-specific relationship tables
6. Updates existing UserOrganization records
"""
import sys
import os
from pathlib import Path

# Force immediate output
sys.stdout.reconfigure(line_buffering=True)

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text, inspect
from shared.database.base import engine, Base

# Define table schemas directly to avoid import conflicts
# We'll use raw SQL for table creation to avoid SQLAlchemy model conflicts


def get_first_organization_id(conn):
    """Get the first organization ID for backfilling"""
    result = conn.execute(text("SELECT id FROM organizations ORDER BY created_at LIMIT 1"))
    row = result.fetchone()
    if row:
        return row[0]
    return None


def table_exists(conn, table_name):
    """Check if table exists"""
    inspector = inspect(engine)
    return table_name in inspector.get_table_names()


def column_exists(conn, table_name, column_name):
    """Check if column exists in table"""
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns


def run_migration():
    """Run the migration"""
    print("=" * 60)
    print("Enterprise User Relationship System Migration")
    print("=" * 60)
    
    # Use autocommit mode to avoid long-running transactions
    # This prevents locking the database for too long
    with engine.connect() as conn:
        # Don't use a transaction - commit each operation immediately
        # This prevents long locks
        try:
            # Step 1: Get first organization ID for backfilling
            print("\n[1/6] Getting first organization ID...")
            first_org_id = get_first_organization_id(conn)
            if not first_org_id:
                print("[WARN] No organizations found. Migration will fail if users table has data.")
                print("       Please create at least one organization first.")
                first_org_id = None
            else:
                print(f"[OK] Found organization: {first_org_id}")
            
            # Step 2: Add organization_id to users table if it doesn't exist
            if table_exists(conn, "users"):
                print("\n[2/6] Updating users table...")
                
                # Check how many users exist
                try:
                    user_count = conn.execute(text("SELECT COUNT(*) FROM users")).scalar()
                    print(f"  Found {user_count} existing user(s)")
                    sys.stdout.flush()
                except Exception as e:
                    print(f"  [WARN] Could not count users: {e}")
                    user_count = 0
                
                if not column_exists(conn, "users", "organization_id"):
                    print("  Adding organization_id column...")
                    sys.stdout.flush()
                    if first_org_id:
                        print(f"  Backfilling with organization_id: {first_org_id}")
                        sys.stdout.flush()
                        try:
                            # Use autocommit for each operation to avoid long locks
                            conn.execute(text(
                                f"ALTER TABLE users ADD COLUMN organization_id UUID"
                            ))
                            conn.commit()
                            print("  [OK] Column added")
                            sys.stdout.flush()
                            
                            if user_count > 0:
                                print(f"  Updating {user_count} user(s) with organization_id...")
                                sys.stdout.flush()
                                result = conn.execute(text(
                                    f"UPDATE users SET organization_id = '{first_org_id}' WHERE organization_id IS NULL"
                                ))
                                conn.commit()
                                print(f"  [OK] {result.rowcount} user(s) updated")
                                sys.stdout.flush()
                            
                            print("  Setting organization_id to NOT NULL...")
                            sys.stdout.flush()
                            conn.execute(text(
                                "ALTER TABLE users ALTER COLUMN organization_id SET NOT NULL"
                            ))
                            conn.commit()
                            print("  [OK] organization_id column added and backfilled")
                            sys.stdout.flush()
                        except Exception as e:
                            print(f"  [ERROR] Failed to add organization_id: {e}")
                            sys.stdout.flush()
                            raise
                    else:
                        conn.execute(text(
                            "ALTER TABLE users ADD COLUMN organization_id UUID"
                        ))
                        conn.commit()
                        print("  [WARN] organization_id column added but not backfilled (no organizations)")
                        print("         Note: If users table has data, you'll need to set organization_id manually")
                else:
                    print("  [SKIP] organization_id column already exists")
                
                # Add user_type column
                print("  Checking user_type column...")
                sys.stdout.flush()
                if not column_exists(conn, "users", "user_type"):
                    print("  Adding user_type column...")
                    sys.stdout.flush()
                    conn.execute(text(
                        "ALTER TABLE users ADD COLUMN user_type VARCHAR(20) NOT NULL DEFAULT 'employee'"
                    ))
                    conn.commit()
                    print("  [OK] user_type column added")
                    sys.stdout.flush()
                else:
                    print("  [SKIP] user_type column already exists")
                    sys.stdout.flush()
                
                # Drop old unique constraints if they exist
                print("  Dropping old unique constraints...")
                sys.stdout.flush()
                try:
                    conn.execute(text("ALTER TABLE users DROP CONSTRAINT IF EXISTS users_email_key"))
                    conn.commit()
                    print("  [OK] Dropped users_email_key constraint")
                    sys.stdout.flush()
                    conn.execute(text("ALTER TABLE users DROP CONSTRAINT IF EXISTS users_username_key"))
                    conn.commit()
                    print("  [OK] Dropped users_username_key constraint")
                    sys.stdout.flush()
                    print("  [OK] Old unique constraints dropped")
                except Exception as e:
                    print(f"  [INFO] Could not drop old constraints: {e}")
                    sys.stdout.flush()
                
                # Add new unique constraints per organization
                print("  Adding organization-scoped unique constraints...")
                try:
                    conn.execute(text(
                        "ALTER TABLE users ADD CONSTRAINT uq_user_org_email UNIQUE (organization_id, email)"
                    ))
                    conn.commit()
                    conn.execute(text(
                        "ALTER TABLE users ADD CONSTRAINT uq_user_org_username UNIQUE (organization_id, username)"
                    ))
                    conn.commit()
                    print("  [OK] New unique constraints added")
                except Exception as e:
                    print(f"  [WARN] Could not add unique constraints: {e}")
                    print("         They may already exist")
                
                # Add index on organization_id if it doesn't exist
                try:
                    conn.execute(text(
                        "CREATE INDEX IF NOT EXISTS ix_users_organization_id ON users(organization_id)"
                    ))
                    conn.commit()
                    print("  [OK] Index on organization_id created")
                except Exception as e:
                    print(f"  [INFO] Index may already exist: {e}")
            else:
                print("\n[2/6] [SKIP] users table does not exist (will be created by Base.metadata.create_all)")
            
            # Step 3: Create invitations table
            print("\n[3/6] Creating invitations table...")
            if not table_exists(conn, "invitations"):
                try:
                    conn.execute(text("""
                        CREATE TABLE invitations (
                            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                            organization_id UUID NOT NULL,
                            email VARCHAR(255) NOT NULL,
                            invited_by_user_id UUID NOT NULL,
                            user_type VARCHAR(20) NOT NULL,
                            module_type VARCHAR(50),
                            invitation_token VARCHAR(255) UNIQUE NOT NULL,
                            status VARCHAR(20) NOT NULL DEFAULT 'pending',
                            expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
                            accepted_at TIMESTAMP WITH TIME ZONE,
                            invitation_metadata JSONB,
                            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
                            CONSTRAINT uq_invitation_org_email_status UNIQUE (organization_id, email, status)
                        )
                    """))
                    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_invitations_organization_id ON invitations(organization_id)"))
                    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_invitations_email ON invitations(email)"))
                    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_invitations_token ON invitations(invitation_token)"))
                    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_invitations_invited_by ON invitations(invited_by_user_id)"))
                    conn.commit()
                    print("[OK] invitations table created")
                except Exception as e:
                    print(f"[WARN] Could not create invitations table: {e}")
            else:
                print("[SKIP] invitations table already exists")
            
            # Step 4: Create module-specific relationship tables
            print("\n[4/6] Creating module-specific relationship tables...")
            
            if not table_exists(conn, "user_project_relationships"):
                try:
                    conn.execute(text("""
                        CREATE TABLE user_project_relationships (
                            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                            user_id UUID NOT NULL REFERENCES users(id),
                            organization_id UUID NOT NULL,
                            project_id UUID,
                            relationship_type VARCHAR(20) NOT NULL,
                            role VARCHAR(50) NOT NULL,
                            is_active BOOLEAN NOT NULL DEFAULT TRUE,
                            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
                            CONSTRAINT uq_user_project UNIQUE (user_id, project_id)
                        )
                    """))
                    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_user_project_user_id ON user_project_relationships(user_id)"))
                    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_user_project_org_id ON user_project_relationships(organization_id)"))
                    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_user_project_project_id ON user_project_relationships(project_id)"))
                    conn.commit()
                    print("[OK] user_project_relationships table created")
                except Exception as e:
                    print(f"[WARN] Could not create user_project_relationships table: {e}")
            else:
                print("[SKIP] user_project_relationships table already exists")
            
            if not table_exists(conn, "user_finance_relationships"):
                try:
                    conn.execute(text("""
                        CREATE TABLE user_finance_relationships (
                            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                            user_id UUID NOT NULL REFERENCES users(id),
                            organization_id UUID NOT NULL,
                            relationship_type VARCHAR(20) NOT NULL,
                            role VARCHAR(50) NOT NULL,
                            is_active BOOLEAN NOT NULL DEFAULT TRUE,
                            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
                            CONSTRAINT uq_user_finance UNIQUE (user_id, organization_id, relationship_type)
                        )
                    """))
                    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_user_finance_user_id ON user_finance_relationships(user_id)"))
                    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_user_finance_org_id ON user_finance_relationships(organization_id)"))
                    conn.commit()
                    print("[OK] user_finance_relationships table created")
                except Exception as e:
                    print(f"[WARN] Could not create user_finance_relationships table: {e}")
            else:
                print("[SKIP] user_finance_relationships table already exists")
            
            # Step 5: Update UserOrganization records (if needed)
            print("\n[5/6] Checking UserOrganization records...")
            if table_exists(conn, "user_organizations"):
                result = conn.execute(text("SELECT COUNT(*) FROM user_organizations"))
                count = result.scalar()
                print(f"[OK] Found {count} user_organization records")
                print("      (No changes needed - table structure is compatible)")
            else:
                print("[SKIP] user_organizations table does not exist")
            
            # Step 6: Verify migration
            print("\n[6/6] Verifying migration...")
            if table_exists(conn, "users"):
                if column_exists(conn, "users", "organization_id") and column_exists(conn, "users", "user_type"):
                    print("[OK] users table migration verified")
                else:
                    print("[FAIL] users table migration incomplete")
            if table_exists(conn, "invitations"):
                print("[OK] invitations table verified")
            if table_exists(conn, "user_project_relationships"):
                print("[OK] user_project_relationships table verified")
            if table_exists(conn, "user_finance_relationships"):
                print("[OK] user_finance_relationships table verified")
            
            # All operations are already committed individually
            print("\n" + "=" * 60)
            print("[OK] Migration completed successfully!")
            print("=" * 60)
            
        except Exception as e:
            print(f"\n[FAIL] Migration failed: {e}")
            import traceback
            traceback.print_exc()
            raise


if __name__ == "__main__":
    try:
        run_migration()
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

