#ifndef GROQ_CLIENT_HPP
#define GROQ_CLIENT_HPP

#include "modelApi.hpp" // Include the base class definition
#include <string>
#include <json/json.h> // Or your preferred JSON library

// time
#include <ctime>

class GroqClient : public LLMClient {
public:
    // Constructor: API key is required (can be empty string to try ENV var)
    GroqClient(const std::string& apiKey = "");

    // Override the pure virtual generate function from the base class
    std::string generate(const std::string& prompt) override;

    // --- Groq-Specific Configuration ---
    void setApiKey(const std::string& apiKey);
    void setModel(const std::string& model) override;
    void setTemperature(double temperature) override;
    void setMaxTokens(int maxTokens) override;
    void setBaseUrl(const std::string& baseUrl); // Default: https://api.groq.com/openai/v1

private:
    std::string m_apiKey;
    std::string m_model;
    double m_temperature;
    int m_maxTokens;

    std::time_t m_lastRequestTime;
    int m_requestCount;
    static const int MAX_REQUESTS_PER_MINUTE = 30; // Adjust based on your tier
    
    // Helper methods
    void enforceRateLimit();
    int estimateTokens(const std::string& text) const;   std::string m_baseUrl;

    // Internal helper for HTTP POST request (specific to Groq/OpenAI structure)
    std::string performHttpRequest(const std::string& url, const std::string& payload);
    // Internal helper to parse Groq/OpenAI JSON response structure
    std::string parseJsonResponse(const std::string& jsonResponse) const;

    // Static helper for curl callback
    static size_t writeCallback(void* contents, size_t size, size_t nmemb, void* userp);
};

#endif // GROQ_CLIENT_HPP
