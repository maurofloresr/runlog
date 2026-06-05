# runlog 🏃

> CS50x Final Project — A smart running training log that uses AI to extract workout data from fitness app screenshots and provides personalized aerobic training insights.
#### Video Demo: https://youtu.be/EERFbF2Ulrc
[![Demo Video](https://img.shields.io/badge/▶_Watch_Demo-YouTube-red?style=for-the-badge)](https://youtu.be/EERFbF2Ulrc)

---

## Screenshots

### Login
![Login](screenshots/login.png)

### Register
![Register](screenshots/register.png)

### Home — Weather alert + metrics
![Home](screenshots/home.png)

### Upload — AI extracts training data from screenshot
![Upload AI](screenshots/upload_ai.png)

### Profile
![Profile](screenshots/profile.png)

### Progress
![Progress](screenshots/progress.png)

---

## What it does

RunLog turns your Samsung Health (or any fitness app) screenshots into structured training data. Upload a photo of your workout summary and the AI extracts distance, duration, heart rate, cadence, calories, Zone 2 time and VO2max automatically.

Beyond data entry, the app gives you real coaching context:

- **Zone 2 training** — personalized ceiling using the Karvonen formula (not a generic 145 bpm)
- **ACWR (Acute:Chronic Workload Ratio)** — compares your weekly load against your 4-week average to flag injury risk before it happens
- **Weather alerts** — real-time conditions for your training location with actionable advice (heat, cold, storms)
- **Cadence tracking** — monitors your steps per minute toward the 160-170 spm target
- **Shoe mileage** — tracks km on your active shoe and warns you before cushioning degrades
- **Pain history** — logs discomfort zones and fires an alert if the same area hurts 3+ sessions in a row
- **Achievements** — unlocks for distance milestones and process goals (Zone 2 sessions, cadence, monthly volume)

---

## Stack

| Layer | Tech |
|---|---|
| Backend | Python · Flask · cs50 SQL |
| Database | SQLite |
| Frontend | Jinja2 · Tailwind CSS (CDN) · Chart.js |
| AI | Google Gemini 2.5 Flash |
| Weather | OpenWeatherMap API |
| Auth | Werkzeug password hashing · Flask-Session · Flask-WTF CSRF |

---

## Features

- 🔐 Register / login with secure hashed passwords and CSRF protection
- 📷 Upload 1 or more fitness app screenshots — AI consolidates into one record
- 🤖 Gemini extracts: distance, duration, avg HR, max HR, cadence, calories, Zone 2 minutes, VO2max
- 🌤 Real-time weather with alerts for heat, cold, rain, snow and thunderstorms
- 📊 Dashboard with weekly/monthly view — total km, ACWR, Zone 2 avg, cadence avg
- 📈 Progress charts — HR over time, % Zone 2 per session, cadence trend
- 🎯 Goal tracking — visual progress bar toward your target distance (7k → 10k → 15k → 21k)
- 👟 Shoe tracker with configurable km limit and wear warning
- 🏅 Achievement system — distance and process milestones

---

## Run locally

```bash
# Clone the repo
git clone https://github.com/maurofloresr/runlog.git
cd runlog

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create the database
sqlite3 training.db < schema.sql

# Create your .env file
cp .env.example .env
# Edit .env and add your API keys

# Run
flask run
```

### Environment variables

Create a `.env` file in the root:

```
FLASK_SECRET_KEY=your_secret_key_here
OPENWEATHER_API_KEY=your_openweather_key
GEMINI_API_KEY=your_gemini_key
```

- OpenWeatherMap API key → [openweathermap.org](https://openweathermap.org/api) (free tier)
- Gemini API key → [aistudio.google.com](https://aistudio.google.com/apikey) (free tier)

---

## What I learned

This was my CS50x final project. Coming in with a Python and JS freelance background, the main things I deepened:

- Structuring a Flask app across multiple files (`app.py`, `db.py`, `helpers.py`, `weather.py`, `ai.py`)
- SQLite schema design with foreign keys and normalized tables
- Integrating a multimodal AI API (Gemini) to extract structured data from images
- Building a real-time data pipeline: photo upload → base64 encoding → AI extraction → DB insert
- Medical metrics for endurance sports: Karvonen Zone 2, ACWR, cardiac drift concepts
- Security basics: CSRF protection, secret key management, input validation on both client and server

---

## Author

**Mauro** · [LinkedIn](https://linkedin.com/in/mauro-flores-454863230/) · [GitHub](https://github.com/maurofloresr)

Built as the final project for [CS50x](https://cs50.harvard.edu/) — Harvard's Introduction to Computer Science.