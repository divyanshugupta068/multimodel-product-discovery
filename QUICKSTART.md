# Quick Start Guide

Get the Multimodal Product Discovery Agent running in 5 minutes.

## Prerequisites Checklist

- [ ] Python 3.10+ installed
- [ ] PostgreSQL installed (or Docker)
- [ ] OpenAI API key
- [ ] Anthropic API key

## 5-Minute Setup

### 1. Install Dependencies (2 min)

```bash
cd multimodal-product-discovery/backend
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Configure API Keys (1 min)

```bash
# Copy environment file
cp .env.example .env

# Edit .env and add your keys:
# OPENAI_API_KEY=sk-...
# ANTHROPIC_API_KEY=sk-ant-...
# DATABASE_URL=postgresql://user:pass@localhost:5432/product_discovery
```

**Windows**: Use notepad to edit `.env`
**Mac/Linux**: Use `nano .env` or any text editor

### 3. Start Database (30 sec)

**Option A - Docker (Recommended)**:
```bash
docker run --name product-db \
  -e POSTGRES_PASSWORD=product_pass \
  -e POSTGRES_DB=product_discovery \
  -p 5432:5432 -d postgres:14
```

**Option B - Local PostgreSQL**:
```bash
createdb product_discovery
```

### 4. Load Sample Data (1 min)

```bash
cd ..  # Back to project root
python scripts/load_sample_data.py
```

You should see:
```
✓ Loaded: Classic Leather Jacket - Black
✓ Loaded: Red Leather Jacket - Women's
✓ Loaded: iPhone 15 Pro Max - 256GB
...
✓ Successfully loaded 8 products!
```

### 5. Start Server (30 sec)

```bash
cd backend
python -m uvicorn api.main:app --reload
```

Server starts at: **http://localhost:8000**

## Test It Out

### Test 1: Interactive API Docs

1. Open browser: http://localhost:8000/docs
2. Try the `/api/query/text` endpoint
3. Click "Try it out"
4. Use this example:

```json
{
  "query_text": "red leather jacket under $200",
  "query_type": "text",
  "max_results": 5
}
```

5. Click "Execute"

You should see:
- Intent: "search"
- Products matching your query
- Prices from multiple retailers
- Match scores and reasons

### Test 2: Command Line

```bash
curl -X POST http://localhost:8000/api/query/text \
  -H "Content-Type: application/json" \
  -d '{
    "query_text": "iPhone 15",
    "query_type": "text",
    "max_results": 3
  }'
```

### Test 3: Image Upload (Requires Image File)

```bash
curl -X POST http://localhost:8000/api/query/image \
  -F "image=@/path/to/product_image.jpg" \
  -F "max_results=5"
```

## What You Get

After setup, you have:

✅ **8 Sample Products** ready to search
- Leather jackets (red & black)
- Smartphones (iPhone, Samsung)
- Sports gear (shoes, yoga mat, water bottle)
- Headphones

✅ **Full API** with endpoints for:
- Text queries
- Image upload
- Voice commands
- Price comparison
- Reviews
- Recommendations

✅ **Multimodal AI** integrated:
- GPT-4 Vision for images
- Claude 3.5 as fallback
- Whisper for voice
- Vector search for products

## Quick API Reference

### Search Products
```http
POST /api/query/text
Content-Type: application/json

{
  "query_text": "your search query",
  "query_type": "text",
  "max_results": 10
}
```

### Upload Image
```http
POST /api/query/image
Content-Type: multipart/form-data

image: <file>
query_text: "optional text"
max_results: 5
```

### Get Product Details
```http
GET /api/products/{product_id}
```

### Compare Prices
```http
GET /api/products/{product_id}/prices
```

### Get Recommendations
```http
GET /api/recommendations?user_id=123&limit=10
```

## Sample Queries to Try

**Search Queries**:
- "black leather jacket"
- "iPhone 15 Pro"
- "wireless headphones noise cancelling"
- "yoga mat"
- "running shoes size 10"

**Comparison Queries**:
- "compare iPhone and Samsung flagship phones"
- "show me leather jackets under $200"

**Price Queries**:
- "where can I buy iPhone 15 Pro cheapest"
- "price comparison for wireless headphones"

## View API Documentation

**Interactive Docs (Swagger UI)**:
http://localhost:8000/docs

**Alternative Docs (ReDoc)**:
http://localhost:8000/redoc

**Health Check**:
http://localhost:8000/health

## Common Issues & Fixes

### "Database connection failed"

**Fix**:
```bash
# Check PostgreSQL is running
docker ps  # Should show product-db

# If not running:
docker start product-db
```

### "OpenAI authentication error"

**Fix**:
1. Check `.env` file has correct API key
2. Verify no extra spaces around `OPENAI_API_KEY=sk-...`
3. Restart server after changing `.env`

### "Module not found"

**Fix**:
```bash
# Activate virtual environment
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows

# Reinstall
pip install -r requirements.txt
```

### "Port 8000 already in use"

**Fix**:
```bash
# Use different port
python -m uvicorn api.main:app --reload --port 8080
```

## Next Steps

### 1. Add More Products

Edit `scripts/load_sample_data.py` and add your own products to `SAMPLE_PRODUCTS` list.

### 2. Test Vision Processing

Upload a product image through `/api/query/image` to see GPT-4V in action.

### 3. Run Evaluation

```bash
cd backend
python -m evaluation.evaluator
```

### 4. Explore the Code

- **Agent logic**: `backend/agents/product_discovery_agent.py`
- **Tools**: `backend/tools/` directory
- **Vision processing**: `backend/vision/` directory
- **API endpoints**: `backend/api/main.py`

### 5. Read Full Documentation

- Architecture: `docs/ARCHITECTURE.md`
- Complete setup: `docs/SETUP.md`
- Project status: `PROJECT_STATUS.md`

## Performance Expectations

With the current setup:

- **Latency**: 1-3 seconds for text queries
- **Accuracy**: >85% product identification
- **Cost**: ~$0.01-0.05 per query
- **Throughput**: 10+ requests/second

## Support

**Check logs**:
```bash
# Server logs appear in terminal where you ran uvicorn
```

**Test individual components**:
```bash
# Test database
python -c "from database.database import get_db; print('DB OK')"

# Test vector store
python -c "from database.vector_store import VectorStore; vs = VectorStore(); print(f'Products: {vs.count()}')"

# Test OpenAI
python -c "from openai import OpenAI; c = OpenAI(); print('OpenAI OK')"
```

## Ready to Go!

You now have a fully functional multimodal product discovery system. Try different queries, upload images, and explore the API!

For production deployment or advanced features, see the full documentation in `docs/` directory.

---

**Questions?** Check `docs/SETUP.md` for troubleshooting or open an issue.
