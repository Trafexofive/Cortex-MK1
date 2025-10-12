#include "MiniGemini.hpp"
#include <curl/curl.h>
#include <json/json.h>
#include <sstream>
#include <cstdlib> // For getenv
#include <stdexcept>
#include <iostream> // For potential debug logging

// Libcurl write callback (Implementation remains the same)
size_t MiniGemini::writeCallback(void *contents, size_t size, size_t nmemb, void *userp) {
    ((std::string*)userp)->append((char*)contents, size * nmemb);
    return size * nmemb;
}

// Constructor implementation
MiniGemini::MiniGemini(const std::string& apiKey) :
    // Sensible defaults for Gemini
    m_model("gemini-2.0-flash"), // Use a common, stable model
    // m_model("gemini-2.5-pro-exp-04-14"),
    m_temperature(0.5), // Adjusted default temperature
    m_maxTokens(4096),
    m_baseUrl("https://generativelanguage.googleapis.com")  // Base URL without version
{
    if (!apiKey.empty()) {
        m_apiKey = apiKey;
    } else {
        const char* envKey = std::getenv("GEMINI_API_KEY");
        if (envKey != nullptr && envKey[0] != '\0') {
            m_apiKey = envKey;
            std::cout << "[INFO] GeminiClient: Using API key from GEMINI_API_KEY environment variable." << std::endl;
        } else {
            std::cerr << "[WARN] GeminiClient: API key not provided via constructor or GEMINI_API_KEY env var. API calls will likely fail." << std::endl;
            // Consider throwing here if the key is absolutely mandatory for initialization
            // throw std::invalid_argument("Gemini API key required: Provide via constructor or GEMINI_API_KEY env var");
        }
    }
     // Note: curl_global_init should ideally be called once in main()
}

// Helper function to determine API version based on model
std::string MiniGemini::getApiVersion() const {
    // gemini-1.5-* models use v1 (stable API)
    // gemini-2.0-* and experimental models use v1beta
    if (m_model.find("gemini-1.5") == 0) {
        return "v1";
    }
    return "v1beta";
}

// Helper function to build complete model endpoint URL
std::string MiniGemini::getModelUrl() const {
    return m_baseUrl + "/" + getApiVersion() + "/models/" + m_model;
}

// Configuration Setters
void MiniGemini::setApiKey(const std::string& apiKey) { m_apiKey = apiKey; }
void MiniGemini::setModel(const std::string& model) { m_model = model; }
void MiniGemini::setTemperature(double temperature) { m_temperature = temperature; }
void MiniGemini::setMaxTokens(int maxTokens) { m_maxTokens = maxTokens; }
void MiniGemini::setBaseUrl(const std::string& baseUrl) { m_baseUrl = baseUrl; }


