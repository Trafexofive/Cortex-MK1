#include "Relic.hpp"
#include "Utils.hpp"
#include <yaml-cpp/yaml.h>
#include <fstream>
#include <sstream>
#include <curl/curl.h>
#include <cstdlib>
#include <iostream>
#include <unistd.h>  // For sleep()

// Utility for expanding environment variables in strings
static std::string expandEnvVars(const std::string& input) {
    std::string result = input;
    size_t pos = 0;
    
    while ((pos = result.find("${", pos)) != std::string::npos) {
        size_t end = result.find("}", pos);
        if (end == std::string::npos) break;
        
        std::string fullVar = result.substr(pos, end - pos + 1);
        std::string varContent = result.substr(pos + 2, end - pos - 2);
        
        // Handle ${VAR:-default} syntax
        std::string varName, defaultValue;
        size_t colonDash = varContent.find(":-");
        if (colonDash != std::string::npos) {
            varName = varContent.substr(0, colonDash);
            defaultValue = varContent.substr(colonDash + 2);
        } else {
            varName = varContent;
        }
        
        const char* envVal = std::getenv(varName.c_str());
        std::string replacement = envVal ? envVal : defaultValue;
        
        result.replace(pos, fullVar.length(), replacement);
        pos += replacement.length();
    }
    
    return result;
}

// CURL callback for HTTP responses
static size_t writeCallback(void* contents, size_t size, size_t nmemb, std::string* userp) {
    userp->append((char*)contents, size * nmemb);
    return size * nmemb;
}

// ============================================================================
// Relic Implementation
// ============================================================================

Relic::Relic(const std::string& manifestPath) 
    : running(false) {
    loadManifest(manifestPath);
}

Relic::~Relic() {
    if (running) {
        stop();
    }
}

void Relic::loadManifest(const std::string& manifestPath) {
    try {
        YAML::Node config = YAML::LoadFile(manifestPath);
        
        // Basic metadata
        name = config["name"].as<std::string>();
        summary = config["summary"] ? config["summary"].as<std::string>() : "";
        description = config["description"] ? config["description"].as<std::string>() : "";
        author = config["author"] ? config["author"].as<std::string>() : "";
        version = config["version"] ? config["version"].as<std::string>("1.0") : "1.0";
        state = config["state"] ? config["state"].as<std::string>("stable") : "stable";
        serviceType = config["service_type"] ? config["service_type"].as<std::string>("service") : "service";
        
        // Interface configuration
        if (config["interface"]) {
            auto iface = config["interface"];
            interfaceType = iface["type"] ? iface["type"].as<std::string>() : "rest_api";
            
            // base_url is optional
            if (iface["base_url"]) {
                baseUrl = expandEnvVars(iface["base_url"].as<std::string>());
            }
            
            // Load endpoints
            if (iface["endpoints"]) {
                for (const auto& ep : iface["endpoints"]) {
                    RelicEndpoint endpoint;
                    endpoint.name = ep["name"].as<std::string>();
                    endpoint.method = ep["method"].as<std::string>("GET");
                    endpoint.path = ep["path"].as<std::string>();
                    endpoint.description = ep["description"] ? ep["description"].as<std::string>() : "";
                    
                    if (ep["parameters"]) {
                        for (auto it = ep["parameters"].begin(); it != ep["parameters"].end(); ++it) {
                            std::string paramName = it->first.as<std::string>();
                            Json::Value paramSchema;
                            
                            // Convert YAML to JSON
                            auto paramNode = it->second;
                            if (paramNode["type"]) {
                                paramSchema["type"] = paramNode["type"].as<std::string>();
                            }
                            if (paramNode["required"]) {
                                paramSchema["required"] = paramNode["required"].as<bool>();
                            }
                            
                            endpoint.parameters[paramName] = paramSchema;
                        }
                    }
                    
                    endpoints.push_back(endpoint);
                }
            }
        }
        
        // Health check
        if (config["health_check"]) {
            auto hc = config["health_check"];
            healthCheck.type = hc["type"] ? hc["type"].as<std::string>() : "api_request";
            healthCheck.endpoint = hc["endpoint"] ? hc["endpoint"].as<std::string>() : "/health";
            healthCheck.method = hc["method"] ? hc["method"].as<std::string>() : "GET";
            healthCheck.expectedStatus = hc["expected_status"] ? hc["expected_status"].as<int>() : 200;
            healthCheck.timeoutSeconds = hc["timeout_seconds"] ? hc["timeout_seconds"].as<int>() : 5;
            healthCheck.intervalSeconds = hc["interval_seconds"] ? hc["interval_seconds"].as<int>() : 30;
        }
        
        // Deployment configuration
        if (config["deployment"]) {
            auto deploy = config["deployment"];
            deployment.type = deploy["type"] ? deploy["type"].as<std::string>() : "docker";
            
            if (deploy["docker_compose_file"]) {
                // Get directory of manifest for relative path
                size_t lastSlash = manifestPath.find_last_of('/');
                std::string manifestDir = lastSlash != std::string::npos ? 
                    manifestPath.substr(0, lastSlash) : ".";
                
                std::string composeFile = deploy["docker_compose_file"].as<std::string>();
                if (composeFile.find("./") == 0) {
                    deployment.dockerComposeFile = manifestDir + "/" + composeFile.substr(2);
                } else if (composeFile[0] != '/') {
                    deployment.dockerComposeFile = manifestDir + "/" + composeFile;
                } else {
                    deployment.dockerComposeFile = composeFile;
                }
            }
            
            if (deploy["image"]) {
                deployment.imageName = deploy["image"].as<std::string>();
            }
        }
        
        // Environment variables
        if (config["environment"] && config["environment"]["variables"]) {
            for (auto it = config["environment"]["variables"].begin(); 
                 it != config["environment"]["variables"].end(); ++it) {
                std::string key = it->first.as<std::string>();
                std::string value = it->second.as<std::string>();
                environmentVars[key] = expandEnvVars(value);
            }
        }
        
        logMessage(LogLevel::INFO, "Loaded relic manifest", "Name: " + name);
        
    } catch (const std::exception& e) {
        logMessage(LogLevel::ERROR, "Failed to load relic manifest", 
                  "Path: " + manifestPath + ", Error: " + e.what());
        throw;
    }
}

