#ifndef GEMINI_CLIENT_HPP
#define GEMINI_CLIENT_HPP

#include "modelApi.hpp" // Include the base class definition
#include <string>
#include <json/json.h> // For Json::Value (or your preferred JSON library)

// const std::string MODELS[] = {
//     // Main models
//     "gemini-2.0-flash",         // Latest Flash model
//     "gemini-2.0-flash-lite",    // Cost-efficient Flash variant
//     "gemini-1.5-flash",         // Previous generation Flash model
//     "gemini-1.5-flash-8b",      // Lightweight 8B parameter variant
//     "gemini-2.5-pro-exp-03-25", // Experimental Pro model
//
//     // Special purpose models
//     "gemini-embedding-exp",      // Text embedding model
//     "models/text-embedding-004", // Basic text embedding model
//     "imagen-3.0-generate-002",   // Image generation model
//     "models/embedding-001"       // Legacy embedding model
// };

const std::string MODELS[] = {
    // Main models
    "models/gemini-2.5-pro-exp-03-25", // Gemini 2.5 Pro Experimental
    "models/gemini-2.0-flash",         // Gemini 2.0 Flash (default production)
    "models/gemini-2.0-flash-lite",    // Gemini 2.0 Flash Lite (cost-efficient)
    "models/gemini-2.0-flash-thinking",// Gemini 2.0 Flash Thinking Experimental
    "models/gemini-1.5-pro",           // Gemini 1.5 Pro
    "models/gemini-1.5-flash",         // Gemini 1.5 Flash
    "models/gemini-1.5-flash-8b",      // Gemini 1.5 Flash 8B (lightweight)

    // Embedding models
    "models/text-embedding-004",       // Latest text embedding model
    "models/embedding-001",            // Legacy embedding model

    // Image generation
    "models/imagen-3.0-generate-002",  // Imagen 3.0 for text-to-image generation

    // Open models (Gemma)
    "models/gemma-2b",                 // Gemma 2B open model
    "models/gemma-7b",                 // Gemma 7B open model
    "models/gemma-9b",                 // Gemma 9B open model
    "models/gemma-27b"                 // Gemma 27B open model
};

class MiniGemini : public LLMClient {
public:
    // Constructor: API key is required (can be empty string to try ENV var)
    MiniGemini(const std::string& apiKey = "");

    // Override the pure virtual generate function from the base class
    std::string generate(const std::string& prompt) override;
    
    // Override streaming generation
    void generateStream(const std::string& prompt, StreamCallback callback) override;

    // --- Gemini-Specific Configuration ---
    void setApiKey(const std::string& apiKey);
    void setModel(const std::string& model) override;
    void setTemperature(double temperature) override;
    void setMaxTokens(int maxTokens) override;
    void setBaseUrl(const std::string& baseUrl); // Allow changing the base URL if needed

private:
    std::string m_apiKey;
    std::string m_model;
    double m_temperature;
    int m_maxTokens;
    std::string m_baseUrl;

    // Helper functions for API versioning
    std::string getApiVersion() const;
    std::string getModelUrl() const;
    
    // Helper functions for LLM Gateway integration
    std::string generateViaGateway(const std::string& prompt, const std::string& gatewayUrl, bool stream);
    void generateStreamViaGateway(const std::string& prompt, const std::string& gatewayUrl, StreamCallback callback);
    void performGatewayStreamingRequest(const std::string& url, const std::string& payload, StreamCallback callback);
    static size_t gatewayStreamWriteCallback(void* contents, size_t size, size_t nmemb, void* userp);

    // Internal helper for HTTP POST request (specific to Gemini structure)
    std::string performHttpRequest(const std::string& url, const std::string& payload);
    
    // Internal helper for streaming HTTP request
    void performStreamingHttpRequest(const std::string& url, const std::string& payload, StreamCallback callback);
    
    // Internal helper to parse Gemini's JSON response structure
    std::string parseJsonResponse(const std::string& jsonResponse) const;

    // Static helper for curl callback (can be shared or made global if needed)
    static size_t writeCallback(void* contents, size_t size, size_t nmemb, void* userp);
    
    // Streaming callback wrapper
    struct StreamCallbackData {
        StreamCallback userCallback;
        std::string buffer;
    };
    static size_t streamWriteCallback(void* contents, size_t size, size_t nmemb, void* userp);
};

#endif // GEMINI_CLIENT_HPP
