#pragma once

#include <json/json.h>
#include <string>
#include <vector>
#include <map>
#include <functional>
#include <thread>
#include <atomic>

/**
 * ==============================================================================
 * RELIC - Persistent Service Infrastructure
 * ==============================================================================
 * 
 * Relics are long-running services that provide persistent functionality:
 * - Databases (SQL, NoSQL, Vector stores)
 * - Caches (Redis, KV stores)
 * - Message queues
 * - External APIs
 * - Custom microservices
 * 
 * Relics are:
 * - Self-contained (docker-compose or standalone)
 * - Persistent (survive agent restarts)
 * - Accessible via REST API
 * - Health-checked and auto-recovered
 */

// Relic endpoint definition
struct RelicEndpoint {
    std::string name;
    std::string method;  // GET, POST, PUT, DELETE, PATCH
    std::string path;
    std::map<std::string, Json::Value> parameters;  // name -> schema
    std::string description;
};

// Relic health check configuration
struct HealthCheck {
    std::string type;  // "api_request", "tcp_port", "custom_script"
    std::string endpoint;
    std::string method;
    int expectedStatus;
    int timeoutSeconds;
    int intervalSeconds;
};

// Relic deployment configuration
struct RelicDeployment {
    std::string type;  // "docker", "docker_compose", "k8s", "external"
    std::string dockerComposeFile;
    std::string imageName;
    std::map<std::string, std::string> environment;
};

// Main Relic class
class Relic {
public:
    Relic(const std::string& manifestPath);
    ~Relic();
    
    // Lifecycle management
    bool start();
    bool stop();
    bool restart();
    bool isRunning() const;
    bool isHealthy() const;
    
    // API interactions
    Json::Value callEndpoint(const std::string& endpointName, 
                            const Json::Value& parameters);
    
    std::string httpRequest(const std::string& method,
                          const std::string& path,
                          const Json::Value& body = Json::Value::null,
                          const std::map<std::string, std::string>& headers = {});
    
    // Getters
    const std::string& getName() const { return name; }
    const std::string& getSummary() const { return summary; }
    const std::string& getServiceType() const { return serviceType; }
    const std::string& getBaseUrl() const { return baseUrl; }
    const std::vector<RelicEndpoint>& getEndpoints() const { return endpoints; }
    
    // Status and monitoring
    std::string getStatus() const;
    Json::Value getMetrics() const;

private:
    // Identity
    std::string name;
    std::string summary;
    std::string description;
    std::string author;
    std::string version;
    std::string state;
    std::string serviceType;
    
    // Interface
    std::string interfaceType;  // rest_api, grpc, custom
    std::string baseUrl;
    std::vector<RelicEndpoint> endpoints;
    
    // Health and lifecycle
    HealthCheck healthCheck;
    RelicDeployment deployment;
    bool running;
    std::string containerId;  // Docker container ID
    
    // Environment
    std::map<std::string, std::string> environmentVars;
    
    // Helper methods
    void loadManifest(const std::string& manifestPath);
    bool startDocker();
    bool stopDocker();
    bool checkHealth();
    std::string executeDockerCommand(const std::string& cmd);
};

// Relic manager - handles multiple relics
class RelicManager {
public:
    static RelicManager& getInstance();
    
    // Load and manage relics
    bool loadRelic(const std::string& manifestPath);
    bool startRelic(const std::string& relicName);
    bool stopRelic(const std::string& relicName);
    bool restartRelic(const std::string& relicName);
    
    Relic* getRelic(const std::string& name);
    std::vector<std::string> listRelics() const;
    
    // Health monitoring
    void startHealthMonitoring();
    void stopHealthMonitoring();
    void checkAllHealth();
    bool isMonitoring() const { return monitoring; }
    
    // Cleanup
    void stopAll();
    
private:
    RelicManager();
    ~RelicManager() { stopAll(); }
    RelicManager(const RelicManager&) = delete;
    RelicManager& operator=(const RelicManager&) = delete;
    
    void healthMonitorLoop();
    
    std::map<std::string, Relic*> relics;
    bool monitoring = false;
    std::thread* monitorThread = nullptr;
};
