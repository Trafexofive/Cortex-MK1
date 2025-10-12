#include "InternalTools.hpp"
#include "Utils.hpp"
#include <chrono>
#include <iomanip>
#include <sstream>
#include <ctime>
#include <fstream>
#include <cstdlib>
#include <cstdio>
#include <regex>

namespace InternalTools {

std::string systemClock(const Json::Value& params) {
    // Get parameters
    std::string format = "ISO8601";
    std::string timezone = "UTC";
    
    if (params.isMember("format") && params["format"].isString()) {
        format = params["format"].asString();
    }
    if (params.isMember("timezone") && params["timezone"].isString()) {
        timezone = params["timezone"].asString();
    }
    
    // Get current time
    auto now = std::chrono::system_clock::now();
    auto now_time_t = std::chrono::system_clock::to_time_t(now);
    auto now_ms = std::chrono::duration_cast<std::chrono::milliseconds>(
        now.time_since_epoch()) % 1000;
    
    std::stringstream ss;
    
    if (format == "ISO8601") {
        // ISO 8601 format: 2024-01-10T16:30:45.123Z
        std::tm tm = {};
        #ifdef _WIN32
            gmtime_s(&tm, &now_time_t);
        #else
            gmtime_r(&now_time_t, &tm);
        #endif
        
        ss << std::put_time(&tm, "%Y-%m-%dT%H:%M:%S");
        ss << '.' << std::setfill('0') << std::setw(3) << now_ms.count();
        ss << 'Z';
    } else if (format == "unix") {
        ss << now_time_t;
    } else if (format == "human") {
        std::tm tm = {};
        #ifdef _WIN32
            gmtime_s(&tm, &now_time_t);
        #else
            gmtime_r(&now_time_t, &tm);
        #endif
        ss << std::put_time(&tm, "%Y-%m-%d %H:%M:%S %Z");
    } else {
        // Custom format
        std::tm tm = {};
        #ifdef _WIN32
            gmtime_s(&tm, &now_time_t);
        #else
            gmtime_r(&now_time_t, &tm);
        #endif
        ss << std::put_time(&tm, format.c_str());
    }
    
    Json::Value result;
    result["timestamp"] = ss.str();
    result["format"] = format;
    result["timezone"] = timezone;
    result["unix"] = static_cast<Json::Int64>(now_time_t);
    
    Json::StreamWriterBuilder builder;
    builder["indentation"] = "";
    return Json::writeString(builder, result);
}

std::string agentMetadata(const Json::Value& params) {
    // This is a placeholder - actual implementation would need Agent context
    // For now, return basic metadata
    std::string include = "name,iteration";
    
    if (params.isMember("include") && params["include"].isString()) {
        include = params["include"].asString();
    }
    
    Json::Value result;
    result["available"] = true;
    result["included_fields"] = include;
    
    // Note: In practice, this would be called with agent context
    // and would return actual agent state
    result["note"] = "Agent metadata requires agent context";
    
    Json::StreamWriterBuilder builder;
    builder["indentation"] = "";
    return Json::writeString(builder, result);
}

std::string contextFeedManager(const Json::Value& params) {
    if (!params.isMember("action") || !params["action"].isString()) {
        Json::Value error;
        error["error"] = "Missing 'action' parameter";
        Json::StreamWriterBuilder builder;
        builder["indentation"] = "";
        return Json::writeString(builder, error);
    }
    
    std::string action = params["action"].asString();
    Json::Value result;
    
    if (action == "list") {
        result["action"] = "list";
        result["feeds"] = Json::arrayValue;
        result["count"] = 0;
    } else if (action == "add") {
        if (!params.isMember("feed_id")) {
            result["error"] = "Missing 'feed_id' for add action";
        } else {
            result["action"] = "add";
            result["feed_id"] = params["feed_id"];
            result["status"] = "success";
        }
    } else if (action == "remove") {
        if (!params.isMember("feed_id")) {
            result["error"] = "Missing 'feed_id' for remove action";
        } else {
            result["action"] = "remove";
            result["feed_id"] = params["feed_id"];
            result["status"] = "success";
        }
    } else {
        result["error"] = "Unknown action: " + action;
    }
    
    Json::StreamWriterBuilder builder;
    builder["indentation"] = "";
    return Json::writeString(builder, result);
}

std::string variableManager(const Json::Value& params) {
    if (!params.isMember("action") || !params["action"].isString()) {
        Json::Value error;
        error["error"] = "Missing 'action' parameter";
        Json::StreamWriterBuilder builder;
        builder["indentation"] = "";
        return Json::writeString(builder, error);
    }
    
    std::string action = params["action"].asString();
    Json::Value result;
    
    if (action == "set") {
        if (!params.isMember("key") || !params.isMember("value")) {
            result["error"] = "Missing 'key' or 'value' for set action";
        } else {
            result["action"] = "set";
            result["key"] = params["key"];
            result["value"] = params["value"];
            result["status"] = "success";
        }
    } else if (action == "get") {
        if (!params.isMember("key")) {
            result["error"] = "Missing 'key' for get action";
        } else {
            result["action"] = "get";
            result["key"] = params["key"];
            result["value"] = Json::nullValue;
        }
    } else if (action == "delete") {
        if (!params.isMember("key")) {
            result["error"] = "Missing 'key' for delete action";
        } else {
            result["action"] = "delete";
            result["key"] = params["key"];
            result["status"] = "success";
        }
    } else {
        result["error"] = "Unknown action: " + action;
    }
    
    Json::StreamWriterBuilder builder;
    builder["indentation"] = "";
    return Json::writeString(builder, result);
}

std::string fileOperations(const Json::Value& params) {
    if (!params.isMember("action") || !params["action"].isString()) {
        Json::Value error;
        error["error"] = "Missing 'action' parameter";
        Json::StreamWriterBuilder builder;
        return Json::writeString(builder, error);
    }
    
    std::string action = params["action"].asString();
    Json::Value result;
    
    // Sandbox to agent_workspace directory
    std::string workspace = "agent_workspace/";
    
    if (action == "read") {
        if (!params.isMember("path")) {
            result["error"] = "Missing 'path' for read action";
        } else {
            std::string path = workspace + params["path"].asString();
            std::ifstream file(path);
            if (file.is_open()) {
                std::stringstream buffer;
                buffer << file.rdbuf();
                result["action"] = "read";
                result["path"] = params["path"];
                result["content"] = buffer.str();
                result["status"] = "success";
            } else {
                result["error"] = "Failed to open file: " + params["path"].asString();
            }
        }
    } else if (action == "write" || action == "append") {
        if (!params.isMember("path") || !params.isMember("content")) {
            result["error"] = "Missing 'path' or 'content' for " + action + " action";
        } else {
            std::string path = workspace + params["path"].asString();
            std::ios::openmode mode = (action == "append") ? 
                (std::ios::out | std::ios::app) : std::ios::out;
            
            // Create directory if needed
            size_t lastSlash = path.find_last_of('/');
            if (lastSlash != std::string::npos) {
                std::string dir = path.substr(0, lastSlash);
                system(("mkdir -p " + dir).c_str());
            }
            
            std::ofstream file(path, mode);
            if (file.is_open()) {
                file << params["content"].asString();
                result["action"] = action;
                result["path"] = params["path"];
                result["status"] = "success";
            } else {
                result["error"] = "Failed to write file: " + params["path"].asString();
            }
        }
    } else if (action == "delete") {
        if (!params.isMember("path")) {
            result["error"] = "Missing 'path' for delete action";
        } else {
            std::string path = workspace + params["path"].asString();
            if (remove(path.c_str()) == 0) {
                result["action"] = "delete";
                result["path"] = params["path"];
                result["status"] = "success";
            } else {
                result["error"] = "Failed to delete file: " + params["path"].asString();
            }
        }
    } else {
        result["error"] = "Unknown action: " + action;
    }
    
    Json::StreamWriterBuilder builder;
    builder["indentation"] = "";
    return Json::writeString(builder, result);
}

std::string environmentInfo(const Json::Value& params) {
    std::string include = "cpu,memory";
    if (params.isMember("include") && params["include"].isString()) {
        include = params["include"].asString();
    }
    
    Json::Value result;
    result["timestamp"] = static_cast<Json::Int64>(std::time(nullptr));
    
    // Use system commands to gather info
    if (include.find("cpu") != std::string::npos) {
        // Get CPU info (simplified)
        FILE* pipe = popen("nproc 2>/dev/null", "r");
        if (pipe) {
            char buffer[128];
            if (fgets(buffer, sizeof(buffer), pipe)) {
                result["cpu_cores"] = std::atoi(buffer);
            }
            pclose(pipe);
        }
    }
    
    if (include.find("memory") != std::string::npos) {
        // Get memory info (Linux)
        FILE* pipe = popen("free -m | grep Mem | awk '{print $2,$3,$4}' 2>/dev/null", "r");
        if (pipe) {
            char buffer[256];
            if (fgets(buffer, sizeof(buffer), pipe)) {
                int total, used, free;
                if (sscanf(buffer, "%d %d %d", &total, &used, &free) == 3) {
                    result["memory_total_mb"] = total;
                    result["memory_used_mb"] = used;
                    result["memory_free_mb"] = free;
                }
            }
            pclose(pipe);
        }
    }
    
    if (include.find("disk") != std::string::npos) {
        // Get disk info
        FILE* pipe = popen("df -h . | tail -1 | awk '{print $2,$3,$4,$5}' 2>/dev/null", "r");
        if (pipe) {
            char buffer[256];
            if (fgets(buffer, sizeof(buffer), pipe)) {
                result["disk_info"] = std::string(buffer);
            }
            pclose(pipe);
        }
    }
    
    Json::StreamWriterBuilder builder;
    builder["indentation"] = "";
    return Json::writeString(builder, result);
}

std::string randomGenerator(const Json::Value& params) {
    std::string type = "int";
    if (params.isMember("type") && params["type"].isString()) {
        type = params["type"].asString();
    }
    
    Json::Value result;
    result["type"] = type;
    
    // Seed random (simple approach)
    static bool seeded = false;
    if (!seeded) {
        srand(time(nullptr));
        seeded = true;
    }
    
    if (type == "int") {
        int min = params.get("min", 0).asInt();
        int max = params.get("max", 100).asInt();
        result["value"] = min + (rand() % (max - min + 1));
    } else if (type == "float") {
        double min = params.get("min", 0.0).asDouble();
        double max = params.get("max", 1.0).asDouble();
        result["value"] = min + (static_cast<double>(rand()) / RAND_MAX) * (max - min);
    } else if (type == "uuid") {
        // Simple UUID v4 (not cryptographically secure)
        std::stringstream ss;
        ss << std::hex << std::setfill('0');
        for (int i = 0; i < 4; i++) {
            ss << std::setw(8) << (rand() % 0xFFFFFFFF);
            if (i < 3) ss << "-";
        }
        result["value"] = ss.str();
    } else if (type == "string") {
        int length = params.get("length", 16).asInt();
        const char charset[] = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
        std::string randomStr;
        for (int i = 0; i < length; i++) {
            randomStr += charset[rand() % (sizeof(charset) - 1)];
        }
        result["value"] = randomStr;
    } else {
        result["error"] = "Unknown type: " + type;
    }
    
    Json::StreamWriterBuilder builder;
    builder["indentation"] = "";
    return Json::writeString(builder, result);
}

std::string base64Codec(const Json::Value& params) {
    if (!params.isMember("action") || !params["action"].isString()) {
        Json::Value error;
        error["error"] = "Missing 'action' parameter";
        Json::StreamWriterBuilder builder;
        return Json::writeString(builder, error);
    }
    
    std::string action = params["action"].asString();
    Json::Value result;
    
    // Simple base64 using system command (not ideal but works)
    if (action == "encode") {
        if (!params.isMember("data")) {
            result["error"] = "Missing 'data' for encode action";
        } else {
            std::string data = params["data"].asString();
            std::string tmpfile = "/tmp/agent_b64_" + std::to_string(rand()) + ".txt";
            std::ofstream out(tmpfile);
            out << data;
            out.close();
            
            std::string cmd = "base64 " + tmpfile + " 2>/dev/null";
            FILE* pipe = popen(cmd.c_str(), "r");
            if (pipe) {
                std::stringstream ss;
                char buffer[256];
                while (fgets(buffer, sizeof(buffer), pipe)) {
                    ss << buffer;
                }
                pclose(pipe);
                result["encoded"] = ss.str();
                result["status"] = "success";
            }
            remove(tmpfile.c_str());
        }
    } else if (action == "decode") {
        if (!params.isMember("data")) {
            result["error"] = "Missing 'data' for decode action";
        } else {
            std::string data = params["data"].asString();
            std::string tmpfile = "/tmp/agent_b64_" + std::to_string(rand()) + ".txt";
            std::ofstream out(tmpfile);
            out << data;
            out.close();
            
            std::string cmd = "base64 -d " + tmpfile + " 2>/dev/null";
            FILE* pipe = popen(cmd.c_str(), "r");
            if (pipe) {
                std::stringstream ss;
                char buffer[256];
                while (fgets(buffer, sizeof(buffer), pipe)) {
                    ss << buffer;
                }
                pclose(pipe);
                result["decoded"] = ss.str();
                result["status"] = "success";
            }
            remove(tmpfile.c_str());
        }
    } else {
        result["error"] = "Unknown action: " + action;
    }
    
    Json::StreamWriterBuilder builder;
    builder["indentation"] = "";
    return Json::writeString(builder, result);
}

std::string jsonOperations(const Json::Value& params) {
    if (!params.isMember("action") || !params["action"].isString()) {
        Json::Value error;
        error["error"] = "Missing 'action' parameter";
        Json::StreamWriterBuilder builder;
        return Json::writeString(builder, error);
    }
    
    std::string action = params["action"].asString();
    Json::Value result;
    
    if (action == "validate") {
        if (!params.isMember("data")) {
            result["error"] = "Missing 'data' for validate action";
        } else {
            std::string data = params["data"].asString();
            Json::CharReaderBuilder reader;
            Json::Value parsed;
            std::string errs;
            std::istringstream stream(data);
            
            bool valid = Json::parseFromStream(reader, stream, &parsed, &errs);
            result["valid"] = valid;
            if (!valid) {
                result["errors"] = errs;
            }
            result["status"] = "success";
        }
    } else if (action == "pretty" || action == "minify") {
        if (!params.isMember("data")) {
            result["error"] = "Missing 'data' for " + action + " action";
        } else {
            std::string data = params["data"].asString();
            Json::CharReaderBuilder reader;
            Json::Value parsed;
            std::string errs;
            std::istringstream stream(data);
            
            if (Json::parseFromStream(reader, stream, &parsed, &errs)) {
                Json::StreamWriterBuilder writer;
                if (action == "pretty") {
                    writer["indentation"] = "  ";
                } else {
                    writer["indentation"] = "";
                }
                result["formatted"] = Json::writeString(writer, parsed);
                result["status"] = "success";
            } else {
                result["error"] = "Invalid JSON: " + errs;
            }
        }
    } else {
        result["error"] = "Unknown action: " + action;
    }
    
    Json::StreamWriterBuilder builder;
    builder["indentation"] = "";
    return Json::writeString(builder, result);
}

// Call subagent - delegate task to a specialized sub-agent
// This is a placeholder that will be properly implemented per-agent
std::string callSubagent(const Json::Value& params, void* agentPtr) {
    Json::Value result;
    result["tool"] = "call_subagent";
    result["status"] = "pending";
    
    // Validate parameters
    if (!params.isMember("agent")) {
        result["error"] = "Missing required parameter: 'agent' (sub-agent name)";
        result["status"] = "error";
    } else if (!params.isMember("task")) {
        result["error"] = "Missing required parameter: 'task' (task description)";
        result["status"] = "error";
    } else {
        std::string agentName = params["agent"].asString();
        std::string task = params["task"].asString();
        
        result["agent"] = agentName;
        result["task"] = task;
        result["status"] = "delegated";
        
        // Note: Actual sub-agent execution will be handled by the Agent class
        // This tool just validates and structures the delegation request
        result["message"] = "Task delegated to sub-agent: " + agentName;
        
        // Include optional context if provided
        if (params.isMember("context")) {
            result["context"] = params["context"];
        }
    }
    
    Json::StreamWriterBuilder builder;
    builder["indentation"] = "";
    return Json::writeString(builder, result);
}

} // namespace InternalTools
