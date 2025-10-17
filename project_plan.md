# LeetCode Study Assistant - Project Plan
## Simplified for Single-User Pet Project

## Tech Stack
- **Frontend**: React + TypeScript + Tailwind CSS
- **Backend**: Python (FastAPI) + Pydantic
- **Database**: PostgreSQL (local)
- **AI**: Claude API (Anthropic)
- **Development**: Cursor IDE

---

## Database Schema

### Tables

**1. `problems`**
```sql
- id (PK, auto-increment)
- leetcode_number (unique, int)
- title (text)
- difficulty (enum: easy, medium, hard)
- topics (text[], array of LeetCode tags)
- leetcode_url (text)
```

**2. `submissions`**
```sql
- id (PK, auto-increment)
- problem_id (FK to problems)
- solved_date (date)
- attempts (int)
- created_at (timestamp)
```

**3. `daily_plans`**
```sql
- id (PK, auto-increment)
- plan_date (date, unique)
- available_time_minutes (int)
- problem_recommendations (jsonb) -- array of {leetcode_number, reason, estimated_time}
- focus_topic (text) -- the one new topic for the day
- ai_rationale (text) -- Claude's explanation
- created_at (timestamp)
```

**Note:** Topic stats will be calculated on-demand, no separate table needed.

---

## Data Format

### Initial Historical Data Import
**CSV format:**
```csv
leetcode_number,title,difficulty,solved_date,attempts,topics
1,Two Sum,easy,2024-01-15,1,"Array|Hash Table"
2,Add Two Numbers,medium,2024-01-16,2,"Linked List|Math|Recursion"
```

- Topics separated by `|`
- Date format: `YYYY-MM-DD`
- Difficulty: lowercase (easy, medium, hard)

### Daily Update Data Fetch
**LeetCode GraphQL API** (unofficial but widely used):
- Endpoint: `https://leetcode.com/graphql`
- Query recent submissions
- Parse and insert into database

---

## Simplified Project Structure

```
leetcode-assistant/
├── backend/
│   ├── main.py              # FastAPI app + all routes (~250 lines)
│   ├── database.py          # SQLAlchemy models + DB setup (~150 lines)
│   ├── schemas.py           # Pydantic models (~100 lines)
│   ├── leetcode.py          # LeetCode API client (~100 lines)
│   ├── claude.py            # Claude API + prompt template (~150 lines)
│   ├── analytics.py         # Topic stats calculation (~100 lines)
│   ├── import_csv.py        # One-time CSV import script
│   ├── requirements.txt
│   └── .env
│
├── frontend/
│   ├── src/
│   │   ├── App.tsx          # Main UI component (~300 lines)
│   │   ├── components/
│   │   │   ├── TopicCard.tsx     # Reusable topic display
│   │   │   └── ProblemCard.tsx   # Reusable problem display
│   │   ├── api.ts           # API client (~80 lines)
│   │   └── types.ts         # TypeScript interfaces
│   ├── package.json
│   └── tailwind.config.js
│
├── data/
│   └── historical.csv       # Your seed data
│
├── .gitignore
└── README.md
```

---

## Implementation Phases

### Phase 1: Database & Backend Foundation
**Cursor Tasks:**
1. Set up PostgreSQL database
2. Create SQLAlchemy models in `database.py` for all tables
3. Create Pydantic schemas in `schemas.py` for request/response validation
4. Set up FastAPI app in `main.py` with database initialization (`create_all()` on startup)
5. Create CSV import script `import_csv.py`

**Key Files:**
- `backend/database.py` - SQLAlchemy models + DB connection
- `backend/schemas.py` - Pydantic models for validation
- `backend/main.py` - FastAPI setup + database init
- `backend/import_csv.py` - CSV import

**Example database.py structure:**
```python
from sqlalchemy import create_engine, Column, Integer, String, Date, ARRAY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class Problem(Base):
    __tablename__ = "problems"
    id = Column(Integer, primary_key=True)
    leetcode_number = Column(Integer, unique=True)
    title = Column(String)
    difficulty = Column(String)
    topics = Column(ARRAY(String))
    leetcode_url = Column(String)

# ... other models
```

**Deliverables:**
- Working database with all tables created on startup
- CSV import successfully populates `problems` and `submissions`
- Basic FastAPI server running

### Phase 2: LeetCode Data Sync
**Cursor Tasks:**
1. Implement LeetCode GraphQL API client in `leetcode.py`
2. Create `POST /api/sync` endpoint in `main.py`:
   - Fetches recent submissions from LeetCode
   - Compares with existing data
   - Inserts new submissions and problems
   - Returns sync summary
3. Add Pydantic models for sync response
4. Error handling and basic rate limiting

**Key Files:**
- `backend/leetcode.py` - LeetCode GraphQL client
- `backend/main.py` - Add sync endpoint
- `backend/schemas.py` - Add SyncResponse schema

