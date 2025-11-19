"""
Script to check and kill database locks (if needed)
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from shared.database.base import engine

def check_locks():
    """Check for active locks on users table"""
    print("=" * 60)
    print("Checking Database Locks")
    print("=" * 60)
    
    with engine.connect() as conn:
        try:
            # Check for locks on users table
            result = conn.execute(text("""
                SELECT 
                    pid,
                    usename,
                    application_name,
                    state,
                    query,
                    query_start,
                    now() - query_start as duration
                FROM pg_stat_activity
                WHERE state = 'active'
                AND query NOT LIKE '%pg_stat_activity%'
                ORDER BY query_start
            """))
            
            locks = result.fetchall()
            print(f"\nFound {len(locks)} active queries:")
            for lock in locks:
                print(f"\n  PID: {lock[0]}")
                print(f"  User: {lock[1]}")
                print(f"  Application: {lock[2]}")
                print(f"  State: {lock[3]}")
                print(f"  Duration: {lock[6]}")
                print(f"  Query: {lock[4][:100]}...")
            
            # Check for locks specifically on users table
            result = conn.execute(text("""
                SELECT 
                    l.pid,
                    l.mode,
                    l.locktype,
                    l.relation::regclass,
                    a.query,
                    a.query_start
                FROM pg_locks l
                JOIN pg_stat_activity a ON l.pid = a.pid
                WHERE l.relation = 'users'::regclass::oid
                OR l.relation = (SELECT oid FROM pg_class WHERE relname = 'users')
            """))
            
            table_locks = result.fetchall()
            if table_locks:
                print(f"\n[WARN] Found {len(table_locks)} lock(s) on users table:")
                for lock in table_locks:
                    print(f"  PID: {lock[0]}, Mode: {lock[1]}, Type: {lock[2]}")
                    print(f"  Query: {lock[4][:100] if lock[4] else 'N/A'}...")
                    print(f"\n  To kill this process, run:")
                    print(f"    SELECT pg_terminate_backend({lock[0]});")
            else:
                print("\n[OK] No locks found on users table")
                
        except Exception as e:
            print(f"\n[ERROR] {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    check_locks()

