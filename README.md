# MoD Semantic Search

A multimodal semantic search application for UK Ministry of Defence and Five Eyes users, enabling natural language queries across documents, audio files, and images related to military equipment and operations.

## 🎯 Overview

This demo application showcases semantic search capabilities across different data modalities:

- **PDF Documents**: Technical manuals, field reports, maintenance guides
- **Audio Files**: Briefings, training sessions, operational communications
- **Images**: Equipment photos, vehicle recognition, operational scenes

The system uses **Voyage AI embeddings** and **MongoDB Atlas Vector Search** to enable natural language queries like:
- "Show me documents about Challenger tanks"
- "Find audio related to artillery maintenance"
- "Search for images of armored vehicles"

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (HTML/JS)                   │
│  - Search Interface  - Upload Interface  - Results UI   │
└────────────────────┬────────────────────────────────────┘
                     │ REST API
┌────────────────────▼────────────────────────────────────┐
│              Backend (Python/FastAPI)                   │
│  - Search API  - Ingestion Logic  - Voyage AI Client   │
└────────────────────┬────────────────────────────────────┘
                     │
         ┌───────────┴───────────┐
         │                       │
┌────────▼─────────┐   ┌────────▼────────────┐
│  MongoDB Atlas   │   │   Voyage AI API     │
│  Vector Search   │   │   Embeddings        │
│  (MoD_Data)      │   │   (voyage-3)        │
└──────────────────┘   └─────────────────────┘
```

## 📋 Prerequisites

- Python 3.9+
- MongoDB Atlas account with Vector Search enabled
- Voyage AI API key
- Modern web browser

## 🚀 Setup Instructions

### 1. Clone and Navigate

```bash
cd ~/source/MoD_Semantic
```

### 2. Set Up Python Environment

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure MongoDB Atlas

1. **Create a MongoDB Atlas cluster** (if you haven't already):
   - Go to [MongoDB Atlas](https://cloud.mongodb.com)
   - Create a new cluster (M0 free tier works for testing)
   - Create a database user with read/write permissions
   - Whitelist your IP address (or use 0.0.0.0/0 for testing)

2. **Get your connection string**:
   - Click "Connect" on your cluster
   - Choose "Connect your application"
   - Copy the connection string (format: `mongodb+srv://...`)

3. **Create Vector Search Index**:
   - Navigate to your cluster → "Search" tab
   - Click "Create Search Index"
   - Choose "JSON Editor"
   - Use this configuration:

```json
{
  "fields": [
    {
      "type": "vector",
      "path": "embedding",
      "numDimensions": 1024,
      "similarity": "cosine"
    }
  ]
}
```

   - Name the index: `vector_index`
   - Database: `mod_semantic_search`
   - Collection: `MoD_Data`

### 4. Get Voyage AI API Key

