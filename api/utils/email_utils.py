import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from api.utils.settings import settings
from html import escape
import logging

logger = logging.getLogger(__name__)

class EmailUtils:
    def __init__(self):
        self.brevo_api_key = settings.BREVO_API_KEY
        self.mail_from = settings.MAIL_FROM
        self.mail_from_name = settings.MAIL_FROM_NAME

    @staticmethod
    def _build_otp_html(user_name: str, otp_code: str, is_password_reset: bool) -> str:
                safe_name = escape(user_name)
                safe_otp = escape(otp_code)
                heading = "Reset your password" if is_password_reset else "Verify your email"
                description = (
                        "Use this one-time code to finish resetting your Kanec password."
                        if is_password_reset
                        else "Use this one-time code to confirm your email address and activate your Kanec account."
                )
                security_note = (
                        "If you did not request a password reset, you can safely ignore this email."
                        if is_password_reset
                        else "If you did not create a Kanec account, you can safely ignore this email."
                )
                accent = "#0f766e" if not is_password_reset else "#b45309"
                accent_soft = "#ccfbf1" if not is_password_reset else "#fef3c7"

                return f"""
<!doctype html>
<html lang="en">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{heading} | Kanec</title>
    </head>
    <body style="margin:0;background:#eef2f1;color:#19312f;font-family:Arial,sans-serif;">
        <div style="display:none;max-height:0;overflow:hidden;opacity:0;">
            Your Kanec one-time code is {safe_otp}. It expires in 10 minutes.
        </div>
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#eef2f1;padding:36px 16px;">
            <tr><td align="center">
                <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:600px;background:#ffffff;border:1px solid #d9e5e2;border-radius:16px;overflow:hidden;">
                    <tr><td style="background:#173f3a;padding:26px 36px;">
                        <div style="color:#9ee7d8;font-size:12px;font-weight:bold;letter-spacing:2px;text-transform:uppercase;">KANEC IMPACT</div>
                        <div style="color:#ffffff;font-size:26px;font-weight:bold;margin-top:10px;">{heading}</div>
                    </td></tr>
                    <tr><td style="padding:38px 36px 32px;">
                        <p style="margin:0 0 18px;font-size:18px;font-weight:bold;">Hello {safe_name},</p>
                        <p style="margin:0;color:#526966;font-size:15px;line-height:1.7;">{description}</p>
                        <div style="margin:28px 0;padding:22px 16px;background:{accent_soft};border:1px solid {accent};border-radius:12px;text-align:center;">
                            <div style="color:{accent};font-size:11px;font-weight:bold;letter-spacing:2px;text-transform:uppercase;">ONE-TIME CODE</div>
                            <div style="color:#173f3a;font-size:36px;font-weight:bold;letter-spacing:8px;margin:12px 0 4px;">{safe_otp}</div>
                            <div style="color:#526966;font-size:12px;">Expires in 10 minutes</div>
                        </div>
                        <p style="margin:0;color:#526966;font-size:14px;line-height:1.7;">{security_note}</p>
                        <div style="height:1px;background:#e6efed;margin:30px 0 22px;"></div>
                        <p style="margin:0;color:#78908c;font-size:12px;line-height:1.6;">For your security, never share this code. Kanec support will never ask for your one-time code.</p>
                    </td></tr>
                    <tr><td style="background:#f7faf9;padding:20px 36px;text-align:center;">
                        <p style="margin:0;color:#78908c;font-size:12px;">Kanec Impact · Building change together</p>
                    </td></tr>
                </table>
            </td></tr>
        </table>
    </body>
</html>
"""

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
            html_content = self._build_otp_html(
                user_name,
                otp_code,
                email_type == "PASSWORD RESET",
            )

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
            raise

    async def send_otp_email(self, email: str, otp_code: str, user_name: str):
        """
        Async wrapper for sync email sending with Brevo
        """
        return self.send_otp_email_sync(email, otp_code, user_name)

email_utils = EmailUtils()