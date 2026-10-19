#!/usr/bin/env bash
set -e

echo "Starting LedgerLens Backend (FastAPI)..."
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 &

echo "Starting LedgerLens Frontend & Mastra Orchestrator (Node.js)..."
node frontend/server.js
