"""
Initialize database with tables
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import create_engine, text
import sys
import os

# Add services to path
services_path = os.path.join(os.path.dirname(__file__), '..', 'services')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from shared.database.base import Base, engine

# Import models to register them
# Import models - need to handle the directory structure
# Since services use hyphens, we need to import differently
import importlib.util

# Load tenant service schemas
tenant_spec = importlib.util.spec_from_file_location(
    "tenant_schemas",
    os.path.join(os.path.dirname(__file__), '..', 'services', 'tenant-service', 'app', 'schemas.py')
)
tenant_schemas = importlib.util.module_from_spec(tenant_spec)
tenant_spec.loader.exec_module(tenant_schemas)
Organization = tenant_schemas.Organization
SubscriptionPlan = tenant_schemas.SubscriptionPlan
OrganizationSubscription = tenant_schemas.OrganizationSubscription
OrganizationModule = tenant_schemas.OrganizationModule

# Load auth service schemas
auth_spec = importlib.util.spec_from_file_location(
    "auth_schemas",
    os.path.join(os.path.dirname(__file__), '..', 'services', 'auth-service', 'app', 'schemas.py')
)
auth_schemas = importlib.util.module_from_spec(auth_spec)
auth_spec.loader.exec_module(auth_schemas)
User = auth_schemas.User
UserOrganization = auth_schemas.UserOrganization
RefreshToken = auth_schemas.RefreshToken

def init_database():
    """Create all database tables"""
    print("Initializing database...")
    
    # Import all models to register them with Base
    # This ensures all tables are created
    
    try:
        # Drop all existing tables first (for clean setup)
        # WARNING: This will delete all data!
        print("Dropping existing tables (if any)...")
        Base.metadata.drop_all(bind=engine)
        print("[OK] Existing tables dropped")
        
        # Create all tables
        print("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        print("[OK] Database tables created successfully!")
        
        # Create default subscription plans
        from sqlalchemy.orm import sessionmaker
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()
        
        try:
            # Check if plans already exist
            existing_plans = db.query(SubscriptionPlan).count()
            if existing_plans == 0:
                print("Creating default subscription plans...")
                
                basic_plan = SubscriptionPlan(
                    name="Basic",
                    stripe_price_id="price_basic",
                    price_monthly=29.99,
                    max_users=10,
                    max_projects=20,
                    features=["projects", "tasks", "employees"],
                    limits={"storage_gb": 5}
                )
                
                pro_plan = SubscriptionPlan(
                    name="Pro",
                    stripe_price_id="price_pro",
                    price_monthly=99.99,
                    max_users=50,
                    max_projects=100,
                    features=["projects", "tasks", "employees", "attendance", "leave"],
                    limits={"storage_gb": 50}
                )
                
                enterprise_plan = SubscriptionPlan(
                    name="Enterprise",
                    stripe_price_id="price_enterprise",
                    price_monthly=299.99,
                    max_users=None,  # Unlimited
                    max_projects=None,  # Unlimited
                    features=["projects", "tasks", "employees", "attendance", "leave", "finance", "crm"],
                    limits={"storage_gb": 500}
                )
                
                db.add(basic_plan)
                db.add(pro_plan)
                db.add(enterprise_plan)
                db.commit()
                print("[OK] Default subscription plans created!")
            else:
                print("[OK] Subscription plans already exist")
                
        except Exception as e:
            print(f"Error creating plans: {e}")
            db.rollback()
        finally:
            db.close()
            
    except Exception as e:
        print(f"Error creating tables: {e}")
        raise

if __name__ == "__main__":
    init_database()

