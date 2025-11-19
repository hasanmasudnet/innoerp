"""
Script to create super admin user (admin@innoerp.io)
Super admin can manage all tenant accounts without being tied to a specific organization
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
import uuid

# Password hashing - use bcrypt directly
try:
    import bcrypt
    def get_password_hash(password: str) -> str:
        """Hash password using bcrypt directly"""
        # Encode password to bytes
        password_bytes = password.encode('utf-8')
        # Truncate if longer than 72 bytes (bcrypt limit)
        if len(password_bytes) > 72:
            password_bytes = password_bytes[:72]
        # Generate salt and hash
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode('utf-8')
except ImportError:
    # Fallback to passlib if bcrypt not available
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    def get_password_hash(password: str) -> str:
        """Hash password using passlib"""
        return pwd_context.hash(password)

# Load auth service schemas (SQLAlchemy models)
auth_spec = importlib.util.spec_from_file_location(
    "auth_schemas",
    project_root / "services" / "auth-service" / "app" / "schemas.py"
)
auth_schemas = importlib.util.module_from_spec(auth_spec)
auth_spec.loader.exec_module(auth_schemas)
User = auth_schemas.User
UserOrganization = auth_schemas.UserOrganization

# Load tenant service schemas to get first organization (for organization_id requirement)
tenant_spec = importlib.util.spec_from_file_location(
    "tenant_schemas",
    project_root / "services" / "tenant-service" / "app" / "schemas.py"
)
tenant_schemas = importlib.util.module_from_spec(tenant_spec)
tenant_spec.loader.exec_module(tenant_schemas)
Organization = tenant_schemas.Organization


def create_super_admin():
    """Create super admin user (admin@innoerp.io)"""
    print("=" * 60)
    print("Creating Super Admin User")
    print("=" * 60)
    
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        # Step 1: Get first organization (required for user table, but super admin won't use it)
        print("\n[1/4] Finding first organization (for database constraint)...")
        first_org = db.query(Organization).first()
        
        if not first_org:
            print("[WARN] No organizations found. Creating one...")
            # Create a system organization for super admin
            first_org = Organization(
                id=uuid.uuid4(),
                name="System",
                slug="system",
                subdomain="system",
                is_active=True
            )
            db.add(first_org)
            db.commit()
            db.refresh(first_org)
            print(f"[OK] Created system organization: {first_org.id}")
        else:
            print(f"[OK] Using organization: {first_org.name} (ID: {first_org.id})")
        
        # Step 2: Check if super admin already exists
        print("\n[2/4] Checking for existing super admin user...")
        existing_user = db.query(User).filter(
            User.email == "admin@innoerp.io"
        ).first()
        
        if existing_user:
            print(f"[SKIP] Super admin user already exists!")
            print(f"       Email: {existing_user.email}")
            print(f"       Username: {existing_user.username}")
            print(f"       Is Superuser: {existing_user.is_superuser}")
            print(f"       Organization ID: {existing_user.organization_id}")
            
            # Update to ensure it's a superuser
            if not existing_user.is_superuser:
                print("\n[UPDATE] Setting is_superuser=True...")
                existing_user.is_superuser = True
                db.commit()
                print("[OK] Updated to superuser")
            
            return existing_user.id
        
        # Step 3: Create super admin user
        print("\n[3/4] Creating super admin user...")
        
        # Default password (should be changed after first login)
        default_password = "SuperAdmin@123"  # Change this!
        
        super_admin_user = User(
            id=uuid.uuid4(),
            organization_id=first_org.id,  # Required by DB, but super admin doesn't use it
            email="admin@innoerp.io",
            username="superadmin",
            password_hash=get_password_hash(default_password),
            user_type="admin",
            first_name="Super",
            last_name="Admin",
            is_active=True,
            is_superuser=True  # This is the key flag for super admin
        )
        
        db.add(super_admin_user)
        db.commit()
        db.refresh(super_admin_user)
        
        print(f"[OK] Super admin user created!")
        print(f"     ID: {super_admin_user.id}")
        print(f"     Email: {super_admin_user.email}")
        print(f"     Username: {super_admin_user.username}")
        print(f"     User Type: {super_admin_user.user_type}")
        print(f"     Is Superuser: {super_admin_user.is_superuser}")
        print(f"     Organization ID: {super_admin_user.organization_id} (not used for super admin)")
        
        # Step 4: Note about UserOrganization (optional for super admin)
        print("\n[4/4] Note: Super admin doesn't require UserOrganization relationship")
        print("      Super admin can access all organizations via is_superuser flag")
        
        print("\n" + "=" * 60)
        print("[OK] Super admin user created successfully!")
        print("=" * 60)
        print(f"\nLogin Credentials:")
        print(f"  Email: admin@innoerp.io")
        print(f"  Username: superadmin")
        print(f"  Password: {default_password}")
        print(f"\n⚠️  IMPORTANT: Change the password after first login!")
        print(f"\n📝 Note: Login at /super-admin/login (not /login)")
        print("=" * 60)
        
        return super_admin_user.id
        
    except Exception as e:
        db.rollback()
        print(f"\n[FAIL] Error creating super admin user: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    try:
        user_id = create_super_admin()
        if user_id:
            print(f"\n✅ Super admin user ID: {user_id}")
            print("\nYou can now:")
            print("  1. Login at http://localhost:3000/super-admin/login")
            print("  2. Manage all tenant accounts")
            print("  3. Access super admin dashboard")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

