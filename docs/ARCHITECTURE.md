# System Architecture

## Overview

The Multimodal Product Discovery Agent is a production-ready AI system that enables natural product search and discovery through images, voice, and text. Built with LangGraph for orchestration and integrated with GPT-4V, Claude 3.5, and Whisper.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend Layer (React)                    │
│  - Image Upload  - Voice Recording  - Text Input            │
└──────────────────────────┬──────────────────────────────────┘
                           │ REST API
┌──────────────────────────▼──────────────────────────────────┐
│                    API Layer (FastAPI)                       │
│  - Request Validation  - Response Formatting                │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│              Agent Orchestration (LangGraph)                 │
│  ┌────────────────────────────────────────────────────┐     │
│  │ 1. Input Processing  → 2. Intent Classification    │     │
│  │ 3. Tool Execution    → 4. Response Generation      │     │
│  └────────────────────────────────────────────────────┘     │
└──────────────────────────┬──────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
┌───────▼────────┐ ┌──────▼─────┐ ┌─────────▼────────┐
│ Vision Module  │ │Speech Module│ │  Tool Layer      │
│ - GPT-4V       │ │ - Whisper   │ │ - Product Search │
│ - Claude 3.5   │ │ - Deepgram  │ │ - Price Compare  │
└───────┬────────┘ └──────┬─────┘ │ - Inventory      │
        │                  │       │ - Recommendations│
        │                  │       │ - Review Analysis│
        │                  │       └─────────┬────────┘
        │                  │                 │
        └──────────────────┼─────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                    Data Layer                                │
│  ┌──────────────────┐  ┌──────────────────┐                │
│  │  PostgreSQL      │  │  ChromaDB        │                │
│  │  (Products,      │  │  (Vector Store)  │                │
│  │   Prices, etc)   │  │                  │                │
│  └──────────────────┘  └──────────────────┘                │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Input Processing Layer

**Vision Processing**
- **GPT-4V Integration**: Primary vision model for product identification
- **Claude 3.5 Sonnet**: Fallback/comparison model
- **Features**:
  - Extract visual features (color, style, brand)
  - Identify products from images
  - Generate search queries from visual analysis
  - Support for various image formats and qualities

**Speech Processing**
- **Whisper API**: Primary speech-to-text
- **Deepgram**: Optional alternative for faster processing
- **Features**:
  - Real-time transcription
  - Intent extraction from voice commands
  - Multi-language support
  - Background noise handling

**Text Processing**
- Direct text query support
- Entity extraction (brand, price, features)
- Query refinement and clarification

### 2. Agent Orchestration (LangGraph)

**State Management**
- Maintains conversation context across turns
- Tracks user preferences and browsing history
- Preserves multimodal context (image + voice + text)

**Workflow Stages**:
1. **Input Processing**: Handle multimodal inputs
2. **Intent Classification**: Determine user intent (search, compare, purchase, etc.)
3. **Tool Selection & Execution**: Choose and run appropriate tools
4. **Response Generation**: Create natural language response

**Decision Logic**:
- Parallel tool execution where possible
- Fallback strategies for failed API calls
- Caching for repeated queries

### 3. Tool Integration Layer

**Product Search Tool**
- Vector similarity search using embeddings
- SQL-based filtering (price, category, brand)
- Hybrid search combining semantic and keyword matching

**Price Comparison Tool**
- Multi-retailer price tracking
- Historical price analysis
- Deal detection and alerts

**Inventory Check Tool**
- Real-time availability checking
- Stock level tracking
- Alternative product suggestions for out-of-stock items

**Recommendation Engine**
- Collaborative filtering based on user behavior
- Content-based recommendations using product embeddings
- Trending products and bestsellers

**Review Analysis Tool**
- Sentiment analysis of customer reviews
- Key point extraction (pros/cons)
- Rating distribution and statistics

### 4. Data Layer

**PostgreSQL Schema**:
- `products`: Product catalog
- `price_history`: Time-series price data
- `reviews`: Customer reviews
- `users`: User profiles and preferences
- `search_history`: Query and interaction logs

**Vector Store (ChromaDB)**:
- Product embeddings for semantic search
- Fast similarity search (cosine distance)
- Metadata filtering support

## Data Flow

### Example: Image-based Product Search

