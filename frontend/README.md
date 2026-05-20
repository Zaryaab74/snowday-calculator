# ❄️ Snow Day Calculator

US & Canada snow day prediction — Weather.gov + Environment Canada.

---

## Quick Start

### Backend
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
python main.py
# Runs on http://localhost:8000
# Docs at http://localhost:8000/docs
```

### Frontend
```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
# Runs on http://localhost:5173
```

---

## APIs Used (All FREE, No Keys Needed)
| API | Purpose |
|-----|---------|
| Weather.gov | US weather forecasts |
| Environment Canada | Canadian weather |
| Open-Meteo | Fallback for both |
| Nominatim (OSM) | ZIP → coordinates |

---

## Deploy

### Frontend → Vercel
```bash
cd frontend && npm run build
# Push to GitHub → connect to Vercel
# Set VITE_API_URL to your backend URL
```

### Backend → Railway
```bash
# Push to GitHub → connect to Railway
# It auto-detects Python + requirements.txt
```

---

## Project Structure
```
snowday/
├── backend/
│   ├── main.py        # FastAPI routes
│   ├── weather.py     # Weather API calls
│   ├── calculator.py  # Snow day logic
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx    # Main UI
│   │   ├── hooks/
│   │   │   └── useSnowDay.js
│   │   └── index.css
│   ├── index.html
│   └── vite.config.js
```
