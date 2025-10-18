# LeetCode AI Study Assistant

An intelligent study assistant that helps you create personalized LeetCode study plans using AI. The system analyzes your LeetCode submission history and generates daily study plans with topic recommendations and problem suggestions.

![Project Plan](plan_screenshot.png)

## Features

- **Smart Sync**: Automatically syncs your LeetCode submissions via GraphQL API
- **AI-Powered Planning**: Uses Claude AI to generate personalized study plans
- **Topic Analysis**: Tracks your progress across different algorithm topics
- **Progress Tracking**: Visualizes your solving patterns and streaks
- **Two-Step Planning**: First recommends topics, then suggests specific problems
- **Real-time Updates**: Live sync with your LeetCode activity

## Quick Start

### Prerequisites

- Python 3.8+
- Node.js 16+
- PostgreSQL database
- LeetCode account (for syncing submissions)

### Backend Setup

1. **Install dependencies**:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Configure environment**:
   ```bash
   cp env_template.txt .env
   # Edit .env with your database URL, API keys, and LeetCode credentials
   ```

3. **Set up database**:
   ```bash
   # Create PostgreSQL database
   createdb leetcode_assistant
   
   # Run the backend to create tables
   python main.py
   ```

4. **Start the backend**:
   ```bash
   python main.py
   ```

### Frontend Setup

1. **Install dependencies**:
   ```bash
   cd frontend
   npm install
   ```

2. **Start development server**:
   ```bash
   npm run dev
   ```

3. **Open in browser**: http://localhost:5173

## System Design

### Architecture Overview

The system follows a modern full-stack architecture with clear separation of concerns:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   External      │
│   (React/Vite)  │◄──►│   (FastAPI)     │◄──►│   Services      │
│                 │    │                 │    │                 │
│ • React UI      │    │ • REST API      │    │ • LeetCode API  │
│ • TypeScript    │    │ • PostgreSQL    │    │ • Claude AI     │
│ • Tailwind CSS  │    │ • SQLAlchemy    │    │ • Langfuse      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Core Components

#### 1. Data Layer
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Models**: 
  - `Problem`: LeetCode problem metadata (number, title, difficulty, topics)
  - `Submission`: User's solved problems with timestamps
  - `DailyPlan`: Generated study plans
- **Analytics**: Topic statistics and progress tracking

#### 2. API Layer
- **Framework**: FastAPI with async support
- **Endpoints**:
  - `POST /api/sync`: Sync LeetCode submissions
  - `GET /api/stats`: Overall progress statistics
  - `GET /api/stats/topics`: Topic-wise breakdown
  - `GET /api/daily-plan/topics-preview`: AI topic recommendations
  - `POST /api/daily-plan/confirm`: Generate detailed study plan

#### 3. AI Integration
- **LLM**: Anthropic Claude for intelligent planning
- **Two-Step Process**:
  1. **Topic Decision**: Analyze user history → recommend focus topics
  2. **Problem Selection**: Given topics → suggest specific problems
- **Prompt Engineering**: Structured prompts for consistent AI responses

#### 4. External Integrations
- **LeetCode GraphQL API**: Fetch user submissions and problem metadata
- **Session Management**: Authenticated requests using session cookies
- **Rate Limiting**: Built-in protection against API abuse

### Data Flow

#### Sync Process
```
User Clicks Sync → Frontend → Backend → LeetCode API
                                    ↓
Database ← Process Data ← Fetch Submissions
```

#### Study Plan Generation
```
User Request → Topic Analysis → AI Topic Decision → AI Problem Selection → Response
     ↓              ↓                ↓                    ↓
  Time/Goals → User History → Focus Topics → Specific Problems → UI Display
```

### Key Design Decisions

#### 1. Two-Step AI Planning
**Why**: Separates topic selection from problem selection for better control and user review.

**Implementation**:
- Step 1: `build_prompt1_topic_decision()` - Analyzes user history, recommends topics
- Step 2: `build_prompt2_daily_plan()` - Given topics, selects specific problems

#### 2. Async-First Architecture
**Why**: Network I/O operations (LeetCode API, Claude AI) are naturally async.

**Implementation**:
- Backend: FastAPI with async endpoints
- LeetCode Client: aiohttp for non-blocking HTTP requests
- Frontend: Proper async/await handling

#### 3. Comprehensive Logging
**Why**: AI systems need observability for debugging and improvement.