**Example leetcode.py structure:**
```python
import requests
from typing import List, Dict

class LeetCodeClient:
    def __init__(self, session_cookie: str = None):
        self.base_url = "https://leetcode.com/graphql"
        self.session = session_cookie
    
    def fetch_recent_submissions(self, limit: int = 20) -> List[Dict]:
        # GraphQL query implementation
        pass
```

**Deliverables:**
- `POST /api/sync` endpoint functional
- Can fetch and store new LeetCode submissions
- Returns meaningful sync results

### Phase 3: Analytics & Topic Stats
**Cursor Tasks:**
1. Implement topic statistics calculation in `analytics.py`:
   - Function to calculate stats for all topics
   - Group submissions by topic and time window (3d, 7d, 14d, 28d+)
   - Calculate weighted scores per topic
   - Identify recency and gaps
2. Create stats endpoints in `main.py`:
   - `GET /api/stats` - overall statistics
   - `GET /api/stats/topics` - all topic breakdowns
   - `GET /api/stats/topics/:topic` - specific topic details
3. Create Pydantic models for stats responses

**Key Files:**
- `backend/analytics.py` - Stats calculation logic
- `backend/main.py` - Add stats endpoints
- `backend/schemas.py` - Add stats response schemas

**Example analytics.py structure:**
```python
from datetime import datetime, timedelta
from typing import Dict, List
from collections import defaultdict

def calculate_topic_stats(db_session) -> List[Dict]:
    """Calculate statistics for all topics across time windows"""
    now = datetime.now()
    
    # Time window boundaries
    windows = {
        '3d': now - timedelta(days=3),
        '7d': now - timedelta(days=7),
        '14d': now - timedelta(days=14),
        '28d': now - timedelta(days=28)
    }
    
    # Query and aggregate logic
    # ...
    
    return topic_stats

def calculate_weighted_score(topic_data: Dict) -> float:
    """Calculate weighted score based on difficulty and recency"""
    recency_multiplier = {'3d': 1.0, '7d': 0.8, '14d': 0.5, '28d+': 0.3}
    difficulty_weight = {'easy': 1, 'medium': 2, 'hard': 3}
    # ... calculation logic
    return score
```

**Deliverables:**
- `GET /api/stats` returns overall progress metrics
- `GET /api/stats/topics` returns all topics with time-windowed breakdowns
- Weighted scoring formula implemented
- Fast enough for on-demand calculation

### Phase 4: Claude Integration & Daily Plan
**Cursor Tasks:**
1. Set up Claude API client in `claude.py` with error handling
2. Create prompt template function in `claude.py`:
   - Takes topic statistics and user parameters
   - Constructs structured prompt
   - Includes requirements (1 new topic, review mix, difficulty balance)
3. Implement `GET /api/daily-plan` endpoint in `main.py`:
   - Accept query params: `date`, `time_minutes`, `custom_instructions`
   - Check if plan exists for the date
   - If exists: return cached plan
   - If not: generate with Claude, save, return
4. Add Pydantic models for daily plan request/response

**Key Files:**
- `backend/claude.py` - Claude API client + prompt template
- `backend/main.py` - Add daily plan endpoint
- `backend/schemas.py` - Add daily plan schemas

**Example claude.py structure:**
```python
import anthropic
from typing import Dict, List

class ClaudeClient:
    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = "claude-sonnet-4-5-20250929"
    
    def generate_daily_plan(
        self, 
        topic_stats: List[Dict], 
        time_minutes: int,
        custom_instructions: str = None
    ) -> Dict:
        prompt = self._build_prompt(topic_stats, time_minutes, custom_instructions)
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        # Parse JSON response from Claude
        return self._parse_response(response.content[0].text)
    
    def _build_prompt(self, stats, time_minutes, custom_instructions):
        return f"""
You are a LeetCode study assistant. Generate a personalized daily study plan.

AVAILABLE TIME: {time_minutes} minutes

RECENT ACTIVITY:
{self._format_stats(stats)}

REQUIREMENTS:
1. Recommend specific LeetCode problems (by number and title)
2. Include ONE new topic the user hasn't practiced recently
3. Include review problems from topics solved 7-14 days ago
4. Balance difficulty: prioritize Medium, include 1 Hard if time permits
5. Estimate 15 min for Easy, 25 min for Medium, 40 min for Hard

OUTPUT FORMAT (JSON):
{{
  "focus_topic": "topic name",
  "recommendations": [
    {{"leetcode_number": 123, "title": "Problem", "difficulty": "medium", 
      "reason": "...", "estimated_minutes": 25}}
  ],
  "rationale": "explanation..."
}}

{f"ADDITIONAL: {custom_instructions}" if custom_instructions else ""}
"""
```

