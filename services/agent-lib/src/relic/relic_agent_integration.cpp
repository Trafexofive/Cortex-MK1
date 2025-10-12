#include "Agent.hpp"
#include "Relic.hpp"

void Agent::addRelic(Relic* relic) {
    if (!relic) return;
    
    std::string name = relic->getName();
    if (registeredRelics.count(name)) {
        logMessage(LogLevel::WARN, "Agent '" + agentName + "': Replacing existing relic: " + name);
    }
    
    registeredRelics[name] = relic;
    logMessage(LogLevel::DEBUG, "Agent '" + agentName + "': Registered relic: " + name);
}

Relic* Agent::getRelic(const std::string& relicName) const {
    auto it = registeredRelics.find(relicName);
    if (it != registeredRelics.end()) {
        return it->second;
    }
    return nullptr;
}

std::vector<std::string> Agent::listRelics() const {
    std::vector<std::string> names;
    for (const auto& pair : registeredRelics) {
        names.push_back(pair.first);
    }
    return names;
}
