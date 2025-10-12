#pragma once
#include <stdexcept>
#include <string>
#include <functional>

// Custom exception for API errors (can be shared by all clients)
class ApiError : public std::runtime_error {
public:
    ApiError(const std::string& message) : std::runtime_error(message) {}
};

// Callback type for streaming token reception
// Parameters: token (string chunk), is_final (bool indicating end of stream)
using StreamCallback = std::function<void(const std::string& token, bool is_final)>;

// Abstract base class for LLM clients
class LLMClient {
public:
    // Virtual destructor is crucial for base classes with virtual functions
    virtual ~LLMClient() = default;

    // Pure virtual function that all derived clients MUST implement
    // Takes a prompt and returns the generated text or throws ApiError
    virtual std::string generate(const std::string& prompt) = 0;

    // Streaming version - calls callback for each token as it arrives
    // Default implementation: generates full response, then calls callback once
    virtual void generateStream(const std::string& prompt, StreamCallback callback) {
        std::string fullResponse = generate(prompt);
        callback(fullResponse, true);
    }

    // Optional: Add common configuration setters if desired,
    // but they might be better handled in derived classes if APIs differ significantly.
    virtual void setModel(const std::string& model) = 0;
    virtual void setTemperature(double temperature) = 0;
    virtual void setMaxTokens(int maxTokens) = 0;
};