**Deliverables:**
- `GET /api/daily-plan` endpoint functional
- Returns cached plan if exists, generates new one if not
- Claude integration working with structured JSON output
- Prompt template produces good recommendations

### Phase 5: Frontend - Complete UI
**Cursor Tasks:**
1. Set up React app with TypeScript + Tailwind
2. Create API client in `api.ts` for all backend endpoints
3. Build main `App.tsx` with:
   - Overall stats dashboard section
   - Topic breakdown grid (use TopicCard component)
   - Daily plan generator form (time input + custom instructions)
   - Daily plan display (use ProblemCard component)
   - Sync button in header/nav
4. Create `TopicCard.tsx` component:
   - Display topic name, weighted score
   - Show breakdown by time windows
   - Color-coded by recency (green=recent, yellow=fading, red=stale)
5. Create `ProblemCard.tsx` component:
   - Display problem number, title, difficulty
   - Link to LeetCode
   - Show AI's reason for recommendation
   - Time estimate
6. Add TypeScript interfaces in `types.ts`

**Key Files:**
- `frontend/src/App.tsx` - Main application UI
- `frontend/src/components/TopicCard.tsx` - Topic display
- `frontend/src/components/ProblemCard.tsx` - Problem display
- `frontend/src/api.ts` - Backend API client
- `frontend/src/types.ts` - TypeScript interfaces

**Example App.tsx structure:**
```typescript
function App() {
  const [stats, setStats] = useState(null);
  const [topics, setTopics] = useState([]);
  const [dailyPlan, setDailyPlan] = useState(null);
  const [timeMinutes, setTimeMinutes] = useState(60);
  
  // Fetch initial data
  useEffect(() => { ... }, []);
  
  const handleSync = async () => { ... };
  const handleGeneratePlan = async () => { ... };
  
  return (
    <div className="min-h-screen bg-gray-50">
      <header>
        <SyncButton onClick={handleSync} />
      </header>
      
      <main className="container mx-auto p-6">
        {/* Stats Dashboard */}
        <section className="mb-8">
          <h2>Overall Progress</h2>
          {stats && <StatsDisplay stats={stats} />}
        </section>
        
        {/* Topic Breakdown */}
        <section className="mb-8">
          <h2>Topics</h2>
          <div className="grid grid-cols-3 gap-4">
            {topics.map(topic => <TopicCard key={topic.name} {...topic} />)}
          </div>
        </section>
        
        {/* Daily Plan Generator */}
        <section>
          <h2>Daily Plan</h2>
          <DailyPlanForm 
            onGenerate={handleGeneratePlan}
            timeMinutes={timeMinutes}
            setTimeMinutes={setTimeMinutes}
          />
          {dailyPlan && <DailyPlanDisplay plan={dailyPlan} />}
        </section>
      </main>
    </div>
  );
}
```

**Deliverables:**
- Complete functional UI
- Can view stats and topic breakdowns
- Can generate daily plans with custom parameters
- Can sync new data from LeetCode
- Responsive design with Tailwind
- All components have loading and error states

### Phase 6: Polish & Testing
**Cursor Tasks:**
1. Add comprehensive error handling throughout
2. Add loading states and spinners
3. Test edge cases:
   - No historical data (empty database)
   - LeetCode API failures
   - Claude API rate limits
   - Invalid date/time inputs
   - Requesting plan for past dates
4. Add input validation (time ranges, date formats)
5. Add visual feedback for user actions (toasts/notifications)
6. Write comprehensive README with:
   - Setup instructions
   - Environment variables
   - CSV format
   - How to run
   - API documentation
7. Create `.gitignore` (exclude .env, node_modules, __pycache__, etc.)
8. Optional: Add simple charts/visualizations for progress over time

**Deliverables:**
- Polished, production-ready application
- Comprehensive error handling
- Documentation for setup and usage
- Ready to push to GitHub


## Phase 7: Intelligent Daily Plan Generation

Tasks:

Implement a two-prompt LLM workflow to generate personalized daily study plans.

Prompt 1:

Fetch topic summary statistics from the analytics layer.

Pass the stats to the LLM to determine:

new_topic — the next topic to introduce.

focus_topics — refresher topics based on recency and performance gaps.

The LLM response must return a deterministic JSON object with these fields populated.

Prompt 2:

Query the database for problems solved in the last 30 days under the returned topics.

Pass the relevant LeetCode problem numbers to the LLM.

Generate a structured daily plan with recommended problems, review strategy, and pacing.

Add support for custom parameters (e.g., number of problems, difficulty distribution, time available).

Ensure the output is predictable and machine-readable, enabling future automation (e.g., calendar or dashboard integrations).

Key Files:

backend/analytics.py — source of topic stats

backend/llm_prompts.py — encapsulate both prompts for maintainability

backend/main.py — add /api/daily-plan endpoint to trigger this workflow

