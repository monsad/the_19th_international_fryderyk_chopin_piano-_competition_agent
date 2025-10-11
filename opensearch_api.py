y
"""
Additional API endpoints for OpenSearch functionality
Add these to main.py
"""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List
from datetime import datetime, timedelta
from opensearch_client import OpenSearchClient
from config import settings
from models import SourceType

router = APIRouter(prefix="/opensearch", tags=["OpenSearch Analytics"])

# Initialize OpenSearch client
os_client = OpenSearchClient(
    host=settings.OPENSEARCH_HOST,
    port=settings.OPENSEARCH_PORT,
    auth=(settings.OPENSEARCH_USER, settings.OPENSEARCH_PASSWORD),
    use_ssl=settings.OPENSEARCH_USE_SSL,
    verify_certs=settings.OPENSEARCH_VERIFY_CERTS
)

@router.get("/search/data-points")
async def search_data_points(
    query: str = Query(..., description="Search query"),
    source_type: Optional[str] = Query(None, description="Filter by source type"),
    hours_back: int = Query(24, description="Hours to look back"),
    min_relevance: float = Query(0.0, description="Minimum relevance score"),
    size: int = Query(100, description="Number of results")
):
    """
    Search collected data points with full-text search
    
    Example: /opensearch/search/data-points?query=military+mobilization&hours_back=48
    """
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(hours=hours_back)
        
        source_type_enum = None
        if source_type:
            try:
                source_type_enum = SourceType(source_type)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid source_type: {source_type}")
        
        results = await os_client.search_data_points(
            query=query,
            source_type=source_type_enum,
            start_date=start_date,
            end_date=end_date,
            min_relevance=min_relevance,
            size=size
        )
        
        return {
            "query": query,
            "filters": {
                "source_type": source_type,
                "hours_back": hours_back,
                "min_relevance": min_relevance
            },
            "results_count": len(results),
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search/keywords")
async def search_by_keywords(
    keywords: List[str] = Query(..., description="List of keywords to search"),
    hours_back: int = Query(24, description="Hours to look back"),
    size: int = Query(50, description="Number of results")
):
    """
    Search data points by specific keywords
    
    Example: /opensearch/search/keywords?keywords=war&keywords=invasion&hours_back=24
    """
    try:
        results = await os_client.search_by_keywords(
            keywords=keywords,
            hours_back=hours_back,
            size=size
        )
        
        return {
            "keywords": keywords,
            "hours_back": hours_back,
            "results_count": len(results),
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/predictions/history")
async def get_predictions_history(
    days_back: int = Query(7, description="Days to look back"),
    min_risk_score: Optional[float] = Query(None, description="Minimum risk score filter"),
    size: int = Query(100, description="Number of results")
):
    """
    Get historical predictions with optional filters
    
    Example: /opensearch/predictions/history?days_back=7&min_risk_score=0.5
    """
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        results = await os_client.get_predictions_history(
            start_date=start_date,
            end_date=end_date,
            min_risk_score=min_risk_score,
            size=size
        )
        
        return {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "days": days_back
            },
            "filters": {
                "min_risk_score": min_risk_score
            },
            "predictions_count": len(results),
            "predictions": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/risk-by-region")
async def get_risk_by_region(
    days: int = Query(7, description="Number of days to analyze")
):
    """
    Get aggregated risk scores by region
    
    Example: /opensearch/analytics/risk-by-region?days=7
    """
    try:
        aggregations = await os_client.aggregate_risk_by_region(days=days)
        
        return {
            "period_days": days,
            "regions": aggregations
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/trending-keywords")
async def get_trending_keywords(
    hours: int = Query(24, description="Hours to analyze"),
    size: int = Query(20, description="Number of keywords to return")
):
    """
    Get trending conflict-related keywords
    
    Example: /opensearch/analytics/trending-keywords?hours=24&size=20
    """
    try:
        trends = await os_client.get_trending_keywords(
            hours=hours,
            size=size
        )
        
        return {
            "period_hours": hours,
            "keywords_count": len(trends),
            "trending_keywords": trends
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/sentiment")
async def get_sentiment_analysis(
    hours: int = Query(24, description="Hours to analyze")
):
    """
    Get sentiment analysis of collected data
    
    Example: /opensearch/analytics/sentiment?hours=24
    """
    try:
        sentiment_data = await os_client.get_sentiment_analysis(hours=hours)
        
        return {
            "period_hours": hours,
            "sentiment_distribution": sentiment_data["distribution"],
            "average_sentiment": sentiment_data["average"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/alerts")
async def get_alerts(
    hours: int = Query(24, description="Hours to look back"),
    size: int = Query(50, description="Number of alerts to return")
):
    """
    Get recent alerts
    
    Example: /opensearch/alerts?hours=24
    """
    try:
        alerts = await os_client.get_recent_alerts(
            hours=hours,
            size=size
        )
        
        return {
            "period_hours": hours,
            "alerts_count": len(alerts),
            "alerts": alerts
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/alerts/create")
async def create_manual_alert(
    alert_type: str,
    severity: str,
    region: str,
    message: str,
    risk_score: float,
    triggered_by: str = "manual"
):
    """
    Create a manual alert
    
    Example:
    POST /opensearch/alerts/create
    {
        "alert_type": "high_risk",
        "severity": "critical",
        "region": "Middle East",
        "message": "Escalating tensions detected",
        "risk_score": 0.85,
        "triggered_by": "analyst"
    }
    """
    try:
        await os_client.create_alert(
            alert_type=alert_type,
            severity=severity,
            region=region,
            message=message,
            risk_score=risk_score,
            triggered_by=triggered_by
        )
        
        return {
            "status": "success",
            "message": "Alert created successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/dashboard")
async def get_dashboard_data(
    hours: int = Query(24, description="Hours for recent data"),
    days: int = Query(7, description="Days for historical trends")
):
    """
    Get comprehensive dashboard data combining multiple analytics
    
    Example: /opensearch/analytics/dashboard?hours=24&days=7
    """
    try:
        # Gather all analytics in parallel
        trending_keywords = await os_client.get_trending_keywords(hours=hours, size=10)
        sentiment = await os_client.get_sentiment_analysis(hours=hours)
        risk_by_region = await os_client.aggregate_risk_by_region(days=days)
        recent_alerts = await os_client.get_recent_alerts(hours=hours, size=10)
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        predictions = await os_client.get_predictions_history(
            start_date=start_date,
            end_date=end_date,
            size=20
        )
        
        return {
            "timestamp": datetime.now().isoformat(),
            "periods": {
                "recent_hours": hours,
                "historical_days": days
            },
            "trending_keywords": trending_keywords,
            "sentiment_analysis": sentiment,
            "regional_risk": risk_by_region,
            "recent_alerts": recent_alerts,
            "recent_predictions": predictions[:5],
            "statistics": {
                "total_predictions": len(predictions),
                "total_alerts": len(recent_alerts),
                "high_risk_regions": [
                    region for region, data in risk_by_region.items()
                    if data["avg_risk"] > 0.6
                ]
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))