#!/usr/bin/env python3
"""
One-time script to encrypt a private key and update the database.
Run this separately from your main application.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from cryptography.fernet import Fernet
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from api.utils.settings import settings

ENCRYPTION_KEY = "wRuWsd44r6Uj5SW_jk9_DjzUqNt7FMx-xo_2pyZpkmw="

def encrypt_private_key(private_key_plaintext: str) -> str:
    """Encrypt a private key using Fernet"""
    f = Fernet(ENCRYPTION_KEY.encode())
    encrypted_key = f.encrypt(private_key_plaintext.encode())
    return encrypted_key.decode()

def update_user_private_key(user_email: str, private_key_plaintext: str):
    """Update a user's encrypted private key in the database"""
    
    engine = create_engine(settings.SQLALCHEMY_DATABASE_URI)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        from api.v1.models.user import User
        
        user = db.query(User).filter(User.email == user_email).first()
        if not user:
            print(f"❌ User {user_email} not found")
            return False
        
        if user.encrypted_private_key:
            print(f"⚠️ User {user_email} already has an encrypted private key")
            return False
        
        encrypted_key = encrypt_private_key(private_key_plaintext)
        
        user.encrypted_private_key = encrypted_key
        db.commit()
        
        print(f"✅ Successfully encrypted private key for {user_email}")
        print(f"📧 User: {user_email}")
        print(f"👛 Wallet: {user.wallet_address}")
        print(f"🔐 Private key encrypted and stored")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    # Replace these with your actual values
    USER_EMAIL = "example@gmail.com"  # The user's email
    PRIVATE_KEY = "...."  # The plaintext private key
    
    print("🔐 Starting private key encryption...")
    print(f"📧 User: {USER_EMAIL}")
    
    success = update_user_private_key(USER_EMAIL, PRIVATE_KEY)
    
    if success:
        print("🎉 Encryption completed successfully!")
    else:
        print("💥 Encryption failed!")