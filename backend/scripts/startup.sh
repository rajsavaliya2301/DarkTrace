#!/bin/bash
set -e

echo "=== DarkTrace Startup Script ==="

# Read auth from environment (with defaults matching docker-compose)
MONGO_URI="${MONGODB_URI:-mongodb://darktrace:darktrace_pass@mongodb:27017/darktrace?authSource=admin}"
ES_HOSTS="${ELASTICSEARCH_HOSTS:-http://elasticsearch:9200}"
ES_USER="${ELASTICSEARCH_USERNAME:-elastic}"
ES_PASS="${ELASTICSEARCH_PASSWORD:-darktrace_es_pass}"
REDIS_URI="${REDIS_URI:-redis://:darktrace_redis_pass@redis:6379/0}"
NEO4J_URI="${NEO4J_URI:-bolt://neo4j:7687}"
NEO4J_USER="${NEO4J_USERNAME:-neo4j}"
NEO4J_PASS="${NEO4J_PASSWORD:-darktrace_neo4j_pass}"

# Wait for dependent services
echo "Waiting for MongoDB..."
until python -c "from pymongo import MongoClient; MongoClient('$MONGO_URI').admin.command('ping')" 2>/dev/null; do
  sleep 2
done
echo "MongoDB is ready."

echo "Waiting for Elasticsearch..."
until python -c "from elasticsearch import Elasticsearch; es = Elasticsearch(['$ES_HOSTS'], basic_auth=('$ES_USER','$ES_PASS')); assert es.ping()" 2>/dev/null; do
  sleep 2
done
echo "Elasticsearch is ready."

echo "Waiting for Redis..."
until python -c "import redis; url='$REDIS_URI'; r=redis.from_url(url); r.ping()" 2>/dev/null; do
  sleep 2
done
echo "Redis is ready."

echo "Waiting for Neo4j..."
until python -c "from neo4j import GraphDatabase; GraphDatabase.driver('$NEO4J_URI', auth=('$NEO4J_USER','$NEO4J_PASS')).verify_connectivity()" 2>/dev/null; do
  sleep 2
done
echo "Neo4j is ready."

# Initialize ML models (pre-download so first pipeline run is fast)
echo "Initializing ML models..."
cd /app
python -c "
import asyncio
import logging
logging.basicConfig(level=logging.INFO)

async def init():
    print('Downloading spaCy transformer model...')
    import spacy
    nlp = spacy.load('en_core_web_trf')
    print('spaCy transformer model loaded successfully')
    
    print('Initializing HuggingFace zero-shot classifier...')
    from app.nlp.ml_classifier import get_ml_classifier
    clf = await get_ml_classifier()
    await clf.ensure_loaded()
    print('Zero-shot classifier ready')
    
    print('Initializing HuggingFace sentiment model...')
    from app.nlp.ml_sentiment import get_ml_sentiment
    sent = await get_ml_sentiment()
    await sent.ensure_loaded()
    print('Sentiment model ready')

asyncio.run(init())
" 2>&1 | grep -v "^$"
echo "ML model initialization complete."

# Start the application
echo "Starting DarkTrace backend..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
