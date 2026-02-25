#!/usr/bin/env python3
"""
Database Migration Script - Remove Plaintext Password Storage
==============================================================

SECURITY FIX: This script removes the plain_password column from the users table.

What this script does:
1. Backs up the current database
2. Removes the plain_password column (which stored passwords in plaintext)
3. Verifies the migration was successful

Usage:
    python migrate_remove_plaintext_passwords.py

IMPORTANT:
- This migration is IRREVERSIBLE for password data (by design - plaintext passwords should never be stored)
- A backup will be created before migration
- Users can still log in normally (hashed_password column is preserved)
- Admins will need to use password reset functionality instead of viewing plaintext passwords
"""

import sqlite3
import shutil
import os
from datetime import datetime
from pathlib import Path


def backup_database(db_path: str) -> str:
    """Create a backup of the database before migration."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{db_path}.backup_{timestamp}"

    print(f"Creating backup: {backup_path}")
    shutil.copy2(db_path, backup_path)
    print(f"✓ Backup created successfully")

    return backup_path


def check_column_exists(cursor: sqlite3.Cursor, table: str, column: str) -> bool:
    """Check if a column exists in a table."""
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [row[1] for row in cursor.fetchall()]
    return column in columns


def migrate_database(db_path: str):
    """Remove plain_password column from users table."""
    print("\n" + "=" * 60)
    print("Database Migration: Remove Plaintext Password Storage")
    print("=" * 60)

    if not os.path.exists(db_path):
        print(f"✗ Database not found: {db_path}")
        print("  This is normal if you haven't created any users yet.")
        print("  The new schema (without plain_password) will be used automatically.")
        return

    # Create backup
    backup_path = backup_database(db_path)

    # Connect to database
    print(f"\nConnecting to database: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check if plain_password column exists
        if not check_column_exists(cursor, "users", "plain_password"):
            print("✓ Migration already completed - plain_password column does not exist")
            conn.close()
            return

        print("\n⚠ WARNING: About to remove plain_password column")
        print("  This will permanently delete all plaintext passwords from the database.")
        print("  Users will still be able to log in (hashed passwords are preserved).")

        response = input("\nProceed with migration? (yes/no): ").strip().lower()
        if response != "yes":
            print("✗ Migration cancelled")
            conn.close()
            return

        # SQLite doesn't support DROP COLUMN directly in older versions
        # We need to recreate the table without the plain_password column
        print("\nStarting migration...")

        # Get current table schema
        cursor.execute("PRAGMA table_info(users)")
        columns_info = cursor.fetchall()

        # Filter out plain_password column
        new_columns = [
            col for col in columns_info
            if col[1] != "plain_password"
        ]

        # Build column definitions for new table
        column_defs = []
        for col in new_columns:
            col_def = f"{col[1]} {col[2]}"
            if col[3]:  # NOT NULL
                col_def += " NOT NULL"
            if col[4] is not None:  # DEFAULT value
                col_def += f" DEFAULT {col[4]}"
            if col[5]:  # PRIMARY KEY
                col_def += " PRIMARY KEY"
            column_defs.append(col_def)

        # Build column names list for data copy
        column_names = [col[1] for col in new_columns]
        columns_str = ", ".join(column_names)

        # Step 1: Create new table
        print("  Creating new users table without plain_password column...")
        create_table_sql = f"""
        CREATE TABLE users_new (
            {", ".join(column_defs)}
        )
        """
        cursor.execute(create_table_sql)

        # Step 2: Copy data (excluding plain_password)
        print("  Copying user data...")
        cursor.execute(f"""
            INSERT INTO users_new ({columns_str})
            SELECT {columns_str}
            FROM users
        """)

        # Step 3: Get indexes
        print("  Recreating indexes...")
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='index' AND tbl_name='users'")
        indexes = cursor.fetchall()

        # Step 4: Drop old table
        print("  Dropping old users table...")
        cursor.execute("DROP TABLE users")

        # Step 5: Rename new table
        print("  Renaming new table...")
        cursor.execute("ALTER TABLE users_new RENAME TO users")

        # Step 6: Recreate indexes
        for index_sql in indexes:
            if index_sql[0]:  # Skip auto-created indexes
                cursor.execute(index_sql[0])

        # Commit changes
        conn.commit()
        print("\n✓ Migration completed successfully!")

        # Verify
        print("\nVerifying migration...")
        if not check_column_exists(cursor, "users", "plain_password"):
            print("✓ Verification passed - plain_password column removed")
        else:
            print("✗ Verification failed - plain_password column still exists")

        # Show stats
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        print(f"✓ {user_count} user(s) migrated successfully")

        print(f"\n✓ Database backup available at: {backup_path}")
        print("  You can delete the backup file once you verify everything works.")

    except Exception as e:
        print(f"\n✗ Migration failed: {e}")
        print(f"  Your original database is safe at: {backup_path}")
        print("  To restore: cp {backup_path} {db_path}")
        conn.rollback()
        raise

    finally:
        conn.close()

    print("\n" + "=" * 60)
    print("Migration Summary")
    print("=" * 60)
    print("✓ Plaintext passwords removed from database")
    print("✓ User login functionality preserved (hashed passwords intact)")
    print("✓ Database backup created")
    print("\nNext steps:")
    print("1. Test user login functionality")
    print("2. Verify admin can still create/update users")
    print("3. Delete backup file after verification")
    print("=" * 60)


def main():
    """Main migration entry point."""
    # Determine database path
    db_path = os.environ.get("DATABASE_PATH", "portal.db")

    # If running in Docker, use /data/portal.db
    if os.path.exists("/data"):
        db_path = "/data/portal.db"

    # If data directory exists in current path, use it
    if os.path.exists("./data"):
        db_path = "./data/portal.db"

    migrate_database(db_path)


if __name__ == "__main__":
    main()
