import requests
import json
import logging
from app.config import settings

logger = logging.getLogger(__name__)

class GeminiClient:
    def __init__(self, api_key: str = None, model: str = None):
        self._api_key = api_key
        self._model = model

    @property
    def api_key(self):
        return self._api_key or settings.gemini_api_key

    @property
    def model(self):
        return self._model or settings.gemini_model

    def chat(self, messages: list[dict], system_prompt: str = None) -> str:
        """
        Trimite mesaje către Gemini API.
        Formatul Gemini diferă de cel OpenAI/Ollama.
        """
        contents = []
        
        # În Gemini, system prompt-ul poate fi pus ca o parte specială sau într-un câmp dedicat (în funcție de versiunea API)
        # Pentru simplitate și compatibilitate, îl adăugăm ca prim mesaj dacă există.
        if system_prompt:
            contents.append({
                "role": "user",
                "parts": [{"text": f"SYSTEM INSTRUCTIONS: {system_prompt}\n\nPlease acknowledge these instructions and wait for my next input."}]
            })
            contents.append({
                "role": "model",
                "parts": [{"text": "I understand and will follow these instructions."}]
            })

        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            contents.append({
                "role": role,
                "parts": [{"text": msg["content"]}]
            })

        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": 0.1,
                "topK": 1,
                "topP": 1,
                "maxOutputTokens": 2048,
                "stopSequences": []
            }
        }

        # Re-construim URL-ul în chat pentru a ne asigura că folosim modelul curent (poate fi setat dinamic)
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        
        try:
            response = requests.post(url, json=payload, timeout=120)
            response.raise_for_status()
            result = response.json()
            
            # Extragere text din structura Gemini
            if "candidates" in result and len(result["candidates"]) > 0:
                parts = result["candidates"][0].get("content", {}).get("parts", [])
                if parts:
                    return parts[0].get("text", "")
            
            logger.error(f"Răspuns Gemini neașteptat: {result}")
            return ""
        except Exception as e:
            logger.error(f"Eroare la apelul Gemini: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Detalii eroare: {e.response.text}")
            raise

    def generate_json(self, prompt: str, system_prompt: str = None) -> dict:
        """
        Cere un răspuns în format JSON de la Gemini.
        """
        # Adăugăm o notă suplimentară pentru a asigura formatul JSON
        json_prompt = f"{prompt}\n\nIMPORTANT: Return ONLY a valid JSON object. Do not include markdown formatting or explanations."
        
        messages = [{"role": "user", "content": json_prompt}]
        response_text = self.chat(messages, system_prompt)
        
        try:
            # Curățare text (Gemini uneori pune ```json ... ```)
            clean_text = response_text.strip()
            if clean_text.startswith("```"):
                # Eliminăm blocurile de cod markdown
                lines = clean_text.splitlines()
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                clean_text = "\n".join(lines).strip()

            start = clean_text.find('{')
            end = clean_text.rfind('}') + 1
            if start != -1 and end != 0:
                json_str = clean_text[start:end]
                return json.loads(json_str)
            return json.loads(clean_text)
        except Exception as e:
            logger.error(f"Eroare la parsarea JSON din răspunsul Gemini: {e}")
            logger.debug(f"Răspuns brut: {response_text}")
            raise ValueError(f"Gemini nu a returnat un JSON valid: {e}")

gemini_client = GeminiClient()
