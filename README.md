
Chopin Competition Analysis Agent

System AI do analizy występów uczestników XIX Konkursu Chopinowskiego i przewidywania szans na wygraną.

## Funkcjonalności

- **Analiza Występów**: Szczegółowa ocena techniki, muzykalności i interpretacji
- **Predykcja Zwycięzcy**: AI przewiduje kto wygra konkurs
- **Porównania Pianistów**: Porównaj dwóch pianistów bezpośrednio
- **Rankings**: Aktualne rankingi uczestników
- **Analiza Repertuaru**: Ocena wyboru utworów Chopina
- **Agregacja Recenzji**: Zbieranie opinii ekspertów i krytyków
- **Analiza Video**: Opcjonalna analiza nagrań z YouTube
- **Sentiment Analysis**: Analiza opinii publicznej

## 🎼 Kryteria Oceny

System ocenia pianistów według 5 głównych kryteriów:

1. **Technika (25%)**
   - Technika palcowa
   - Pedalowanie
   - Kontrola tempa
   - Dynamika
   - Artykulacja

2. **Muzykalność (30%)**
   - Frazowanie
   - Ekspresja
   - Jakość dźwięku
   - Użycie rubato
   - Głębia emocjonalna

3. **Interpretacja (20%)**
   - Oryginalność
   - Autentyczność stylistyczna
   - Spójność
   - Zrozumienie kompozytora

4. **Obecność Sceniczna (10%)**
   - Pewność siebie
   - Kontakt z publicznością
   - Prezentacja fizyczna
   - Radzenie sobie z błęd
5. **Repertuar (15%)**
   - Poziom trudności
   - Różnorodność
   - Dopasowanie do pianisty
   - Strategiczne wybory

## 📊 Skala Ocen

- **0-6.0**: Eliminated (odpadnięcie)
- **6.0-7.5**: Average (przeciętnie)
- **7.5-8.5**: Good (dobrze)
- **8.5-9.0**: Excellent (świetnie)
- **9.0-10.0**: Outstanding (wybitnie)

## Instalacja

### Wymagania
- Python 3.11+
- Redis
- OpenAI API key

### Krok 1: Klonowanie
```bash
git clone <repo>
cd chopin-competition-agent
```

### Krok 2: Instalacja zależności
```bash
pip install -r requirements.txt
```

### Krok 3: Konfiguracja
```bash
cp .env.example .env
nano .env
```

Wypełnij:
```bash
OPENAI_API_KEY=sk-...              # WYMAGANE
YOUTUBE_API_KEY=...                # Opcjonalne
```

### Krok 4: Uruchomienie
```bash
# Z Docker Compose
docker-compose up -d

# Lub lokalnie
redis-server &
uvicorn main:app --reload
```

##  API Endpoints

### `POST /analyze`
Główna analiza konkursu

**Request:**
```json
{
  "pianist_name": "Bruce Liu",
  "stage": "final",
  "include_videos": true,
  "include_expert_reviews": true,
  "lookback_days": 30
}
```

**Response:**
```json
{
  "timestamp": "2025-10-11T10:00:00",
  "predicted_winner": "Bruce Liu",
  "predicted_finalists": ["Bruce Liu", "Martin Garcia", "Alexander Gadjiev", ...],
  "top_10_predictions": [...],
  "dark_horses": ["Pianist X", "Pianist Y"],
  "evaluated_pianists": [
    {
      "pianist_name": "Bruce Liu",
      "nationality": "Canada",
      "overall_score": 9.2,
      "weighted_score": 9.15,
      "performance_level": "outstanding",
      "win_probability": 0.85,
      "technical_analysis": {
        "overall_technical_score": 9.5,
        "comments": "Exceptional finger technique..."
      },
      "strengths": ["Perfect technique", "Deep musicality"],
      "weaknesses": ["Occasional over-pedaling"],
      "detailed_analysis": "Bruce Liu demonstrates..."
    }
  ],
  "overall_competition_analysis": "The XIX Chopin Competition shows...",
  "confidence": 0.78
}
```

### `GET /pianist/{name}`
Szczegółowa analiza konkretnego pianisty

```bash
curl http://localhost:8000/pianist/Bruce%20Liu
```

### `GET /rankings`
Aktualne rankingi

```bash
curl http://localhost:8000/rankings?stage=final&limit=10
```

**Response:**
```json
{
  "rankings": [
    {
      "rank": 1,
      "pianist": "Bruce Liu",
      "nationality": "Canada",
      "score": 9.15,
      "level": "outstanding",
      "win_probability": 0.85
    },
    ...
  ]
}
```

