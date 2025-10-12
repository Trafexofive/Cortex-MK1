#include "ToolRegistry.hpp"
#include "Utils.hpp" // For logMessage

bool ToolRegistry::registerFunction(const std::string& identifier, FunctionalToolCallback callback) {
    if (registry_.count(identifier)) {
        logMessage(LogLevel::WARN, "ToolRegistry: Duplicate function identifier registration attempted for '" + identifier + "'. Keeping existing definition.");
        return false; // Do not overwrite, or decide on a strategy
    }
    registry_[identifier] = callback;
    logMessage(LogLevel::DEBUG, "ToolRegistry: Successfully registered internal function: '" + identifier + "'.");
    return true;
}

FunctionalToolCallback ToolRegistry::getFunction(const std::string& identifier) const {
    auto it = registry_.find(identifier);
    if (it != registry_.end()) {
        return it->second;
    }
    logMessage(LogLevel::WARN, "ToolRegistry: Internal function identifier not found in registry: '" + identifier + "'.");
    return nullptr; // Return nullptr if not found
}
