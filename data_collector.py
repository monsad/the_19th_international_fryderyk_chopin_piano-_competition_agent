# data_collectors.py
import httpx
import feedparser
from bs4 import BeautifulSoup
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from models import PerformanceData, SourceType, CompetitionStage
from config import settings
import asyncio
import hashlib
import json
import re

class CompetitionWebsiteCollector:
    """Collector for official Chopin Competition website"""
    
    async def collect(self, days_back: int = 30) -> List[PerformanceData]:
        performances = []
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            for url in settings.COMPETITION_SOURCES:
                try:
                    performances.extend(await self._scrape_website(client, url, cutoff_date))
                except Exception as e:
                    print(f"Error collecting from {url}: {e}")
        
        return performances
    
    async def _scrape_website(self, client: httpx.AsyncClient, url: str, cutoff_date: datetime) -> List[PerformanceData]:
        try:
            print(f"🌐 Scraping website: {url}")
            response = await client.get(url, follow_redirects=True)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            performances = []
            
            # Specjalna obsługa dla chopincompetition.pl
            if 'chopincompetition.pl' in url:
                performances.extend(await self._scrape_chopincompetition_pl(client, soup, url))
            
            # Ogólne szukanie informacji o występach
            performance_sections = soup.find_all(['div', 'article'], class_=lambda x: x and ('performance' in str(x).lower() or 'pianist' in str(x).lower()))
            
            for section in performance_sections[:50]:
                try:
                    # Wyciągnij nazwisko pianisty
                    name_elem = section.find(['h2', 'h3', 'span'], class_=lambda x: x and 'name' in str(x).lower())
                    if not name_elem:
                        continue
                    
                    pianist_name = name_elem.get_text(strip=True)
                    
                    # Wyciągnij utwory
                    pieces = self._extract_pieces(section.get_text())
                    
                    # Określ etap konkursu
                    stage_text = section.get_text().lower()
                    stage = self._determine_stage(stage_text)
                    
                    # Wyciągnij narodowość
                    nationality = self._extract_nationality(section.get_text())
                    
                    performance = PerformanceData(
                        id=hashlib.md5((pianist_name + str(datetime.now())).encode()).hexdigest(),
                        pianist_name=pianist_name,
                        nationality=nationality or "Unknown",
                        stage=stage,
                        performance_date=datetime.now(),
                        pieces_performed=pieces,
                        video_url=self._extract_video_url(section),
                        source=url,
                        source_type=SourceType.COMPETITION_WEBSITE,
                        timestamp=datetime.now()
                    )
                    
                    performances.append(performance)
                    
                except Exception as e:
                    print(f"Error parsing section: {e}")
                    continue
            
            return performances
            
        except Exception as e:
            print(f"Error scraping {url}: {e}")
            return []
    
    def _extract_pieces(self, text: str) -> List[str]:
        """Extract Chopin pieces from text"""
        pieces = []
        
        # Szukaj wzorców jak "Op. 10", "Ballade No. 1", etc.
        patterns = [
            r'Op\.\s*\d+',
            r'Ballade No\.\s*\d+',
            r'Scherzo No\.\s*\d+',
            r'Etude.*?Op\.\s*\d+',
            r'Polonaise.*?Op\.\s*\d+',
            r'Concerto No\.\s*\d+',
            r'Sonata No\.\s*\d+'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            pieces.extend(matches)
        
        return list(set(pieces))[:10]  # Max 10, unique
    
    def _determine_stage(self, text: str) -> CompetitionStage:
        """Determine competition stage from text"""
        text_lower = text.lower()
        
        if 'final' in text_lower:
            return CompetitionStage.FINAL
        elif 'stage 3' in text_lower or 'third stage' in text_lower:
            return CompetitionStage.STAGE_3
        elif 'stage 2' in text_lower or 'second stage' in text_lower:
            return CompetitionStage.STAGE_2
        elif 'stage 1' in text_lower or 'first stage' in text_lower:
            return CompetitionStage.STAGE_1
        else:
            return CompetitionStage.PRELIMINARY
    
    def _extract_nationality(self, text: str) -> Optional[str]:
        """Extract nationality from text"""
        # Lista krajów uczestniczących w Konkursie Chopinowskim
        countries = [
            "Poland", "China", "Japan", "Russia", "South Korea", 
            "United States", "Canada", "France", "Germany", "Italy",
            "Ukraine", "Spain", "United Kingdom", "Taiwan", "Vietnam"
        ]
        
        for country in countries:
            if country.lower() in text.lower():
                return country
        
        return None
    
    def _extract_video_url(self, section) -> Optional[str]:
        """Extract video URL if present"""
        video_link = section.find('a', href=lambda x: x and ('youtube' in str(x).lower() or 'video' in str(x).lower()))
        if video_link:
            return video_link.get('href')
        return None
    
    async def _scrape_chopincompetition_pl(self, client: httpx.AsyncClient, soup, base_url: str) -> List[PerformanceData]:
        """Specjalna obsługa dla oficjalnej strony chopincompetition.pl"""
        performances = []
        
        try:
            print("   🎹 Parsowanie chopincompetition.pl...")
            
            # Szukaj linków do uczestników (competitors)
            competitors_link = soup.find('a', href=lambda x: x and 'competitors' in str(x).lower())
            if competitors_link and competitors_link.get('href'):
                competitor_url = competitors_link['href']
                if not competitor_url.startswith('http'):
                    competitor_url = base_url.rsplit('/', 1)[0] + '/' + competitor_url.lstrip('/')
                
                print(f"      📋 Znaleziono link do uczestników: {competitor_url}")
                # TODO: w przyszłości można pobrać listę uczestników
            
            # Szukaj newsów o występach
            news_items = soup.find_all(['article', 'div'], class_=lambda x: x and 'news' in str(x).lower())
            print(f"      📰 Znaleziono {len(news_items)} elementów newsów")
            
            for item in news_items[:20]:
                try:
                    # Szukaj tytułów z nazwiskami pianistów
                    title = item.find(['h1', 'h2', 'h3', 'h4'])
                    if not title:
                        continue
                    
                    title_text = title.get_text(strip=True)
                    
                    # Sprawdź czy tytuł zawiera nazwisko pianisty (wzór: "IMIĘ NAZWISKO")
                    pianist_match = re.search(r'\b([A-Z][a-z]+\s+[A-Z][a-z]+)\b', title_text)
                    if pianist_match:
                        pianist_name = pianist_match.group(1)
                        
                        # Wyciągnij opis
                        description = item.get_text()[:500]
                        pieces = self._extract_pieces(description)
                        stage = self._determine_stage(description)
                        
                        performance = PerformanceData(
                            id=hashlib.md5((pianist_name + base_url).encode()).hexdigest(),
                            pianist_name=pianist_name,
                            nationality=self._extract_nationality(description) or "Unknown",
                            stage=stage,
                            performance_date=datetime.now(),
                            pieces_performed=pieces,
                            video_url=None,
                            source=base_url,
                            source_type=SourceType.COMPETITION_WEBSITE,
                            timestamp=datetime.now()
                        )
                        performances.append(performance)
                        print(f"      ✅ Znaleziono pianistę: {pianist_name}")
                
                except Exception as e:
                    continue
            
        except Exception as e:
            print(f"      ⚠️  Błąd parsowania chopincompetition.pl: {e}")
        
        return performances


class YouTubeCollector:
    """Collector for YouTube performances and reviews"""
    
    def __init__(self):
        self.api_key = settings.YOUTUBE_API_KEY
    
    async def collect(self, search_query: str = "Chopin Competition 2025", max_results: int = 50) -> List[PerformanceData]:
        if not self.api_key:
            print("YouTube API key not provided, skipping YouTube collection")
            return []
        
        performances = []
        
        try:
            from googleapiclient.discovery import build
            
            youtube = build('youtube', 'v3', developerKey=self.api_key)
            
            # Wyszukaj wideo
            search_response = youtube.search().list(
                q=search_query,
                part='snippet',
                maxResults=max_results,
                type='video',
                order='relevance'
            ).execute()
            
            items = search_response.get('items', [])
            print(f"📺 Found {len(items)} YouTube videos for '{search_query}'")
            
            for item in items:
                try:
                    video_id = item['id']['videoId']
                    snippet = item['snippet']
                    
                    # Wyciągnij nazwisko pianisty z tytułu
                    title = snippet['title']
                    print(f"   📹 Video: {title[:80]}...")
                    pianist_name = self._extract_pianist_name(title)
                    
                    if not pianist_name:
                        print(f"      ⚠️  Could not extract pianist name, skipping")
                        continue
                    
                    print(f"      ✅ Found pianist: {pianist_name}")
                    
                    # Wyciągnij utwory z opisu
                    description = snippet['description']
                    pieces = self._extract_pieces_from_description(description)
                    
                    performance = PerformanceData(
                        id=video_id,
                        pianist_name=pianist_name,
                        nationality="Unknown",
                        stage=CompetitionStage.STAGE_1,  # Domyślnie
                        performance_date=datetime.fromisoformat(snippet['publishedAt'].replace('Z', '+00:00')),
                        pieces_performed=pieces,
                        video_url=f"https://www.youtube.com/watch?v={video_id}",
                        source="YouTube",
                        source_type=SourceType.YOUTUBE,
                        timestamp=datetime.now()
                    )
                    
                    performances.append(performance)
                    
                except Exception as e:
                    print(f"Error parsing YouTube video: {e}")
                    continue
            
        except Exception as e:
            print(f"Error collecting from YouTube: {e}")
        
        return performances
    
    def _extract_pianist_name(self, title: str) -> Optional[str]:
        """Extract pianist name from video title"""
        # Wzorce do wyciągania nazwiska
        # Przykład: "ERIC LU – second round" lub "John Smith plays Chopin"
        
        patterns = [
            # Format: "ERIC LU – second round" (wszystkie duże litery)
            r'^([A-Z]+(?:\s+[A-Z]+)+)\s+[–-]',
            # Format: "John Smith plays Chopin"
            r'^([A-Z][a-z]+\s+[A-Z][a-z]+)\s+plays',
            # Format: "John Smith - some text"
            r'^([A-Z][a-z]+\s+[A-Z][a-z]+)\s+-',
            # Format: "Pianist: John Smith"
            r'Pianist:\s+([A-Z][a-z]+\s+[A-Z][a-z]+)',
            # Format: "PIANIST NAME in capitals"
            r'^([A-Z]+(?:\s+[A-Z]+){1,3})\s+[–-–—]',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, title)
            if match:
                name = match.group(1).strip()
                # Konwertuj na Title Case dla spójności
                return name.title()
        
        return None
    
    def _extract_pieces_from_description(self, description: str) -> List[str]:
        """Extract piece names from description"""
        pieces = []
        
        lines = description.split('\n')
        for line in lines:
            if 'op.' in line.lower() or 'ballade' in line.lower() or 'etude' in line.lower():
                pieces.append(line.strip()[:100])
        
        return pieces[:5]


class NewsReviewCollector:
    """Collector for news and expert reviews"""
    
    async def collect(self, days_back: int = 30) -> List[Dict]:
        reviews = []
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            for source_url in settings.NEWS_SOURCES:
                try:
                    reviews.extend(await self._scrape_news(client, source_url, days_back))
                except Exception as e:
                    print(f"Error collecting news from {source_url}: {e}")
        
        return reviews
    
    async def _scrape_news(self, client: httpx.AsyncClient, url: str, days_back: int) -> List[Dict]:
        try:
            response = await client.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            reviews = []
            articles = soup.find_all(['article', 'div'], class_=lambda x: x and ('article' in str(x).lower() or 'post' in str(x).lower()))
            
            for article in articles[:20]:
                title_elem = article.find(['h1', 'h2', 'h3'])
                if not title_elem:
                    continue
                
                title = title_elem.get_text(strip=True)
                
                # Sprawdź czy dotyczy Chopina/konkursu
                if not self._is_chopin_related(title):
                    continue
                
                content = article.get_text(strip=True)[:1000]
                
                reviews.append({
                    "title": title,
                    "content": content,
                    "source": url,
                    "url": self._extract_article_url(article, url),
                    "timestamp": datetime.now(),
                    "pianist_mentioned": self._extract_mentioned_pianists(content)
                })
            
            return reviews
            
        except Exception as e:
            print(f"Error scraping news from {url}: {e}")
            return []
    
    def _is_chopin_related(self, text: str) -> bool:
        """Check if text is related to Chopin Competition"""
        keywords = ['chopin', 'competition', 'piano', 'pianist', 'warsaw', 'contest']
        text_lower = text.lower()
        return sum(1 for kw in keywords if kw in text_lower) >= 2
    
    def _extract_article_url(self, article, base_url: str) -> str:
        """Extract article URL"""
        link = article.find('a', href=True)
        if link:
            href = link['href']
            if href.startswith('http'):
                return href
            else:
                return base_url.rstrip('/') + '/' + href.lstrip('/')
        return base_url
    
    def _extract_mentioned_pianists(self, text: str) -> List[str]:
        """Extract pianist names mentioned in text"""
        # Prosty wzorzec: wielka litera + małe + spacja + wielka litera + małe
        pattern = r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b'
        matches = re.findall(pattern, text)
        
        # Filtruj typowe fałszywe dopasowania
        exclude = ['New York', 'Los Angeles', 'United States', 'The Guardian']
        
        return [m for m in matches if m not in exclude][:5]


class SocialMediaCollector:
    """Collector for social media sentiment (Twitter, forums)"""
    
    async def collect(self, search_terms: List[str] = None) -> List[Dict]:
        """
        Zbiera opinie z mediów społecznościowych
        W praktycznej implementacji połączyłby się z Twitter API, Reddit API, etc.
        """
        # Placeholder - w pełnej wersji podłącz Twitter API
        print("Social media collection - placeholder implementation")
        return []