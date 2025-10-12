#include "Groq.hpp"
#include <curl/curl.h>
#include <json/json.h>
#include <sstream>
#include <cstdlib>
#include <stdexcept>
#include <iostream>
#include <memory>
#include <thread>
#include <chrono>
#include <ctime>

// Add these members to your header file:
// std::time_t m_lastRequestTime;
// int m_requestCount;
// static const int MAX_REQUESTS_PER_MINUTE = 30; // Conservative estimate

// Libcurl write callback
size_t GroqClient::writeCallback(void *contents, size_t size, size_t nmemb, void *userp) {
    ((std::string*)userp)->append((char*)contents, size * nmemb);
    return size * nmemb;
}

// Constructor implementation
GroqClient::GroqClient(const std::string& apiKey) :
    // m_model("deepseek-r1-distill-llama-70b"),
    m_model("qwen/qwen3-32b"),
    m_temperature(0.5),
    m_maxTokens(2048), // Reduced from 4096 to stay under TPM limit
    m_baseUrl("https://api.groq.com/openai/v1"),
    m_lastRequestTime(0),
    m_requestCount(0)
{
    if (!apiKey.empty()) {
        m_apiKey = apiKey;
    } else {
        const char* envKey = std::getenv("GROQ_API_KEY");
        if (envKey != nullptr && envKey[0] != '\0') {
            m_apiKey = envKey;
            std::cout << "[INFO] GroqClient: Using API key from GROQ_API_KEY environment variable." << std::endl;
        } else {
            std::cerr << "[WARN] GroqClient: API key not provided via constructor or GROQ_API_KEY env var. API calls will likely fail." << std::endl;
        }
    }
}

// Rate limiting helper
void GroqClient::enforceRateLimit() {
    std::time_t currentTime = std::time(nullptr);
    
    // Reset counter if more than a minute has passed
    if (currentTime - m_lastRequestTime >= 60) {
        m_requestCount = 0;
        m_lastRequestTime = currentTime;
    }
    
    // If we've hit our request limit, wait
    if (m_requestCount >= MAX_REQUESTS_PER_MINUTE) {
        int waitTime = 60 - (currentTime - m_lastRequestTime);
        if (waitTime > 0) {
            std::cout << "[INFO] Rate limit reached. Waiting " << waitTime << " seconds..." << std::endl;
            std::this_thread::sleep_for(std::chrono::seconds(waitTime));
            m_requestCount = 0;
            m_lastRequestTime = std::time(nullptr);
        }
    }
    
    m_requestCount++;
}

// Token estimation helper (rough approximation)
int GroqClient::estimateTokens(const std::string& text) const {
    // Very rough estimation: ~4 characters per token
    // This is conservative for most languages
    return static_cast<int>(text.length() / 4.0) + 50; // +50 for overhead
}

// Configuration Setters
void GroqClient::setApiKey(const std::string& apiKey) { m_apiKey = apiKey; }
void GroqClient::setModel(const std::string& model) { m_model = model; }
void GroqClient::setTemperature(double temperature) { m_temperature = temperature; }
void GroqClient::setMaxTokens(int maxTokens) { 
    // Cap max tokens to stay under TPM limit
    const int MAX_SAFE_TOKENS = 2000;
    m_maxTokens = (maxTokens > MAX_SAFE_TOKENS) ? MAX_SAFE_TOKENS : maxTokens;
    if (maxTokens > MAX_SAFE_TOKENS) {
        std::cout << "[WARN] Max tokens capped at " << MAX_SAFE_TOKENS << " to avoid TPM limits" << std::endl;
    }
}
void GroqClient::setBaseUrl(const std::string& baseUrl) { m_baseUrl = baseUrl; }

// Generate implementation with rate limiting and retry logic
std::string GroqClient::generate(const std::string& prompt) {
    if (m_apiKey.empty()) {
        throw ApiError("Groq API key is not set.");
    }
    
    // Estimate tokens and warn if too large
    int estimatedTokens = estimateTokens(prompt) + m_maxTokens;
    if (estimatedTokens > 5500) { // Leave buffer under 6000 TPM limit
        std::cout << "[WARN] Estimated tokens (" << estimatedTokens 
                  << ") may exceed TPM limit. Consider reducing prompt size." << std::endl;
    }
    
    // Enforce rate limiting
    enforceRateLimit();
    
    std::string url = m_baseUrl + "/chat/completions";

    // Build JSON payload
    Json::Value root;
    Json::Value message;
    Json::Value messagesArray(Json::arrayValue);

    message["role"] = "user";
    message["content"] = prompt;
    messagesArray.append(message);

    root["messages"] = messagesArray;
    root["model"] = m_model;
    root["temperature"] = m_temperature;
    root["max_tokens"] = m_maxTokens;

    Json::StreamWriterBuilder writerBuilder;
    writerBuilder["indentation"] = "";
    std::string payload = Json::writeString(writerBuilder, root);

    const int MAX_RETRIES = 3;
    int attempt = 0;
    
    while (attempt < MAX_RETRIES) {
        try {
            std::string responseBody = performHttpRequest(url, payload);
            return parseJsonResponse(responseBody);
            
        } catch (const ApiError& e) {
            std::string errorMsg = e.what();
            
            // Check if it's a rate limit error
            if (errorMsg.find("rate_limit_exceeded") != std::string::npos ||
                errorMsg.find("Request too large") != std::string::npos) {
                
                attempt++;
                if (attempt < MAX_RETRIES) {
                    int backoffTime = 10 * attempt; // Exponential backoff: 10s, 20s, 30s
                    std::cout << "[WARN] Rate limit hit. Retrying in " << backoffTime 
                              << " seconds... (Attempt " << attempt + 1 << "/" << MAX_RETRIES << ")" << std::endl;
                    std::this_thread::sleep_for(std::chrono::seconds(backoffTime));
                    continue;
                } else {
                    std::cerr << "[ERROR] Max retries exceeded for rate limit." << std::endl;
                    throw;
                }
            } else {
                // Non-rate-limit error, don't retry
                std::cerr << "[ERROR] GroqClient API Error: " << e.what() << std::endl;
                throw;
            }
            
        } catch (const std::exception& e) {
            std::cerr << "[ERROR] GroqClient Request Failed: " << e.what() << std::endl;
            throw ApiError(std::string("Groq request failed: ") + e.what());
        } catch (...) {
            std::cerr << "[ERROR] GroqClient Unknown request failure." << std::endl;
            throw ApiError("Unknown error during Groq request.");
        }
    }
    
    throw ApiError("All retry attempts failed.");
}

