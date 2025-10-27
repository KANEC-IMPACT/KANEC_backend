#!/usr/bin/env python3
"""
Debug script to check the encrypted private key
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from cryptography.fernet import Fernet
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from api.utils.settings import settings

ENCRYPTION_KEY = "wRuWsd44r6Uj5SW_jk9_DjzUqNt7FMx-xo_2pyZpkmw="

def decrypt_private_key(encrypted_key: str, encryption_key: str) -> str:
    """Decrypt a private key."""
    f = Fernet(encryption_key.encode())
    decrypted_key = f.decrypt(encrypted_key.encode())
    return decrypted_key.decode()

def debug_user_private_key(user_email: str):
    """Debug a user's encrypted private key"""
    
    engine = create_engine(settings.SQLALCHEMY_DATABASE_URI)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        from api.v1.models.user import User
        
        user = db.query(User).filter(User.email == user_email).first()
        if not user:
            print(f"❌ User {user_email} not found")
            return
        
        print(f"📧 User: {user_email}")
        print(f"👛 Wallet: {user.wallet_address}")
        print(f"🔐 Has encrypted key: {bool(user.encrypted_private_key)}")
        
        if user.encrypted_private_key:
            print(f"📏 Encrypted key length: {len(user.encrypted_private_key)}")
            print(f"🔍 Encrypted key (first 100 chars): {user.encrypted_private_key[:100]}...")
            
            # Try to decrypt
            try:
                decrypted = decrypt_private_key(user.encrypted_private_key, ENCRYPTION_KEY)
                print(f"✅ Decrypted successfully")
                print(f"📏 Decrypted key length: {len(decrypted)}")
                print(f"🔍 Decrypted key (first 100 chars): {decrypted[:100]}...")
                
                # Try to load as private key
                from hiero_sdk_python import PrivateKey
                try:
                    pk = PrivateKey.from_string_ecdsa(decrypted)
                    print(f"🎯 Successfully loaded as ECDSA private key!")
                    print(f"Public key: {pk.public_key()}")
                except Exception as e:
                    print(f"❌ Failed to load as ECDSA: {e}")
                    
            except Exception as e:
                print(f"❌ Failed to decrypt: {e}")
        
    except Exception as e:
        print(f"💥 Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    user_email = "example@gmail.com"  # Replace with your admin email
    debug_user_private_key(user_email)