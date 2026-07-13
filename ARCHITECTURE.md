# MoD Semantic Search - Architecture Documentation

## System Architecture

### High-Level Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                          │
│                    (Browser-based Frontend)                     │
│                                                                 │
│  ┌───────────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │ Search Tab    │  │ Upload Tab   │  │ Results Display   │  │
│  │ - Query Input │  │ - File Upload│  │ - Ranked Results  │  │
│  │ - Filters     │  │ - Metadata   │  │ - Preview Cards   │  │
│  └───────────────┘  └──────────────┘  └───────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP/REST API
┌────────────────────────────▼────────────────────────────────────┐
│                     APPLICATION LAYER                           │
│                    (FastAPI Python Backend)                     │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐ │
│  │ Search API   │  │ Upload API   │  │ Health/Config APIs   │ │
│  │ /search      │  │ /upload      │  │ /health /config      │ │
│  └──────┬───────┘  └──────┬───────┘  └──────────────────────┘ │
│         │                  │                                    │
│  ┌──────▼──────────────────▼───────────────────────────────┐  │
│  │           Business Logic Layer                          │  │
│  │  - Vector Search Service                                │  │
│  │  - Data Ingestion Service                               │  │
│  │  - Embedding Generation                                 │  │
│  │  - PDF Text Extraction                                  │  │
│  └─────────────┬──────────────────┬────────────────────────┘  │
└────────────────┼──────────────────┼────────────────────────────┘
                 │                  │
         ┌───────▼─────┐    ┌──────▼──────┐
         │   MongoDB   │    │  Voyage AI  │
         │   Atlas     │    │  Embedding  │
         │             │    │  Service    │
         │ ┌─────────┐ │    │             │
         │ │MoD_Data │ │    │  voyage-3   │
         │ │Collection│ │    │  Model      │
         │ └─────────┘ │    │  (1024-dim) │
         │             │    │             │
         │ Vector      │    └─────────────┘
         │ Search      │
         │ Index       │
         └─────────────┘
