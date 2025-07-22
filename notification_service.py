import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from twilio.rest import Client
import os
from dotenv import load_dotenv
from typing import Dict, Optional

load_dotenv()

class NotificationService:
    def __init__(self):
        """
        Initialize the notification service using email and SMS credentials.
        """
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        
        self.twilio_account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.twilio_auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.twilio_phone_number = os.getenv("TWILIO_PHONE_NUMBER")
        
        self.twilio_client = None
        if self.twilio_account_sid and self.twilio_auth_token:
            self.twilio_client = Client(self.twilio_account_sid, self.twilio_auth_token)
    
    def send_email(self, recipient: str, title: str, content: str) -> bool:
        """
        Sends an email using SMTP credentials.
        """
        try:
            message = MIMEMultipart()
            message["From"] = self.smtp_username
            message["To"] = recipient
            message["Subject"] = title
            message.attach(MIMEText(content, "html"))
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as smtp_conn:
                smtp_conn.starttls()
                smtp_conn.login(self.smtp_username, self.smtp_password)
                smtp_conn.send_message(message)
                
            return True
        except Exception as err:
            print(f"Error sending email: {str(err)}")
            return False

    def send_sms(self, phone: str, text: str) -> bool:
        """
        Sends an SMS using the Twilio API.
        """
        if not self.twilio_client:
            print("Twilio client not initialized.")
            return False
        try:
            self.twilio_client.messages.create(
                body=text,
                from_=self.twilio_phone_number,
                to=phone
            )
            return True
        except Exception as err:
            print(f"Error sending SMS: {str(err)}")
            return False

    def notify_match(
        self,
        email: str,
        phone: Optional[str],
        data: Dict
    ) -> Dict:
        """
        Sends job match notification via email and optionally via SMS.
        """
        outcome = {"email": False, "sms": False}
        
        subject = "You Have a New Job Match!"
        html_msg = f"""
        <h2>Good News!</h2>
        <p>We've found a matching job for you:</p>
        <ul>
            <li>Match Score: {data['match_percentage']}%</li>
            <li>Missing Skills: {', '.join(data['missing_skills']) if data['missing_skills'] else 'None'}</li>
        </ul>
        <p>Check your profile for more details.</p>
        """
        
        sms_msg = f"Job match found! Match: {data['match_percentage']}%. See your profile for more."

        if email:
            outcome["email"] = self.send_email(email, subject, html_msg)
        if phone:
            outcome["sms"] = self.send_sms(phone, sms_msg)
        
        return outcome