// Generate implementation (Overrides base class)
std::string MiniGemini::generate(const std::string& prompt) {
    // Check if LLM Gateway URL is configured via environment variable
    const char* gatewayUrl = std::getenv("LLM_GATEWAY_URL");
    if (gatewayUrl && gatewayUrl[0] != '\0') {
        return generateViaGateway(prompt, gatewayUrl, false);
    }
    
    // Original direct API implementation
    if (m_apiKey.empty()) {
        throw ApiError("Gemini API key is not set.");
    }
    std::string url = getModelUrl() + ":generateContent?key=" + m_apiKey;

    // Build JSON payload specific to Gemini API
    Json::Value root;
    Json::Value content;
    Json::Value part;
    Json::Value genConfig;
    Json::Value systemInstruction;

    part["text"] = prompt;
    content["parts"].append(part);
    content["role"] = "user";
    root["contents"].append(content);

    // Add system instruction to enforce protocol
    Json::Value systemPart;
    systemPart["text"] = R"(CRITICAL INSTRUCTION: You MUST use this exact format for ALL responses:

<thought>
[Your reasoning and analysis here]
</thought>

<response final="true">
[Your final answer in Markdown]
</response>

RULES:
1. ALWAYS start with <thought> tag - explain your thinking
2. ALWAYS end with <response final="true"> tag - provide the answer  
3. NO plain text before or after these tags
4. NO markdown code fences (``` blocks)
5. Output XML tags directly

Example:
<thought>
The user greeted me. I should respond warmly.
</thought>

<response final="true">
Hello! How can I help you today?
</response>

This format is MANDATORY for every single response. Do not deviate from it.)";
    systemInstruction["parts"].append(systemPart);
    root["systemInstruction"] = systemInstruction;

    // Add generation config
    genConfig["temperature"] = m_temperature;
    genConfig["maxOutputTokens"] = m_maxTokens;
    root["generationConfig"] = genConfig;

    Json::StreamWriterBuilder writerBuilder;
    writerBuilder["indentation"] = "";
    std::string payload = Json::writeString(writerBuilder, root);

    try {
        std::string responseBody = performHttpRequest(url, payload);
        return parseJsonResponse(responseBody);
    } catch (const ApiError& e) {
        std::cerr << "[ERROR] GeminiClient API Error: " << e.what() << std::endl;
        throw;
    } catch (const std::exception& e) {
         std::cerr << "[ERROR] GeminiClient Request Failed: " << e.what() << std::endl;
        throw ApiError(std::string("Gemini request failed: ") + e.what());
    } catch (...) {
        std::cerr << "[ERROR] GeminiClient Unknown request failure." << std::endl;
        throw ApiError("Unknown error during Gemini request.");
    }
}


// HTTP request helper (Remains mostly the same, ensure correct headers)
std::string MiniGemini::performHttpRequest(const std::string& url, const std::string& payload) {
    CURL* curl = curl_easy_init();
    if (!curl) throw std::runtime_error("Failed to initialize libcurl");

    std::string readBuffer;
    long http_code = 0;
    struct curl_slist* headers = nullptr;
    // Ensure correct Content-Type for Gemini
    headers = curl_slist_append(headers, "Content-Type: application/json");
    // Wrap slist in unique_ptr for RAII
    std::unique_ptr<struct curl_slist, decltype(&curl_slist_free_all)> header_list(headers, curl_slist_free_all);

    curl_easy_setopt(curl, CURLOPT_URL, url.c_str());
    curl_easy_setopt(curl, CURLOPT_POSTFIELDS, payload.c_str());
    curl_easy_setopt(curl, CURLOPT_POSTFIELDSIZE, payload.length());
    curl_easy_setopt(curl, CURLOPT_HTTPHEADER, header_list.get());
    curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, writeCallback);
    curl_easy_setopt(curl, CURLOPT_WRITEDATA, &readBuffer);
    curl_easy_setopt(curl, CURLOPT_TIMEOUT, 30L); // Increased timeout slightly
    curl_easy_setopt(curl, CURLOPT_FOLLOWLOCATION, 1L); // Follow redirects
    curl_easy_setopt(curl, CURLOPT_NOPROGRESS, 1L); // Disable progress meter
    curl_easy_setopt(curl, CURLOPT_ACCEPT_ENCODING, ""); // Allow curl to handle encoding


    CURLcode res = curl_easy_perform(curl);
    std::unique_ptr<CURL, decltype(&curl_easy_cleanup)> curl_handle(curl, curl_easy_cleanup); // RAII cleanup


    if (res != CURLE_OK) {
        throw ApiError("curl_easy_perform() failed: " + std::string(curl_easy_strerror(res)));
    }

    curl_easy_getinfo(curl, CURLINFO_RESPONSE_CODE, &http_code);

    if (http_code < 200 || http_code >= 300) {
        std::ostringstream errMsg;
        errMsg << "HTTP Error: " << http_code;
        errMsg << " | Response: " << readBuffer.substr(0, 500); // Include more response context
         if (readBuffer.length() > 500) errMsg << "...";
        throw ApiError(errMsg.str());
    }

    return readBuffer;
}

// JSON parsing helper (Adapted for Gemini's typical response structure)
std::string MiniGemini::parseJsonResponse(const std::string& jsonResponse) const {
    Json::Value root;
    Json::CharReaderBuilder readerBuilder;
    std::unique_ptr<Json::CharReader> reader(readerBuilder.newCharReader());
    std::string errors;

    bool parsingSuccessful = reader->parse(jsonResponse.c_str(), jsonResponse.c_str() + jsonResponse.length(), &root, &errors);

    if (!parsingSuccessful) {
        throw ApiError("Failed to parse Gemini JSON response: " + errors);
    }

    // Check for Gemini-specific error structure first
    if (root.isMember("error") && root["error"].isObject()) {
        std::string errorMsg = "API Error: ";
        if (root["error"].isMember("message") && root["error"]["message"].isString()) {
            errorMsg += root["error"]["message"].asString();
        } else {
             errorMsg += Json::writeString(Json::StreamWriterBuilder(), root["error"]); // Dump error object if message missing
        }
         return errorMsg; // Return error message instead of throwing? Or throw ApiError(errorMsg)? Let's throw.
         throw ApiError(errorMsg);
    }

    // Navigate the expected Gemini success structure
    try {
        // Gemini structure: root -> candidates[0] -> content -> parts[0] -> text
        if (root.isMember("candidates") && root["candidates"].isArray() && !root["candidates"].empty()) {
            const Json::Value& firstCandidate = root["candidates"][0u];
            if (firstCandidate.isMember("content") && firstCandidate["content"].isObject()) {
                 const Json::Value& content = firstCandidate["content"];
                 if (content.isMember("parts") && content["parts"].isArray() && !content["parts"].empty()) {
                     const Json::Value& firstPart = content["parts"][0u];
                     if (firstPart.isMember("text") && firstPart["text"].isString()) {
                         return firstPart["text"].asString();
                     }
                 }
            }
             // Handle cases where content might be blocked (safety ratings)
             if (firstCandidate.isMember("finishReason") && firstCandidate["finishReason"].asString() != "STOP") {
                 std::string reason = firstCandidate["finishReason"].asString();
                 std::string safetyInfo = "";
                 if (firstCandidate.isMember("safetyRatings")) {
                    safetyInfo = Json::writeString(Json::StreamWriterBuilder(), firstCandidate["safetyRatings"]);
                 }
                 throw ApiError("Content generation stopped due to safety settings or other reason: " + reason + ". Safety Ratings: " + safetyInfo);
             }
        }
        // If structure wasn't as expected
        throw ApiError("Could not extract text from Gemini API response structure. Response: " + jsonResponse.substr(0, 500) + "...");

    } catch (const Json::Exception& e) { // Catch JSON access errors
        throw ApiError(std::string("JSON access error while parsing Gemini response: ") + e.what());
    } catch (const ApiError& e) { // Re-throw our specific errors
        throw;
    } catch (const std::exception& e) { // Catch other potential errors
         throw ApiError(std::string("Standard exception while parsing Gemini response: ") + e.what());
    }
}

// Streaming callback implementation
size_t MiniGemini::streamWriteCallback(void* contents, size_t size, size_t nmemb, void* userp) {
    size_t totalSize = size * nmemb;
    StreamCallbackData* data = static_cast<StreamCallbackData*>(userp);
    
    // Append received data to buffer
    data->buffer.append(static_cast<char*>(contents), totalSize);
    
    // Process complete lines (for Server-Sent Events format)
    size_t pos;
    while ((pos = data->buffer.find('\n')) != std::string::npos) {
        std::string line = data->buffer.substr(0, pos);
        data->buffer.erase(0, pos + 1);
        
        // Parse SSE data lines
        if (line.find("data: ") == 0) {
            std::string jsonData = line.substr(6); // Skip "data: "
            
            if (jsonData == "[DONE]") {
                data->userCallback("", true);
                continue;
            }
            
            try {
                Json::Value root;
                Json::CharReaderBuilder readerBuilder;
                std::string errs;
                std::istringstream stream(jsonData);
                
                if (Json::parseFromStream(readerBuilder, stream, &root, &errs)) {
                    // Extract text delta from Gemini streaming response
                    if (root.isMember("candidates") && root["candidates"].isArray() && 
                        !root["candidates"].empty()) {
                        const Json::Value& candidate = root["candidates"][0];
                        
                        if (candidate.isMember("content") && 
                            candidate["content"].isMember("parts") &&
                            candidate["content"]["parts"].isArray() &&
                            !candidate["content"]["parts"].empty()) {
                            
                            const Json::Value& part = candidate["content"]["parts"][0];
                            if (part.isMember("text") && part["text"].isString()) {
                                std::string token = part["text"].asString();
                                if (!token.empty()) {
                                    data->userCallback(token, false);
                                }
                            }
                        }
                    }
                }
            } catch (...) {
                // Ignore parsing errors for individual chunks
            }
        }
    }
    
    return totalSize;
}

// Streaming HTTP request implementation
void MiniGemini::performStreamingHttpRequest(const std::string& url, const std::string& payload, StreamCallback callback) {
    CURL* curl = curl_easy_init();
    if (!curl) throw std::runtime_error("Failed to initialize libcurl for streaming");

    struct curl_slist* headers = nullptr;
    headers = curl_slist_append(headers, "Content-Type: application/json");
    
    StreamCallbackData callbackData;
    callbackData.userCallback = callback;

    curl_easy_setopt(curl, CURLOPT_URL, url.c_str());
    curl_easy_setopt(curl, CURLOPT_POST, 1L);
    curl_easy_setopt(curl, CURLOPT_POSTFIELDS, payload.c_str());
    curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);
    curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, streamWriteCallback);
    curl_easy_setopt(curl, CURLOPT_WRITEDATA, &callbackData);
    curl_easy_setopt(curl, CURLOPT_TIMEOUT, 300L);

    CURLcode res = curl_easy_perform(curl);
    
    // Process any remaining data in buffer
    if (!callbackData.buffer.empty()) {
        callback(callbackData.buffer, false);
    }
    
    // Signal end of stream
    callback("", true);

    long http_code = 0;
    curl_easy_getinfo(curl, CURLINFO_RESPONSE_CODE, &http_code);

    curl_slist_free_all(headers);
    curl_easy_cleanup(curl);

    if (res != CURLE_OK) {
        throw ApiError(std::string("Streaming request failed: ") + curl_easy_strerror(res));
    }
    
    if (http_code != 200) {
        throw ApiError("Streaming request returned HTTP " + std::to_string(http_code));
    }
}

// Streaming generate implementation
void MiniGemini::generateStream(const std::string& prompt, StreamCallback callback) {
    // Check if LLM Gateway URL is configured via environment variable
    const char* gatewayUrl = std::getenv("LLM_GATEWAY_URL");
    if (gatewayUrl && gatewayUrl[0] != '\0') {
        generateStreamViaGateway(prompt, gatewayUrl, callback);
        return;
    }
    
    // Original direct API implementation
    if (m_apiKey.empty()) {
        throw ApiError("Gemini API key is not set.");
    }
    
    // Use streamGenerateContent endpoint with alt=sse parameter
    std::string url = getModelUrl() + ":streamGenerateContent?alt=sse&key=" + m_apiKey;

    // Build JSON payload (same as non-streaming)
    Json::Value root;
    Json::Value content;
    Json::Value part;
    Json::Value genConfig;
    Json::Value systemInstruction;

    part["text"] = prompt;
    content["parts"].append(part);
    content["role"] = "user";
    root["contents"].append(content);

    // Add system instruction to enforce protocol
    Json::Value systemPart;
    systemPart["text"] = R"(CRITICAL INSTRUCTION: You MUST use this exact format for ALL responses:

<thought>
[Your reasoning and analysis here]
</thought>

<response final="true">
[Your final answer in Markdown]
</response>

RULES:
1. ALWAYS start with <thought> tag - explain your thinking
2. ALWAYS end with <response final="true"> tag - provide the answer
3. NO plain text before or after these tags
4. NO markdown code fences (``` blocks)
5. Output XML tags directly

Example:
<thought>
The user greeted me. I should respond warmly.
</thought>

<response final="true">
Hello! How can I help you today?
</response>

This format is MANDATORY for every single response. Do not deviate from it.)";
    systemInstruction["parts"].append(systemPart);
    root["systemInstruction"] = systemInstruction;

    genConfig["temperature"] = m_temperature;
    genConfig["maxOutputTokens"] = m_maxTokens;
    root["generationConfig"] = genConfig;

    Json::StreamWriterBuilder writerBuilder;
    writerBuilder["indentation"] = "";
    std::string payload = Json::writeString(writerBuilder, root);

    try {
        performStreamingHttpRequest(url, payload, callback);
    } catch (const ApiError& e) {
        std::cerr << "[ERROR] GeminiClient Streaming API Error: " << e.what() << std::endl;
        throw;
    } catch (const std::exception& e) {
        std::cerr << "[ERROR] GeminiClient Streaming Request Failed: " << e.what() << std::endl;
        throw ApiError(std::string("Gemini streaming request failed: ") + e.what());
    } catch (...) {
        std::cerr << "[ERROR] GeminiClient Unknown streaming failure." << std::endl;
        throw ApiError("Unknown error during Gemini streaming request.");
    }
}

