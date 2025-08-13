from .gemini import GeminiProvider
from .groq import GroqProvider

PROVIDERS = {
    "gemini-1.5-flash-latest": GeminiProvider(),
    "llama3-8b-8192": GroqProvider(),
}

def get_provider(model_name: str):
    # This is a simplified manager for the B-Line
    if "gemini" in model_name.lower():
        return PROVIDERS["gemini-2.5-flash"]
    elif "llama" in model_name.lower():
        return PROVIDERS["llama3-8b-8192"]
    else:
        raise ValueError(f"No provider found for model: {model_name}")
