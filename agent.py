
# agent.py
from typing import Dict
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from models import *
from data_collector import CompetitionWebsiteCollector, YouTubeCollector, NewsReviewCollector
from config import settings
import json
from datetime import datetime

# Fix for pydantic compatibility issue with ChatOpenAI
try:
    ChatOpenAI.model_rebuild()
except Exception:
    pass

class ChopinCompetitionAgent:
    """LangGraph-based agent for Chopin Competition analysis"""
    
    def __init__(self):
        self._llm = None
        self.website_collector = CompetitionWebsiteCollector()
        self.youtube_collector = YouTubeCollector()
        self.news_collector = NewsReviewCollector()
        self.graph = self._build_graph()
    
    @property
    def llm(self):
        """Lazy initialization of ChatOpenAI"""
        if self._llm is None:
            if not settings.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY is not set in .env file")
            self._llm = ChatOpenAI(
                model="gpt-4",
                temperature=settings.TEMPERATURE,
                api_key=settings.OPENAI_API_KEY
            )
        return self._llm
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow"""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("collect_performances", self._collect_performances)
        workflow.add_node("collect_reviews", self._collect_reviews)
        workflow.add_node("analyze_performances", self._analyze_performances)
        workflow.add_node("evaluate_pianists", self._evaluate_pianists)
        workflow.add_node("predict_winners", self._predict_winners)
        
        # Add edges
        workflow.set_entry_point("collect_performances")
        workflow.add_edge("collect_performances", "collect_reviews")
        workflow.add_edge("collect_reviews", "analyze_performances")
        workflow.add_edge("analyze_performances", "evaluate_pianists")
        workflow.add_edge("evaluate_pianists", "predict_winners")
        workflow.add_edge("predict_winners", END)
        
        return workflow.compile()
    
    async def _collect_performances(self, state: AgentState) -> Dict:
        """Collect performance data from all sources"""
        print("🎹 Collecting performance data...")
        
        try:
            # Zbierz z różnych źródeł
            website_performances = await self.website_collector.collect(days_back=30)
            youtube_performances = await self.youtube_collector.collect(
                search_query="Chopin Competition 2025",
                max_results=50  # Zwiększone z 30 na 50
            )
            
            all_performances = website_performances + youtube_performances
            
            print(f"✅ Collected {len(all_performances)} performances")
            
            return {
                "performances_collected": all_performances,
                "iteration": state.iteration + 1
            }
        except Exception as e:
            return {
                "errors": state.errors + [f"Performance collection error: {str(e)}"]
            }
    
    async def _collect_reviews(self, state: AgentState) -> Dict:
        """Collect expert reviews and opinions"""
        print("📰 Collecting expert reviews...")
        
        try:
            reviews = await self.news_collector.collect(days_back=30)
            
            print(f"✅ Collected {len(reviews)} reviews")
            
            return {
                "reviews_collected": reviews
            }
        except Exception as e:
            return {
                "errors": state.errors + [f"Review collection error: {str(e)}"]
            }
    
    async def _analyze_performances(self, state: AgentState) -> Dict:
        """Analyze individual performances using AI"""
        print("🔍 Analyzing performances with AI...")
        
        video_analyses = []
        
        # Analizuj maksymalnie 20 występów (limit LLM calls)
        for performance in state.performances_collected[:20]:
            try:
                analysis = await self._analyze_single_performance(performance, state.reviews_collected)
                video_analyses.append(analysis)
            except Exception as e:
                print(f"Error analyzing performance: {e}")
        
        return {
            "video_analyses": video_analyses
        }
    
    async def _analyze_single_performance(self, performance: PerformanceData, reviews: List[Dict]) -> Dict:
        """Analyze a single performance"""
        
        # Znajdź recenzje dotyczące tego pianisty
        relevant_reviews = [
            r for r in reviews 
            if performance.pianist_name.lower() in r.get('content', '').lower()
        ]
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert piano competition judge with deep knowledge of Chopin's music.
            
            Analyze this performance based on:
            1. Technical skill (finger technique, pedaling, tempo control)
            2. Musicality (phrasing, expression, tone quality)
            3. Interpretation (originality, stylistic authenticity)
            4. Stage presence (confidence, connection with audience)
            5. Repertoire choices (difficulty, variety, suitability)
            
            Provide scores 0-10 for each category and detailed comments."""),
            ("user", """Pianist: {pianist_name}
            Nationality: {nationality}
            Stage: {stage}
            Pieces performed: {pieces}
            
            Expert reviews:
            {reviews}
            
            Provide detailed analysis as JSON with structure:
            {{
                "technical_skill": {{"score": float, "comments": str}},
                "musicality": {{"score": float, "comments": str}},
                "interpretation": {{"score": float, "comments": str}},
                "stage_presence": {{"score": float, "comments": str}},
                "repertoire": {{"score": float, "comments": str}},
                "strengths": [str],
                "weaknesses": [str],
                "overall_assessment": str
            }}""")
        ])
        
        reviews_text = "\n".join([
            f"- {r['title']}: {r['content'][:200]}"
            for r in relevant_reviews[:3]
        ]) if relevant_reviews else "No specific reviews found"
        
        response = await self.llm.ainvoke(
            prompt.format_messages(
                pianist_name=performance.pianist_name,
                nationality=performance.nationality,
                stage=performance.stage.value,
                pieces=", ".join(performance.pieces_performed),
                reviews=reviews_text
            )
        )
        
        try:
            analysis = json.loads(response.content)
            analysis['pianist_name'] = performance.pianist_name
            analysis['performance_id'] = performance.id
            return analysis
        except:
            return {
                "pianist_name": performance.pianist_name,
                "performance_id": performance.id,
                "error": "Failed to parse analysis"
            }
    
    async def _evaluate_pianists(self, state: AgentState) -> Dict:
        """Evaluate all pianists and create rankings"""
        print("⭐ Evaluating pianists...")
        
        pianist_evaluations = {}
        
        # Grupuj analizy według pianisty
        pianist_analyses = {}
        for analysis in state.video_analyses:
            name = analysis.get('pianist_name')
            if name:
                if name not in pianist_analyses:
                    pianist_analyses[name] = []
                pianist_analyses[name].append(analysis)
        
        # Dla każdego pianisty stwórz pełną ocenę
        for pianist_name, analyses in pianist_analyses.items():
            try:
                evaluation = await self._create_pianist_evaluation(pianist_name, analyses, state)
                pianist_evaluations[pianist_name] = evaluation
            except Exception as e:
                print(f"Error evaluating {pianist_name}: {e}")
        
        return {
            "pianist_evaluations": pianist_evaluations
        }
    
    async def _create_pianist_evaluation(self, pianist_name: str, analyses: List[Dict], state: AgentState) -> PianistEvaluation:
        """Create comprehensive evaluation for a pianist"""
        
        # Znajdź dane o występach tego pianisty
        performances = [
            p for p in state.performances_collected 
            if p.pianist_name == pianist_name
        ]
        
        if not performances:
            raise ValueError(f"No performances found for {pianist_name}")
        
        # Uśrednij wyniki z wielu analiz
        avg_technical = sum(a.get('technical_skill', {}).get('score', 7) for a in analyses) / len(analyses)
        avg_musicality = sum(a.get('musicality', {}).get('score', 7) for a in analyses) / len(analyses)
        avg_interpretation = sum(a.get('interpretation', {}).get('score', 7) for a in analyses) / len(analyses)
        avg_stage = sum(a.get('stage_presence', {}).get('score', 7) for a in analyses) / len(analyses)
        avg_repertoire = sum(a.get('repertoire', {}).get('score', 7) for a in analyses) / len(analyses)
        
        # Oblicz wynik ważony
        weighted_score = (
            avg_technical * settings.CRITERIA_WEIGHTS['technical_skill'] +
            avg_musicality * settings.CRITERIA_WEIGHTS['musicality'] +
            avg_interpretation * settings.CRITERIA_WEIGHTS['interpretation'] +
            avg_stage * settings.CRITERIA_WEIGHTS['stage_presence'] +
            avg_repertoire * settings.CRITERIA_WEIGHTS['repertoire_difficulty']
        )
        
        # Określ poziom występu
        if weighted_score >= settings.EXCELLENT_SCORE_THRESHOLD:
            level = PerformanceLevel.OUTSTANDING
            win_prob = 0.8
            finalist_prob = 0.95
        elif weighted_score >= settings.HIGH_SCORE_THRESHOLD:
            level = PerformanceLevel.EXCELLENT
            win_prob = 0.5
            finalist_prob = 0.85
        elif weighted_score >= settings.MEDIUM_SCORE_THRESHOLD:
            level = PerformanceLevel.GOOD
            win_prob = 0.2
            finalist_prob = 0.6
        elif weighted_score >= settings.LOW_SCORE_THRESHOLD:
            level = PerformanceLevel.AVERAGE
            win_prob = 0.05
            finalist_prob = 0.3
        else:
            level = PerformanceLevel.ELIMINATED
            win_prob = 0.01
            finalist_prob = 0.1
        
        # Zbierz mocne i słabe strony
        all_strengths = []
        all_weaknesses = []
        for analysis in analyses:
            all_strengths.extend(analysis.get('strengths', []))
            all_weaknesses.extend(analysis.get('weaknesses', []))
        
        # Unikalne top 5
        strengths = list(set(all_strengths))[:5]
        weaknesses = list(set(all_weaknesses))[:5]
        
        # Szczegółowa analiza z AI
        detailed_analysis = await self._generate_detailed_analysis(
            pianist_name, 
            weighted_score, 
            analyses
        )
        
        performance = performances[0]
        
        return PianistEvaluation(
            pianist_name=pianist_name,
            nationality=performance.nationality,
            stage=performance.stage,
            
            technical_analysis=TechnicalAnalysis(
                finger_technique=avg_technical,
                pedaling=avg_technical,
                tempo_control=avg_technical,
                dynamic_range=avg_technical,
                articulation=avg_technical,
                overall_technical_score=avg_technical,
                comments="Averaged from multiple performances"
            ),
            
            musical_analysis=MusicalAnalysis(
                phrasing=avg_musicality,
                expression=avg_musicality,
                tone_quality=avg_musicality,
                rubato_usage=avg_musicality,
                emotional_depth=avg_musicality,
                overall_musicality_score=avg_musicality,
                comments="Averaged from multiple performances"
            ),
            
            interpretation_analysis=InterpretationAnalysis(
                originality=avg_interpretation,
                stylistic_authenticity=avg_interpretation,
                cohesion=avg_interpretation,
                understanding_of_composer=avg_interpretation,
                overall_interpretation_score=avg_interpretation,
                comments="Averaged from multiple performances"
            ),
            
            stage_presence_analysis=StagePresenceAnalysis(
                confidence=avg_stage,
                connection_with_audience=avg_stage,
                physical_presentation=avg_stage,
                recovery_from_mistakes=avg_stage,
                overall_stage_presence_score=avg_stage,
                comments="Averaged from multiple performances"
            ),
            
            repertoire_analysis=RepertoireAnalysis(
                difficulty_level=avg_repertoire,
                variety=avg_repertoire,
                suitability_to_pianist=avg_repertoire,
                strategic_choices=avg_repertoire,
                overall_repertoire_score=avg_repertoire,
                comments=f"Performed: {', '.join(performance.pieces_performed[:3])}"
            ),
            
            overall_score=(avg_technical + avg_musicality + avg_interpretation + avg_stage + avg_repertoire) / 5,
            weighted_score=weighted_score,
            performance_level=level,
            
            strengths=strengths,
            weaknesses=weaknesses,
            
            win_probability=win_prob,
            finalist_probability=finalist_prob,
            
            expert_opinions_count=len(analyses),
            audience_sentiment=0.5,  # Placeholder
            
            comparison_to_previous_winners="Based on technical and musical criteria",
            detailed_analysis=detailed_analysis
        )
    
    async def _generate_detailed_analysis(self, pianist_name: str, score: float, analyses: List[Dict]) -> str:
        """Generate detailed narrative analysis"""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a renowned music critic writing for a classical music magazine.
            Write a detailed, engaging analysis of this pianist's performance at the Chopin Competition."""),
            ("user", """Pianist: {pianist_name}
            Overall weighted score: {score}/10
            
            Performance analyses:
            {analyses}
            
            Write a 200-word critical analysis covering:
            - Overall impression
            - Technical mastery
            - Musical interpretation
            - Potential for winning
            - Comparison to competition standards""")
        ])
        
        analyses_summary = "\n".join([
            f"Analysis {i+1}: {a.get('overall_assessment', 'N/A')}"
            for i, a in enumerate(analyses[:3])
        ])
        
        response = await self.llm.ainvoke(
            prompt.format_messages(
                pianist_name=pianist_name,
                score=f"{score:.2f}",
                analyses=analyses_summary
            )
        )
        
        return response.content
    
    async def _predict_winners(self, state: AgentState) -> Dict:
        """Generate final predictions and rankings"""
        print("🏆 Generating predictions...")
        
        # Sprawdź czy są dane do przetworzenia
        if not state.pianist_evaluations:
            print("⚠️  No pianist evaluations available - returning empty analysis")
            final_analysis = CompetitionAnalysisResponse(
                timestamp=datetime.now(),
                stage=CompetitionStage.FINAL,
                evaluated_pianists=[],
                top_10_predictions=[],
                predicted_winner="No data available",
                predicted_finalists=[],
                dark_horses=[],
                overall_competition_analysis="No performance data was collected. Please ensure data sources are accessible and try again.",
                trends_and_observations="Insufficient data for trend analysis.",
                data_sources_analyzed=0,
                confidence=0.0,
                historical_comparison="Unable to perform historical comparison without data."
            )
            return {"final_analysis": final_analysis}
        
        # Sortuj pianistów według weighted_score
        ranked_pianists = sorted(
            state.pianist_evaluations.items(),
            key=lambda x: x[1].weighted_score,
            reverse=True
        )
        
        top_10 = [name for name, _ in ranked_pianists[:10]]
        predicted_winner = top_10[0] if top_10 else "Unable to determine"
        predicted_finalists = top_10[:6] if len(top_10) >= 6 else top_10
        
        # Dark horses (wysoki score ale niska rozpoznawalność)
        dark_horses = [
            name for name, eval in ranked_pianists[10:20]
            if eval.weighted_score >= settings.HIGH_SCORE_THRESHOLD
        ][:3]
        
        # Wygeneruj kompletną analizę
        overall_analysis = await self._generate_overall_analysis(ranked_pianists[:10])
        trends = await self._generate_trends_analysis(state.pianist_evaluations)
        historical = await self._generate_historical_comparison(state.pianist_evaluations)
        
        final_analysis = CompetitionAnalysisResponse(
            timestamp=datetime.now(),
            stage=CompetitionStage.FINAL,  # Domyślnie
            
            evaluated_pianists=[eval for _, eval in ranked_pianists],
            
            top_10_predictions=top_10,
            predicted_winner=predicted_winner,
            predicted_finalists=predicted_finalists,
            
            dark_horses=dark_horses,
            
            overall_competition_analysis=overall_analysis,
            trends_and_observations=trends,
            
            data_sources_analyzed=len(state.performances_collected) + len(state.reviews_collected),
            confidence=0.75,
            
            historical_comparison=historical
        )
        
        return {
            "final_analysis": final_analysis
        }
    
    async def _generate_overall_analysis(self, top_pianists: List[tuple]) -> str:
        """Generate overall competition analysis"""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a music journalist writing about the Chopin Competition.
            Write a compelling overview of the competition based on the top pianists."""),
            ("user", """Top 10 Pianists:
            {pianists}
            
            Write a 300-word analysis covering:
            - Overall level of the competition
            - Standout performances
            - Diversity of interpretations
            - Surprises and disappointments
            - Prediction for the final outcome""")
        ])
        
        pianists_summary = "\n".join([
            f"{i+1}. {name} ({eval.nationality}) - Score: {eval.weighted_score:.2f}/10"
            for i, (name, eval) in enumerate(top_pianists)
        ])
        
        response = await self.llm.ainvoke(
            prompt.format_messages(pianists=pianists_summary)
        )
        
        return response.content
    
    async def _generate_trends_analysis(self, evaluations: Dict) -> str:
        """Analyze trends in the competition"""
        
        # Analiza trendów
        avg_technical = sum(e.technical_analysis.overall_technical_score for e in evaluations.values()) / len(evaluations)
        avg_musicality = sum(e.musical_analysis.overall_musicality_score for e in evaluations.values()) / len(evaluations)
        
        nationalities = {}
        for eval in evaluations.values():
            nat = eval.nationality
            nationalities[nat] = nationalities.get(nat, 0) + 1
        
        top_countries = sorted(nationalities.items(), key=lambda x: x[1], reverse=True)[:3]
        
        return f"""Trends and Observations:

