# MongoDB Atlas Setup Guide

Follow these steps to configure your MongoDB Atlas connection.

## ✅ Connection Configuration

Create a `.env` file (copy from `.env.example`) and set your connection details:
```
MONGODB_URI=mongodb+srv://<username>:<password>@<cluster>.mongodb.net/?retryWrites=true&w=majority
MONGODB_DATABASE=mod_semantic_search
MONGODB_COLLECTION=MoD_Data
```

## 📋 Next Steps

### Step 1: Verify Connection

Test your MongoDB Atlas connection:

```bash
cd ~/source/MoD_Semantic
python3 scripts/verify_atlas_setup.py
```

This will check:
- MongoDB connection
- Database and collection access
- Current document count

### Step 2: Create Vector Search Index

**IMPORTANT**: The vector search index MUST be created through the Atlas UI.

Run this script to get the configuration:

```bash
python3 scripts/create_atlas_vector_index.py
```

Then follow these steps:

1. **Go to MongoDB Atlas**: https://cloud.mongodb.com/
2. **Select your cluster**: Cluster0
3. **Click "Search" tab** (not "Browse Collections")
4. **Click "Create Search Index"**
5. **Select "JSON Editor"**
6. **Paste this configuration**:

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

7. **Set these values**:
   - Index Name: `vector_index`
   - Database: `mod_semantic_search`
   - Collection: `MoD_Data`

8. **Click "Create Search Index"**

9. **Wait 1-2 minutes** for the index to build

### Step 3: Verify Index Creation

After creating the index, verify it:

```bash
python3 scripts/verify_atlas_setup.py
```

If the vector search test passes, you're ready to go!

### Step 4: Configure Voyage AI

You still need to add your Voyage AI API key to `.env`:

```bash
nano .env
```

Replace `your_voyage_api_key_here` with your actual Voyage AI API key.

Get a key at: https://www.voyageai.com/

### Step 5: Create Sample Data

```bash
python3 scripts/create_sample_data.py
```

### Step 6: Seed the Database

```bash
cd backend
python3 seed_database.py
```

This will:
- Extract text from PDFs for embedding generation
- Generate 1024-dimensional embeddings via Voyage AI
- Store **only** embeddings, metadata, and file references in MongoDB
- **NOT** store full text content (saves space!)

### Step 7: Start the Application

```bash
cd ~/source/MoD_Semantic
./RUN.sh
```

Or start manually:

```bash
# Terminal 1 - Backend
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 - Frontend
cd frontend
python3 -m http.server 3000
```

Then open: http://localhost:3000

## 🔍 Architecture Change: File References Only

The project has been updated to use a more efficient architecture:

### What's Stored in MongoDB:
✅ Document embeddings (1024 dimensions)
✅ Metadata (title, tags, modality, dates)
✅ Preview snippets
✅ **File paths/URLs** (references to actual files)

### What's NOT Stored in MongoDB:
❌ Full PDF text content
❌ Full audio transcripts
❌ Full image captions

### Why This Is Better:
- **Smaller database**: Embeddings only, not full text
- **Faster queries**: Less data to transfer
- **Flexible storage**: Files can be on disk, S3, or any file system
- **Cost effective**: Cheaper MongoDB storage costs
- **Scalable**: Easy to move files to CDN or object storage

### How It Works:
1. During ingestion, text is extracted temporarily for embedding generation
2. Embedding is generated and stored in MongoDB
3. Original file stays on disk (or object storage)
4. MongoDB stores just the file path/URL
5. When users want the file, they access it via the file path

## 🧪 Testing

### Test Connection
```bash
python3 scripts/verify_atlas_setup.py
```

### Test API
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "mongodb_connected": true,
  "voyage_configured": true,
  "timestamp": "..."
}
```

### Test Search
```bash
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "Challenger tank maintenance", "top_k": 5}'
```

## ⚠️ Troubleshooting

### "MongoDB connection failed"
- Check your connection string in `.env`
- Verify you can access: https://cloud.mongodb.com/
- Ensure your IP is whitelisted in Network Access

### "Vector search index not found"
- Make sure you created the index in Atlas UI (Step 2 above)
- Wait 1-2 minutes after creation
- Check the Search tab in Atlas to see index status

### "Voyage AI error"
- Add your API key to `.env`
- Verify it at: https://www.voyageai.com/
- Check you have available credits

## 📚 File Serving

Files are served via the `/files` endpoint:

- PDFs: `http://localhost:8000/files/pdfs/document.pdf`
- Audio: `http://localhost:8000/files/audio/file.mp3`
- Images: `http://localhost:8000/files/images/photo.jpg`

This is configured in `backend/app/main.py` using FastAPI's StaticFiles.

## 🎯 Summary

1. ✅ MongoDB connection configured
2. ⏳ Create vector search index in Atlas UI
3. ⏳ Add Voyage AI key to `.env`
4. ⏳ Create sample data
5. ⏳ Seed database
6. ⏳ Start application

**Current Status**: Connection configured, ready for vector index creation!
