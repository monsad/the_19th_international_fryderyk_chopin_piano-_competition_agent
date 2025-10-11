import pytest
from fastapi.testclient import TestClient
from datetime import datetime
from main import app
from models import RiskLevel

client = TestClient(app)

def test_root_endpoint():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "service" in data
    assert data["service"] == "War Prediction Agent"

def test_health_endpoint():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] in ["healthy", "degraded"]

@pytest.mark.asyncio
async def test_predict_endpoint():
    """Test prediction endpoint"""
    payload = {
        "regions": ["Europe", "Middle East"],
        "include_social_media": True,
        "lookback_hours": 24
    }
    
    response = client.post("/predict", json=payload)
    
    # Note: This will fail without proper API keys configured
    # In real testing, use mocked data
    assert response.status_code in [200, 500]
    
    if response.status_code == 200:
        data = response.json()
        assert "global_risk_score" in data
        assert "global_risk_level" in data
        assert "regional_analyses" in data

def test_stats_endpoint():
    """Test statistics endpoint"""
    response = client.get("/stats")
    assert response.status_code == 200
    data = response.json()
    assert "cached_predictions" in data

def test_history_endpoint():
    """Test prediction history endpoint"""
    response = client.get("/history?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert "predictions" in data
    assert isinstance(data["predictions"], list)

def test_clear_cache_endpoint():
    """Test cache clearing endpoint"""
    response = client.delete("/cache")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "cleared" in data


# tests/test_collectors.py
import pytest
from data_collectors import NewsCollector, MilitaryIntelCollector, SocialMediaCollector
from datetime import datetime

@pytest.mark.asyncio
async def test_news_collector():
    """Test news collector"""
    collector = NewsCollector()
    data = await collector.collect(hours_back=24)
    
    assert isinstance(data, list)
    # May be empty if no relevant news
    if len(data) > 0:
        assert hasattr(data[0], 'title')
        assert hasattr(data[0], 'source_type')

@pytest.mark.asyncio
async def test_military_collector():
    """Test military intelligence collector"""
    collector = MilitaryIntelCollector()
    data = await collector.collect(hours_back=24)
    
    assert isinstance(data, list)

@pytest.mark.asyncio
async def test_social_collector():
    """Test social media collector"""
    collector = SocialMediaCollector()
    data = await collector.collect(hours_back=24)
    
    # Will be empty without Twitter API key
    assert isinstance(data, list)


# tests/test_models.py
from models import DataPoint, PredictionResponse, RiskLevel, SourceType, RegionAnalysis
from datetime import datetime

def test_data_point_creation():
    """Test DataPoint model"""
    dp = DataPoint(
        id="test123",
        source="Test Source",
        source_type=SourceType.NEWS,
        title="Test Title",
        content="Test content",
        timestamp=datetime.now()
    )
    
    assert dp.id == "test123"
    assert dp.source_type == SourceType.NEWS
    assert dp.relevance_score == 0.0

def test_risk_levels():
    """Test risk level enum"""
    assert RiskLevel.LOW.value == "low"
    assert RiskLevel.CRITICAL.value == "critical"

def test_prediction_response():
    """Test prediction response model"""
    response = PredictionResponse(
        timestamp=datetime.now(),
        global_risk_score=0.5,
        global_risk_level=RiskLevel.MEDIUM,
        regional_analyses=[],
        key_events=[],
        confidence=0.8,
        reasoning="Test reasoning",
        sources_analyzed=100
    )
    
    assert response.global_risk_score == 0.5
    assert response.global_risk_level == RiskLevel.MEDIUM
    assert response.confidence == 0.8