**Implementation**:
- Langfuse integration for LLM call tracking
- Structured logging for all AI interactions
- Request/response logging for debugging

#### 4. User-Friendly Error Handling
**Why**: Network operations can fail, users need clear feedback.

**Implementation**:
- Info banners for successful operations
- Error banners for failures
- Auto-clearing messages for better UX

### Database Schema

```sql
-- Core entities
Problems (id, leetcode_number, title, difficulty, topics, leetcode_url)
Submissions (id, problem_id, solved_date, attempts)
DailyPlans (id, date, time_minutes, custom_instructions, plan_data)

-- Relationships
Submissions.problem_id → Problems.id (Many-to-One)
```

### API Design

#### RESTful Endpoints
- `GET /api/stats` - Overall statistics
- `GET /api/stats/topics` - Topic breakdown
- `POST /api/sync` - Sync LeetCode data
- `GET /api/daily-plan/topics-preview` - Preview topic recommendations
- `POST /api/daily-plan/confirm` - Generate full study plan

#### Response Formats
```json
// Sync Response
{
  "new_problems": 0,
  "new_submissions": 5,
  "message": "No new submissions since last sync.",
  "sync_timestamp": "2025-10-17T18:27:39.672275"
}

// Topic Decision
{
  "new_topic": "Dynamic Programming",
  "review_topics": ["Arrays", "Two Pointers"],
  "rationale": "Focusing on DP as it has been less practiced recently..."
}
```

### Security Considerations

1. **API Keys**: Stored in environment variables, never committed
2. **Session Cookies**: Secure handling of LeetCode session tokens
3. **CORS**: Properly configured for development and production
4. **Rate Limiting**: Built-in sync rate limiting (60 seconds)
5. **Input Validation**: Pydantic models for request/response validation

### Performance Optimizations

1. **Database Indexing**: Optimized queries for topic statistics
2. **Async Operations**: Non-blocking I/O for better concurrency
3. **Caching**: In-memory rate limiting and session management
4. **Efficient Queries**: Batch operations for data processing

### Monitoring & Observability

1. **Langfuse Integration**: Track all LLM calls and responses
2. **Structured Logging**: Comprehensive logging for debugging
3. **Health Checks**: Built-in health check endpoints
4. **Error Tracking**: Proper error handling and reporting

## Configuration

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/leetcode_assistant

# AI
ANTHROPIC_API_KEY=your_claude_api_key

# LeetCode (for syncing)
LEETCODE_USERNAME=your_username
LEETCODE_SESSION=your_session_cookie

# Observability
LANGFUSE_PUBLIC_KEY=your_langfuse_key
LANGFUSE_SECRET_KEY=your_langfuse_secret
LANGFUSE_HOST=https://us.cloud.langfuse.com

# Application
BACKEND_PORT=8000
FRONTEND_PORT=3000
```

### LeetCode Session Setup

1. Log into LeetCode in your browser
2. Open Developer Tools (F12)
3. Go to Application → Cookies → https://leetcode.com
4. Copy the `LEETCODE_SESSION` cookie value
5. Add it to your `.env` file

## Development

### Project Structure
```
leetai/
├── backend/                 # FastAPI backend
│   ├── main.py             # Application entry point
│   ├── database.py         # Database models and connection
│   ├── leetcode.py         # LeetCode API client
│   ├── claude.py           # Claude AI integration
│   ├── analytics.py        # Data analysis and statistics
│   ├── llm_prompts.py      # AI prompt templates
│   ├── schemas.py          # Pydantic models
│   └── observability.py    # Logging and monitoring
├── frontend/               # React frontend
│   ├── src/
│   │   ├── App.tsx         # Main application component
│   │   ├── api.ts          # API client
│   │   ├── types.ts        # TypeScript definitions
│   │   └── components/     # React components
│   └── package.json
└── data/                   # Sample data and imports
```

### Adding New Features

1. **Backend**: Add new endpoints in `main.py`, models in `schemas.py`
2. **Frontend**: Add new components in `src/components/`, API calls in `api.ts`
3. **AI Prompts**: Modify prompts in `llm_prompts.py`
4. **Database**: Add migrations for schema changes

### Testing

```bash
# Backend tests
cd backend
python -m pytest

# Frontend tests
cd frontend
npm test
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Support

For issues and questions:
1. Check the GitHub Issues
2. Review the system design documentation
3. Check the logs for debugging information