### `GET /predictions`
Predykcje zwycięzcy

```bash
curl http://localhost:8000/predictions
```

### `GET /compare`
Porównaj dwóch pianistów

```bash
curl "http://localhost:8000/compare?pianist1=Bruce%20Liu&pianist2=Martin%20Garcia"
```

**Response:**
```json
{
  "pianist1": {
    "name": "Bruce Liu",
    "score": 9.15,
    "technical": 9.5,
    "musicality": 9.3,
    "win_probability": 0.85
  },
  "pianist2": {
    "name": "Martin Garcia",
    "score": 8.7,
    "technical": 8.9,
    "musicality": 8.6,
    "win_probability": 0.45
  },
  "comparison": {
    "score_difference": 0.45,
    "technical_advantage": 0.6,
    "better_performer": "Bruce Liu"
  }
}
```

### `GET /statistics`
Statystyki konkursu

```bash
curl http://localhost:8000/statistics
```

## 🎯 Przykłady użycia

### Python Client

```python
import httpx
import asyncio

async def analyze_competition():
    async with httpx.AsyncClient() as client:
        # Pełna analiza
        response = await client.post(
            "http://localhost:8000/analyze",
            json={"lookback_days": 30}
        )
        
        analysis = response.json()
        
        print(f"Predicted Winner: {analysis['predicted_winner']}")
        print(f"Confidence: {analysis['confidence']:.2%}")
        print(f"\nTop 10:")
        for i, name in enumerate(analysis['top_10_predictions'], 1):
            print(f"  {i}. {name}")

asyncio.run(analyze_competition())
```

### Analiza konkretnego pianisty

```python
async def analyze_pianist(name: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"http://localhost:8000/pianist/{name}"
        )
        
        pianist = response.json()
        
        print(f"Pianist: {pianist['pianist_name']}")
        print(f"Score: {pianist['weighted_score']:.2f}/10")
        print(f"Win Probability: {pianist['win_probability']:.2%}")
        print(f"\nStrengths: {', '.join(pianist['strengths'])}")
        print(f"Weaknesses: {', '.join(pianist['weaknesses'])}")
        print(f"\nAnalysis:\n{pianist['detailed_analysis']}")

asyncio.run(analyze_pianist("Bruce Liu"))
```

### Porównanie pianistów

```python
async def compare_two(pianist1: str, pianist2: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"http://localhost:8000/compare",
            params={"pianist1": pianist1, "pianist2": pianist2}
        )
        
        comparison = response.json()
        
        print(f"{pianist1} vs {pianist2}")
        print(f"\nScores:")
        print(f"  {pianist1}: {comparison['pianist1']['score']:.2f}")
        print(f"  {pianist2}: {comparison['pianist2']['score']:.2f}")
        print(f"\nBetter performer: {comparison['comparison']['better_performer']}")
        print(f"Score difference: {comparison['comparison']['score_difference']:.2f}")

asyncio.run(compare_two("Bruce Liu", "Martin Garcia"))
```

## 🎼 Źródła Danych

System zbiera dane z:

1. **Oficjalna strona konkursu**
   - chopin2020.pl
   - nifc.pl

2. **YouTube**
   - Chopin Institute channel
   - Nagrania występów

3. **Media**
   - The Guardian Music
   - New York Times Classical
   - Classic FM

4. **Social Media**
   - Twitter/X (opcjonalnie)
   - Forum dyskusyjne (opcjonalnie)

## 🔧 Konfiguracja

### Wagi kryteriów (config.py)

Możesz dostosować wagi kryteriów oceny:

```python
CRITERIA_WEIGHTS = {
    "technical_skill": 0.25,        # 25%
    "musicality": 0.30,             # 30% (najważniejsze!)
    "interpretation": 0.20,         # 20%
    "stage_presence": 0.10,         # 10%
    "repertoire_difficulty": 0.15   # 15%
}
```

### Progi ocen

```python
LOW_SCORE_THRESHOLD = 6.0
MEDIUM_SCORE_THRESHOLD = 7.5
HIGH_SCORE_THRESHOLD = 8.5
EXCELLENT_SCORE_THRESHOLD = 9.0
```

## 🎹 Kategorie utworów Chopina

System rozpoznaje:

- **Etiudy**: Op. 10, Op. 25
- **Preludia**: Op. 28
- **Ballady**: No. 1-4
- **Scherza**: No. 1-4
- **Polonezy**: Polonaise-Fantaisie, Op. 53
- **Koncerty**: No. 1-2
- **Sonaty**: No. 2-3
- **Nokturny**, **Walce**, **Mazurki**

## 📊 Jak działa Agent?

### LangGraph Workflow

```
1. collect_performances
   ↓
   Zbiera dane o występach z wielu źródeł
   ↓
2. collect_reviews
   ↓
   Zbiera recenzje ekspertów i krytyków
   ↓
3. analyze_performances
   ↓
   AI analizuje każdy występ według kryteriów
   ↓
4. evaluate_pianists
   ↓
   Tworzy kompleksowe oceny pianistów
   ↓
5. predict_winners
   ↓
   Generuje predykcje i rankingi
```

### Przykład analizy występu

```python
# AI analizuje występ według prompta:

"""
Pianist: Bruce Liu
Pieces: Ballade No. 1 Op. 23, Etude Op. 10 No. 4

Oceń występ w skali 0-10:
- Technika palcowa
- Pedalowanie
- Kontrola tempa
- Muzykalność
- Interpretacja
...

Podaj mocne strony i słabości.
"""

# GPT-4 zwraca szczegółową analizę
```

## 🏆 Historyczne porównania

System porównuje obecnych uczestników do poprzednich zwycięzców:

- **2021**: Bruce Liu (Kanada)
- **2015**: Seong-Jin Cho (Korea Południowa)
- **2010**: Yulianna Avdeeva (Rosja)
- **2005**: Rafał Blechacz (Polska)

## 📈 Metryki

System śledzi:
- Łączna liczba analizowanych pianistów
- Rozkład narodowości
- Średnie wyniki według kategorii
- Liczba źródeł danych
- Pewność predykcji (confidence score)

## 🧪 Testowanie

```bash
# Uruchom testy
pytest tests/ -v

# Test konkretnego modułu
pytest tests/test_agent.py -v

# Test z output
pytest tests/ -v -s
```

## 🐛 Troubleshooting

### Problem: "No performances found"
```bash
# Sprawdź czy źródła są dostępne
curl https://chopin2020.pl/en

# Sprawdź logi
docker-compose logs -f api
```

### Problem: "YouTube API quota exceeded"
Bez YouTube API key system działa, ale bez analizy video.

### Problem: "OpenAI rate limit"
Zmniejsz liczbę analizowanych występów lub zwiększ opóźnienia.

## 📚 Struktura projektu

```
chopin-competition-agent/
├── main.py                  # FastAPI application
├── agent.py                 # LangGraph agent
├── models.py                # Pydantic models
├── config.py                # Configuration
├── data_collectors.py       # Data collection
├── requirements.txt         # Dependencies
├── docker-compose.yml       # Docker setup
├── .env                     # Environment variables
└── README.md               # This file
```

## 🎯 Roadmap

- [ ] Analiza audio (librosa)
- [ ] Więcej źródeł danych
- [ ] Dashboard web UI (React)
- [ ] Real-time updates podczas konkursu
- [ ] Integracja z OpenSearch
- [ ] Machine learning model (sklearn)
- [ ] Analiza filmów z kamer
- [ ] System alertów
- [ ] Multi-language support

## 🎼 Dodatkowe informacje

### O Konkursie Chopinowskim

Międzynarodowy Konkurs Pianistyczny im. Fryderyka Chopina odbywa się co 5 lat w Warszawie od 1927 roku. To najbardziej prestiżowy konkurs pianistyczny na świecie.

### Etapy konkursu

1. **Preliminary Stage**: Eliminacje wstępne
2. **Stage I**: I etap (recital)
3. **Stage II**: II etap (recital)
4. **Stage III**: III etap (recital + koncert kameralny)
5. **Final**: Finał (koncert z orkiestrą)

### Jury

Oceny jury są tajne do momentu ogłoszenia wyników. Nasz AI agent przewiduje wyniki na podstawie:
- Analizy technicznej
- Opinii krytyków
- Reakcji publiczności
- Danych historycznych

## 📄 Licencja

MIT License

## 🤝 Contributing

Pull requests are welcome! For major changes, please open an issue first.

## 📧 Kontakt

W razie pytań lub problemów, otwórz issue na GitHub.

---

**Zbudowane z ❤️ dla miłośników muzyki Chopina i AI**

🎹 *"Simplicité est la note de toutes les vraies grandeurs"* - Fryderyk Chopin