from app.database import SessionLocal
from app.models import User, Product, ICP
import uuid
import re
from groq import Groq
from .config import settings
import logging

logger = logging.getLogger(__name__)
groq_client = Groq()

def analyze_product_for_icp(product_name: str, product_desc: str) -> dict:
    """Use Groq to analyze the product and suggest pain points and search strategies"""
    try:
        prompt = f"""As a sales strategy expert, analyze this product and help identify ideal customer characteristics.

Product: {product_name}
Description: {product_desc}

Please analyze this product and provide:
1. List the top 5 specific pain points this product solves (be very specific)
2. List 5 key search terms that would help find companies needing this solution
3. List 3-5 alternative ways to describe the target industry

Format your response exactly like this:
Pain Point: [specific pain point]
Search Term: [search term]
Industry: [industry description]"""

        completion = groq_client.chat.completions.create(
            model="llama-3.1-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=1,
            max_completion_tokens=1024,
            top_p=1,
            stream=False,
            stop=None
        )
        
        response = completion.choices[0].message.content
        
        # Parse response
        pain_points = []
        search_terms = []
        industries = []
        
        for line in response.split('\n'):
            line = line.strip()
            if line.startswith('Pain Point:'):
                pain_points.append(line.split(':', 1)[1].strip())
            elif line.startswith('Search Term:'):
                search_terms.append(line.split(':', 1)[1].strip())
            elif line.startswith('Industry:'):
                industries.append(line.split(':', 1)[1].strip())
                
        return {
            "pain_points": pain_points,
            "search_terms": search_terms,
            "industries": industries
        }
    except Exception as e:
        logger.error(f"Error analyzing product: {str(e)}")
        return None

def collect_company_info():
    print("\n=== Welcome to Sales Bot Setup ===")
    print("Let's get your account ready (5 minutes)\n")
    
    # Basic company info
    company_info = {
        "name": input("1. Your full name: ").strip(),
        "company_name": input("2. Your company name: ").strip(),
        "email": get_valid_email(),
        "industry": input("4. Your industry: ").strip(),
    }
    
    # Product info
    print("\nNow tell us about your product/service:")
    product_info = {
        "name": input("5. Product/Service name: ").strip(),
        "description": input("6. Describe your product and its main benefits\n   (be specific about problems it solves): ").strip(),
    }
    
    # Use Groq to analyze product and suggest ICP characteristics
    analysis = analyze_product_for_icp(product_info["name"], product_info["description"])
    
    print("\nBased on your product, we've identified these target characteristics.")
    print("\nPain Points your product solves:")
    for i, point in enumerate(analysis["pain_points"], 1):
        print(f"{i}. {point}")
    
    print("\nSuggested target industries:")
    for i, industry in enumerate(analysis["industries"], 1):
        print(f"{i}. {industry}")
        
    print("\nLet's finalize your targeting:")
    
    # Get ICP info with suggestions
    icp_info = {
        "target_industries": input("\n7. Target industries (comma-separated, you can use our suggestions or add your own):\n   ").strip().split(","),
        "target_pain_points": analysis["pain_points"],  # Use the AI-generated pain points
        "geography": input("8. Target regions/countries: ").strip()
    }
    
    return company_info, product_info, icp_info

def get_valid_email():
    while True:
        email = input("3. Your work email: ").strip()
        if re.match(r"[^@]+@[^@]+\.[^@]+", email):
            return email
        print("Invalid email. Try again (e.g.: name@company.com)")

def save_to_db(company_info: dict, product_info: dict, icp_info: dict):
    db = SessionLocal()
    try:
        # Create User
        user = User(
            user_id=uuid.uuid4(),
            name=company_info["name"],
            email=company_info["email"],
            company_name=company_info["company_name"],
            industry=company_info["industry"]
        )
        db.add(user)
        
        # Create Product
        product = Product(
            user_id=user.user_id,
            name=product_info["name"],
            description=product_info["description"]
        )
        db.add(product)
        
        # Create ICP
        icp = ICP(
            user_id=user.user_id,
            target_industries=[i.strip() for i in icp_info["target_industries"]],
            target_pain_points=icp_info["target_pain_points"],
            geography=icp_info["geography"]
        )
        db.add(icp)

        db.commit()
        print("\n✅ Setup completed successfully!")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error saving data: {str(e)}")
        print(f"\n❌ Error during setup: {str(e)}")
    finally:
        db.close()