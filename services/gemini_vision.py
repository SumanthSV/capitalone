# services/gemini_vision.py
import google.generativeai as genai
import os
import json
from dotenv import load_dotenv
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import base64

# Load environment variables
load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Choose one of these vision-capable models
VISION_MODELS = [
    "models/gemini-1.5-pro-latest",        # Best overall
    "models/gemini-1.5-flash-latest",      # Faster response
    "models/gemini-2.0-flash",             # Lightweight option
]

def analyze_disease_image(image_path):
    """Analyze crop disease using Gemini Vision"""
    try:
        # Select the first available vision model
        model_name = next((m for m in VISION_MODELS if m in [model.name for model in genai.list_models()]), None)
        
        if not model_name:
            raise ValueError("No supported vision model available")
        
        model = genai.GenerativeModel(model_name)
        
        # Load and encode image
        with open(image_path, "rb") as image_file:
            image_data = base64.b64encode(image_file.read()).decode("utf-8")
        
        # Create the prompt
        prompt = f"""
        Analyze this crop disease image. Provide information in JSON format with these keys:
        - crop: common name of the crop
        - disease: specific disease name
        - confidence: High/Medium/Low
        - symptoms: brief description of visible symptoms
        - organic_treatment: organic treatment methods
        - chemical_treatment: chemical treatments (if applicable)
        - prevention: prevention strategies
        
        If the image doesn't show a recognizable crop disease, set disease to 'Unknown'
        and confidence to 'Low'.
        """
        
        # Generate response
        response = model.generate_content(
            contents=[
                {"text": prompt},
                {"mime_type": "image/jpeg", "data": image_data}
            ]
        )
        
        # Extract and parse the JSON response
        response_text = response.text.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:-3]  # Remove markdown code block
        
        return json.loads(response_text)
    
    except Exception as e:
        print(f"Gemini Vision error: {str(e)}")
        return {
            "crop": "Unknown",
            "disease": "Analysis Failed",
            "confidence": "Low",
            "symptoms": "",
            "organic_treatment": "Please consult a local agriculture expert",
            "chemical_treatment": "",
            "prevention": ""
        }
    
def extract_json(text: str) -> dict:
    """Extract JSON from Gemini's response"""
    try:
        # Find JSON substring
        start = text.find('{')
        end = text.rfind('}') + 1
        json_str = text[start:end]
        
        # Clean and parse
        json_str = json_str.replace('```json', '').replace('```', '').strip()
        return json.loads(json_str)
    except:
        return {
            "error": "Failed to parse response",
            "raw_output": text
        }