"""
Script to create UnlockLive organization
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

# Load tenant service schemas
tenant_spec = importlib.util.spec_from_file_location(
    "tenant_schemas",
    project_root / "services" / "tenant-service" / "app" / "schemas.py"
)
tenant_schemas = importlib.util.module_from_spec(tenant_spec)
tenant_spec.loader.exec_module(tenant_schemas)
Organization = tenant_schemas.Organization


def create_unlocklive_organization():
    """Create UnlockLive organization"""
    print("=" * 60)
    print("Creating UnlockLive Organization")
    print("=" * 60)
    
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        # Check if organization already exists
        existing = db.query(Organization).filter(
            Organization.slug == "unlocklive"
        ).first()
        
        if existing:
            print(f"\n[SKIP] Organization 'UnlockLive' already exists!")
            print(f"       ID: {existing.id}")
            print(f"       Name: {existing.name}")
            print(f"       Slug: {existing.slug}")
            return existing.id
        
        # Create UnlockLive organization
        print("\nCreating UnlockLive organization...")
        org = Organization(
            name="UnlockLive",
            slug="unlocklive",
            subdomain="unlocklive",
            owner_email="admin@unlocklive.com",  # Update with actual email
            owner_name="UnlockLive Admin",
            is_active=True
        )
        
        db.add(org)
        db.commit()
        db.refresh(org)
        
        # Verify it was actually created
        verify_org = db.query(Organization).filter(Organization.id == org.id).first()
        if not verify_org:
            raise Exception("Organization was not created in database!")
        print(f"  [VERIFY] Organization verified in database")
        
        print(f"[OK] Organization created successfully!")
        print(f"     ID: {org.id}")
        print(f"     Name: {org.name}")
        print(f"     Slug: {org.slug}")
        print(f"     Subdomain: {org.subdomain}")
        print("\n" + "=" * 60)
        print("[OK] UnlockLive organization is ready!")
        print("=" * 60)
        
        return org.id
        
    except Exception as e:
        db.rollback()
        print(f"\n[FAIL] Error creating organization: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    try:
        org_id = create_unlocklive_organization()
        print(f"\nOrganization ID: {org_id}")
        print("\nYou can now:")
        print("  1. Run the migration again to backfill users with this organization_id")
        print("  2. Create users for this organization")
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)