1. Sign up at [Voyage AI](https://www.voyageai.com/)
2. Navigate to API Keys section
3. Create a new API key
4. Copy the key

### 5. Configure Environment Variables

Create a `.env` file in the project root:

```bash
cd ~/source/MoD_Semantic
cp .env.example .env
```

Edit `.env` with your credentials:

```env
# MongoDB Configuration
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority
MONGODB_DATABASE=mod_semantic_search
MONGODB_COLLECTION=MoD_Data

# Voyage AI Configuration
VOYAGE_API_KEY=your_actual_voyage_api_key
VOYAGE_MODEL=voyage-3

# Application Configuration
APP_HOST=0.0.0.0
APP_PORT=8000
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://localhost:8000

# Vector Search Configuration
VECTOR_INDEX_NAME=vector_index
VECTOR_DIMENSION=1024
```

### 6. Get the Media Assets

The demo media assets (PDFs, images, audio, video — ~795 MB) live in a private
S3 bucket (`s3://mod-semantic-demo/sample_data/`) rather than in git. You need
AWS credentials with read access to the bucket (`aws configure`).

There are two ways to use them:

**Option A: Fetch on demand from S3 (recommended, no download step)**

Set the S3 config in your `.env` (already the default in `.env.example`):

```bash
S3_BUCKET=mod-semantic-demo
S3_PREFIX=sample_data
FILE_CACHE_PATH=sample_data
AWS_REGION=us-east-2
```

The backend fetches any missing file from S3 the first time it is requested
and caches it locally under `FILE_CACHE_PATH`. Nothing to download up front.

**Option B: Download everything up front**

```bash
./scripts/download_assets.sh
```

This runs `aws s3 sync` into `sample_data/`. Use this if you want all assets
offline, or to seed the database from local files.

**Option C: Bring your own files**

Place your own files under `sample_data/` and describe them in a
`sample_data/manifest.json`, then seed (below).

### 7. Seed the Database

Run the seeding script to ingest sample data:

```bash
cd backend
python3 seed_database.py
```

This will:
- Extract text from PDFs
- Generate embeddings using Voyage AI
- Store documents with vectors in MongoDB
- Display ingestion statistics

**Expected output:**
```
============================================================
MoD Semantic Search - Database Seeding
============================================================

[1/5] Loading configuration...
  ✓ Database: mod_semantic_search
  ✓ Collection: MoD_Data
  ✓ Voyage Model: voyage-3

[2/5] Initializing services...
  ✓ MongoDB connected
  ✓ Voyage AI initialized

[3/5] Checking existing data...
  → Collection is empty

[4/5] Loading manifest...
  ✓ Found manifest: .../sample_data/manifest.json

[5/5] Ingesting documents...
  This may take a few minutes...

============================================================
Seeding Complete!
============================================================

  Total processed: 15
  ✓ Successfully ingested: 15
  ✗ Failed: 0

  By modality:
    • PDFs: 5
    • Audio: 5
    • Images: 5

  Total documents in collection: 15

✓ Database seeding successful!
```

### 8. Start the Backend

```bash
cd backend
source venv/bin/activate  # If not already activated
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

**Test the API:**
```bash
curl http://localhost:8000/health
```

### 9. Open the Frontend

Open the frontend in your browser:

```bash
# Option 1: Direct file access
open frontend/index.html  # macOS
xdg-open frontend/index.html  # Linux
start frontend/index.html  # Windows

# Option 2: Use a local web server
cd frontend
python3 -m http.server 3000
# Then open http://localhost:3000
```

## 🔍 Using the Application

### Search Tab

1. **Enter a natural language query** in the search box:
   - "Show me documents about Challenger tanks"
   - "Find information on 120mm gun systems"
   - "Search for artillery maintenance procedures"

2. **Filter by modality** (optional):
   - All (default)
   - PDFs only
   - Audio only
   - Images only

3. **View results**:
   - Results are ranked by semantic similarity
   - Each result shows: title, modality, relevance score, preview, tags, source file

### Upload Tab

1. **Select a file** to upload
2. **Enter metadata**:
   - Title
   - Type (PDF, Audio, or Image)
   - Tags (comma-separated)
   - Caption (for images) or Transcript (for audio)

3. **Click "Upload & Embed"**
4. The document will be:
   - Processed and embedded
   - Added to the database
   - Immediately searchable

## 📊 API Endpoints

### GET /health
Health check endpoint

**Response:**
```json
{
  "status": "healthy",
  "mongodb_connected": true,
  "voyage_configured": true,
  "timestamp": "2024-06-25T10:30:00Z"
}
```

### GET /config-status
Configuration status

### POST /search
Perform semantic search

**Request:**
```json
{
  "query": "Challenger tank maintenance",
  "modality": "all",
  "top_k": 10
}
```

**Response:**
```json
{
  "query": "Challenger tank maintenance",
  "results": [
    {
      "_id": "...",
      "title": "Challenger 2 Main Battle Tank Technical Overview",
      "modality": "pdf",
      "score": 0.8543,
      "preview": "...",
      "tags": ["tanks", "challenger", "technical"],
      "source_file": "challenger2_technical.pdf",
      "metadata": {}
    }
  ],
  "total": 5,
  "modality_filter": "all"
}
```

### POST /upload
Upload and embed a document

**Form Data:**
- `file`: File to upload
- `title`: Document title
- `modality`: Type (pdf/audio/image)
- `tags`: Comma-separated tags
- `caption`: Image caption (if image)
- `transcript`: Audio transcript (if audio)

## 🧪 Testing

### Test Search Queries

```bash
# Test semantic search
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "artillery fire support procedures",
    "modality": "all",
    "top_k": 5
  }'
```

### Example Queries

1. **Equipment queries:**
   - "Challenger 2 tank specifications"
   - "AS90 artillery system"
   - "120mm ammunition types"

2. **Maintenance queries:**
   - "tank maintenance procedures"
   - "artillery servicing requirements"
   - "daily vehicle inspections"

3. **Operational queries:**
   - "fire support coordination"
   - "convoy procedures"
   - "communications protocols"

4. **Visual queries:**
   - "desert camouflage vehicles"
   - "armored vehicle formations"
   - "artillery in firing position"

## 🔧 Troubleshooting

### MongoDB Connection Issues

**Problem:** Can't connect to MongoDB Atlas

**Solutions:**
- Verify your connection string in `.env`
- Check IP whitelist in Atlas (Security → Network Access)
- Ensure database user has correct permissions
- Test connection: `mongosh "your_connection_string"`

### Vector Search Not Working

**Problem:** Search returns no results or errors

**Solutions:**
- Verify vector index is created in Atlas (see Setup step 3)
- Check index name matches `VECTOR_INDEX_NAME` in `.env`
- Ensure documents have been seeded (`python3 seed_database.py`)
- Verify embedding dimension is 1024 (voyage-3 default)

### Voyage AI Errors

**Problem:** Embedding generation fails

**Solutions:**
- Verify API key is correct in `.env`
- Check your Voyage AI account has available credits
- Test API key: `curl -H "Authorization: Bearer YOUR_KEY" https://api.voyageai.com/v1/models`

