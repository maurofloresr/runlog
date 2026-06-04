import os
import base64
import json
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash")


def extract_training_data(photos):
    images = []
    for photo in photos:
        if photo and photo.filename:
            image_bytes = photo.read()
            image_b64 = base64.b64encode(image_bytes).decode("utf-8")
            images.append({
                "mime_type": photo.content_type,
                "data": image_b64
            })
    
    if not images:
        return None
    
    prompt = """
    Analyze these fitness app screenshots (Samsung Health, Apple Health, Strava, Garmin, or any other running app)
    and extract the running session data.
    Return ONLY a valid JSON object with these exact keys (use null if not found):
    
    {
        "distance_km": float,
        "duration_min": integer,
        "avg_hr": integer,
        "max_hr": integer,
        "cadence": integer,
        "calories": integer,
        "zone2_minutes": integer,
        "vo2max": float
    }
    
    Return ONLY the JSON, no explanation, no markdown, no backticks.
    """
    
    
    try:
        content = [prompt] + [{"mime_type": img["mime_type"], "data": img["data"]} for img in images]
        response = model.generate_content(content)
        text = response.text.strip()
        data = json.loads(text)
        return data
    except Exception as e:
        print(f"Gemini error: {e}")
        return None
    
    
    
    
    
    