Example daily plan prompt flow:

Prompt 1 → (topics + stats) → { "new_topic": "Heap", "focus_topics": ["DP", "Graph"] }
Prompt 2 → (problem numbers) → structured plan response


Deliverables:

Two modular LLM prompts powering daily plan generation

Structured JSON output for deterministic downstream use

Working endpoint that can generate daily plans with custom parameters

---

## Environment Variables (.env)

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/leetcode_assistant

# Claude API
ANTHROPIC_API_KEY=your_api_key_here

# LeetCode (optional, for authenticated API access)
LEETCODE_SESSION=optional_session_cookie

# App Config (optional)
BACKEND_PORT=8000
FRONTEND_PORT=3000
```

---

## API Endpoints (Final)

```
POST   /api/sync                    # Fetch latest from LeetCode, create submissions
GET    /api/stats                   # Overall statistics
GET    /api/stats/topics            # All topic breakdowns
GET    /api/stats/topics/{topic}    # Specific topic details
GET    /api/daily-plan              # Get plan for date (or generate if doesn't exist)
                                    # Query params: ?date=YYYY-MM-DD&time_minutes=60&custom_instructions=...
GET    /api/problems                # List all problems (for reference)
```

### Endpoint Details

**GET /api/daily-plan**
- **Query Parameters:**
  - `date` (optional): YYYY-MM-DD format, defaults to today
  - `time_minutes` (required if generating): integer, available study time
  - `custom_instructions` (optional): string, additional instructions for Claude
- **Behavior:**
  - Checks if plan exists for specified date
  - If exists: returns cached plan
  - If not: generates with Claude, saves, returns
- **Response:**
  ```json
  {
    "plan_date": "2024-10-14",
    "available_time_minutes": 60,
    "focus_topic": "Dynamic Programming",
    "recommendations": [
      {
        "leetcode_number": 70,
        "title": "Climbing Stairs",
        "difficulty": "easy",
        "reason": "Foundation for DP thinking",
        "estimated_minutes": 15,
        "leetcode_url": "https://leetcode.com/problems/climbing-stairs/"
      }
    ],
    "ai_rationale": "Starting with DP basics since you haven't practiced this in 20 days...",
    "is_cached": false
  }
  ```

---

## Time Window Rationale

- **3 days**: Recent/fresh practice - topics actively working on
- **7 days**: Current focus - topics to maintain
- **14 days**: Starting to fade - good review candidates
- **28+ days**: Long-term retention - topics mastered or needing refresh

This gives Claude context about recency decay and helps identify:
1. Topics needing immediate review (14-28 day gap)
2. Topics to maintain (7d active)
3. Topics that are "cold" (28d+ gap)

---

## Weighted Score Formula

```python
# Recency multipliers (more recent = higher weight)
recency_multiplier = {
    '3d': 1.0,
    '7d': 0.8,
    '14d': 0.5,
    '28d+': 0.3
}

# Difficulty weights (harder = more points)
difficulty_weight = {
    'easy': 1,
    'medium': 2,
    'hard': 3
}

# Topic score = sum of (count × difficulty × recency) for all problems
topic_score = sum(
    count * difficulty_weight[diff] * recency_multiplier[window]
    for each (count, diff, window) in topic_stats
)
```

Recent hard problems count most; older easy problems count least.

---

## Key Pydantic Models (schemas.py)

```python
from pydantic import BaseModel, Field
from datetime import date
from typing import List, Optional

class ProblemBase(BaseModel):
    leetcode_number: int
    title: str
    difficulty: str
    topics: List[str]
    leetcode_url: str

class SubmissionBase(BaseModel):
    problem_id: int
    solved_date: date
    attempts: int

class TopicStats(BaseModel):
    topic: str
    easy_3d: int = 0
    medium_3d: int = 0
    hard_3d: int = 0
    easy_7d: int = 0
    medium_7d: int = 0
    hard_7d: int = 0
    easy_14d: int = 0
    medium_14d: int = 0
    hard_14d: int = 0
    easy_28d_plus: int = 0
    medium_28d_plus: int = 0
    hard_28d_plus: int = 0
    last_solved_date: Optional[date]
    weighted_score: float

class ProblemRecommendation(BaseModel):
    leetcode_number: int
    title: str
    difficulty: str
    reason: str
    estimated_minutes: int
    leetcode_url: str

class DailyPlan(BaseModel):
    plan_date: date
    available_time_minutes: int
    focus_topic: str
    recommendations: List[ProblemRecommendation]
    ai_rationale: str
    is_cached: bool = False

class SyncResponse(BaseModel):
    new_problems: int
    new_submissions: int
    message: str
```



## Backend Dependencies (requirements.txt)

```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
pydantic==2.5.0
anthropic==0.7.0
python-dotenv==1.0.0
requests==2.31.0
```

---