```
1. User uploads image → API receives base64 image
2. Vision processor (GPT-4V) analyzes image
   → Extracts: "red leather jacket, women's, modern style"
3. Generate search queries: ["red leather jacket women's", "modern leather jacket"]
4. Vector store finds similar products using embeddings
5. SQL filter applies constraints (price, availability)
6. Results ranked by relevance score
7. LLM generates conversational response
8. Return structured response with ProductCard objects
```

## Performance Optimizations

### Latency Reduction
- **Parallel Execution**: Vision/speech processing + tool calls
- **Caching**: Redis for repeated queries (TTL: 1 hour)
- **Connection Pooling**: Database and API connections
- **Response Streaming**: Stream LLM responses for faster TTFB

### Cost Optimization
- **Model Selection**: Route to cheaper models when possible
- **Prompt Engineering**: Minimize token usage
- **Embedding Caching**: Reuse product embeddings
- **Batch Processing**: Batch API calls where applicable

### Scalability
- **Horizontal Scaling**: Stateless API servers
- **Database Indexing**: Optimized queries with proper indexes
- **Vector Store Sharding**: Distribute embeddings across nodes
- **Rate Limiting**: Protect against abuse

## Security Considerations

- **API Key Management**: Environment variables, never committed
- **Input Validation**: Pydantic models validate all inputs
- **SQL Injection Prevention**: SQLAlchemy ORM, parameterized queries
- **Rate Limiting**: Per-user and per-IP limits
- **CORS Configuration**: Whitelist allowed origins
- **Data Privacy**: No PII logging, GDPR compliance

## Monitoring & Observability

### Metrics Tracked
- **Latency**: P50, P95, P99 for each component
- **Accuracy**: Product ID precision, intent classification F1
- **Cost**: Per-query cost breakdown
- **Errors**: Error rates by type and component

### Logging
- Structured JSON logs (Loguru)
- Request/response tracing with correlation IDs
- Performance timings for each pipeline stage

### Alerting
- Latency exceeding thresholds
- Error rate spikes
- Cost anomalies
- API quota warnings

## Deployment Architecture

### Development
```
Local: FastAPI (reload) + React dev server
Database: PostgreSQL (Docker)
Vector Store: ChromaDB (local persist)
```

### Production
```
Frontend: Vercel (static React build)
Backend: AWS Lambda / Modal (serverless)
Database: AWS RDS PostgreSQL
Vector Store: Pinecone / Weaviate (managed)
Caching: Redis (AWS ElastiCache)
CDN: CloudFront for static assets
```

## API Specification

### Endpoints

**POST /api/query/text**
- Process text queries
- Input: `{query_text, filters, max_results}`
- Output: `QueryResponse` with products

**POST /api/query/image**
- Process image uploads
- Input: multipart/form-data with image file
- Output: `QueryResponse` with identified products

**POST /api/query/voice**
- Process voice commands
- Input: multipart/form-data with audio file
- Output: `QueryResponse` with transcription and results

**POST /api/query/multimodal**
- Process combined inputs
- Input: text + image + audio (any combination)
- Output: `QueryResponse` with unified results

## Extension Points

### Adding New Tools
1. Create tool class in `backend/tools/`
2. Implement required interface methods
3. Register tool in agent's tool selection logic
4. Add to evaluation test cases

### Adding New Models
1. Create processor in `backend/vision/` or `backend/speech/`
2. Implement standardized interface
3. Add to orchestrator for fallback/comparison
4. Update configuration options

### Custom Filters
1. Extend `QueryFilters` Pydantic model
2. Update vector store filter builder
3. Add SQL query modifications
4. Document filter options in API

## Testing Strategy

### Unit Tests
- Individual tool functions
- Model output parsing
- Database queries

### Integration Tests
- End-to-end API flows
- Multi-tool orchestration
- Error handling and retries

### Evaluation Tests
- Accuracy benchmarks (100+ scenarios)
- Latency profiling
- Cost analysis
- Model comparisons (GPT-4V vs Claude)

## Future Enhancements

1. **Fine-tuned Models**: Custom vision models for specific product categories
2. **Personalization**: User-specific ranking and preferences
3. **Multi-language**: Support for non-English queries
4. **AR Integration**: Virtual try-on features
5. **Social Features**: Share and collaborate on product searches