bool Relic::start() {
    if (running) {
        logMessage(LogLevel::WARN, "Relic already running", "Name: " + name);
        return true;
    }
    
    logMessage(LogLevel::INFO, "Starting relic", "Name: " + name);
    
    if (deployment.type == "docker" || deployment.type == "docker_compose") {
        return startDocker();
    } else if (deployment.type == "external") {
        // External services are assumed to be already running
        running = true;
        return checkHealth();
    }
    
    logMessage(LogLevel::ERROR, "Unsupported deployment type", "Type: " + deployment.type);
    return false;
}

bool Relic::stop() {
    if (!running) {
        return true;
    }
    
    logMessage(LogLevel::INFO, "Stopping relic", "Name: " + name);
    
    if (deployment.type == "docker" || deployment.type == "docker_compose") {
        return stopDocker();
    } else if (deployment.type == "external") {
        running = false;
        return true;
    }
    
    return false;
}

bool Relic::restart() {
    return stop() && start();
}

bool Relic::isRunning() const {
    return running;
}

bool Relic::isHealthy() const {
    return const_cast<Relic*>(this)->checkHealth();
}

bool Relic::startDocker() {
    if (deployment.dockerComposeFile.empty()) {
        logMessage(LogLevel::ERROR, "No docker-compose file specified", "Relic: " + name);
        return false;
    }
    
    // Build environment variable exports
    std::string envExports;
    for (const auto& pair : environmentVars) {
        envExports += "export " + pair.first + "='" + pair.second + "' && ";
    }
    
    // Start docker compose
    std::string cmd = envExports + "docker-compose -f " + deployment.dockerComposeFile + 
                     " -p relic_" + name + " up -d 2>&1";
    
    logMessage(LogLevel::DEBUG, "Executing docker command", cmd);
    std::string output = executeDockerCommand(cmd);
    
    if (output.find("error") != std::string::npos || 
        output.find("Error") != std::string::npos) {
        logMessage(LogLevel::ERROR, "Failed to start docker", output);
        return false;
    }
    
    running = true;
    
    // Wait for health check
    int maxRetries = 30;  // 30 seconds
    for (int i = 0; i < maxRetries; i++) {
        if (checkHealth()) {
            logMessage(LogLevel::INFO, "Relic is healthy", "Name: " + name);
            return true;
        }
        sleep(1);
    }
    
    logMessage(LogLevel::WARN, "Relic started but health check failing", "Name: " + name);
    return true;  // Still return true, health might come later
}

bool Relic::stopDocker() {
    std::string cmd = "docker-compose -f " + deployment.dockerComposeFile + 
                     " -p relic_" + name + " down 2>&1";
    
    logMessage(LogLevel::DEBUG, "Executing docker command", cmd);
    std::string output = executeDockerCommand(cmd);
    
    running = false;
    return true;
}

