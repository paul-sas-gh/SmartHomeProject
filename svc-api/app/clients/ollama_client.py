import requests
import json
import logging
from app.config import settings

logger = logging.getLogger(__name__)

class OllamaClient:
    def __init__(self, base_url: str = None, model: str = None):
        self.base_url = base_url or settings.ollama_base_url
        self.model = model or settings.llm_model
        self.chat_url = f"{self.base_url}/api/chat"

    def chat(self, messages: list[dict], system_prompt: str = None) -> str:
        """
        Trimite o listă de mesaje către Ollama folosind endpoint-ul /api/chat.
        """
        payload_messages = []
        if system_prompt:
            payload_messages.append({"role": "system", "content": system_prompt})
        
        payload_messages.extend(messages)

        payload = {
            "model": self.model,
            "messages": payload_messages,
            "stream": False,
            "options": {
                "temperature": 0
            }
        }

        try:
            response = requests.post(self.chat_url, json=payload, timeout=120)
            response.raise_for_status()
            result = response.json()
            return result.get("message", {}).get("content", "")
        except Exception as e:
            logger.error(f"Eroare la apelul Ollama: {e}")
            raise

    def generate_json(self, prompt: str, system_prompt: str = None) -> dict:
        """
        Cere un răspuns în format JSON de la Ollama.
        """
        messages = [{"role": "user", "content": prompt}]
        response_text = self.chat(messages, system_prompt)
        
        try:
            # Încercăm să găsim JSON-ul în text dacă modelul adaugă explicații
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            if start != -1 and end != 0:
                json_str = response_text[start:end]
                return json.loads(json_str)
            return json.loads(response_text)
        except Exception as e:
            logger.error(f"Eroare la parsarea JSON din răspunsul LLM: {e}")
            logger.debug(f"Răspuns brut: {response_text}")
            raise ValueError(f"LLM nu a returnat un JSON valid: {e}")

ollama_client = OllamaClient()