### CORS Errors in Frontend

**Problem:** Frontend can't reach backend API

**Solutions:**
- Ensure backend is running on port 8000
- Check `CORS_ORIGINS` in `.env` includes your frontend URL
- Try accessing API directly: `curl http://localhost:8000/health`

### Seeding Fails

**Problem:** `seed_database.py` throws errors

**Solutions:**
- Ensure sample data files exist (run `create_sample_data.py`)
- Check file paths in `manifest.json`
- Verify MongoDB connection works
- Check Voyage AI API key and credits

## 📁 Project Structure

```
MoD_Semantic/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI application
│   │   ├── config.py            # Configuration management
│   │   ├── models.py            # Pydantic models
│   │   ├── database.py          # MongoDB connection
│   │   ├── embeddings.py        # Voyage AI client
│   │   ├── search.py            # Vector search logic
│   │   └── ingestion.py         # Data ingestion
│   ├── requirements.txt         # Python dependencies
│   └── seed_database.py         # Database seeding script
├── frontend/
│   ├── index.html               # Main UI
│   ├── styles.css               # Styling
│   └── app.js                   # Frontend logic
├── sample_data/
│   ├── manifest.json            # Data metadata
│   ├── README.txt              # Data documentation
│   ├── pdfs/                   # PDF documents
│   ├── audio/                  # Audio files
│   └── images/                 # Image files
├── scripts/
│   └── create_sample_data.py   # Sample data generator
├── .env                         # Environment variables (create from .env.example)
├── .env.example                # Environment template
├── .gitignore
└── README.md                   # This file
```

## 🔐 Security Notes

**For Production Deployment:**

1. **Environment Variables:**
   - Never commit `.env` to version control
   - Use secure secret management (AWS Secrets Manager, Azure Key Vault, etc.)

2. **MongoDB:**
   - Use specific IP whitelisting (not 0.0.0.0/0)
   - Enable authentication and TLS/SSL
   - Use least-privilege database users

3. **API Security:**
   - Add authentication (JWT tokens, OAuth)
   - Implement rate limiting
   - Use HTTPS only
   - Validate and sanitize all inputs

4. **CORS:**
   - Restrict `CORS_ORIGINS` to specific domains
   - Don't use wildcards in production

5. **Data:**
   - This demo uses unclassified public data only
   - For real MoD use: implement proper access controls, classification handling, and audit logging

## 🎓 Key Assumptions

1. **Embeddings:** Using Voyage AI's `voyage-3` model (1024 dimensions) for all modalities
2. **Audio Processing:** Transcripts are provided in the manifest; automatic transcription is not implemented
3. **Image Processing:** Captions are provided in the manifest; automatic captioning is not implemented
4. **PDF Text Extraction:** Using PyPDF2 for text extraction (simple PDFs only)
5. **Sample Data:** All content is unclassified and for demonstration purposes only
6. **Scalability:** This is a demo; production deployments would need connection pooling, caching, and load balancing

## 🚀 Future Enhancements

- Automatic audio transcription (Whisper API)
- Automatic image captioning (CLIP, GPT-4 Vision)
- Advanced filtering (date ranges, classification levels)
- User authentication and access control
- Document versioning
- Export search results
- Analytics dashboard
- Batch upload interface
- RESTful pagination for large result sets

## 📝 License

This is a demonstration project for educational purposes.

## 🤝 Support

For issues or questions:
1. Check the Troubleshooting section above
2. Review MongoDB Atlas and Voyage AI documentation
3. Verify all environment variables are set correctly
4. Check application logs for detailed error messages

## ✅ Success Criteria

The application is working correctly when:

1. ✓ Backend starts without errors on port 8000
2. ✓ `/health` endpoint returns all services as healthy
3. ✓ Database contains seeded documents
4. ✓ Frontend loads in browser
5. ✓ Natural language queries return relevant results
6. ✓ Results are ranked by semantic similarity
7. ✓ Manual upload works for all modalities
8. ✓ Filters (PDF/Audio/Image) work correctly

---

**Built with:** Python • FastAPI • MongoDB Atlas • Voyage AI • Vanilla JavaScript
