from .gemini import GeminiProvider
# Import other providers like GroqProvider here

PROVIDERS = {
    "gemini": GeminiProvider(),
    # "groq": GroqProvider(),
}

def get_provider(model_name: str):
    # Simple logic for B-Line: determine provider from model name string
    if "gemini" in model_name.lower():
        return PROVIDERS["gemini"]
    # elif "llama" in model_name.lower() or "mixtral" in model_name.lower():
    #     return PROVIDERS["groq"]
    else:
        # Default to Gemini if no clear provider identified
        return PROVIDERS["gemini"]
