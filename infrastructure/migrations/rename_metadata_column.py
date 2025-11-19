"""
Quick migration to rename 'metadata' column to 'invitation_metadata' in invitations table
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from shared.database.base import engine

def rename_metadata_column():
    """Rename metadata column to invitation_metadata"""
    print("=" * 60)
    print("Renaming 'metadata' to 'invitation_metadata' in invitations table")
    print("=" * 60)
    
    with engine.connect() as conn:
        try:
            # Check if column exists
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'invitations' 
                AND column_name = 'metadata'
            """))
            
            if result.fetchone():
                print("\n[1/2] Found 'metadata' column, renaming to 'invitation_metadata'...")
                conn.execute(text("ALTER TABLE invitations RENAME COLUMN metadata TO invitation_metadata"))
                conn.commit()
                print("[OK] Column renamed successfully!")
            else:
                # Check if invitation_metadata already exists
                result = conn.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'invitations' 
                    AND column_name = 'invitation_metadata'
                """))
                
                if result.fetchone():
                    print("\n[SKIP] Column 'invitation_metadata' already exists!")
                else:
                    print("\n[SKIP] Column 'metadata' does not exist (table may not exist yet)")
            
            print("\n" + "=" * 60)
            print("[OK] Migration completed!")
            print("=" * 60)
            
        except Exception as e:
            print(f"\n[FAIL] Error: {e}")
            import traceback
            traceback.print_exc()
            raise

if __name__ == "__main__":
    try:
        rename_metadata_column()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

