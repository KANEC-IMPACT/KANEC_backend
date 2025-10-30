# test_brevo.py
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from api.utils.settings import settings

def test_brevo():
    print("=== Testing Brevo ===")
    print(f"BREVO_API_KEY: {'*' * len(settings.BREVO_API_KEY) if settings.BREVO_API_KEY else 'NOT SET'}")
    print(f"MAIL_FROM: {settings.MAIL_FROM}")
    
    if not settings.BREVO_API_KEY:
        print("❌ BREVO_API_KEY not set")
        return False
        
    try:
        configuration = sib_api_v3_sdk.Configuration()
        configuration.api_key['api-key'] = settings.BREVO_API_KEY

        api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))

        send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
            sender=sib_api_v3_sdk.SendSmtpEmailSender(
                name="Kanec",
                email=settings.MAIL_FROM
            ),
            to=[sib_api_v3_sdk.SendSmtpEmailTo(
                email="akinrogundej@gmail.com",
                name="Test User"
            )],
            subject="Brevo Test from Kanec",
            html_content="<strong>This is a test email from Brevo!</strong>"
        )

        api_response = api_instance.send_transac_email(send_smtp_email)
        print(f"✅ Brevo test successful! Message ID: {api_response.message_id}")
        return True
        
    except ApiException as e:
        print(f"❌ Brevo API exception: {e}")
        return False
    except Exception as e:
        print(f"❌ Brevo test failed: {str(e)}")
        return False

if __name__ == "__main__":
    test_brevo()