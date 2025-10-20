# jury_analyzer.py
import httpx
import asyncio
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from dataclasses import dataclass
from config import settings
import json

@dataclass
class JuryMember:
    name: str
    country: str
    role: str
    achievements: List[str]
    preferences: Dict[str, float]  # Preferencje w różnych kategoriach
    influence_score: float  # Wpływ na decyzje jury

class JuryAnalyzer:
    """Analizator składu sędziowskiego i ich preferencji"""
    
    def __init__(self):
        self.jury_members: List[JuryMember] = []
        self.jury_preferences: Dict[str, float] = {}
        
    async def analyze_jury(self) -> Dict:
        """Główna funkcja analizy jury"""
        print("🎭 Analyzing jury composition and preferences...")
        
        # Zbierz informacje o jury
        await self._collect_jury_data()
        
        # Przeanalizuj preferencje
        await self._analyze_preferences()
        
        # Oblicz wpływy
        self._calculate_influence()
        
        return {
            "jury_members": len(self.jury_members),
            "preferences": self.jury_preferences,
            "analysis": self._generate_analysis()
        }
    
    async def _collect_jury_data(self):
        """Zbierz dane o składzie jury"""
        async with httpx.AsyncClient() as client:
            for source in settings.JURY_SOURCES:
                try:
                    print(f"🎭 Scraping jury data from: {source}")
                    response = await client.get(source, timeout=30.0)
                    response.raise_for_status()
                    
                    soup = BeautifulSoup(response.text, 'html.parser')
                    await self._parse_jury_data(soup, source)
                    
                except Exception as e:
                    print(f"⚠️  Error scraping {source}: {e}")
                    continue
    
    async def _parse_jury_data(self, soup: BeautifulSoup, source: str):
        """Parsuj dane o jury z HTML"""
        if "radiozet.pl" in source:
            await self._parse_radiozet_jury(soup)
        elif "chopin2020.pl" in source:
            await self._parse_chopin2020_jury(soup)
        elif "nifc.pl" in source:
            await self._parse_nifc_jury(soup)
    
    async def _parse_radiozet_jury(self, soup: BeautifulSoup):
        """Parsuj dane jury z Radio ZET"""
        # Znajdź sekcję z jurorami
        jury_section = soup.find('div', class_='article-content') or soup.find('article')
        if not jury_section:
            return
            
        # Szukaj listy jurorów
        jury_items = jury_section.find_all(['h3', 'h4', 'strong'])
        
        for item in jury_items:
            text = item.get_text().strip()
            if any(keyword in text.lower() for keyword in ['jury', 'juror', 'przewodniczący', 'garrick', 'ohlsson']):
                # To jest informacja o jurorze
                member = self._extract_jury_member_from_text(text)
                if member:
                    self.jury_members.append(member)
    
    async def _parse_chopin2020_jury(self, soup: BeautifulSoup):
        """Parsuj dane jury z chopin2020.pl"""
        # Implementacja parsowania dla chopin2020.pl
        pass
    
    async def _parse_nifc_jury(self, soup: BeautifulSoup):
        """Parsuj dane jury z nifc.pl"""
        # Implementacja parsowania dla nifc.pl
        pass
    
    def _extract_jury_member_from_text(self, text: str) -> Optional[JuryMember]:
        """Wyciągnij informacje o jurorze z tekstu"""
        # Przykładowe parsowanie na podstawie struktury z Radio ZET
        if "Garrick Ohlsson" in text:
            return JuryMember(
                name="Garrick Ohlsson",
                country="Stany Zjednoczone",
                role="Przewodniczący jury",
                achievements=["Zwycięzca Konkursu Chopinowskiego 1970", "Avery Fisher Prize"],
                preferences={"technical_skill": 0.9, "musicality": 0.8, "interpretation": 0.9},
                influence_score=1.0
            )
        elif "Yulianna Avdeeva" in text:
            return JuryMember(
                name="Yulianna Avdeeva",
                country="Rosja",
                role="Juror",
                achievements=["Zwyciężczyni Konkursu Chopinowskiego 2010"],
                preferences={"technical_skill": 0.8, "musicality": 0.9, "interpretation": 0.8},
                influence_score=0.9
            )
        elif "Michel Beroff" in text:
            return JuryMember(
                name="Michel Beroff",
                country="Francja",
                role="Juror",
                achievements=["Zwycięzca Konkursu Messiaena", "Grand Prix du Disque"],
                preferences={"technical_skill": 0.7, "musicality": 0.9, "interpretation": 0.9},
                influence_score=0.8
            )
        elif "Sa Chen" in text:
            return JuryMember(
                name="Sa Chen",
                country="Chiny",
                role="Juror",
                achievements=["Paszport Chopinowski", "Solistka i dyrygentka"],
                preferences={"technical_skill": 0.8, "musicality": 0.9, "interpretation": 0.8},
                influence_score=0.8
            )
        elif "Akiko Ebi" in text:
            return JuryMember(
                name="Akiko Ebi",
                country="Japonia",
                role="Juror",
                achievements=["Grand Prix Marguerite Long", "V miejsce Konkursu Chopinowskiego"],
                preferences={"technical_skill": 0.9, "musicality": 0.8, "interpretation": 0.7},
                influence_score=0.7
            )
        elif "Krzysztof Jabłoński" in text:
            return JuryMember(
                name="Krzysztof Jabłoński",
                country="Polska",
                role="Juror",
                achievements=["III nagroda Konkursu Chopinowskiego", "Profesor"],
                preferences={"technical_skill": 0.8, "musicality": 0.8, "interpretation": 0.9},
                influence_score=0.8
            )
        elif "Kevin Kenner" in text:
            return JuryMember(
                name="Kevin Kenner",
                country="Stany Zjednoczone",
                role="Juror",
                achievements=["II nagroda Konkursu Chopinowskiego", "III nagroda Konkursu Czajkowskiego"],
                preferences={"technical_skill": 0.9, "musicality": 0.8, "interpretation": 0.8},
                influence_score=0.8
            )
        
        return None
    
    async def _analyze_preferences(self):
        """Przeanalizuj preferencje jury"""
        if not self.jury_members:
            # Fallback - użyj domyślnych preferencji jury
            self.jury_preferences = {
                "technical_skill": 0.25,
                "musicality": 0.30,
                "interpretation": 0.20,
                "stage_presence": 0.10,
                "repertoire_difficulty": 0.15
            }
            return
        
        # Oblicz średnie preferencje
        total_influence = sum(member.influence_score for member in self.jury_members)
        
        for criterion in ["technical_skill", "musicality", "interpretation", "stage_presence", "repertoire_difficulty"]:
            weighted_sum = sum(
                member.preferences.get(criterion, 0.5) * member.influence_score 
                for member in self.jury_members
            )
            self.jury_preferences[criterion] = weighted_sum / total_influence if total_influence > 0 else 0.5
        
        # Normalizuj wagi żeby sumowały się do 1.0
        total_weight = sum(self.jury_preferences.values())
        if total_weight > 0:
            for criterion in self.jury_preferences:
                self.jury_preferences[criterion] = self.jury_preferences[criterion] / total_weight
    
    def _calculate_influence(self):
        """Oblicz wpływy członków jury"""
        for member in self.jury_members:
            # Przewodniczący ma największy wpływ
            if "przewodniczący" in member.role.lower() or "chair" in member.role.lower():
                member.influence_score = 1.0
            # Zwycięzcy poprzednich konkursów mają duży wpływ
            elif any("zwycięzca" in ach.lower() or "winner" in ach.lower() for ach in member.achievements):
                member.influence_score = 0.9
            # Profesorowie i eksperci
            elif any("profesor" in ach.lower() or "professor" in ach.lower() for ach in member.achievements):
                member.influence_score = 0.8
            else:
                member.influence_score = 0.7
    
    def _generate_analysis(self) -> str:
        """Generuj analizę preferencji jury"""
        if not self.jury_members:
            return "Brak danych o składzie jury - używane domyślne preferencje."
        
        analysis = f"Analiza składu jury ({len(self.jury_members)} członków):\n\n"
        
        # Przewodniczący
        chair = next((m for m in self.jury_members if "przewodniczący" in m.role.lower()), None)
        if chair:
            analysis += f"Przewodniczący: {chair.name} ({chair.country}) - {chair.role}\n"
            analysis += f"Wpływ: {chair.influence_score:.1f}\n\n"
        
        # Preferencje jury
        analysis += "Preferencje jury:\n"
        for criterion, weight in self.jury_preferences.items():
            analysis += f"- {criterion}: {weight:.2f}\n"
        
        # Wnioski
        analysis += "\nWnioski:\n"
        if self.jury_preferences.get("musicality", 0) > 0.8:
            analysis += "- Jury szczególnie ceni muzykalność i ekspresję\n"
        if self.jury_preferences.get("technical_skill", 0) > 0.8:
            analysis += "- Wysokie wymagania techniczne\n"
        if self.jury_preferences.get("interpretation", 0) > 0.8:
            analysis += "- Duży nacisk na oryginalność interpretacji\n"
        
        return analysis
    
    def get_jury_weights(self) -> Dict[str, float]:
        """Zwróć wagi jury do użycia w ocenie"""
        return self.jury_preferences.copy()
    
    def get_jury_members_info(self) -> List[Dict]:
        """Zwróć informacje o członkach jury"""
        return [
            {
                "name": member.name,
                "country": member.country,
                "role": member.role,
                "influence": member.influence_score,
                "preferences": member.preferences
            }
            for member in self.jury_members
        ]
