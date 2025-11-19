"""
Script to create initial admin user for UnlockLive organization
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

# Load tenant service schemas
tenant_spec = importlib.util.spec_from_file_location(
    "tenant_schemas",
    project_root / "services" / "tenant-service" / "app" / "schemas.py"
)
tenant_schemas = importlib.util.module_from_spec(tenant_spec)
tenant_spec.loader.exec_module(tenant_schemas)
Organization = tenant_schemas.Organization

# Load auth service schemas (SQLAlchemy models)
auth_spec = importlib.util.spec_from_file_location(
    "auth_schemas",
    project_root / "services" / "auth-service" / "app" / "schemas.py"
)
auth_schemas = importlib.util.module_from_spec(auth_spec)
auth_spec.loader.exec_module(auth_schemas)
User = auth_schemas.User
UserOrganization = auth_schemas.UserOrganization


def create_initial_admin():
    """Create initial admin user for UnlockLive organization"""
    print("=" * 60)
    print("Creating Initial Admin User")
    print("=" * 60)
    
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        # Step 1: Get UnlockLive organization
        print("\n[1/3] Finding UnlockLive organization...")
        org = db.query(Organization).filter(
            Organization.slug == "unlocklive"
        ).first()
        
        if not org:
            print("[ERROR] UnlockLive organization not found!")
            print("        Please run: python infrastructure/create_unlocklive_org.py")
            return None
        
        print(f"[OK] Found organization: {org.name} (ID: {org.id})")
        
        # Step 2: Check if admin user already exists
        print("\n[2/3] Checking for existing admin user...")
        existing_user = db.query(User).filter(
            User.email == "admin@unlocklive.com",
            User.organization_id == org.id
        ).first()
        
        if existing_user:
            print(f"[SKIP] Admin user already exists!")
            print(f"       Email: {existing_user.email}")
            print(f"       Username: {existing_user.username}")
            print(f"       User Type: {existing_user.user_type}")
            return existing_user.id
        
        # Step 3: Create admin user
        print("\n[3/3] Creating admin user...")
        
        # Default password (should be changed after first login)
        default_password = "Admin@123"  # Change this!
        
        admin_user = User(
            id=uuid.uuid4(),
            organization_id=org.id,
            email="admin@unlocklive.com",
            username="admin",
            password_hash=get_password_hash(default_password),
            user_type="admin",
            first_name="Admin",
            last_name="User",
            is_active=True,
            is_superuser=False  # Tenant admin, not super admin
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        print(f"[OK] Admin user created!")
        print(f"     ID: {admin_user.id}")
        print(f"     Email: {admin_user.email}")
        print(f"     Username: {admin_user.username}")
        print(f"     User Type: {admin_user.user_type}")
        
        # Step 4: Create user-organization relationship
        print("\n[4/4] Creating user-organization relationship...")
        
        user_org = UserOrganization(
            id=uuid.uuid4(),
            user_id=admin_user.id,
            organization_id=org.id,
            role="admin"
        )
        
        db.add(user_org)
        db.commit()
        db.refresh(user_org)
        
        print(f"[OK] User-organization relationship created!")
        print(f"     User ID: {user_org.user_id}")
        print(f"     Organization ID: {user_org.organization_id}")
        print(f"     Role: {user_org.role}")
        
        print("\n" + "=" * 60)
        print("[OK] Initial admin user created successfully!")
        print("=" * 60)
        print(f"\nLogin Credentials:")
        print(f"  Email: admin@unlocklive.com")
        print(f"  Username: admin")
        print(f"  Password: {default_password}")
        print(f"\n⚠️  IMPORTANT: Change the password after first login!")
        print("=" * 60)
        
        return admin_user.id
        
    except Exception as e:
        db.rollback()
        print(f"\n[FAIL] Error creating admin user: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    try:
        user_id = create_initial_admin()
        if user_id:
            print(f"\n✅ Admin user ID: {user_id}")
            print("\nYou can now:")
            print("  1. Test login with the credentials above")
            print("  2. Create more users via the API or invitation system")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