// ======================================================================================
// LLM GATEWAY INTEGRATION
// ======================================================================================

// Helper function to generate via LLM Gateway (non-streaming)
std::string MiniGemini::generateViaGateway(const std::string& prompt, const std::string& gatewayUrl, bool stream) {
    std::string url = std::string(gatewayUrl) + "/completion";
    
    // Build gateway-compatible JSON payload
    Json::Value root;
    Json::Value message;
    message["role"] = "user";
    message["content"] = prompt;
    root["messages"].append(message);
    root["provider"] = "gemini";
    root["model"] = m_model;
    root["stream"] = stream;
    root["temperature"] = m_temperature;
    root["max_tokens"] = m_maxTokens;
    
    Json::StreamWriterBuilder writerBuilder;
    writerBuilder["indentation"] = "";
    std::string payload = Json::writeString(writerBuilder, root);
    
    try {
        std::string responseBody = performHttpRequest(url, payload);
        
        // Parse gateway response
        Json::CharReaderBuilder readerBuilder;
        Json::Value responseJson;
        std::string errs;
        std::istringstream stream(responseBody);
        
        if (!Json::parseFromStream(readerBuilder, stream, &responseJson, &errs)) {
            throw ApiError("Failed to parse gateway response: " + errs);
        }
        
        // Extract content from gateway response
        if (responseJson.isMember("content") && responseJson["content"].isString()) {
            return responseJson["content"].asString();
        } else {
            throw ApiError("Gateway response missing 'content' field");
        }
    } catch (const ApiError& e) {
        std::cerr << "[ERROR] Gateway API Error: " << e.what() << std::endl;
        throw;
    } catch (const std::exception& e) {
        std::cerr << "[ERROR] Gateway Request Failed: " << e.what() << std::endl;
        throw ApiError(std::string("Gateway request failed: ") + e.what());
    }
}