// HTTP request helper (unchanged)
std::string GroqClient::performHttpRequest(const std::string& url, const std::string& payload) {
    CURL* curl = curl_easy_init();
    if (!curl) throw std::runtime_error("Failed to initialize libcurl");

    std::string readBuffer;
    long http_code = 0;
    struct curl_slist* headers = nullptr;

    std::string authHeader = "Authorization: Bearer " + m_apiKey;
    headers = curl_slist_append(headers, authHeader.c_str());
    headers = curl_slist_append(headers, "Content-Type: application/json");
    std::unique_ptr<struct curl_slist, decltype(&curl_slist_free_all)> header_list(headers, curl_slist_free_all);

    curl_easy_setopt(curl, CURLOPT_URL, url.c_str());
    curl_easy_setopt(curl, CURLOPT_POSTFIELDS, payload.c_str());
    curl_easy_setopt(curl, CURLOPT_POSTFIELDSIZE, payload.length());
    curl_easy_setopt(curl, CURLOPT_HTTPHEADER, header_list.get());
    curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, writeCallback);
    curl_easy_setopt(curl, CURLOPT_WRITEDATA, &readBuffer);
    curl_easy_setopt(curl, CURLOPT_TIMEOUT, 60L); // Increased timeout for retries
    curl_easy_setopt(curl, CURLOPT_FOLLOWLOCATION, 1L);
    curl_easy_setopt(curl, CURLOPT_NOPROGRESS, 1L);
    curl_easy_setopt(curl, CURLOPT_ACCEPT_ENCODING, "");

    CURLcode res = curl_easy_perform(curl);
    std::unique_ptr<CURL, decltype(&curl_easy_cleanup)> curl_handle(curl, curl_easy_cleanup);

    if (res != CURLE_OK) {
        throw ApiError("curl_easy_perform() failed: " + std::string(curl_easy_strerror(res)));
    }
    curl_easy_getinfo(curl, CURLINFO_RESPONSE_CODE, &http_code);

    if (http_code < 200 || http_code >= 300) {
        std::ostringstream errMsg;
        errMsg << "HTTP Error: " << http_code;
        errMsg << " | Response: " << readBuffer.substr(0, 500);
        if (readBuffer.length() > 500) errMsg << "...";
        throw ApiError(errMsg.str());
    }

    return readBuffer;
}

// JSON parsing (unchanged)
std::string GroqClient::parseJsonResponse(const std::string& jsonResponse) const {
    Json::Value root;
    Json::CharReaderBuilder readerBuilder;
    std::unique_ptr<Json::CharReader> reader(readerBuilder.newCharReader());
    std::string errors;

    bool parsingSuccessful = reader->parse(jsonResponse.c_str(), jsonResponse.c_str() + jsonResponse.length(), &root, &errors);

    if (!parsingSuccessful) {
        throw ApiError("Failed to parse Groq JSON response: " + errors);
    }

    if (root.isMember("error") && root["error"].isObject()) {
        std::string errorMsg = "API Error: ";
        if (root["error"].isMember("message") && root["error"]["message"].isString()) {
            errorMsg += root["error"]["message"].asString();
        } else if (root["error"].isMember("type") && root["error"]["type"].isString()) {
            errorMsg += root["error"]["type"].asString();
        } else {
            errorMsg += Json::writeString(Json::StreamWriterBuilder(), root["error"]);
        }
        throw ApiError(errorMsg);
    }
    
    if (root.isMember("detail") && root["detail"].isString()) {
        throw ApiError("API Error Detail: " + root["detail"].asString());
    }

    try {
        if (root.isMember("choices") && root["choices"].isArray() && !root["choices"].empty()) {
            const Json::Value& firstChoice = root["choices"][0u];
            if (firstChoice.isMember("message") && firstChoice["message"].isObject()) {
                const Json::Value& message = firstChoice["message"];
                if (message.isMember("content") && message["content"].isString()) {
                    return message["content"].asString();
                }
            }
            if (firstChoice.isMember("finish_reason") && firstChoice["finish_reason"].asString() != "stop") {
                throw ApiError("Content generation finished unexpectedly. Reason: " + firstChoice["finish_reason"].asString());
            }
        }
        throw ApiError("Could not extract content from Groq API response structure. Response: " + jsonResponse.substr(0, 500) + "...");

    } catch (const Json::Exception& e) {
        throw ApiError(std::string("JSON access error while parsing Groq response: ") + e.what());
    } catch (const ApiError& e) {
        throw;
    } catch (const std::exception& e) {
        throw ApiError(std::string("Standard exception while parsing Groq response: ") + e.what());
    }
}