bool Relic::checkHealth() {
    if (healthCheck.type == "api_request") {
        try {
            std::string response = httpRequest(healthCheck.method, healthCheck.endpoint);
            // Simple check - if we got a response without exception, consider it healthy
            return true;
        } catch (...) {
            return false;
        }
    }
    
    // For now, assume healthy if not api_request
    return true;
}

std::string Relic::executeDockerCommand(const std::string& cmd) {
    std::array<char, 128> buffer;
    std::string result;
    
    FILE* pipe = popen(cmd.c_str(), "r");
    if (!pipe) {
        return "ERROR: Failed to execute command";
    }
    
    while (fgets(buffer.data(), buffer.size(), pipe) != nullptr) {
        result += buffer.data();
    }
    
    pclose(pipe);
    return result;
}

Json::Value Relic::callEndpoint(const std::string& endpointName, 
                                const Json::Value& parameters) {
    // Find endpoint
    const RelicEndpoint* endpoint = nullptr;
    for (const auto& ep : endpoints) {
        if (ep.name == endpointName) {
            endpoint = &ep;
            break;
        }
    }
    
    if (!endpoint) {
        Json::Value error;
        error["error"] = "Endpoint not found: " + endpointName;
        return error;
    }
    
    // Build path with parameters
    std::string path = endpoint->path;
    Json::Value body;
    
    // Replace path parameters like {key}
    for (auto it = parameters.begin(); it != parameters.end(); ++it) {
        std::string paramName = it.key().asString();
        std::string placeholder = "{" + paramName + "}";
        
        if (path.find(placeholder) != std::string::npos) {
            // Path parameter
            std::string value;
            if ((*it).isString()) {
                value = (*it).asString();
            } else {
                Json::StreamWriterBuilder builder;
                builder["indentation"] = "";
                value = Json::writeString(builder, *it);
            }
            
            // URL-encode the value
            CURL* curl = curl_easy_init();
            if (curl) {
                char* encoded = curl_easy_escape(curl, value.c_str(), value.length());
                if (encoded) {
                    path.replace(path.find(placeholder), placeholder.length(), encoded);
                    curl_free(encoded);
                }
                curl_easy_cleanup(curl);
            }
        } else {
            // Body parameter
            body[paramName] = *it;
        }
    }
    
    // Make HTTP request
    try {
        std::string response = httpRequest(endpoint->method, path, body);
        
        // Parse JSON response
        Json::CharReaderBuilder builder;
        Json::Value result;
        std::string errors;
        std::istringstream stream(response);
        
        if (Json::parseFromStream(builder, stream, &result, &errors)) {
            return result;
        }
        
        // If not JSON, return as string
        result["response"] = response;
        return result;
        
    } catch (const std::exception& e) {
        Json::Value error;
        error["error"] = e.what();
        return error;
    }
}

std::string Relic::httpRequest(const std::string& method,
                              const std::string& path,
                              const Json::Value& body,
                              const std::map<std::string, std::string>& headers) {
    CURL* curl = curl_easy_init();
    if (!curl) {
        throw std::runtime_error("Failed to initialize CURL");
    }
    
    std::string url = baseUrl + path;
    std::string response;
    
    curl_easy_setopt(curl, CURLOPT_URL, url.c_str());
    curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, writeCallback);
    curl_easy_setopt(curl, CURLOPT_WRITEDATA, &response);
    curl_easy_setopt(curl, CURLOPT_TIMEOUT, (long)healthCheck.timeoutSeconds);
    
    struct curl_slist* headerList = nullptr;
    headerList = curl_slist_append(headerList, "Content-Type: application/json");
    
    for (const auto& pair : headers) {
        std::string header = pair.first + ": " + pair.second;
        headerList = curl_slist_append(headerList, header.c_str());
    }
    
    curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headerList);
    
    std::string bodyStr;
    if (!body.isNull() && (method == "POST" || method == "PUT" || method == "PATCH")) {
        Json::StreamWriterBuilder builder;
        builder["indentation"] = "";
        bodyStr = Json::writeString(builder, body);
        curl_easy_setopt(curl, CURLOPT_POSTFIELDS, bodyStr.c_str());
    }
    
    if (method == "POST") {
        curl_easy_setopt(curl, CURLOPT_POST, 1L);
    } else if (method == "PUT") {
        curl_easy_setopt(curl, CURLOPT_CUSTOMREQUEST, "PUT");
    } else if (method == "DELETE") {
        curl_easy_setopt(curl, CURLOPT_CUSTOMREQUEST, "DELETE");
    } else if (method == "PATCH") {
        curl_easy_setopt(curl, CURLOPT_CUSTOMREQUEST, "PATCH");
    }
    
    CURLcode res = curl_easy_perform(curl);
    
    long httpCode = 0;
    curl_easy_getinfo(curl, CURLINFO_RESPONSE_CODE, &httpCode);
    
    curl_slist_free_all(headerList);
    curl_easy_cleanup(curl);
    
    if (res != CURLE_OK) {
        throw std::runtime_error(std::string("HTTP request failed: ") + curl_easy_strerror(res));
    }
    
    return response;
}

