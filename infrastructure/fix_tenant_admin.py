"""
Script to fix admin@unlocklive.com - remove superuser flag so it's a tenant admin only
"""
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import sessionmaker
from shared.database.base import engine
import importlib.util

# Load auth service schemas (SQLAlchemy models)
auth_spec = importlib.util.spec_from_file_location(
    "auth_schemas",
    project_root / "services" / "auth-service" / "app" / "schemas.py"
)
auth_schemas = importlib.util.module_from_spec(auth_spec)
auth_spec.loader.exec_module(auth_schemas)
User = auth_schemas.User

# Load tenant service schemas
tenant_spec = importlib.util.spec_from_file_location(
    "tenant_schemas",
    project_root / "services" / "tenant-service" / "app" / "schemas.py"
)
tenant_schemas = importlib.util.module_from_spec(tenant_spec)
tenant_spec.loader.exec_module(tenant_schemas)
Organization = tenant_schemas.Organization


def fix_tenant_admin():
    """Fix admin@unlocklive.com to be tenant admin only (not superuser)"""
    print("=" * 60)
    print("Fixing Tenant Admin User")
    print("=" * 60)
    
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        # Find UnlockLive organization
        print("\n[1/2] Finding UnlockLive organization...")
        org = db.query(Organization).filter(
            Organization.slug == "unlocklive"
        ).first()
        
        if not org:
            print("[ERROR] UnlockLive organization not found!")
            return None
        
        print(f"[OK] Found organization: {org.name} (ID: {org.id})")
        
        # Find admin user
        print("\n[2/2] Finding admin@unlocklive.com...")
        admin_user = db.query(User).filter(
            User.email == "admin@unlocklive.com",
            User.organization_id == org.id
        ).first()
        
        if not admin_user:
            print("[ERROR] admin@unlocklive.com not found!")
            return None
        
        print(f"[OK] Found user: {admin_user.email}")
        print(f"     Current is_superuser: {admin_user.is_superuser}")
        print(f"     Current user_type: {admin_user.user_type}")
        
        # Update to remove superuser flag
        if admin_user.is_superuser:
            print("\n[UPDATE] Removing superuser flag...")
            admin_user.is_superuser = False
            admin_user.user_type = "admin"  # Ensure it's admin type
            db.commit()
            db.refresh(admin_user)
            print("[OK] Updated! User is now tenant admin only")
            print(f"     New is_superuser: {admin_user.is_superuser}")
            print(f"     New user_type: {admin_user.user_type}")
        else:
            print("[SKIP] User is already not a superuser")
        
        print("\n" + "=" * 60)
        print("[OK] Tenant admin user fixed!")
        print("=" * 60)
        print(f"\nUser will now:")
        print(f"  - Login at /login (not /super-admin/login)")
        print(f"  - Redirect to /tenant-admin dashboard")
        print(f"  - Only manage UnlockLive organization")
        print("=" * 60)
        
        return admin_user.id
        
    except Exception as e:
        db.rollback()
        print(f"\n[FAIL] Error fixing tenant admin: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    try:
        user_id = fix_tenant_admin()
        if user_id:
            print(f"\n✅ Tenant admin user ID: {user_id}")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

