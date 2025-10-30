import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from api.utils.settings import settings
import logging

logger = logging.getLogger(__name__)

class EmailUtils:
    def __init__(self):
        self.brevo_api_key = settings.BREVO_API_KEY
        self.mail_from = settings.MAIL_FROM
        self.mail_from_name = settings.MAIL_FROM_NAME

    def send_otp_email_sync(self, email: str, otp_code: str, user_name: str, subject: str = None, html_content: str = None):
        """
        Sync version of send_otp_email using Brevo with custom content support
        """
        email_type = "PASSWORD RESET" if subject and "Password Reset" in subject else "VERIFICATION"
        print("\n" + "="*50)
        print(f"🎯 {email_type} OTP")
        print("="*50)
        print(f"📧 Email: {email}")
        print(f"👤 User: {user_name}")
        print(f"🔑 OTP Code: {otp_code}")
        print(f"⏰ This code expires in 10 minutes")
        print("="*50 + "\n")

        if not self.brevo_api_key or self.brevo_api_key.startswith("your_"):
            logger.info(f"{email_type} OTP logged to console for {email}: {otp_code}")
            return True

        if subject is None:
            subject = "Verify Your Email - Kanec"
        
        if html_content is None:
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: #4F46E5; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
                    .content {{ padding: 30px; background: #f9f9f9; border-radius: 0 0 8px 8px; }}
                    .otp-code {{ 
                        font-size: 32px; 
                        font-weight: bold; 
                        color: #4F46E5; 
                        text-align: center; 
                        margin: 20px 0; 
                        padding: 15px;
                        background: #ffffff;
                        border: 2px dashed #4F46E5;
                        border-radius: 8px;
                        letter-spacing: 5px;
                    }}
                    .footer {{ text-align: center; padding: 20px; font-size: 12px; color: #666; }}
                    .warning {{ background: #fff3cd; padding: 10px; border-radius: 4px; border: 1px solid #ffeaa7; margin: 15px 0; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>Kanec</h1>
                    </div>
                    <div class="content">
                        <h2>Hello {user_name},</h2>
                        <p>Thank you for registering with Kanec. Please use the following OTP code to verify your email address:</p>
                        <div class="otp-code">{otp_code}</div>
                        <div class="warning">
                            <strong>Note:</strong> This code will expire in 10 minutes.
                        </div>
                        <p>If you didn't create an account with Kanec, please ignore this email.</p>
                        <p>Best regards,<br>The Kanec Team</p>
                    </div>
                    <div class="footer">
                        <p>&copy; 2024 Kanec. All rights reserved.</p>
                    </div>
                </div>
            </body>
            </html>
            """

        try:
            configuration = sib_api_v3_sdk.Configuration()
            configuration.api_key['api-key'] = self.brevo_api_key

            api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))

            send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
                sender=sib_api_v3_sdk.SendSmtpEmailSender(
                    name=self.mail_from_name,
                    email=self.mail_from
                ),
                to=[sib_api_v3_sdk.SendSmtpEmailTo(
                    email=email,
                    name=user_name
                )],
                subject=subject,
                html_content=html_content
            )

            api_response = api_instance.send_transac_email(send_smtp_email)
            logger.info(f"Email sent successfully to {email}. Message ID: {api_response.message_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {email}: {str(e)}")
            return True

    async def send_otp_email(self, email: str, otp_code: str, user_name: str):
        """
        Async wrapper for sync email sending with Brevo
        """
        return self.send_otp_email_sync(email, otp_code, user_name)

email_utils = EmailUtils()