```

## Component Details

### 1. Frontend Layer (HTML/CSS/JavaScript)

**Purpose**: User-facing interface for search and data upload

**Components**:
- `index.html`: Main application structure with two tabs
- `styles.css`: Defense-oriented styling with military color scheme
- `app.js`: Client-side logic, API calls, UI state management

**Key Features**:
- Real-time search with natural language queries
- Modality filtering (All, PDF, Audio, Image)
- Manual document upload with metadata
- Results visualization with scoring and previews

**Technology Stack**:
- Vanilla JavaScript (no frameworks)
- Fetch API for backend communication
- CSS Grid/Flexbox for responsive layout

### 2. API Layer (FastAPI)

**Purpose**: RESTful API serving search and ingestion requests

**File**: `backend/app/main.py`

**Endpoints**:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Health check and service status |
| `/config-status` | GET | Configuration verification |
| `/search` | POST | Semantic search query |
| `/upload` | POST | Manual document upload |
| `/` | GET | API information |

**Key Features**:
- CORS middleware for cross-origin requests
- Pydantic models for request/response validation
- Async/await for non-blocking operations
- Comprehensive error handling
- Structured logging

### 3. Business Logic Layer

#### 3.1 Configuration Management (`config.py`)

**Purpose**: Environment variable management and validation

**Features**:
- Pydantic Settings for type-safe configuration
- `.env` file loading
- Configuration validation on startup
- Sensible defaults for optional settings

#### 3.2 Database Layer (`database.py`)

**Purpose**: MongoDB Atlas connection management

**Features**:
- Connection pooling via PyMongo
- Health check capabilities
- Collection access abstraction
- Connection lifecycle management

**Key Methods**:
- `connect()`: Establish database connection
- `disconnect()`: Clean shutdown
- `is_connected()`: Connection status check
- `collection`: Direct access to MoD_Data collection

#### 3.3 Embeddings Service (`embeddings.py`)

**Purpose**: Voyage AI integration for vector generation

**Features**:
- Voyage AI client wrapper
- Document vs. query embedding differentiation
- Batch embedding support
- Error handling and logging

**Key Methods**:
- `embed_text(text)`: Single text embedding
- `embed_texts(texts)`: Batch embedding
- `embed_query(query)`: Query-optimized embedding

**Embedding Model**: `voyage-3`
- Dimension: 1024
- Optimized for semantic search
- Separate input types for documents and queries

#### 3.4 Vector Search Service (`search.py`)

**Purpose**: MongoDB Atlas Vector Search execution

**Features**:
- Query embedding generation
- Vector similarity search
- Modality filtering
- Result ranking and formatting

**Search Pipeline**:
1. Generate query embedding via Voyage AI
2. Build MongoDB aggregation pipeline
3. Execute $vectorSearch with filters
4. Project relevant fields with scores
5. Format results for frontend

**Search Parameters**:
- `query`: Natural language search text
- `modality`: Filter by data type (all/pdf/audio/image)
- `top_k`: Number of results (1-100)

#### 3.5 Ingestion Service (`ingestion.py`)

**Purpose**: Multimodal data processing and storage

**Features**:
- PDF text extraction (PyPDF2)
- Searchable text composition
- Embedding generation
- MongoDB document creation
- Manifest-based batch ingestion

**Data Flow**:
1. Extract content based on modality:
   - PDF → Extract text from file
   - Audio → Use provided transcript
   - Image → Use provided caption
2. Compose searchable text (title + tags + content)
3. Generate embedding via Voyage AI
4. Create preview snippet
5. Store in MongoDB with metadata

### 4. Data Models (`models.py`)

**Pydantic Models**:

- `SearchRequest`: Search query payload
- `SearchResult`: Individual result item
- `SearchResponse`: Complete search response
- `DocumentUpload`: Upload metadata
- `DocumentRecord`: MongoDB document schema
- `HealthResponse`: Health check response
- `ConfigStatusResponse`: Configuration status

**Benefits**:
- Type safety
- Automatic validation
- JSON serialization
- API documentation generation

### 5. Data Layer

#### 5.1 MongoDB Atlas

**Collection**: `MoD_Data`

**Document Schema**:
```json
{
  "_id": ObjectId,
  "title": "string",
  "modality": "pdf|audio|image",
  "source_file": "string",
  "text_content": "string | null",
  "transcript": "string | null",
  "image_caption": "string | null",
  "preview": "string",
  "tags": ["string"],
  "metadata": {object},
  "embedding": [float],  // 1024 dimensions
  "created_at": ISODate
}
```

**Vector Search Index**: `vector_index`
```json
{
  "fields": [{
    "type": "vector",
    "path": "embedding",
    "numDimensions": 1024,
    "similarity": "cosine"
  }]
}
```

#### 5.2 Voyage AI

**Model**: `voyage-3`
- **Dimensions**: 1024
- **Context Window**: 16,000 tokens
- **Similarity Metric**: Cosine similarity
- **Input Types**: document vs. query optimization

## Data Flow

### Search Flow

```
1. User enters query in frontend
   ↓
2. Frontend sends POST /search with query text
   ↓
3. Backend generates query embedding (Voyage AI)
   ↓
4. Vector search executed against MongoDB
   ↓
5. Results ranked by cosine similarity
   ↓
6. Results formatted and returned to frontend
   ↓
7. Frontend displays ranked results with previews
```

### Ingestion Flow

```
1. File + metadata submitted via upload form
   ↓
2. Backend receives multipart/form-data
   ↓
3. Content extracted based on modality:
   - PDF: PyPDF2 text extraction
   - Audio: Transcript from form
   - Image: Caption from form
   ↓
4. Searchable text composed (title + tags + content)
   ↓
5. Document embedding generated (Voyage AI)
   ↓
6. Document stored in MongoDB with embedding
   ↓
7. Confirmation returned to frontend
   ↓
