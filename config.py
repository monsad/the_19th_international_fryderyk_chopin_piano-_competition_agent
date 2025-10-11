# config.py - Chopin Competition Agent
from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import List, Dict, Optional

class Settings(BaseSettings):
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra='ignore'
    )
    
    # API Keys
    OPENAI_API_KEY: Optional[str] = None
    YOUTUBE_API_KEY: Optional[str] = None
    SPOTIFY_CLIENT_ID: Optional[str] = None
    SPOTIFY_CLIENT_SECRET: Optional[str] = None
    
    # Redis Configuration
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    
    # Competition Sources
    COMPETITION_SOURCES: List[str] = [
        "https://www.chopincompetition.pl/pl",  # Oficjalna strona konkursu 2025
        "https://www.chopincompetition.pl/en",  # English version
        "https://www.youtube.com/@ChopinInstitute",
        "https://nifc.pl/en/news"
    ]
    
    # News Sources for reviews
    NEWS_SOURCES: List[str] = [
        "https://www.polskieradio.pl/8,dwojka",  # Polskie Radio Dwójka - relacje z konkursu!
        "https://www.theguardian.com/music",
        "https://www.nytimes.com/section/arts/music",
        "https://www.classicfm.com/news/"
    ]
    
    # Musical Criteria (weights)
    CRITERIA_WEIGHTS: Dict[str, float] = {
        "technical_skill": 0.25,
        "musicality": 0.30,
        "interpretation": 0.20,
        "stage_presence": 0.10,
        "repertoire_difficulty": 0.15
    }
    
    # Score thresholds
    LOW_SCORE_THRESHOLD: float = 6.0
    MEDIUM_SCORE_THRESHOLD: float = 7.5
    HIGH_SCORE_THRESHOLD: float = 8.5
    EXCELLENT_SCORE_THRESHOLD: float = 9.0
    
    # Chopin works categories
    CHOPIN_CATEGORIES: Dict[str, List[str]] = {
        "etudes": ["Op. 10", "Op. 25"],
        "preludes": ["Op. 28"],
        "ballades": ["Ballade No. 1", "Ballade No. 2", "Ballade No. 3", "Ballade No. 4"],
        "scherzi": ["Scherzo No. 1", "Scherzo No. 2", "Scherzo No. 3", "Scherzo No. 4"],
        "polonaises": ["Polonaise-Fantaisie", "Polonaise Op. 53"],
        "concertos": ["Piano Concerto No. 1", "Piano Concerto No. 2"],
        "sonatas": ["Piano Sonata No. 2", "Piano Sonata No. 3"],
        "nocturnes": ["Various Op. numbers"],
        "waltzes": ["Various Op. numbers"],
        "mazurkas": ["Various Op. numbers"]
    }
    
    # Agent Configuration
    MAX_ITERATIONS: int = 5
    TEMPERATURE: float = 0.4

settings = Settings()
