# test_otp_flow.py
import asyncio
from api.v1.services.otp import otp_service
from api.utils.redis_utils import redis_client

async def test_otp_flow():
    test_email = "test@example.com"
    
    print("=== Testing OTP Flow ===")
    
    # Generate OTP
    otp = otp_service.generate_otp()
    print(f"1. Generated OTP: {otp}")
    
    # Store in Redis
    print(f"2. Storing OTP for {test_email}...")
    stored = await redis_client.set_otp(test_email, otp, 600)
    print(f"   Storage successful: {stored}")
    
    # Retrieve from Redis
    print(f"3. Retrieving OTP for {test_email}...")
    retrieved = await redis_client.get_otp(test_email)
    print(f"   Retrieved OTP: {retrieved}")
    print(f"   Match: {retrieved == otp}")
    
    # Test validation
    print(f"4. Testing validation...")
    is_valid = await redis_client.is_otp_valid(test_email, otp)
    print(f"   OTP valid: {is_valid}")
    
    # Clean up
    await redis_client.delete_otp(test_email)

if __name__ == "__main__":
    asyncio.run(test_otp_flow())