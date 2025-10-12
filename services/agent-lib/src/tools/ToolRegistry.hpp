
#pragma once

#include <string>
#include <functional>
#include <map>
#include <json/json.h> // Or your chosen JSON library, ensure consistent usage

// Standardized functional callback type for all tools.
using FunctionalToolCallback = std::function<std::string(const Json::Value&)>;

class ToolRegistry {
public:
    // Singleton access
    static ToolRegistry& getInstance() {
        static ToolRegistry instance; // Meyers' Singleton
        return instance;
    }

    // Registers a C++ function (typically an internal tool)
    bool registerFunction(const std::string& identifier, FunctionalToolCallback callback);

    // Retrieves a C++ function callback
    FunctionalToolCallback getFunction(const std::string& identifier) const;

private:
    ToolRegistry() = default; // Private constructor
    ~ToolRegistry() = default; // Private destructor

    std::map<std::string, FunctionalToolCallback> registry_;

public:
    // Delete copy and move operations for Singleton
    ToolRegistry(const ToolRegistry&) = delete;
    void operator=(const ToolRegistry&) = delete;
    ToolRegistry(ToolRegistry&&) = delete;
    void operator=(ToolRegistry&&) = delete;
};

// Optional Helper Macro for registering C++ functions easily
#define REGISTER_TOOL_FUNCTION(identifier, func_ptr) \
    static bool ANONYMOUS_VARIABLE(auto_register_##func_ptr) = \
        ToolRegistry::getInstance().registerFunction(identifier, func_ptr);

#define ANONYMOUS_VARIABLE(str) ANONYMOUS_VARIABLE_CONCAT(str, __LINE__)
#define ANONYMOUS_VARIABLE_CONCAT(str, line) ANONYMOUS_VARIABLE_CONCAT_INNER(str, line)
#define ANONYMOUS_VARIABLE_CONCAT_INNER(str, line) str##line
