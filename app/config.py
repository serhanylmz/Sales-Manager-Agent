from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database settings
    database_url: str = "sqlite:///./app.db"
    
    # Groq API settings
    groq_api_key: str = ""
    
    # Email settings (using Gmail SMTP)
    gmail_email: str = "rekaassignmentbot@gmail.com"
    gmail_password: str = ""  # App password from Gmail
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    
    # Lead search settings
    min_relevance_score: int = 30
    max_leads_per_run: int = 10
    
    # Scheduler settings
    search_interval_minutes: int = 1 # 1440  # 24 hours
    
    class Config:
        env_file = ".env"

settings = Settings()