// Helper function to generate via LLM Gateway (streaming)
void MiniGemini::generateStreamViaGateway(const std::string& prompt, const std::string& gatewayUrl, StreamCallback callback) {
    std::string url = std::string(gatewayUrl) + "/completion";
    
    // Build gateway-compatible JSON payload
    Json::Value root;
    Json::Value message;
    message["role"] = "user";
    message["content"] = prompt;
    root["messages"].append(message);
    root["provider"] = "gemini";
    root["model"] = m_model;
    root["stream"] = true;
    root["temperature"] = m_temperature;
    root["max_tokens"] = m_maxTokens;
    
    Json::StreamWriterBuilder writerBuilder;
    writerBuilder["indentation"] = "";
    std::string payload = Json::writeString(writerBuilder, root);
    
    try {
        performGatewayStreamingRequest(url, payload, callback);
    } catch (const ApiError& e) {
        std::cerr << "[ERROR] Gateway Streaming API Error: " << e.what() << std::endl;
        throw;
    } catch (const std::exception& e) {
        std::cerr << "[ERROR] Gateway Streaming Request Failed: " << e.what() << std::endl;
        throw ApiError(std::string("Gateway streaming request failed: ") + e.what());
    }
}

// Gateway-specific SSE streaming callback
size_t MiniGemini::gatewayStreamWriteCallback(void* contents, size_t size, size_t nmemb, void* userp) {
    size_t totalSize = size * nmemb;
    StreamCallbackData* data = static_cast<StreamCallbackData*>(userp);
    
    // Append received data to buffer
    data->buffer.append(static_cast<char*>(contents), totalSize);
    
    // Process complete lines (for Server-Sent Events format)
    size_t pos;
    while ((pos = data->buffer.find('\n')) != std::string::npos) {
        std::string line = data->buffer.substr(0, pos);
        data->buffer.erase(0, pos + 1);
        
        // Parse SSE data lines
        if (line.find("data: ") == 0) {
            std::string jsonData = line.substr(6); // Skip "data: "
            
            if (jsonData.empty() || jsonData == "[DONE]") {
                continue;
            }
            
            try {
                Json::Value root;
                Json::CharReaderBuilder readerBuilder;
                std::string errs;
                std::istringstream stream(jsonData);
                
                if (Json::parseFromStream(readerBuilder, stream, &root, &errs)) {
                    // Gateway format: {"content": "text chunk", "done": false}
                    if (root.isMember("content") && root["content"].isString()) {
                        std::string content = root["content"].asString();
                        bool done = root.isMember("done") && root["done"].asBool();
                        
                        if (!content.empty()) {
                            data->userCallback(content, false);
                        }
                        
                        if (done) {
                            data->userCallback("", true);
                        }
                    }
                }
            } catch (const std::exception& e) {
                std::cerr << "[WARN] Failed to parse gateway SSE chunk: " << e.what() << std::endl;
            }
        }
    }
    
    return totalSize;
}

