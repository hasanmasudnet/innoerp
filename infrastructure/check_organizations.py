"""
Script to check organizations in database
"""
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
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


def check_organizations():
    """Check all organizations in database"""
    print("=" * 60)
    print("Checking Organizations in Database")
    print("=" * 60)
    
    # Show database connection info
    db_url = str(engine.url).replace(str(engine.url.password), "***" if engine.url.password else "")
    print(f"\nDatabase: {db_url}")
    
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        # Check using SQLAlchemy
        print("\n[1] Using SQLAlchemy query:")
        orgs = db.query(Organization).all()
        print(f"  Found {len(orgs)} organization(s)")
        for org in orgs:
            print(f"    - ID: {org.id}")
            print(f"      Name: {org.name}")
            print(f"      Slug: {org.slug}")
            print(f"      Subdomain: {org.subdomain}")
            print(f"      Is Active: {org.is_active}")
        
        # Check using raw SQL
        print("\n[2] Using raw SQL query:")
        result = db.execute(text("SELECT id, name, slug, subdomain, is_active FROM organizations ORDER BY id"))
        rows = result.fetchall()
        print(f"  Found {len(rows)} organization(s)")
        for row in rows:
            print(f"    - ID: {row[0]}")
            print(f"      Name: {row[1]}")
            print(f"      Slug: {row[2]}")
            print(f"      Subdomain: {row[3]}")
            print(f"      Is Active: {row[4]}")
        
        # Check specific organization
        print("\n[3] Checking for 'unlocklive' slug:")
        unlocklive = db.query(Organization).filter(Organization.slug == "unlocklive").first()
        if unlocklive:
            print(f"  [OK] Found UnlockLive organization!")
            print(f"       ID: {unlocklive.id}")
        else:
            print("  [NOT FOUND] UnlockLive organization does not exist")
        
        print("\n" + "=" * 60)
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    check_organizations()

