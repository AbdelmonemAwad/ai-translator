#!/usr/bin/env python3
"""
AI Translator v2.2.5 - Database Login Fix
إصلاح مشكلة تسجيل الدخول في قاعدة البيانات
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

def fix_admin_password():
    """Fix admin password in database"""
    print("🔧 AI Translator - Database Login Fix")
    print("   إصلاح مشكلة تسجيل الدخول في قاعدة البيانات")
    
    # Get database URL from environment or use default
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        database_url = "postgresql://ai_translator:ai_translator_pass2024@localhost/ai_translator"
    
    print(f"📊 Connecting to database...")
    
    try:
        # Create engine and session
        engine = create_engine(database_url)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Check current admin settings
        print("🔍 Checking current admin settings...")
        result = session.execute(text("SELECT key, value FROM settings WHERE key IN ('admin_username', 'admin_password') ORDER BY key"))
        current_settings = dict(result.fetchall())
        
        print(f"   Current username: {current_settings.get('admin_username', 'NOT SET')}")
        print(f"   Current password: {'SET' if current_settings.get('admin_password') else 'NOT SET'}")
        
        # Fix admin username if needed
        if 'admin_username' not in current_settings or not current_settings['admin_username']:
            print("⚙️  Setting admin username...")
            session.execute(text("INSERT INTO settings (key, value, section, type, description) VALUES ('admin_username', 'admin', 'DEFAULT', 'string', 'Admin username') ON CONFLICT (key) DO UPDATE SET value = 'admin'"))
        
        # Fix admin password - set to plain text (not hash)
        print("🔑 Setting admin password...")
        session.execute(text("INSERT INTO settings (key, value, section, type, description) VALUES ('admin_password', 'your_strong_password', 'DEFAULT', 'password', 'Admin password') ON CONFLICT (key) DO UPDATE SET value = 'your_strong_password'"))
        
        # Commit changes
        session.commit()
        print("✅ Database updated successfully!")
        
        # Verify changes
        print("🔍 Verifying changes...")
        result = session.execute(text("SELECT key, value FROM settings WHERE key IN ('admin_username', 'admin_password') ORDER BY key"))
        updated_settings = dict(result.fetchall())
        
        print(f"   Updated username: {updated_settings.get('admin_username', 'ERROR')}")
        print(f"   Updated password: {'your_strong_password' if updated_settings.get('admin_password') == 'your_strong_password' else 'ERROR'}")
        
        session.close()
        
        print("\n🎉 Login fix completed successfully!")
        print("   إصلاح تسجيل الدخول اكتمل بنجاح!")
        print("\n📋 Login Credentials:")
        print("   Username: admin")
        print("   Password: your_strong_password")
        print("\n🔄 Please restart your AI Translator service:")
        print("   sudo systemctl restart ai-translator")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print("💡 Possible solutions:")
        print("   1. Make sure PostgreSQL is running")
        print("   2. Check database connection settings")
        print("   3. Verify DATABASE_URL environment variable")
        print("   4. Run with correct permissions")
        return False

def main():
    """Main function"""
    if len(sys.argv) > 1 and sys.argv[1] in ['--help', '-h']:
        print("AI Translator Database Login Fix")
        print("Usage: python3 fix_database_login.py")
        print("\nThis script fixes the admin password issue in the database.")
        print("Default credentials: admin / your_strong_password")
        return
    
    success = fix_admin_password()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()