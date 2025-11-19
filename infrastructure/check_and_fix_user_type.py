"""
Script to check and fix user_type for admin@unlocklive.com
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


def check_and_fix_user_type():
    """Check and fix user_type for admin@unlocklive.com"""
    print("=" * 60)
    print("Checking and Fixing User Type")
    print("=" * 60)
    
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        # Find UnlockLive organization
        print("\n[1/3] Finding UnlockLive organization...")
        org = db.query(Organization).filter(
            Organization.slug == "unlocklive"
        ).first()
        
        if not org:
            print("[ERROR] UnlockLive organization not found!")
            return None
        
        print(f"[OK] Found organization: {org.name} (ID: {org.id})")
        
        # Find admin user
        print("\n[2/3] Finding admin@unlocklive.com...")
        admin_user = db.query(User).filter(
            User.email == "admin@unlocklive.com",
            User.organization_id == org.id
        ).first()
        
        if not admin_user:
            print("[ERROR] admin@unlocklive.com not found!")
            return None
        
        print(f"[OK] Found user: {admin_user.email}")
        print(f"     Current user_type: {admin_user.user_type}")
        print(f"     Current is_superuser: {admin_user.is_superuser}")
        print(f"     Current organization_id: {admin_user.organization_id}")
        
        # Check and fix user_type
        needs_update = False
        if admin_user.user_type != 'admin':
            print(f"\n[FIX] user_type is '{admin_user.user_type}', should be 'admin'")
            admin_user.user_type = 'admin'
            needs_update = True
        
        if admin_user.is_superuser:
            print(f"\n[FIX] is_superuser is True, should be False for tenant admin")
            admin_user.is_superuser = False
            needs_update = True
        
        if needs_update:
            print("\n[UPDATE] Saving changes...")
            db.commit()
            db.refresh(admin_user)
            print("[OK] User updated successfully!")
            print(f"     New user_type: {admin_user.user_type}")
            print(f"     New is_superuser: {admin_user.is_superuser}")
        else:
            print("\n[OK] User type is already correct!")
        
        print("\n" + "=" * 60)
        print("[OK] User type check complete!")
        print("=" * 60)
        print(f"\nUser will now:")
        print(f"  - Login at /login")
        print(f"  - Redirect to /tenant-admin dashboard")
        print(f"  - Only manage UnlockLive organization")
        print("=" * 60)
        
        return admin_user.id
        
    except Exception as e:
        db.rollback()
        print(f"\n[FAIL] Error checking/fixing user type: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    try:
        user_id = check_and_fix_user_type()
        if user_id:
            print(f"\n✅ User ID: {user_id}")
            print("\nPlease log out and log back in for changes to take effect.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

