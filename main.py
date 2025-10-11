from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import redis.asyncio as redis
from typing import Optional
from datetime import datetime

from agent import ChopinCompetitionAgent
from models import CompetitionAnalysisRequest, CompetitionAnalysisResponse
from config import settings

# Redis client for caching
redis_client: Optional[redis.Redis] = None
agent: Optional[ChopinCompetitionAgent] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown"""
    global redis_client, agent
    
    # Startup
    try:
        redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True
        )
        await redis_client.ping()
        print("✅ Redis connected")
    except Exception as e:
        print(f"⚠️  Redis not available: {e}")
        redis_client = None
    
    agent = ChopinCompetitionAgent()
    print("🎹 Chopin Competition Agent ready!")
    
    yield
    
    # Shutdown
    if redis_client:
        await redis_client.close()
    print("👋 Application shutdown")

app = FastAPI(
    title="🎹 Chopin Competition Analysis API",
    description="AI-powered analysis system for the XIX International Fryderyk Chopin Piano Competition",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "🎹 Chopin Competition Analysis Agent",
        "version": "1.0.0",
        "status": "operational",
        "description": "AI system for analyzing XIX Chopin Competition performances and predicting winners",
        "endpoints": {
            "analyze": "POST /analyze - Full competition analysis",
            "pianist": "GET /pianist/{name} - Analyze specific pianist",
            "rankings": "GET /rankings - Get current rankings",
            "predictions": "GET /predictions - Get winner predictions",
            "compare": "GET /compare?pianist1=X&pianist2=Y - Compare two pianists",
            "health": "GET /health - Health check"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    redis_healthy = False
    if redis_client:
        try:
            await redis_client.ping()
            redis_healthy = True
        except Exception:
            pass
    
    return {
        "status": "healthy",
        "redis": "connected" if redis_healthy else "disconnected",
        "agent": "ready",
        "openai_key": "configured" if settings.OPENAI_API_KEY else "missing",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/analyze", response_model=CompetitionAnalysisResponse)
async def analyze_competition(
    request: CompetitionAnalysisRequest,
    background_tasks: BackgroundTasks
):
    """
    Main competition analysis endpoint
    
    Analyzes performances from the XIX Chopin Competition and predicts winners.
    
    Parameters:
    - pianist_name: Optional - analyze specific pianist only
    - stage: Optional - analyze specific competition stage
    - include_videos: bool - include YouTube video analysis
    - include_expert_reviews: bool - include expert reviews and opinions
    - lookback_days: int - how many days back to analyze (default 30)
    
    Returns comprehensive analysis with:
    - Individual pianist evaluations
    - Winner predictions
    - Rankings and probabilities
    - Detailed technical, musical, and interpretational analysis
    """
    
    if not settings.OPENAI_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="OpenAI API key not configured. Please set OPENAI_API_KEY in .env file"
        )
    
    try:
        print(f"🎹 Starting analysis (lookback: {request.lookback_days} days)...")
        
        # Run the agent
        result = await agent.analyze(
            pianist_name=request.pianist_name,
            lookback_days=request.lookback_days
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )

@app.get("/pianist/{name}")
async def get_pianist_analysis(name: str):
    """Get detailed analysis of a specific pianist"""
    try:
        result = await agent.analyze(
            pianist_name=name,
            lookback_days=30
        )
        
        # Find the pianist in results
        pianist_data = next(
            (p for p in result.evaluated_pianists if p.pianist_name.lower() == name.lower()),
            None
        )
        
        if not pianist_data:
            raise HTTPException(status_code=404, detail=f"Pianist '{name}' not found")
        
        return pianist_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/rankings")
async def get_rankings(stage: Optional[str] = None, limit: int = 10):
    """Get current competition rankings"""
    try:
        result = await agent.analyze(
            lookback_days=30
        )
        
        # Sort by weighted score
        sorted_pianists = sorted(
            result.evaluated_pianists,
            key=lambda p: p.weighted_score,
            reverse=True
        )[:limit]
        
        rankings = []
        for rank, pianist in enumerate(sorted_pianists, 1):
            rankings.append({
                "rank": rank,
                "pianist": pianist.pianist_name,
                "nationality": pianist.nationality,
                "score": pianist.weighted_score,
                "level": pianist.performance_level.value,
                "win_probability": pianist.win_probability
            })
        
        return {"rankings": rankings}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/predictions")
async def get_predictions():
    """Get winner predictions"""
    try:
        result = await agent.analyze(lookback_days=30)
        
        return {
            "predicted_winner": result.predicted_winner,
            "predicted_finalists": result.predicted_finalists,
            "top_10": result.top_10_predictions,
            "dark_horses": result.dark_horses,
            "confidence": result.confidence,
            "timestamp": result.timestamp.isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/compare")
async def compare_pianists(pianist1: str, pianist2: str):
    """Compare two pianists"""
    try:
        result = await agent.analyze(lookback_days=30)
        
        p1 = next((p for p in result.evaluated_pianists if p.pianist_name.lower() == pianist1.lower()), None)
        p2 = next((p for p in result.evaluated_pianists if p.pianist_name.lower() == pianist2.lower()), None)
        
        if not p1:
            raise HTTPException(status_code=404, detail=f"Pianist '{pianist1}' not found")
        if not p2:
            raise HTTPException(status_code=404, detail=f"Pianist '{pianist2}' not found")
        
        return {
            "pianist1": {
                "name": p1.pianist_name,
                "score": p1.weighted_score,
                "technical": p1.technical_analysis.overall_technical_score,
                "musicality": p1.musical_analysis.overall_musicality_score,
                "interpretation": p1.interpretation_analysis.overall_interpretation_score,
                "win_probability": p1.win_probability
            },
            "pianist2": {
                "name": p2.pianist_name,
                "score": p2.weighted_score,
                "technical": p2.technical_analysis.overall_technical_score,
                "musicality": p2.musical_analysis.overall_musicality_score,
                "interpretation": p2.interpretation_analysis.overall_interpretation_score,
                "win_probability": p2.win_probability
            },
            "comparison": {
                "score_difference": abs(p1.weighted_score - p2.weighted_score),
                "technical_advantage": p1.technical_analysis.overall_technical_score - p2.technical_analysis.overall_technical_score,
                "better_performer": p1.pianist_name if p1.weighted_score > p2.weighted_score else p2.pianist_name
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/statistics")
async def get_statistics():
    """Get competition statistics"""
    try:
        result = await agent.analyze(lookback_days=30)
        
        return {
            "total_pianists_analyzed": len(result.evaluated_pianists),
            "data_sources": result.data_sources_analyzed,
            "confidence": result.confidence,
            "average_score": sum(p.weighted_score for p in result.evaluated_pianists) / len(result.evaluated_pianists) if result.evaluated_pianists else 0,
            "timestamp": result.timestamp.isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