8. Document immediately searchable
```

## Security Considerations

### Current Implementation (Demo)

- CORS enabled for local development
- No authentication/authorization
- Environment variables for sensitive data
- Input validation via Pydantic

### Production Requirements

1. **Authentication**:
   - JWT token-based authentication
   - Role-based access control (RBAC)
   - API key management

2. **Authorization**:
   - Document-level access control
   - Classification-based filtering
   - Audit logging

3. **Network Security**:
   - HTTPS/TLS only
   - IP whitelisting
   - Rate limiting

4. **Data Security**:
   - Encryption at rest (MongoDB)
   - Encryption in transit (TLS)
   - Secure secret management

5. **Input Validation**:
   - File type verification
   - Size limits
   - Content scanning
   - SQL injection prevention

## Scalability Considerations

### Current Limitations (Demo)

- Single-instance backend
- No caching layer
- Synchronous processing
- Limited error recovery

### Production Enhancements

1. **Horizontal Scaling**:
   - Load balancer (NGINX, AWS ALB)
   - Multiple FastAPI instances
   - Stateless application design

2. **Caching**:
   - Redis for query results
   - CDN for static assets
   - Embedding cache for common queries

3. **Asynchronous Processing**:
   - Message queue (RabbitMQ, AWS SQS)
   - Background workers for ingestion
   - Batch embedding generation

4. **Database Optimization**:
   - MongoDB connection pooling
   - Read replicas for search
   - Sharding for large datasets

5. **Monitoring**:
   - Application metrics (Prometheus)
   - Logging aggregation (ELK Stack)
   - Distributed tracing (Jaeger)
   - Alerting (PagerDuty)

## Technology Choices - Rationale

| Technology | Purpose | Rationale |
|------------|---------|-----------|
| FastAPI | Backend Framework | Fast, modern, automatic API docs, async support |
| PyMongo | MongoDB Driver | Official driver, mature, well-documented |
| Voyage AI | Embeddings | State-of-art semantic embeddings, optimized for search |
| MongoDB Atlas | Vector Database | Managed service, vector search built-in, scalable |
| Vanilla JS | Frontend | Simple demo, no build step, easy to understand |
| Pydantic | Validation | Type safety, automatic validation, clear schemas |
| PyPDF2 | PDF Processing | Lightweight, pure Python, sufficient for demo |

## Assumptions and Trade-offs

### Assumptions

1. **Audio transcripts provided**: No automatic speech recognition
2. **Image captions provided**: No automatic image captioning
3. **Simple PDFs**: Text-based PDFs, not scanned documents
4. **Unclassified data**: No classification handling or need-to-know controls
5. **English language**: No multi-language support
6. **Small dataset**: Demo-scale with 15 documents

### Trade-offs

1. **No OCR**: Scanned PDFs won't be searchable
   - **Alternative**: Add Tesseract OCR for scanned documents

2. **Manual transcripts**: Audio files require manual transcription
   - **Alternative**: Integrate Whisper API for automatic transcription

3. **Manual captions**: Images require manual descriptions
   - **Alternative**: Use CLIP or GPT-4 Vision for automatic captioning

4. **Synchronous uploads**: Large files block during processing
   - **Alternative**: Implement async processing with job queue

5. **In-memory processing**: Files processed in memory
   - **Alternative**: Stream processing for large files

6. **No versioning**: Documents can't be updated, only replaced
   - **Alternative**: Add version tracking and history

## Future Enhancements

1. **Advanced Search**:
   - Faceted search
   - Date range filtering
   - Advanced boolean queries
   - Saved searches

2. **Content Processing**:
   - Automatic transcription (Whisper)
   - Automatic image captioning (CLIP/GPT-4V)
   - OCR for scanned documents (Tesseract)
   - Video support

3. **User Features**:
   - User accounts and profiles
   - Search history
   - Bookmarks/favorites
   - Export functionality

4. **Analytics**:
   - Search analytics dashboard
   - Popular queries
   - Usage statistics
   - Quality metrics

5. **Integration**:
   - SharePoint integration
   - Email notifications
   - Slack/Teams integration
   - RESTful webhooks

6. **Administration**:
   - Admin dashboard
   - User management
   - Document management
   - System monitoring
