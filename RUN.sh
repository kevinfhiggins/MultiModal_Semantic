#!/bin/bash
# Quick run script for MoD Semantic Search

echo "🚀 MoD Semantic Search - Quick Start"
echo "======================================"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found"
    echo "   Please copy .env.example to .env and configure it"
    echo "   Command: cp .env.example .env"
    exit 1
fi

echo "✅ Environment file found"
echo ""

# Check if venv exists
if [ ! -d backend/venv ]; then
    echo "⚙️  Creating Python virtual environment..."
    cd backend
    python3 -m venv venv
    cd ..
fi

# Activate venv and check dependencies
echo "⚙️  Checking Python dependencies..."
source backend/venv/bin/activate
pip install -q -r backend/requirements.txt

echo ""
echo "Starting services..."
echo "==================="
echo ""

# Start backend
echo "🔧 Starting backend on port 8000..."
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

# Wait for backend to start
sleep 3

# Start frontend
echo "🌐 Starting frontend on port 3000..."
cd frontend
python3 -m http.server 3000 &
FRONTEND_PID=$!
cd ..

echo ""
echo "✅ Services started!"
echo "==================="
echo ""
echo "🔗 Backend API: http://localhost:8000"
echo "🔗 Frontend UI: http://localhost:3000"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Wait for interrupt
trap "echo ''; echo 'Stopping services...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT
wait