// Gateway-specific streaming HTTP request
void MiniGemini::performGatewayStreamingRequest(const std::string& url, const std::string& payload, StreamCallback callback) {
    CURL* curl = curl_easy_init();
    if (!curl) throw std::runtime_error("Failed to initialize libcurl for gateway streaming");

    struct curl_slist* headers = nullptr;
    headers = curl_slist_append(headers, "Content-Type: application/json");
    
    StreamCallbackData callbackData;
    callbackData.userCallback = callback;

    curl_easy_setopt(curl, CURLOPT_URL, url.c_str());
    curl_easy_setopt(curl, CURLOPT_POST, 1L);
    curl_easy_setopt(curl, CURLOPT_POSTFIELDS, payload.c_str());
    curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);
    curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, gatewayStreamWriteCallback);
    curl_easy_setopt(curl, CURLOPT_WRITEDATA, &callbackData);
    curl_easy_setopt(curl, CURLOPT_TIMEOUT, 300L);

    CURLcode res = curl_easy_perform(curl);
    
    // Process any remaining data in buffer
    if (!callbackData.buffer.empty()) {
        callback(callbackData.buffer, false);
    }
    
    // Signal end of stream
    callback("", true);

    long http_code = 0;
    curl_easy_getinfo(curl, CURLINFO_RESPONSE_CODE, &http_code);

    curl_slist_free_all(headers);
    curl_easy_cleanup(curl);

    if (res != CURLE_OK) {
        throw ApiError(std::string("Gateway streaming request failed: ") + curl_easy_strerror(res));
    }
    
    if (http_code != 200) {
        throw ApiError("Gateway streaming request returned HTTP " + std::to_string(http_code));
    }
}
