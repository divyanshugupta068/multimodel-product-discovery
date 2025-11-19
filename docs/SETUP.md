# Setup Guide

Complete setup instructions for the Multimodal Product Discovery Agent.

## Prerequisites

- Python 3.10 or higher
- Node.js 18 or higher
- PostgreSQL 14 or higher
- Git

## Installation Steps

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/multimodal-product-discovery.git
cd multimodal-product-discovery
```

### 2. Backend Setup

#### Create Virtual Environment

```bash
cd backend
python -m venv venv

# On Windows
venv\Scripts\activate

# On Mac/Linux
source venv/bin/activate
```

#### Install Dependencies

```bash
pip install -r requirements.txt
```

#### Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit .env with your API keys
# Required:
# - OPENAI_API_KEY
# - ANTHROPIC_API_KEY
# Optional:
# - DEEPGRAM_API_KEY
```

**Minimum Configuration (.env):**
```ini
OPENAI_API_KEY=sk-your-key-here
ANTHROPIC_API_KEY=sk-ant-your-key-here
DATABASE_URL=postgresql://user:password@localhost:5432/product_discovery
```

#### Setup Database

**Option A: Using Docker (Recommended)**

```bash
# Start PostgreSQL in Docker
docker run --name product-db \
  -e POSTGRES_USER=product_user \
  -e POSTGRES_PASSWORD=product_pass \
  -e POSTGRES_DB=product_discovery \
  -p 5432:5432 \
  -d postgres:14
```

**Option B: Local PostgreSQL Installation**

```bash
# Create database
createdb product_discovery

# Update DATABASE_URL in .env
DATABASE_URL=postgresql://your_user:your_password@localhost:5432/product_discovery
```

#### Initialize Database

```bash
# Run from project root
cd ..
python scripts/load_sample_data.py
```

This will:
- Create all database tables
- Initialize vector store
- Load sample products for testing

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Create environment file
cp .env.example .env.local

# Edit .env.local
# REACT_APP_API_URL=http://localhost:8000
```

### 4. Verify Installation

#### Test Backend

```bash
cd backend

# Run tests (if available)
pytest tests/

# Start development server
python -m uvicorn api.main:app --reload --port 8000
```

Visit http://localhost:8000/docs for interactive API documentation.

#### Test Frontend

```bash
cd frontend

# Start development server
npm start
```

Visit http://localhost:3000

## API Keys Setup

### OpenAI API Key

1. Go to https://platform.openai.com/api-keys
2. Create new API key
3. Add to `.env` as `OPENAI_API_KEY`

**Required for**:
- GPT-4 Vision (image processing)
- GPT-4 Turbo (intent classification, response generation)
- Whisper (speech-to-text)
- Text embeddings

**Estimated costs per 1000 queries**:
- GPT-4V: ~$10
- GPT-4 Turbo: ~$5
- Whisper: ~$6
- Embeddings: ~$0.10
- **Total: ~$21/1000 queries**

### Anthropic API Key

1. Go to https://console.anthropic.com/
2. Create API key
3. Add to `.env` as `ANTHROPIC_API_KEY`

**Required for**:
- Claude 3.5 Sonnet (fallback vision model)

**Estimated costs per 1000 queries**:
- Claude 3.5: ~$12/1000 images

### Deepgram API Key (Optional)

1. Go to https://console.deepgram.com/
2. Create API key
3. Add to `.env` as `DEEPGRAM_API_KEY`

**Required for**:
- Alternative speech-to-text (faster than Whisper)

**Estimated costs per 1000 queries**:
- Nova 2: ~$4/1000 minutes

## Running the Application

### Development Mode

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
python -m uvicorn api.main:app --reload --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm start
```

### Production Mode

**Backend:**
```bash
cd backend
source venv/bin/activate
uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

**Frontend:**
```bash
cd frontend
npm run build
# Serve build/ directory with nginx or similar
```

## Testing

### Run Unit Tests

```bash
cd backend
pytest tests/ -v
```

### Run Evaluation

```bash
cd backend
python -m evaluation.evaluator
```

This runs the comprehensive evaluation suite with 100+ test cases.

### Manual API Testing

**Text Query:**
```bash
curl -X POST http://localhost:8000/api/query/text \
  -H "Content-Type: application/json" \
  -d '{
    "query_text": "red leather jacket under $200",
    "query_type": "text",
    "max_results": 10
  }'
```

**Image Query:**
```bash
curl -X POST http://localhost:8000/api/query/image \
  -F "image=@/path/to/image.jpg" \
  -F "query_text=find similar products" \
  -F "max_results=5"
```

## Troubleshooting

### Database Connection Issues

**Error: "could not connect to server"**

Solution:
```bash
# Check PostgreSQL is running
# On Mac:
brew services start postgresql

# On Windows:
# Start PostgreSQL service from Services app

# On Docker:
docker start product-db
```

### Import Errors

**Error: "No module named 'langchain'"**

Solution:
```bash
# Ensure virtual environment is activated
source venv/bin/activate  # Windows: venv\Scripts\activate

# Reinstall dependencies
pip install -r requirements.txt
```

### API Key Errors

**Error: "Authentication failed"**

Solution:
1. Verify API keys in `.env` are correct
2. Check for extra spaces or quotes
3. Ensure `.env` file is in correct directory (backend/)
4. Restart server after changing `.env`

### ChromaDB Persistence Issues

**Error: "Collection already exists"**

Solution:
```bash
# Clear ChromaDB data
rm -rf backend/data/chroma_db

# Reload sample data
python scripts/load_sample_data.py
```

### Port Already in Use

**Error: "Address already in use"**

Solution:
```bash
# Find process using port 8000
# On Mac/Linux:
lsof -i :8000
kill -9 <PID>

# On Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

## Configuration Options

### Backend Configuration

Edit `backend/.env`:

```ini
# Model Selection
DEFAULT_VISION_MODEL=gpt-4-vision-preview
FALLBACK_VISION_MODEL=claude-3-5-sonnet-20240620
DEFAULT_TEXT_MODEL=gpt-4-turbo-preview
EMBEDDING_MODEL=text-embedding-3-small

# Feature Toggles
ENABLE_VISION_PROCESSING=true
ENABLE_SPEECH_PROCESSING=true
ENABLE_CACHING=true

# Performance
MAX_CONCURRENT_REQUESTS=10
REQUEST_TIMEOUT=30
CACHE_TTL=3600

# Logging
LOG_LEVEL=INFO
```

### Frontend Configuration

Edit `frontend/.env.local`:

```ini
REACT_APP_API_URL=http://localhost:8000
REACT_APP_MAX_IMAGE_SIZE=5242880  # 5MB
REACT_APP_MAX_AUDIO_SIZE=26214400  # 25MB
```

## Next Steps

1. **Test the API**: Try sample queries through the API docs (http://localhost:8000/docs)
2. **Load More Data**: Add your own products to the database
3. **Run Evaluation**: Benchmark performance with evaluation suite
4. **Customize**: Modify tools, models, or UI to fit your use case

## Support

For issues:
1. Check [ARCHITECTURE.md](ARCHITECTURE.md) for system details
2. Review [API Documentation](http://localhost:8000/docs)
3. Open GitHub issue with error details

## Quick Reference

**Start Everything:**
```bash
# Terminal 1
cd backend && source venv/bin/activate && python -m uvicorn api.main:app --reload

# Terminal 2
cd frontend && npm start
```

**Reset Database:**
```bash
python scripts/load_sample_data.py
```

**Run Tests:**
```bash
cd backend && pytest tests/ -v
```

**Check Logs:**
```bash
tail -f backend/logs/app.log
```
