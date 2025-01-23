from typing import List, Dict
import requests
from bs4 import BeautifulSoup
import logging
import re
from time import sleep
from urllib.parse import urlparse
from googlesearch import search
import random
from ..config import settings
from groq import Groq
import json

logger = logging.getLogger(__name__)
groq_client = Groq()

def get_random_user_agent():
    """Get a random user agent to avoid detection"""
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59'
    ]
    return random.choice(user_agents)

def is_company_website(url: str, title: str) -> bool:
    """Check if URL is likely a company website rather than an article/blog"""
    
    # Skip common non-company sites
    skip_domains = {
        'medium.com', 'linkedin.com', 'facebook.com', 'twitter.com', 'youtube.com',
        'github.com', 'wikipedia.org', 'reddit.com', 'quora.com', 'forbes.com',
        'techcrunch.com', 'crunchbase.com', 'bloomberg.com', 'businessinsider.com',
        'wsj.com', 'nytimes.com', 'reuters.com', 'inc.com', 'entrepreneur.com',
        'blog.', 'wordpress.com', 'blogspot.com', 'wix.com', 'squarespace.com'
    }
    
    # Skip if URL contains article/blog indicators
    skip_paths = {'blog', 'news', 'article', 'press', 'about', 'contact', 'careers'}
    
    domain = urlparse(url).netloc.lower()
    path = urlparse(url).path.lower()
    
    # Skip if domain matches skip list
    if any(d in domain for d in skip_domains):
        return False
        
    # Skip if path contains article indicators
    if any(p in path for p in skip_paths):
        return False
        
    # Skip if title contains article indicators
    title_lower = title.lower()
    if any(w in title_lower for w in ['how to', 'guide', 'tips', 'best', 'top', 'list', 'vs', 'versus']):
        return False
        
    # Must be a .com domain
    if not domain.endswith('.com'):
        return False
        
    return True

def generate_search_queries(keywords: List[str], icp: dict, product: dict) -> List[str]:
    """Use Groq to generate effective search queries based on ICP and product"""
    try:
        prompt = f"""As a sales prospecting expert, help me generate effective search queries to find potential companies that might need our solution.

Product: {product['name']} - {product['description']}
Target Industries: {', '.join(icp['target_industries'])}

Generate 5 search queries that would help find relevant companies. Focus on finding companies that might need our solution.
Make the queries simple and direct, good for Google search.

Format your response exactly like this:
Query: [search query]"""

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
        queries = []
        
        for line in response.split('\n'):
            if line.startswith('Query:'):
                query = line.split(':', 1)[1].strip()
                if query:
                    queries.append(query)
        
        # Add some basic queries as fallback
        if not queries:
            queries = [
                f"top companies {industry}" for industry in icp['target_industries']
            ]
        
        return queries
    except Exception as e:
        logger.error(f"Error generating search queries: {str(e)}")
        return []

def is_valid_url(url: str) -> bool:
    """Validate URL and ensure it has a scheme"""
    if not url:
        return False
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def get_company_info(url: str) -> Dict:
    """Extract company information from website"""
    try:
        if not is_valid_url(url):
            return None
            
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url

        headers = {
            'User-Agent': get_random_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }
        
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract domain for fallback
        domain = urlparse(url).netloc.lower()
        domain = domain.replace('www.', '').split('.')[0]
        
        # Extract text content and clean it
        text_content = ' '.join(soup.get_text().split())[:2000]  # First 2000 chars, cleaned
        
        # Extract emails from the page
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        emails = re.findall(email_pattern, response.text)
        contact_emails = [
            email for email in emails
            if not any(x in email.lower() for x in ['noreply', 'no-reply', 'donotreply'])
            and not email.startswith(('example', 'test', 'user', 'admin'))
        ]
        default_email = contact_emails[0] if contact_emails else f'contact@{domain}.com'
        
        # Use Groq to extract company information
        prompt = f"""Extract company information from this website content. The response MUST be a valid JSON object.

Website URL: {url}
Content: {text_content}

Rules:
1. If you can't find a specific piece of information, use "None found" as the value
2. Company name should be the actual business name, not a blog title or article name
3. Lead name should be a real person's name if found, otherwise "None found"
4. Never return null or empty values

Return ONLY a JSON object in this exact format:
{{
    "company_name": "actual company name or domain-based name",
    "lead_name": "real person name or 'None found'",
    "lead_email": "found email or '{default_email}'",
    "company_description": "2-3 sentence description of what the company does"
}}"""

        completion = groq_client.chat.completions.create(
            model="llama-3.1-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a JSON-only API that extracts company information from website content. Only return valid JSON, no other text."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_completion_tokens=1024,
            top_p=1,
            stream=False,
            stop=None
        )
        
        # Parse response
        response_text = completion.choices[0].message.content.strip()
        if response_text.startswith('```json'):
            response_text = response_text[7:]
        if response_text.startswith('```'):
            response_text = response_text[3:]
        if response_text.endswith('```'):
            response_text = response_text[:-3]
        
        extracted_info = json.loads(response_text.strip())
        
        # Ensure we have all required fields with valid values
        result = {
            'company_name': extracted_info.get('company_name', domain.title()),
            'lead_name': extracted_info.get('lead_name', 'None found'),
            'lead_email': extracted_info.get('lead_email', default_email),
            'company_website': url,
            'company_description': extracted_info.get('company_description', 'None found')
        }
        
        # Final validation
        if result['company_name'].lower() in ['none', 'none found', 'unknown']:
            result['company_name'] = domain.title()
        
        return result
        
    except Exception as e:
        logger.error(f"Error extracting company info from {url}: {str(e)}")
        return None

def search_leads(keywords: List[str], icp: dict = None, product: dict = None) -> List[Dict]:
    """Search for potential leads based on keywords and ICP"""
    try:
        # Generate search queries
        search_queries = generate_search_queries(keywords, icp, product)
        logger.info(f"Using search queries: {search_queries}")
        
        results = []
        seen_urls = set()
        
        for query in search_queries:
            try:
                # Use Google Search API to find companies
                for url in search(query, num_results=10):
                    if url in seen_urls:
                        continue
                    
                    try:
                        # Get page title to check if it's a company website
                        headers = {'User-Agent': get_random_user_agent()}
                        response = requests.get(url, headers=headers, timeout=5)
                        soup = BeautifulSoup(response.text, 'html.parser')
                        title = soup.title.string if soup.title else ''
                        
                        if not is_company_website(url, title):
                            continue
                            
                        # Extract company information
                        company_info = get_company_info(url)
                        if company_info and all(k in company_info for k in ['company_name', 'lead_name', 'company_website', 'lead_email']):
                            results.append(company_info)
                            seen_urls.add(url)
                            
                            # Log found company
                            logger.info(f"Found company: {company_info['company_name']}")
                            
                    except Exception as e:
                        logger.error(f"Error processing URL {url}: {str(e)}")
                        continue
                        
                    # Respect rate limits
                    sleep(2)
                    
            except Exception as e:
                logger.error(f"Error processing query '{query}': {str(e)}")
                continue
                
            if len(results) >= 10:  # Limit to 10 leads per run
                break
                
        return results
        
    except Exception as e:
        logger.error(f"Error in search_leads: {str(e)}")
        return []