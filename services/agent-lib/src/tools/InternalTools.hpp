#pragma once

#include <json/json.h>
#include <string>

// Internal tool implementations for agent-lib
// These are registered with ToolRegistry and can be used by agents

namespace InternalTools {

// System clock - returns current date/time
// Parameters: format (optional, default: ISO8601), timezone (optional, default: UTC)
std::string systemClock(const Json::Value& params);

// Agent metadata - returns information about the agent
// Parameters: include (optional, comma-separated: name,iteration,confidence,etc)
std::string agentMetadata(const Json::Value& params);

// Context feed manager - add/remove/list context feeds
// Parameters: action (add/remove/list), feed_id, feed_data
std::string contextFeedManager(const Json::Value& params);

// Variable manager - set/get/delete context variables
// Parameters: action (set/get/delete), key, value
std::string variableManager(const Json::Value& params);

// File operations - read/write/append files (sandboxed to agent workspace)
// Parameters: action (read/write/append/delete), path, content
std::string fileOperations(const Json::Value& params);

// Environment info - system information (CPU, memory, disk, etc)
// Parameters: include (optional, comma-separated: cpu,memory,disk,network)
std::string environmentInfo(const Json::Value& params);

// Random generator - generate random values
// Parameters: type (int/float/string/uuid), min, max, length
std::string randomGenerator(const Json::Value& params);

// Base64 codec - encode/decode base64
// Parameters: action (encode/decode), data
std::string base64Codec(const Json::Value& params);

// JSON operations - validate/pretty/minify JSON
// Parameters: action (validate/pretty/minify), data
std::string jsonOperations(const Json::Value& params);

// Call subagent - delegate task to a specialized sub-agent
// Parameters: agent (name of sub-agent), task (task description), context (optional)
// Note: This is registered per-agent when sub-agents are available
std::string callSubagent(const Json::Value& params, void* agentPtr);

} // namespace InternalTools
