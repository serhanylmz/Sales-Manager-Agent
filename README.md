# Prospecting Bot

An AI-powered sales prospecting bot that automatically identifies and researches potential leads based on your ideal customer profile.

## Features

- Automated lead discovery using customizable search criteria
- AI-powered research and analysis of each lead's company
- Relevance scoring to prioritize the most promising leads
- Email notifications for new lead discoveries
- Persistent storage of all lead data and research insights

## Setup

1. Clone repository:
   ```bash
   git clone https://github.com/yourusername/prospecting-bot.git
   cd prospecting-bot
   ```

2. Create and activate a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a .env file with the following variables:
   ```bash
   GROQ_API_KEY=<your_groq_api_key>
   DATABASE_URL=<your_database_url>
   RESEND_API_KEY=<your_resend_api_key>
   ```

5. Initialize the database:
   ```bash
   python -m app.database
   ```

6. Run the bot:
   ```bash
   python main.py
   ```

## Environment Variables

- `GROQ_API_KEY`: API key for Groq LLM services (get from console.groq.com)
- `DATABASE_URL`: Connection string for your database (default: sqlite:///./prospecting.db)
- `RESEND_API_KEY`: API key for email notifications via Resend

## Configuration

Additional settings can be configured in `app/config.py`, including:

- Search interval frequency
- Minimum relevance score threshold
- Maximum leads per search run
- Email notification settings
