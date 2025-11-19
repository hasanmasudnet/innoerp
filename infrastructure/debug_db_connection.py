"""
Debug script to check database connection configuration
"""
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

print("=" * 60)
print("Database Connection Debug")
print("=" * 60)

# Check .env file
env_path = project_root / '.env'
print(f"\n[1] Checking .env file:")
print(f"    Path: {env_path}")
print(f"    Exists: {env_path.exists()}")

if env_path.exists():
    print(f"    Contents:")
    with open(env_path, 'r') as f:
        for line in f:
            if 'DATABASE_URL' in line or 'PASSWORD' in line:
                # Mask password
                masked = line.replace(line.split('@')[0].split(':')[-1], '***') if '@' in line else line
                print(f"      {masked.strip()}")

# Check system environment variable
print(f"\n[2] System Environment Variable:")
db_url_env = os.getenv("DATABASE_URL")
if db_url_env:
    # Mask password
    if '@' in db_url_env:
        parts = db_url_env.split('@')
        user_part = parts[0]
        if ':' in user_part:
            user, pwd = user_part.rsplit(':', 1)
            masked = f"{user}:***@{parts[1]}"
        else:
            masked = db_url_env
    else:
        masked = db_url_env
    print(f"    DATABASE_URL: {masked}")
else:
    print(f"    DATABASE_URL: (not set)")

# Try to load .env
print(f"\n[3] Loading .env file:")
try:
    from dotenv import load_dotenv
    load_dotenv(env_path)
    print(f"    [OK] .env file loaded")
    
    # Check what DATABASE_URL is after loading
    db_url_after = os.getenv("DATABASE_URL")
    if db_url_after:
        if '@' in db_url_after:
            parts = db_url_after.split('@')
            user_part = parts[0]
            if ':' in user_part:
                user, pwd = user_part.rsplit(':', 1)
                masked = f"{user}:***@{parts[1]}"
            else:
                masked = db_url_after
        else:
            masked = db_url_after
        print(f"    DATABASE_URL after load: {masked}")
    else:
        print(f"    DATABASE_URL after load: (not set)")
except ImportError:
    print(f"    [WARN] python-dotenv not installed")
except Exception as e:
    print(f"    [ERROR] {e}")

# Check what the code will use
print(f"\n[4] What shared/database/base.py will use:")
try:
    from shared.database.base import engine
    db_url = str(engine.url)
    # Mask password
    if '@' in db_url:
        parts = db_url.split('@')
        user_part = parts[0]
        if ':' in user_part:
            user, pwd = user_part.rsplit(':', 1)
            masked = f"{user}:***@{parts[1]}"
        else:
            masked = db_url
    else:
        masked = db_url
    print(f"    Database URL: {masked}")
    print(f"    Database name: {engine.url.database}")
    print(f"    Host: {engine.url.host}")
    print(f"    Port: {engine.url.port}")
except Exception as e:
    print(f"    [ERROR] {e}")

print("\n" + "=" * 60)

