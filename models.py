from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime
from enum import Enum

class PerformanceLevel(str, Enum):
    ELIMINATED = "eliminated"
    AVERAGE = "average"
    GOOD = "good"
    EXCELLENT = "excellent"
    OUTSTANDING = "outstanding"

class CompetitionStage(str, Enum):
    PRELIMINARY = "preliminary"
    STAGE_1 = "stage_1"
    STAGE_2 = "stage_2"
    STAGE_3 = "stage_3"
    FINAL = "final"

class SourceType(str, Enum):
    YOUTUBE = "youtube"
    NEWS = "news"
    SOCIAL_MEDIA = "social_media"
    EXPERT_REVIEW = "expert_review"
    COMPETITION_WEBSITE = "competition_website"

class PerformanceData(BaseModel):
    id: str
    pianist_name: str
    nationality: str
    age: Optional[int] = None
    stage: CompetitionStage
    performance_date: datetime
    pieces_performed: List[str]
    video_url: Optional[str] = None
    source: str
    source_type: SourceType
    timestamp: datetime
    
class TechnicalAnalysis(BaseModel):
    finger_technique: float = Field(ge=0, le=10)
    pedaling: float = Field(ge=0, le=10)
    tempo_control: float = Field(ge=0, le=10)
    dynamic_range: float = Field(ge=0, le=10)
    articulation: float = Field(ge=0, le=10)
    overall_technical_score: float = Field(ge=0, le=10)
    comments: str

class MusicalAnalysis(BaseModel):
    phrasing: float = Field(ge=0, le=10)
    expression: float = Field(ge=0, le=10)
    tone_quality: float = Field(ge=0, le=10)
    rubato_usage: float = Field(ge=0, le=10)
    emotional_depth: float = Field(ge=0, le=10)
    overall_musicality_score: float = Field(ge=0, le=10)
    comments: str

class InterpretationAnalysis(BaseModel):
    originality: float = Field(ge=0, le=10)
    stylistic_authenticity: float = Field(ge=0, le=10)
    cohesion: float = Field(ge=0, le=10)
    understanding_of_composer: float = Field(ge=0, le=10)
    overall_interpretation_score: float = Field(ge=0, le=10)
    comments: str

class StagePresenceAnalysis(BaseModel):
    confidence: float = Field(ge=0, le=10)
    connection_with_audience: float = Field(ge=0, le=10)
    physical_presentation: float = Field(ge=0, le=10)
    recovery_from_mistakes: float = Field(ge=0, le=10)
    overall_stage_presence_score: float = Field(ge=0, le=10)
    comments: str

class RepertoireAnalysis(BaseModel):
    difficulty_level: float = Field(ge=0, le=10)
    variety: float = Field(ge=0, le=10)
    suitability_to_pianist: float = Field(ge=0, le=10)
    strategic_choices: float = Field(ge=0, le=10)
    overall_repertoire_score: float = Field(ge=0, le=10)
    comments: str

class PianistEvaluation(BaseModel):
    pianist_name: str
    nationality: str
    stage: CompetitionStage
    
    technical_analysis: TechnicalAnalysis
    musical_analysis: MusicalAnalysis
    interpretation_analysis: InterpretationAnalysis
    stage_presence_analysis: StagePresenceAnalysis
    repertoire_analysis: RepertoireAnalysis
    
    overall_score: float = Field(ge=0, le=10)
    weighted_score: float = Field(ge=0, le=10)
    performance_level: PerformanceLevel
    
    strengths: List[str]
    weaknesses: List[str]
    
    win_probability: float = Field(ge=0, le=1)
    finalist_probability: float = Field(ge=0, le=1)
    
    expert_opinions_count: int
    audience_sentiment: float = Field(ge=-1, le=1)
    
    comparison_to_previous_winners: str
    detailed_analysis: str

class CompetitionAnalysisRequest(BaseModel):
    pianist_name: Optional[str] = None
    stage: Optional[CompetitionStage] = None
    include_videos: bool = True
    include_expert_reviews: bool = True
    lookback_days: int = 30

class CompetitionAnalysisResponse(BaseModel):
    timestamp: datetime
    stage: CompetitionStage
    
    evaluated_pianists: List[PianistEvaluation]
    
    top_10_predictions: List[str]
    predicted_winner: str
    predicted_finalists: List[str]
    
    dark_horses: List[str]
    
    overall_competition_analysis: str
    trends_and_observations: str
    
    data_sources_analyzed: int
    confidence: float
    
    historical_comparison: str

class AgentState(BaseModel):
    """State for LangGraph agent"""
    performances_collected: List[PerformanceData] = []
    reviews_collected: List[Dict] = []
    video_analyses: List[Dict] = []
    
    # Jury analysis
    jury_preferences: Dict[str, float] = {}
    jury_analysis: Dict = {}
    
    pianist_evaluations: Dict[str, PianistEvaluation] = {}
    
    final_analysis: Optional[CompetitionAnalysisResponse] = None
    iteration: int = 0
    errors: List[str] = []
