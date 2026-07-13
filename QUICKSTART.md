# Quick Start Guide

Get the MoD Semantic Search application running in 15 minutes.

## Prerequisites Checklist

- [ ] Python 3.9 or higher installed
- [ ] MongoDB Atlas account created
- [ ] Voyage AI API key obtained
- [ ] Modern web browser available

## Step-by-Step Setup

### 1. Install Python Dependencies (2 minutes)

```bash
cd ~/source/MoD_Semantic/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. MongoDB Atlas Setup (5 minutes)

**Create Cluster:**
1. Go to https://cloud.mongodb.com
2. Create M0 Free cluster (or use existing)
3. Create database user: Database Access → Add User
4. Whitelist IP: Network Access → Add IP (use 0.0.0.0/0 for testing)

**Get Connection String:**
1. Cluster → Connect → Connect your application
2. Copy connection string (looks like: `mongodb+srv://...`)

**Create Vector Index:**
1. Cluster → Search tab → Create Search Index
2. Select JSON Editor
3. Paste this configuration:

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

4. Index name: `vector_index`
5. Database: `mod_semantic_search`
6. Collection: `MoD_Data`
7. Click Create

### 3. Get Voyage AI Key (2 minutes)

1. Visit https://www.voyageai.com/
2. Sign up / Log in
3. Go to API Keys section
4. Create new API key
5. Copy the key

### 4. Configure Environment (1 minute)

```bash
cd ~/source/MoD_Semantic
cp .env.example .env
nano .env  # or use your preferred editor
```

Edit `.env` with your credentials:
```env
MONGODB_URI=mongodb+srv://YOUR_USER:YOUR_PASSWORD@YOUR_CLUSTER.mongodb.net/?retryWrites=true&w=majority
VOYAGE_API_KEY=your_voyage_api_key_here
```

Save and close.

### 5. Create Sample Data (1 minute)

```bash
cd ~/source/MoD_Semantic
python3 scripts/create_sample_data.py
```

This creates placeholder PDF files with relevant content.

### 6. Seed Database (2 minutes)

```bash
cd backend
python3 seed_database.py
```

Wait for "✓ Database seeding successful!" message.

### 7. Start Backend (30 seconds)

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Keep this terminal open. You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 8. Open Frontend (30 seconds)

Open a new terminal:

```bash
cd ~/source/MoD_Semantic/frontend
python3 -m http.server 3000
```

Open browser to: http://localhost:3000

## Quick Test

1. **Search Tab**: Enter query "Challenger tank maintenance"
2. Click Search button
3. You should see relevant results about tanks and maintenance

**Try these queries:**
- "artillery fire support"
- "120mm ammunition"
- "desert operations"
- "vehicle recognition"

## Troubleshooting

### "MongoDB connection failed"
- Check your connection string in `.env`
- Verify IP is whitelisted in Atlas (Network Access)
- Test with: `mongosh "your_connection_string"`

### "No results found"
- Ensure seeding completed successfully
- Check vector index is created in Atlas (Search tab)
- Verify index name is `vector_index`

### "Voyage AI error"
- Verify API key in `.env` is correct
- Check account has available credits at voyageai.com

### "CORS error in browser"
- Ensure backend is running on port 8000
- Check browser console for exact error
- Try: `curl http://localhost:8000/health`

### "ImportError" when running scripts
- Ensure virtual environment is activated: `source venv/bin/activate`
- Reinstall dependencies: `pip install -r requirements.txt`

## Next Steps

### Upload Your Own Data

1. Click "Upload Data" tab
2. Select a file (PDF, audio, or image)
3. Fill in title, type, and tags
4. For audio: add transcript
5. For images: add caption
6. Click "Upload & Embed"

### Explore the API

```bash
# Health check
curl http://localhost:8000/health

# Search request
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "tank maintenance", "top_k": 5}'
```

### Read Documentation

- `README.md` - Complete documentation
- `ARCHITECTURE.md` - System design and architecture
- `sample_data/README.txt` - Data information

## Production Deployment

For production use, review:
1. Security section in README.md
2. Environment variable management
3. CORS configuration
4. Authentication implementation
5. MongoDB IP whitelisting
6. HTTPS/TLS setup

## Support

If you encounter issues:
1. Check the Troubleshooting section above
2. Review logs in terminal windows
3. Verify all prerequisites are met
4. Check README.md for detailed information

---

**Estimated Total Time**: 15 minutes

**Note**: Times are approximate. First-time setup of MongoDB Atlas or Voyage AI account may take longer.
