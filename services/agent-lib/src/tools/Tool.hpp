#pragma once

#include <json/json.h>
#include <string>
#include <functional> // For std::function
#include <stdexcept>  // For std::runtime_error
#include <vector>
#include <map>

// Forward declaration
class Agent;

using FunctionalToolCallback = std::function<std::string(const Json::Value&)>;

class Tool {
private:
    std::string name;
    std::string description;
    FunctionalToolCallback functionalCallback;

public:
    Tool(const std::string& toolName, const std::string& toolDescription)
        : name(toolName), description(toolDescription), functionalCallback(nullptr) {}

    Tool() : name(""), description(""), functionalCallback(nullptr) {}

    std::string getName() const { return name; }
    std::string getDescription() const { return description; }

    void setName(const std::string& toolName) { name = toolName; }
    void setDescription(const std::string& toolDescription) { description = toolDescription; }

    void setCallback(FunctionalToolCallback callback) {
        functionalCallback = callback;
    }

    std::string execute(const Json::Value& params) {
        if (functionalCallback) {
            return functionalCallback(params);
        }
        throw std::runtime_error("No valid callback function set for tool '" + name + "'");
    }
};





