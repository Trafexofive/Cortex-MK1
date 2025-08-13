from .models import InferenceRequest, InferenceResponse

def transform_request(provider: str, request: InferenceRequest) -> dict:
    """
    Transforms the standardized InferenceRequest into a provider-specific format.
    """
    if provider == "graphrag-app":
        # The graphrag-app expects a simple string message.
        return {"message": request.input.messages[-1].content}
    # Add other providers here
    else:
        # Default to forwarding the request as is.
        return request.dict()

def transform_response(provider: str, response: dict) -> InferenceResponse:
    """
    Transforms a provider-specific response into the standardized InferenceResponse format.
    """
    if provider == "graphrag-app":
        # The graphrag-app returns a simple JSON with a 'response' key.
        return InferenceResponse(
            id="some_id", # Generate a unique ID
            provider=provider,
            model="graphrag-app-model", # Or get from config
            output={
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": response.get("response", ""),
                        }
                    }
                ]
            },
        )
    # Add other providers here
    else:
        # Default to assuming the response is already in the correct format.
        return InferenceResponse(**response)