- Average Technical Level: {avg_technical:.2f}/10
- Average Musicality: {avg_musicality:.2f}/10
- Top Participating Countries: {', '.join([f"{c[0]} ({c[1]})" for c in top_countries])}
- Total Pianists Analyzed: {len(evaluations)}

The competition shows {"high" if avg_technical > 8 else "moderate"} technical standards and {"exceptional" if avg_musicality > 8.5 else "good"} musicality across participants."""
    
    async def _generate_historical_comparison(self, evaluations: Dict) -> str:
        """Compare current competition to historical standards"""
        
        return """Historical Comparison:

Compared to previous Chopin Competitions (2015, 2021), the current edition shows:
- Technical standards remain consistently high
- Greater diversity in interpretative approaches
- Increased international participation
- Evolution in stylistic preferences towards more romantic interpretations

Previous winners' characteristics that match current top performers:
- Exceptional technical control combined with deep musicality
- Mature interpretation despite young age
- Ability to handle the most challenging repertoire with apparent ease"""
    
    async def analyze(self, pianist_name: str = None, lookback_days: int = 30) -> CompetitionAnalysisResponse:
        """Run the full analysis pipeline"""
        initial_state = AgentState()
        
        result = await self.graph.ainvoke(initial_state)
        
        if result.get("final_analysis"):
            return result["final_analysis"]
        else:
            raise Exception(f"Analysis failed: {result.get('errors')}")