# Prospecting Bot

An AI-powered sales prospecting bot that automatically identifies and researches potential leads based on your ideal customer profile. This system combines advanced AI capabilities with robust automation to create a powerful lead generation and research tool.

## System Architecture

### Core Components

1. **Lead Discovery Engine**
   - Automated keyword-based lead search using configurable criteria
   - Smart filtering based on company relevance and potential fit
   - Rate-limited API calls to prevent throttling
   - Asynchronous processing for improved performance

2. **AI Research Module**
   - Integration with Groq's LLM API for advanced analysis
   - Intelligent HTML parsing and content extraction
   - Contextual understanding of company profiles
   - Automated relevance scoring system

3. **Data Management**
   - SQLAlchemy ORM for robust database operations
   - Automated schema management and migrations
   - Efficient data caching and retrieval
   - Transaction management for data integrity

4. **Notification System**
   - Real-time email notifications via Resend
   - Customizable notification templates
   - Delivery status tracking
   - Error handling and retry mechanisms

5. **Scheduling System**
   - APScheduler-based job management
   - Configurable execution intervals
   - Job persistence across restarts
   - Error recovery mechanisms

## Features

- Automated lead discovery using customizable search criteria
- AI-powered research and analysis of each lead's company
- Relevance scoring to prioritize the most promising leads
- Email notifications for new lead discoveries
- Persistent storage of all lead data and research insights
- Rate limiting and throttling protection
- Robust error handling and recovery
- Configurable scheduling system
- Transaction-safe database operations
- Comprehensive logging system

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

5. Run the bot:
   ```bash
   python main.py
   ```

## Containerized Deployment

The application can be run in containers for both development and production:

### Local Development with Docker

```bash
# Build and start the container
docker-compose up --build

# View logs
docker-compose logs -f

# Stop the container
docker-compose down
```

### Production Deployment

For production deployment, we maintain compatibility with the existing configuration while providing containerization:

1. Build the container:
   ```bash
   docker build -t prospecting-bot .
   ```

2. Run with production settings:
   ```bash
   docker run -d \
     --name prospecting-bot \
     -v app_data:/app/data \
     --env-file .env \
     prospecting-bot
   ```

## Configuration

### Environment Variables

- `GROQ_API_KEY`: API key for Groq LLM services (get from console.groq.com)
- `DATABASE_URL`: Connection string for your database (default: sqlite:///./app.db)
- `RESEND_API_KEY`: API key for email notifications via Resend

### Application Settings (`app/config.py`)

The application uses a robust configuration system with the following key settings:

- **Database Settings**
  - Configurable database URL with SQLite default
  - Connection pooling and timeout settings
  - Transaction isolation levels

- **Lead Search Settings**
  - Minimum relevance score threshold (default: 30)
  - Maximum leads per run (default: 10)
  - Customizable search criteria

- **Scheduler Settings**
  - Configurable search interval (default: 24 hours)
  - Job persistence options
  - Error handling configuration

- **Email Settings**
  - SMTP server configuration
  - Authentication settings
  - Template customization

## Data Models

The system uses SQLAlchemy models for robust data management:

- **User Model**: Stores user and company information
- **Lead Model**: Manages prospective lead data
- **Research Model**: Stores AI-generated research insights
- **Email Model**: Tracks notification history

## Error Handling

The system implements comprehensive error handling:

1. **API Rate Limiting**
   - Automatic backoff on API limits
   - Request queuing and retry logic
   - Circuit breaker pattern for external services

2. **Database Operations**
   - Transaction rollback on errors
   - Connection pool management
   - Deadlock detection and retry

3. **Job Processing**
   - Failed job tracking
   - Automatic retry with exponential backoff
   - Error notification system

## Monitoring and Logging

The system includes detailed logging for operational visibility:

- Request/response logging for external APIs
- Database operation tracking
- Job execution status
- Error and exception details
- Performance metrics

## Security Features

- Environment-based configuration
- Secure credential management
- Rate limiting protection
- SQL injection prevention
- Input validation and sanitization

## Best Practices

1. **Running in Production**
   - Use appropriate environment variables
   - Configure proper logging
   - Set up monitoring
   - Use a process manager
   - Implement backup strategy

2. **Maintenance**
   - Regular database cleanup
   - Log rotation
   - Performance monitoring
   - Security updates

3. **Scaling**
   - Configure appropriate job intervals
   - Monitor resource usage
   - Adjust batch sizes as needed
   - Optimize database queries

## Troubleshooting

Common issues and solutions:

1. **Database Connectivity**
   - Check DATABASE_URL setting
   - Verify permissions
   - Check disk space

2. **API Rate Limits**
   - Adjust batch sizes
   - Configure appropriate intervals
   - Check API quotas

3. **Email Delivery**
   - Verify SMTP settings
   - Check API keys
   - Monitor spam filters

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
