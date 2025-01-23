import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from ..config import settings
import logging
from groq import Groq

logger = logging.getLogger(__name__)
groq_client = Groq()

def generate_outreach_email(user_data: dict, lead_data: dict, research: dict) -> str:
    """Generate personalized outreach email using Groq"""
    try:
        prompt = f"""Generate a professional and personalized sales outreach email using this information:

        From:
        - Name: {user_data['name']}
        - Company: {user_data['company_name']}
        - Product/Service: {user_data['product_description']}

        To:
        - Company: {lead_data['company_name']}
        - Website: {lead_data['company_website']}

        Research Insights:
        {research.get('insights', {})}

        Write a concise, professional email that:
        1. Introduces yourself and your company
        2. Shows understanding of their business
        3. Briefly explains how your product could help them
        4. Requests a meeting/call
        5. Has a professional signature

        Keep it under 200 words and make it sound natural and personalized."""

        completion = groq_client.chat.completions.create(
            model="llama-3.1-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_completion_tokens=1024,
            top_p=1,
            stream=False,
            stop=None
        )
        
        return completion.choices[0].message.content
    except Exception as e:
        logger.error(f"Failed to generate outreach email: {str(e)}")
        return "Error generating outreach email template."

def send_email_notification(to_email: str, user_data: dict, lead_data: dict, research: dict) -> bool:
    """Send email notification about new lead"""
    try:
        # Generate outreach email
        outreach_email = generate_outreach_email(user_data, lead_data, research)
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"New Lead Found: {lead_data['company_name']}"
        msg['From'] = f"Reka Sales Bot <{settings.gmail_email}>"
        msg['To'] = to_email
        
        body = f"""Hi {user_data['name']},

I found an interesting company that might be worth reaching out to:

Company: {lead_data['company_name']}
Website: {lead_data['company_website']}
Contact: {lead_data['lead_email']}

Here's what I learned about them:

What They Do:
{research.get('company_description', 'Information not available')}

How Your Product Could Help:
{research.get('value_proposition', 'Information not available')}

Interesting Points for Outreach:
{research.get('outreach_points', 'Information not available')}

Suggested Outreach Email:
-------------------
{outreach_email}
-------------------

I hope this helps with your outreach! Let me know if you need anything else.

Best regards,
Your Sales Assistant"""
        
        # Create both plain text and HTML versions
        text_part = MIMEText(body, 'plain')
        html_part = MIMEText(body.replace('\n', '<br>'), 'html')
        
        msg.attach(text_part)
        msg.attach(html_part)
        
        # Send email via SMTP
        with smtplib.SMTP(settings.smtp_server, settings.smtp_port) as server:
            server.starttls()
            server.login(settings.gmail_email, settings.gmail_password)
            server.send_message(msg)
            
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email notification: {str(e)}")
        return False

def format_list(items: list) -> str:
    """Format a list of items for email"""
    if not items:
        return "Information not available"
    return "\n".join([f"- {item}" for item in items]) 