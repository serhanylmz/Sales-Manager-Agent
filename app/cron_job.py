import requests
import json
from groq import Groq
from .database import get_db
from .models import User, ICP, Lead, LeadResearch, Product
from .config import Settings
from .utils.leads import search_leads
from datetime import datetime
import logging
from typing import List, Dict
import time
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from urllib.parse import urlparse
import uuid

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = Settings()
groq_client = Groq(api_key=settings.groq_api_key)

def send_email_notification(user_email: str, lead_data: dict, user_data: dict) -> bool:
    try:
        # Determine greeting based on lead name availability
        greeting = f"Dear {lead_data['lead_name']}" if lead_data['lead_name'] and lead_data['lead_name'] != 'None found' else f"Dear team at {lead_data['company_name']}"
        
        # Generate personalized email content
        prompt = f"""Write a professional sales email.

Context:
- Your Name: {user_data['name']}
- Your Company: {user_data['company_name']}
- Your Product: {user_data['product_name']} - {user_data['product_description']}
- Target Industries: {', '.join(user_data['target_industries'])}

Lead Information:
- Company: {lead_data['company_name']}
- Website: {lead_data['company_website']}
- Contact Name: {lead_data['lead_name'] if lead_data['lead_name'] != 'None found' else 'None'}
- Company Description: {lead_data['company_description']}

Requirements:
1. Start with: "{greeting}"
2. Write a compelling subject line about AI-powered sales solutions
3. Mention specific details about their company that make them a good fit
4. Explain how our AI solution can help them specifically
5. Suggest next steps using general timeframes (e.g., "next week")
6. End with your name: "{user_data['name']}\n{user_data['company_name']}"
7. Keep it concise and actionable
8. Don't use placeholders - use real company/contact names
9. Don't mention specific dates or times

Use a professional but conversational tone."""

        completion = groq_client.chat.completions.create(
            model="llama-3.1-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a professional sales email writer. Write personalized, compelling emails that use available information effectively."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_completion_tokens=1024,
            top_p=1,
            stream=False,
            stop=None
        )
        
        email_body = completion.choices[0].message.content
        
        # Extract subject line (first line) and body (rest)
        email_lines = email_body.split('\n')
        subject_line = email_lines[0].replace('Subject:', '').strip()
        email_content = '\n'.join(email_lines[1:]).strip()
        
        # Create the full email with lead details header
        full_email = f"""Lead Details:
Company Name: {lead_data['company_name']}
Company Website: {lead_data['company_website']}
Lead Name: {lead_data['lead_name'] if lead_data['lead_name'] != 'None found' else 'TBD'}
Lead Email: {lead_data['lead_email']}

Email Subject: {subject_line}

Email Body:
{email_content}
"""
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"New Lead Discovery: {lead_data['company_name']}"
        msg['From'] = f"Reka Sales Bot <{settings.gmail_email}>"
        msg['To'] = user_email
        
        # Create both plain text and HTML versions
        text_part = MIMEText(full_email, 'plain')
        html_part = MIMEText(full_email.replace('\n', '<br>'), 'html')
        
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
        return "None found"
    return "\n".join([f"- {item}" for item in items])

def fetch_and_clean_website_content(url: str) -> str:
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
            
        # Get text and clean it
        text = soup.get_text(separator=' ', strip=True)
        
        # Limit to first 2000 chars for token efficiency
        return text[:2000]
    except Exception as e:
        logger.error(f"Error fetching website content: {str(e)}")
        return ""

def research_company(website: str, user_product: dict, user_icp: dict) -> dict:
    try:
        website_content = fetch_and_clean_website_content(website)
        if not website_content:
            return {"error": "Could not fetch website content"}
        
        prompt = f"""You are a helpful sales assistant. Analyze this company's website content and provide insights about how our product might help them.

About our product:
{user_product['name']} - {user_product['description']}

Website content to analyze:
{website_content}

Please provide a friendly analysis that could help write a personalized email. Include:
1. What they do (2-3 sentences)
2. How our product might help them (2-3 specific examples)
3. Any interesting points we could mention in our outreach

Keep it conversational and friendly. No scoring or strict evaluation needed."""

        completion = groq_client.chat.completions.create(
            model="llama-3.1-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=1,
            max_completion_tokens=1024,
            top_p=1,
            stream=False,
            stop=None
        )
        
        response_text = completion.choices[0].message.content
        
        # Process into sections for email
        analysis = {
            "company_description": [],
            "potential_benefits": [],
            "interesting_points": [],
            "relevance_score": 70  # Default to moderately relevant
        }
        
        current_section = None
        for line in response_text.split('\n'):
            line = line.strip()
            if not line:
                continue
                
            if "they do" in line.lower():
                current_section = "company_description"
            elif "our product" in line.lower() or "help them" in line.lower():
                current_section = "potential_benefits"
            elif "interesting" in line.lower():
                current_section = "interesting_points"
            elif current_section and line.startswith(('-', '•', '*', '1.', '2.', '3.')):
                analysis[current_section].append(line.lstrip('-•*123. '))
        
        return analysis
        
    except Exception as e:
        logger.error(f"Error in research_company: {str(e)}")
        return {"error": str(e)}

