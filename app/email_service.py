import smtplib

from pydantic import EmailStr
from .config import settings


class Auth_email_service():
    sender_address = settings.auth_email_service_sender_address
    app_password = settings.auth_email_service_password

    _instance = None

    def __new__(cls):
        if cls._instance:
            raise ValueError(
                "The auth_email_service singleton was already instantiated")
        cls._instance = super().__new__(cls)
        return cls._instance
    
    async def password_forgotten(self, recipient: EmailStr, reset_link):
        message = message_generator.password_forgotten(link=reset_link)

        return self.__send_email(recipient=recipient, subject="Reset your password", message=message)

    def __send_email(self, recipient: EmailStr, subject: str, message: str):
        with smtplib.SMTP_SSL(settings.auth_email_service_smtp_server, port=465) as connection:
            connection.starttls()
            connection.login(user=self.sender_address, password=self.app_password)
            result = connection.sendmail(from_addr=self.sender_address,
                                to_addrs=recipient, 
                                msg=f"Subject:{subject}\n\n{message}")
            return result

class Message_generator():
    def password_forgotten(self, link: str):
        # TODO replace by an HTML Template
        return f"""
            Dear User,
            
            Thank you for requesting to reset your password.

            Please click on the following link to get to the reset form:

            {link}

            This link will expire in 5 minutes.

            If you didn't request a password reset, please ignore this email and nothing will happen.

            Should you ever notice any suspicous action kindly reach out to us via kanbanauthservice@gmail.com

            Kind regards,
            Your Kanban-Team
"""

message_generator = Message_generator()
auth_email_service = Auth_email_service()