std::string Relic::getStatus() const {
    Json::Value status;
    status["name"] = name;
    status["running"] = running;
    status["healthy"] = const_cast<Relic*>(this)->checkHealth();
    status["base_url"] = baseUrl;
    status["service_type"] = serviceType;
    
    Json::StreamWriterBuilder builder;
    builder["indentation"] = "  ";
    return Json::writeString(builder, status);
}

Json::Value Relic::getMetrics() const {
    Json::Value metrics;
    metrics["name"] = name;
    metrics["running"] = running;
    metrics["healthy"] = const_cast<Relic*>(this)->checkHealth();
    metrics["endpoint_count"] = static_cast<int>(endpoints.size());
    return metrics;
}

// ============================================================================
// RelicManager Implementation
// ============================================================================

RelicManager& RelicManager::getInstance() {
    static RelicManager instance;
    return instance;
}

bool RelicManager::loadRelic(const std::string& manifestPath) {
    try {
        Relic* relic = new Relic(manifestPath);
        std::string name = relic->getName();
        
        if (relics.count(name)) {
            logMessage(LogLevel::WARN, "Relic already loaded, replacing", "Name: " + name);
            delete relics[name];
        }
        
        relics[name] = relic;
        logMessage(LogLevel::INFO, "Relic loaded", "Name: " + name);
        return true;
        
    } catch (const std::exception& e) {
        logMessage(LogLevel::ERROR, "Failed to load relic", 
                  "Path: " + manifestPath + ", Error: " + e.what());
        return false;
    }
}

bool RelicManager::startRelic(const std::string& relicName) {
    if (!relics.count(relicName)) {
        logMessage(LogLevel::ERROR, "Relic not found", "Name: " + relicName);
        return false;
    }
    
    return relics[relicName]->start();
}

bool RelicManager::stopRelic(const std::string& relicName) {
    if (!relics.count(relicName)) {
        return false;
    }
    
    return relics[relicName]->stop();
}

bool RelicManager::restartRelic(const std::string& relicName) {
    if (!relics.count(relicName)) {
        return false;
    }
    
    return relics[relicName]->restart();
}

Relic* RelicManager::getRelic(const std::string& name) {
    if (relics.count(name)) {
        return relics[name];
    }
    return nullptr;
}

std::vector<std::string> RelicManager::listRelics() const {
    std::vector<std::string> names;
    for (const auto& pair : relics) {
        names.push_back(pair.first);
    }
    return names;
}

void RelicManager::stopAll() {
    stopHealthMonitoring();
    
    for (auto& pair : relics) {
        pair.second->stop();
        delete pair.second;
    }
    relics.clear();
}

RelicManager::RelicManager() : monitoring(false), monitorThread(nullptr) {}

void RelicManager::startHealthMonitoring() {
    if (monitoring) {
        return;  // Already monitoring
    }
    
    monitoring = true;
    monitorThread = new std::thread(&RelicManager::healthMonitorLoop, this);
    logMessage(LogLevel::INFO, "Relic health monitoring started");
}

void RelicManager::stopHealthMonitoring() {
    if (!monitoring) {
        return;
    }
    
    monitoring = false;
    if (monitorThread) {
        monitorThread->join();
        delete monitorThread;
        monitorThread = nullptr;
    }
    logMessage(LogLevel::INFO, "Relic health monitoring stopped");
}

void RelicManager::healthMonitorLoop() {
    while (monitoring) {
        checkAllHealth();
        
        // Sleep for 30 seconds between checks
        for (int i = 0; i < 30 && monitoring; i++) {
            std::this_thread::sleep_for(std::chrono::seconds(1));
        }
    }
}

void RelicManager::checkAllHealth() {
    for (auto& pair : relics) {
        Relic* relic = pair.second;
        
        if (!relic->isRunning()) {
            continue;  // Don't check health if not running
        }
        
        bool healthy = relic->isHealthy();
        
        if (!healthy) {
            logMessage(LogLevel::WARN, 
                      "Relic '" + relic->getName() + "' is unhealthy. Attempting restart...");
            
            if (relic->restart()) {
                logMessage(LogLevel::INFO, 
                          "Successfully restarted relic '" + relic->getName() + "'");
            } else {
                logMessage(LogLevel::ERROR, 
                          "Failed to restart relic '" + relic->getName() + "'");
            }
        }
    }
}