def run_prospecting_job():
    db = next(get_db())
    
    try:
        # Get all users with ICP data
        users = db.query(User).join(ICP).join(Product).all()
        logger.info(f"Found {len(users)} users to process")
        
        for user in users:
            try:
                icp = db.query(ICP).filter(ICP.user_id == user.user_id).first()
                product = db.query(Product).filter(Product.user_id == user.user_id).first()
                
                if not icp or not product:
                    logger.warning(f"Missing ICP or product data for user {user.email}")
                    continue
                
                # Prepare user data for email
                user_data = {
                    "name": user.name,
                    "company_name": user.company_name,
                    "product_name": product.name,
                    "product_description": product.description,
                    "target_industries": icp.target_industries
                }
                
                # Convert ICP and Product to dict for search
                icp_data = {
                    "target_industries": icp.target_industries,
                    "target_pain_points": getattr(icp, 'target_pain_points', []),  # Handle missing attribute
                    "geography": getattr(icp, 'geography', 'global')  # Default to global if not specified
                }
                
                product_data = {
                    "name": product.name,
                    "description": product.description
                }
                
                # Get keywords from ICP and product
                keywords = (
                    icp.target_industries +
                    [user.industry] +
                    product.name.split() +
                    [kw.strip() for kw in product.description.split() if len(kw.strip()) > 4]
                )
                
                # Remove duplicates and limit keywords
                keywords = list(set(keywords))[:10]
                logger.info(f"Searching with keywords: {keywords}")
                
                # Search for new leads
                leads = search_leads(keywords, icp=icp_data, product=product_data)
                logger.info(f"Found {len(leads) if leads else 0} potential leads")
                
                for lead_data in leads:
                    try:
                        logger.info(f"Processing lead: {lead_data.get('lead_name', 'Unknown Company')}")
                        
                        # Skip if missing required data
                        if not all(key in lead_data for key in ['lead_name', 'company_website']):
                            logger.warning(f"Invalid lead data structure: {lead_data}")
                            continue
                        
                        # Use domain email if lead email is missing
                        if 'lead_email' not in lead_data or not lead_data['lead_email']:
                            domain = urlparse(lead_data['company_website']).netloc
                            lead_data['lead_email'] = f'contact@{domain}'
                        
                        # Check for existing lead
                        existing = db.query(Lead).filter(
                            Lead.company_website == lead_data["company_website"]
                        ).first()
                        
                        if existing:
                            logger.info(f"Lead {lead_data['lead_name']} already exists, skipping")
                            continue
                            
                        # Research the company
                        logger.info(f"Researching company: {lead_data['lead_name']}")
                        research = research_company(
                            lead_data["company_website"],
                            product_data,
                            icp_data
                        )
                        
                        if "error" in research:
                            logger.error(f"Research failed for {lead_data['lead_name']}: {research['error']}")
                            continue
                            
                        # Save new lead
                        lead = Lead(
                            user_id=user.user_id,
                            lead_id=uuid.uuid4(),
                            lead_name=lead_data["lead_name"],
                            company_name=lead_data.get("company_name", lead_data["lead_name"]),  # Use lead_name as fallback
                            company_website=lead_data["company_website"],
                            lead_email=lead_data["lead_email"],
                            status="new",
                            created_at=datetime.utcnow(),
                            updated_at=datetime.utcnow()
                        )
                        db.add(lead)
                        
                        # Create research entry
                        lead_research = LeadResearch(
                            lead_id=lead.lead_id,
                            insights=research,
                            source=lead_data["company_website"],
                            created_at=datetime.utcnow()
                        )
                        db.add(lead_research)
                        
                        try:
                            db.commit()
                            logger.info(f"Successfully saved lead: {lead_data['company_name']}")
                            
                            # Send email notification with user data
                            if send_email_notification(user.email, lead_data, user_data):
                                logger.info(f"Email notification sent for lead: {lead_data['company_name']}")
                            
                        except Exception as e:
                            db.rollback()
                            logger.error(f"Error saving lead {lead_data['company_name']}: {str(e)}")
                            continue
                            
                    except Exception as e:
                        logger.error(f"Error processing lead {lead_data.get('lead_name', 'Unknown')}: {str(e)}")
                        continue
                
            except Exception as e:
                logger.error(f"Error processing user {user.email}: {str(e)}")
                continue
                
    except Exception as e:
        logger.error(f"Error in prospecting job: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    run_prospecting_job()