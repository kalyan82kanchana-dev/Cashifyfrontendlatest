from fastapi import FastAPI, APIRouter
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import random
import httpx
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import ssl

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="Cashifygcmart API",
    description="Gift Card Exchange Platform API",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database setup
db_client = None
db = None

# Pydantic models
class GiftCard(BaseModel):
    brand: str
    value: str
    condition: str
    hasReceipt: str
    cardType: str
    digitalCode: Optional[str] = ""
    digitalPin: Optional[str] = ""
    frontImage: Optional[dict] = None
    backImage: Optional[dict] = None
    receiptImage: Optional[dict] = None

class GiftCardSubmission(BaseModel):
    firstName: str
    lastName: str
    email: str
    phoneNumber: str
    cards: List[GiftCard]
    paymentMethod: str
    paypalAddress: Optional[str] = ""
    zelleDetails: Optional[str] = ""
    cashAppTag: Optional[str] = ""
    btcAddress: Optional[str] = ""
    chimeDetails: Optional[str] = ""

# Email Template Functions
def generate_confirmation_email_html(customer_name, reference_number):
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gift Card Submission Confirmation</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            background: linear-gradient(135deg, #ec4899, #3b82f6);
            color: white;
            padding: 30px;
            text-align: center;
            border-radius: 10px 10px 0 0;
        }}
        .content {{
            background: #f8fafc;
            padding: 30px;
            border-radius: 0 0 10px 10px;
        }}
        .reference {{
            background: #e0f2fe;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
            margin: 20px 0;
            font-weight: bold;
            color: #0277bd;
        }}
        .footer {{
            text-align: center;
            margin-top: 30px;
            color: #666;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🎁 CashifyGCmart</h1>
        <p>Gift Card Exchange Platform</p>
    </div>
    
    <div class="content">
        <h2>Thank You for Your Submission!</h2>
        <p>Dear {customer_name},</p>
        
        <p>We have successfully received your gift card submission. Our team will review your submission and get back to you soon.</p>
        
        <div class="reference">
            <strong>Reference Number: {reference_number}</strong>
        </div>
        
        <h3>What happens next?</h3>
        <ul>
            <li>Our team will review your submission</li>
            <li>Payment processed within same day upon acceptance</li>
        </ul>
        
        <p>If you have any questions, please contact us with your reference number.</p>
        
        <p>Best regards,<br>The CashifyGCmart Team</p>
    </div>
    
    <div class="footer">
        <p>This is an automated message. Please do not reply to this email.</p>
    </div>
</body>
</html>
"""

def generate_internal_notification_html(submission_data, customer_name, reference_number):
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>New Gift Card Submission</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .header {{ background: #dc2626; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; }}
        .info-box {{ background: #f3f4f6; padding: 15px; margin: 10px 0; border-radius: 5px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🚨 New Gift Card Submission</h1>
    </div>
    
    <div class="content">
        <h2>Customer Information</h2>
        <div class="info-box">
            <strong>Name:</strong> {customer_name}<br>
            <strong>Email:</strong> {submission_data.get('email', 'N/A')}<br>
            <strong>Phone:</strong> {submission_data.get('phoneNumber', 'N/A')}<br>
            <strong>Reference:</strong> {reference_number}
        </div>
        
        <h2>Gift Cards ({len(submission_data.get('cards', []))} cards)</h2>
        {''.join([f'<div class="info-box"><strong>{card.get("brand", "Unknown")}</strong> - ${card.get("value", "0")} ({card.get("condition", "Unknown")})</div>' for card in submission_data.get('cards', [])])}
        
        <h2>Payment Method</h2>
        <div class="info-box">
            <strong>Method:</strong> {submission_data.get('paymentMethod', 'N/A')}<br>
            {f'<strong>Details:</strong> {submission_data.get("paypalAddress", submission_data.get("zelleDetails", submission_data.get("cashAppTag", submission_data.get("btcAddress", "N/A"))))}' if submission_data.get('paymentMethod') else ''}
        </div>
    </div>
</body>
</html>
"""

# Utility Functions
def generate_reference_number():
    timestamp = datetime.now().strftime("%H%M%S")
    random_num = random.randint(10, 99)
    return f"GC-{timestamp}-{random_num}"

# Email Functions (Simplified - will not fail if email is not configured)
async def send_confirmation_email(email: str, customer_name: str, reference_number: str):
    try:
        # Check if email is configured
        smtp_server = os.environ.get('SMTP_SERVER')
        smtp_username = os.environ.get('SMTP_USERNAME')
        smtp_password = os.environ.get('SMTP_PASSWORD')
        
        if not all([smtp_server, smtp_username, smtp_password]):
            print("⚠️ Email not configured - skipping customer email")
            return False
        
        # Generate email content
        email_html = generate_confirmation_email_html(customer_name, reference_number)
        subject = f"Gift Card Submission Confirmation - Reference #{reference_number}"
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['From'] = smtp_username
        msg['To'] = email
        msg['Subject'] = subject
        
        # Add HTML content
        html_part = MIMEText(email_html, 'html')
        msg.attach(html_part)
        
        # Send email
        smtp_port = int(os.environ.get('SMTP_PORT', 587))
        use_ssl = os.environ.get('SMTP_USE_SSL', 'false').lower() == 'true'
        
        if use_ssl:
            server = smtplib.SMTP_SSL(smtp_server, smtp_port)
        else:
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
        
        server.login(smtp_username, smtp_password)
        server.send_message(msg)
        server.quit()
        
        print(f"✅ Customer confirmation email sent to {email}")
        return True
        
    except Exception as e:
        print(f"❌ Customer email failed: {e}")
        return False

async def send_internal_notification_email(submission_data: dict, customer_name: str, reference_number: str):
    try:
        # Check if email is configured
        smtp_server = os.environ.get('SMTP_SERVER')
        smtp_username = os.environ.get('SMTP_USERNAME')
        smtp_password = os.environ.get('SMTP_PASSWORD')
        to_email = os.environ.get('TO_EMAIL', smtp_username)
        
        if not all([smtp_server, smtp_username, smtp_password]):
            print("⚠️ Email not configured - skipping internal notification")
            return False
        
        # Generate email content
        email_html = generate_internal_notification_html(submission_data, customer_name, reference_number)
        subject = f"New Gift Card Submission - {reference_number}"
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['From'] = smtp_username
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # Add HTML content
        html_part = MIMEText(email_html, 'html')
        msg.attach(html_part)
        
        # Send email
        smtp_port = int(os.environ.get('SMTP_PORT', 587))
        use_ssl = os.environ.get('SMTP_USE_SSL', 'false').lower() == 'true'
        
        if use_ssl:
            server = smtplib.SMTP_SSL(smtp_server, smtp_port)
        else:
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
        
        server.login(smtp_username, smtp_password)
        server.send_message(msg)
        server.quit()
        
        print(f"✅ Internal notification email sent to {to_email}")
        return True
        
    except Exception as e:
        print(f"❌ Internal email failed: {e}")
        return False

# API Router
api_router = APIRouter(prefix="/api")

@api_router.get("/")
async def root():
    return {"message": "API is working", "status": "success"}

@api_router.post("/submit-gift-card")
async def submit_gift_card(submission: GiftCardSubmission):
    try:
        # Generate reference number
        reference_number = generate_reference_number()
        
        # Add timestamp to submission data
        submission_dict = submission.dict()
        submission_dict['reference_number'] = reference_number
        submission_dict['submitted_at'] = datetime.now().isoformat()
        
        print(f"📝 Processing submission: {reference_number}")
        
        # Store in database (if available) - this will not fail the request
        customer_email_sent = False
        internal_email_sent = False
        
        try:
            if db:
                await db.gift_card_submissions.insert_one(submission_dict)
                print(f"✅ Submission stored in database: {reference_number}")
        except Exception as e:
            print(f"⚠️ Database storage failed (continuing anyway): {e}")
        
        # Send confirmation email to customer - this will not fail the request
        try:
            customer_name = f"{submission.firstName} {submission.lastName}"
            customer_email_sent = await send_confirmation_email(
                submission.email, 
                customer_name, 
                reference_number
            )
        except Exception as e:
            print(f"❌ Customer email failed: {e}")
        
        # Send internal notification email - this will not fail the request
        try:
            customer_name = f"{submission.firstName} {submission.lastName}"
            internal_email_sent = await send_internal_notification_email(
                submission_dict, 
                customer_name, 
                reference_number
            )
        except Exception as e:
            print(f"❌ Internal email failed: {e}")
        
        # Always return success if we got this far
        print(f"✅ Submission processed successfully: {reference_number}")
        return {
            "success": True,
            "reference_number": reference_number,
            "message": "Gift card submission received successfully",
            "customer_email_sent": customer_email_sent,
            "internal_email_sent": internal_email_sent
        }
        
    except Exception as e:
        print(f"❌ Submission processing failed: {e}")
        return {
            "success": False,
            "message": f"Submission failed: {str(e)}"
        }

# Include API router
app.include_router(api_router)

# Database connection events
@app.on_event("startup")
async def startup_db_client():
    global db_client, db
    try:
        mongodb_url = os.environ.get('MONGODB_URL')
        if mongodb_url:
            db_client = AsyncIOMotorClient(mongodb_url)
            db = db_client.cashifygcmart
            print("✅ Database connected")
        else:
            print("⚠️ No database URL provided - running without database")
    except Exception as e:
        print(f"⚠️ Database connection failed: {e}")

@app.on_event("shutdown")
async def shutdown_db_client():
    global db_client
    if db_client:
        db_client.close()
        print("✅ Database connection closed")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
