/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   server.cpp                                         :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: AI Assistant <ai@assistant.com>            +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2025/04/07 22:39:30 by mlamkadm          #+#    #+#             */
/*   Updated: 2025/05/16 00:00:00 by PRAETORIAN_CHIMERA      ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "Agent.hpp"
#include "MiniGemini.hpp"
#include "Tool.hpp"
#include "modelApi.hpp" // For ApiError
#include "Import.hpp"   // For loadAgentProfile
#include "ToolRegistry.hpp" // For ToolRegistry
#include "Utils.hpp"    // For logMessage, executeScriptTool etc.

#include "httplib.h"           // HTTP server library
#include <cstdlib>             // For std::getenv
#include <ctime>               // For time functions, std::time, std::localtime, std::strftime
#include <iostream>
#include <json/json.h> // JSON library
#include <memory>      // For std::unique_ptr, std::make_unique
#include <stdexcept>   // For std::runtime_error, std::exception
#include <string>
#include <vector>      // For storing tool unique_ptrs
#include <curl/curl.h> // For curl_global_init/cleanup
#include <filesystem>  // For path operations

namespace fs = std::filesystem;

// --- Forward Declarations for some C++ Tool Functions (examples) ---
std::string get_current_time_tool_impl(const Json::Value &params) {
    (void)params; // Unused
    auto now = std::chrono::system_clock::now();
    std::time_t now_c = std::chrono::system_clock::to_time_t(now);
    std::tm now_tm_buf;
    #ifdef _WIN32
        localtime_s(&now_tm_buf, &now_c);
        std::tm* now_tm = &now_tm_buf;
    #else
        std::tm* now_tm = localtime_r(&now_c, &now_tm_buf);
    #endif
    if (now_tm) {
        std::stringstream ss;
        ss << std::put_time(now_tm, "%Y-%m-%dT%H:%M:%S%Z");
        return ss.str();
    }
    return "Error: Could not get current time.";
}

std::string file_tool_impl(const Json::Value &params) {
    const char *agent_workspace_env = std::getenv("AGENT_WORKSPACE");
    if (!agent_workspace_env) {
        logMessage(LogLevel::ERROR, "[fileTool] AGENT_WORKSPACE environment variable not set.");
        return "Error: AGENT_WORKSPACE not configured for file operations.";
    }
    fs::path workspace_root = fs::path(agent_workspace_env);

    if (!params.isMember("action") || !params["action"].isString()) {
        return "Error: 'action' (string) parameter is required for file tool.";
    }
    if (!params.isMember("path") || !params["path"].isString()) {
        return "Error: 'path' (string) parameter is required for file tool.";
    }

    std::string action = params["action"].asString();
    std::string relative_path_str = params["path"].asString();

    fs::path user_path = fs::path(relative_path_str);
    if (user_path.is_absolute() || user_path.string().find("..") != std::string::npos) {
        logMessage(LogLevel::ERROR, "[fileTool] Attempted path traversal or absolute path", relative_path_str);
        return "Error: Invalid path. Paths must be relative and within the workspace.";
    }

    fs::path full_path = workspace_root / user_path;
    std::error_code ec;
    full_path = fs::weakly_canonical(full_path, ec);
    if (ec) {
        logMessage(LogLevel::ERROR, "[fileTool] Error canonicalizing path: " + full_path.string(), ec.message());
        return "Error: Could not resolve path: " + ec.message();
    }

    if (full_path.string().rfind(workspace_root.string(), 0) != 0) {
        logMessage(LogLevel::ERROR, "[fileTool] Path escaped workspace sandbox after canonicalization", full_path.string());
        return "Error: Path is outside the allowed workspace directory.";
    }

    logMessage(LogLevel::DEBUG, "[fileTool] Action: " + action + ", Path: " + full_path.string());

    if (action == "read") {
        if (!fs::exists(full_path) || !fs::is_regular_file(full_path)) {
            return "Error: File not found or is not a regular file: " + relative_path_str;
        }
        std::ifstream file(full_path);
        if (!file.is_open()) {
            return "Error: Could not open file for reading: " + relative_path_str;
        }
        std::stringstream buffer;
        buffer << file.rdbuf();
        return buffer.str();
    } else if (action == "write") {
        if (!params.isMember("content") || !params["content"].isString()) {
            return "Error: 'content' (string) parameter is required for write action.";
        }
        fs::path parent_dir = full_path.parent_path();
        if (!fs::exists(parent_dir)) {
            if (!fs::create_directories(parent_dir, ec) && ec) {
                 logMessage(LogLevel::ERROR, "[fileTool] Could not create parent directory: " + parent_dir.string(), ec.message());
                return "Error: Could not create parent directory: " + parent_dir.string() + " - " + ec.message();
            }
        }
        std::ofstream file(full_path);
        if (!file.is_open()) {
            return "Error: Could not open file for writing: " + relative_path_str;
        }
        file << params["content"].asString();
        return "Success: Content written to " + relative_path_str;
    } else if (action == "append") {
         if (!params.isMember("content") || !params["content"].isString()) {
            return "Error: 'content' (string) parameter is required for append action.";
        }
        fs::path parent_dir = full_path.parent_path();
         if (!fs::exists(parent_dir)) {
            if (!fs::create_directories(parent_dir, ec) && ec) {
                 logMessage(LogLevel::ERROR, "[fileTool] Could not create parent directory: " + parent_dir.string(), ec.message());
                return "Error: Could not create parent directory: " + parent_dir.string() + " - " + ec.message();
            }
        }
        std::ofstream file(full_path, std::ios::app); // Append mode
        if (!file.is_open()) {
            return "Error: Could not open file for appending: " + relative_path_str;
        }
        file << params["content"].asString();
        return "Success: Content appended to " + relative_path_str;
    } else if (action == "delete") {
        if (!fs::exists(full_path)) {
            return "Error: File or directory not found for deletion: " + relative_path_str;
        }
        if (fs::remove_all(full_path, ec)) { // fs::remove_all for recursive delete
            return "Success: Deleted " + relative_path_str;
        } else {
             logMessage(LogLevel::ERROR, "[fileTool] Failed to delete: " + full_path.string(), ec.message());
            return "Error: Could not delete " + relative_path_str + " - " + ec.message();
        }
    } else if (action == "mkdir") {
        if (fs::create_directories(full_path, ec)) { 
            return "Success: Directory created " + relative_path_str;
        } else if (ec) {
             logMessage(LogLevel::ERROR, "[fileTool] Failed to create directory: " + full_path.string(), ec.message());
            return "Error: Could not create directory " + relative_path_str + " - " + ec.message();
        } else { 
            return "Success: Directory " + relative_path_str + " (likely already exists).";
        }
    } else if (action == "list") {
        if (!fs::exists(full_path) || !fs::is_directory(full_path)) {
            return "Error: Path not found or is not a directory for listing: " + relative_path_str;
        }
        std::stringstream listing;
        for (const auto& entry : fs::directory_iterator(full_path)) {
            listing << entry.path().filename().string() << (fs::is_directory(entry.status()) ? "/" : "") << "\n";
        }
        return listing.str().empty() ? "(empty directory)" : listing.str();

    } else if (action == "info") {
        if (!fs::exists(full_path)) {
            return "Error: Path not found for info: " + relative_path_str;
        }
        std::stringstream info;
        info << "Path: " << relative_path_str << "\n";
        info << "Type: " << (fs::is_directory(full_path) ? "Directory" : (fs::is_regular_file(full_path) ? "File" : "Other")) << "\n";
        if (fs::is_regular_file(full_path)) {
             std::uintmax_t f_size = fs::file_size(full_path, ec);
             if (ec) {
                logMessage(LogLevel::WARN, "[fileTool] Could not get file size for: " + full_path.string(), ec.message());
                info << "Size: Error reading size\n";
             } else {
                info << "Size: " << f_size << " bytes\n";
             }
        }
        return info.str();
    }
    return "Error: Unknown file action '" + action + "'. Supported: read, write, append, delete, mkdir, list, info.";
}


// --- RAII Helper for curl_global_cleanup ---
struct CurlGlobalCleanupGuard {
    ~CurlGlobalCleanupGuard() {
        logMessage(LogLevel::INFO, "Calling curl_global_cleanup().");
        curl_global_cleanup();
    }
    CurlGlobalCleanupGuard(const CurlGlobalCleanupGuard&) = delete;
    CurlGlobalCleanupGuard& operator=(const CurlGlobalCleanupGuard&) = delete;
    CurlGlobalCleanupGuard() = default;
};

// --- Helper to set CORS and common headers ---
void setCommonHeaders(httplib::Response &res) {
    // Allow specific origin or use "*" for development if safe.
    // For production, specify your frontend's origin.
    // res.set_header("Access-Control-Allow-Origin", "http://localhost:8000"); // Development
    res.set_header("Access-Control-Allow-Origin", "https://agent.clevo.ddnsgeek.com"); // Production
    res.set_header("Access-Control-Allow-Headers", "Content-Type, Accept, X-Requested-With");
    res.set_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS, PUT, DELETE"); // Added PUT, DELETE
    res.set_header("Access-Control-Max-Age", "86400"); // Cache preflight for 1 day
}


// ============================================================================
// == HTTP Server Setup & Run Functions                                      ==
// ============================================================================

void setupHttpServer(httplib::Server& svr, Agent& agent) { // Takes agent by reference

    // --- CORS Preflight for all relevant paths ---
    auto preflightHandler = [](const httplib::Request &, httplib::Response &res) {
        setCommonHeaders(res);
        res.status = 204; // No Content for OPTIONS
        logMessage(LogLevel::DEBUG, "Handled OPTIONS (CORS preflight)");
    };
    svr.Options("/prompt", preflightHandler);
    svr.Options("/agent/info", preflightHandler);
    svr.Options("/agent/config", preflightHandler);
    svr.Options("/agent/history", preflightHandler);
    svr.Options("/agent/tools/(.*)/execute", preflightHandler); // Regex for tool name
    svr.Options("/agent/reset", preflightHandler);


    // --- Main Prompt Endpoint ---
    svr.Post("/prompt", [&](const httplib::Request &req, httplib::Response &res) {
        setCommonHeaders(res);
        logMessage(LogLevel::INFO, "POST /prompt from " + req.remote_addr);

        Json::Value requestJson;
        Json::CharReaderBuilder readerBuilder;
        std::unique_ptr<Json::CharReader> reader(readerBuilder.newCharReader());
        std::string errors;

        if (!reader->parse(req.body.c_str(), req.body.c_str() + req.body.length(), &requestJson, &errors)) {
            logMessage(LogLevel::ERROR, "Failed to parse request JSON for /prompt", errors);
            res.status = 400;
            res.set_content("{\"error\": \"Invalid JSON format\", \"details\": " + Json::valueToQuotedString(errors.c_str()) + "}", "application/json");
            return;
        }

        if (!requestJson.isMember("prompt") || !requestJson["prompt"].isString()) {
            logMessage(LogLevel::ERROR, "Missing or invalid 'prompt' field for /prompt");
            res.status = 400;
            res.set_content("{\"error\": \"'prompt' field (string) is required\"}", "application/json");
            return;
        }
        std::string userPrompt = requestJson["prompt"].asString();
        logMessage(LogLevel::DEBUG, "User prompt for /prompt:", userPrompt.substr(0, 150) + (userPrompt.length() > 150 ? "..." : ""));

        std::string agentFinalResponse;
        try {
            agentFinalResponse = agent.prompt(userPrompt); // agent is captured by reference
            logMessage(LogLevel::DEBUG, "Agent final response for /prompt:", agentFinalResponse.substr(0, 200) + (agentFinalResponse.length() > 200 ? "..." : ""));
        } catch (const ApiError& e) {
            logMessage(LogLevel::ERROR, "Agent API error processing /prompt", e.what());
            res.status = 500;
            res.set_content("{\"error\": \"Agent API interaction failed\", \"details\": " + Json::valueToQuotedString(e.what()) + "}", "application/json");
            return;
        } catch (const std::exception &e) {
            logMessage(LogLevel::ERROR, "Agent processing error for /prompt", e.what());
            res.status = 500;
            res.set_content("{\"error\": \"Agent interaction failed\", \"details\": " + Json::valueToQuotedString(e.what()) + "}", "application/json");
            return;
        } // No need for catch(...) if std::exception covers most cases, but can be added

        Json::Value responseJson;
        responseJson["response"] = agentFinalResponse;
        Json::StreamWriterBuilder writerBuilder;
        writerBuilder["indentation"] = "";
        std::string responseBody = Json::writeString(writerBuilder, responseJson);

        res.status = 200;
        res.set_content(responseBody, "application/json");
        logMessage(LogLevel::INFO, "Sent 200 OK for /prompt");
    });

    // --- GET /agent/info ---
    svr.Get("/agent/info", [&](const httplib::Request &req, httplib::Response &res) {
        setCommonHeaders(res);
        logMessage(LogLevel::INFO, "GET /agent/info from " + req.remote_addr);
        Json::Value infoJson;
        infoJson["name"] = agent.getName();
        infoJson["description"] = agent.getDescription();
        infoJson["system_prompt"] = agent.getSystemPrompt();
        infoJson["iteration_cap"] = agent.getIterationCap();

        const auto& directive = agent.getDirective();
        Json::Value directiveJson;
        std::string directiveTypeStr = "NORMAL"; // Default
        switch (directive.type) {
            case Agent::AgentDirective::Type::BRAINSTORMING: directiveTypeStr = "BRAINSTORMING"; break;
            case Agent::AgentDirective::Type::AUTONOMOUS: directiveTypeStr = "AUTONOMOUS"; break;
            case Agent::AgentDirective::Type::EXECUTE: directiveTypeStr = "EXECUTE"; break;
            case Agent::AgentDirective::Type::REPORT: directiveTypeStr = "REPORT"; break;
            case Agent::AgentDirective::Type::NORMAL: default: directiveTypeStr = "NORMAL"; break;
        }
        directiveJson["type"] = directiveTypeStr;
        directiveJson["description"] = directive.description;
        directiveJson["format"] = directive.format;
        infoJson["directive"] = directiveJson;

        Json::Value envVarsJson(Json::arrayValue);
        for (const auto& pair : agent.getEnvironmentVariables()) {
            Json::Value envVar;
            envVar["key"] = pair.first;
            envVar["value"] = pair.second;
            envVarsJson.append(envVar);
        }
        infoJson["environment_variables"] = envVarsJson;

        Json::Value toolsJson(Json::arrayValue);
        // Accessing registeredTools directly if Agent class allows, or add a getter
        // For now, assuming a way to iterate or get tool info. This part might need Agent class changes.
        // Let's simulate getting tool names and descriptions (needs Agent::getRegisteredToolsInfo())
        // For a quick version:
        // const auto& toolMap = agent.getRegisteredToolsMap(); // Hypothetical getter
        // for (const auto& pair : toolMap) {
        //     if (pair.second) { // Check if tool pointer is valid
        //         Json::Value toolInfo;
        //         toolInfo["name"] = pair.second->getName();
        //         toolInfo["description"] = pair.second->getDescription();
        //         toolsJson.append(toolInfo);
        //     }
        // }
        // As Agent::getTool is const, and registeredTools is private, need a getter or iterate internally.
        // For this example, we'll skip detailed tool listing if Agent class does not expose it easily.
        // A better approach: Agent class provides a method like `getToolManifest()` returning vector<ToolInfo>
        infoJson["registered_tools_count"] = agent.getRegisteredTools().size(); // Example access


        Json::StreamWriterBuilder writerBuilder;
        writerBuilder["indentation"] = ""; // Or "  " for pretty print
        std::string responseBody = Json::writeString(writerBuilder, infoJson);
        res.status = 200;
        res.set_content(responseBody, "application/json");
        logMessage(LogLevel::INFO, "Sent 200 OK for /agent/info");
    });

    // --- POST /agent/config ---
    svr.Post("/agent/config", [&](const httplib::Request &req, httplib::Response &res) {
        setCommonHeaders(res);
        logMessage(LogLevel::INFO, "POST /agent/config from " + req.remote_addr);
        Json::Value requestJson;
        Json::CharReaderBuilder readerBuilder;
        std::unique_ptr<Json::CharReader> reader(readerBuilder.newCharReader());
        std::string errors;

        if (!reader->parse(req.body.c_str(), req.body.c_str() + req.body.length(), &requestJson, &errors)) {
            res.status = 400;
            res.set_content("{\"error\": \"Invalid JSON for config update\", \"details\": " + Json::valueToQuotedString(errors.c_str()) + "}", "application/json");
            return;
        }

        if (requestJson.isMember("name") && requestJson["name"].isString()) {
            agent.setName(requestJson["name"].asString());
        }
        if (requestJson.isMember("description") && requestJson["description"].isString()) {
            agent.setDescription(requestJson["description"].asString());
        }
        if (requestJson.isMember("system_prompt") && requestJson["system_prompt"].isString()) {
            agent.setSystemPrompt(requestJson["system_prompt"].asString());
        }
        if (requestJson.isMember("iteration_cap") && requestJson["iteration_cap"].isInt()) {
            agent.setIterationCap(requestJson["iteration_cap"].asInt());
        }
        if (requestJson.isMember("directive") && requestJson["directive"].isObject()) {
            const Json::Value& dirJson = requestJson["directive"];
            Agent::AgentDirective newDirective = agent.getDirective(); // Start with current
            if (dirJson.isMember("type") && dirJson["type"].isString()) {
                std::string typeStr = dirJson["type"].asString();
                if (typeStr == "BRAINSTORMING") newDirective.type = Agent::AgentDirective::Type::BRAINSTORMING;
                else if (typeStr == "AUTONOMOUS") newDirective.type = Agent::AgentDirective::Type::AUTONOMOUS;
                else if (typeStr == "EXECUTE") newDirective.type = Agent::AgentDirective::Type::EXECUTE;
                else if (typeStr == "REPORT") newDirective.type = Agent::AgentDirective::Type::REPORT;
                else newDirective.type = Agent::AgentDirective::Type::NORMAL;
            }
            if (dirJson.isMember("description") && dirJson["description"].isString()) {
                newDirective.description = dirJson["description"].asString();
            }
            if (dirJson.isMember("format") && dirJson["format"].isString()) {
                newDirective.format = dirJson["format"].asString();
            }
            agent.setDirective(newDirective);
        }
        if (requestJson.isMember("add_environment_variables") && requestJson["add_environment_variables"].isArray()){
            for(const auto& env_item : requestJson["add_environment_variables"]){
                if(env_item.isObject() && env_item.isMember("key") && env_item["key"].isString() &&
                   env_item.isMember("value") && env_item["value"].isString()){
                    agent.addEnvironmentVariable(env_item["key"].asString(), env_item["value"].asString());
                }
            }
        }

        res.status = 200;
        res.set_content("{\"status\": \"success\", \"message\": \"Agent configuration updated.\"}", "application/json");
        logMessage(LogLevel::INFO, "Sent 200 OK for /agent/config");
    });

    // --- GET /agent/history ---
    svr.Get("/agent/history", [&](const httplib::Request &req, httplib::Response &res) {
        setCommonHeaders(res);
        logMessage(LogLevel::INFO, "GET /agent/history from " + req.remote_addr);
        Json::Value historyJson;
        Json::Value entriesArray(Json::arrayValue);
        for (const auto& entry : agent.getHistory()) {
            Json::Value entryJson;
            entryJson["role"] = entry.first;
            entryJson["content"] = entry.second;
            entriesArray.append(entryJson);
        }
        historyJson["history"] = entriesArray;
        std::string responseBody = Json::writeString(Json::StreamWriterBuilder(), historyJson);
        res.status = 200;
        res.set_content(responseBody, "application/json");
        logMessage(LogLevel::INFO, "Sent 200 OK for /agent/history");
    });

    // --- POST /agent/tools/{tool_name}/execute ---
    svr.Post(R"(/agent/tools/(.+)/execute)", [&](const httplib::Request &req, httplib::Response &res) {
        setCommonHeaders(res);
        std::string tool_name = req.matches[1].str();
        logMessage(LogLevel::INFO, "POST /agent/tools/" + tool_name + "/execute from " + req.remote_addr);

        Json::Value paramsJson;
        if (!req.body.empty()) {
            Json::CharReaderBuilder readerBuilder;
            std::unique_ptr<Json::CharReader> reader(readerBuilder.newCharReader());
            std::string errors;
            if (!reader->parse(req.body.c_str(), req.body.c_str() + req.body.length(), &paramsJson, &errors)) {
                res.status = 400;
                res.set_content("{\"error\": \"Invalid JSON for tool parameters\", \"details\": " + Json::valueToQuotedString(errors.c_str()) + "}", "application/json");
                return;
            }
        } else {
            paramsJson = Json::objectValue; // Empty object if no body
        }

        try {
            std::string result = agent.manualToolCall(tool_name, paramsJson);
            Json::Value responseJson;
            responseJson["tool_name"] = tool_name;
            responseJson["result"] = result;
            res.status = 200;
            res.set_content(Json::writeString(Json::StreamWriterBuilder(), responseJson), "application/json");
        } catch (const std::runtime_error& e) {
            logMessage(LogLevel::ERROR, "Error executing tool '" + tool_name + "' manually", e.what());
            res.status = 404; // Or 500 if tool found but failed
            res.set_content("{\"error\": \"Tool execution failed\", \"tool_name\": \"" + tool_name + "\", \"details\": " + Json::valueToQuotedString(e.what()) + "}", "application/json");
        }
    });

    // --- POST /agent/reset ---
    svr.Post("/agent/reset", [&](const httplib::Request &req, httplib::Response &res){
        setCommonHeaders(res);
        logMessage(LogLevel::INFO, "POST /agent/reset from " + req.remote_addr);
        try {
            agent.reset();
            res.status = 200;
            res.set_content("{\"status\": \"success\", \"message\": \"Agent reset successfully.\"}", "application/json");
        } catch (const std::exception& e) {
            logMessage(LogLevel::ERROR, "Error during agent reset", e.what());
            res.status = 500;
            res.set_content("{\"error\": \"Failed to reset agent\", \"details\": " + Json::valueToQuotedString(e.what()) + "}", "application/json");
        }
    });


    // --- Health Check Endpoint ---
    svr.Get("/health", [](const httplib::Request &, httplib::Response &res) {
        setCommonHeaders(res); // Also apply to health for consistency
        res.status = 200;
        res.set_content("{\"status\": \"OK\"}", "application/json");
        logMessage(LogLevel::DEBUG, "GET /health");
    });
}


bool startHttpServer(httplib::Server& svr, const std::string& host, int port) {
    logMessage(LogLevel::INFO, "Attempting to start server on " + host + ":" + std::to_string(port));
    if (!svr.listen(host.c_str(), port)) {
        logMessage(LogLevel::ERROR, "Failed to start server on " + host + ":" + std::to_string(port) + ". Check port availability and permissions.");
        return false;
    }
    logMessage(LogLevel::INFO, "Server has stopped listening.");
    return true;
}

// ============================================================================
// == Main Function                                                          ==
// ============================================================================

int main() {
    CurlGlobalCleanupGuard curl_guard; 

    CURLcode curl_global_res = curl_global_init(CURL_GLOBAL_DEFAULT);
    if (curl_global_res != CURLE_OK) {
        logMessage(LogLevel::ERROR, "Failed to initialize libcurl globally", curl_easy_strerror(curl_global_res));
        return 1;
    }
    logMessage(LogLevel::INFO, "libcurl initialized successfully.");

    const char *apiKeyEnv = std::getenv("GEMINI_API_KEY"); 
    if (!apiKeyEnv || std::string(apiKeyEnv).empty()) {
        logMessage(LogLevel::ERROR, "API_KEY environment variable (e.g., GEMINI_API_KEY) not set or empty.");
        return 1;
    }
    std::string apiKey(apiKeyEnv);
    logMessage(LogLevel::INFO, "API Key loaded from environment.");

    const char *agentProfilePathEnv = std::getenv("AGENT_PROFILE_PATH");
    std::string agentProfilePath;
    if (agentProfilePathEnv && std::string(agentProfilePathEnv).empty() == false) {
        agentProfilePath = agentProfilePathEnv;
    } else {
        agentProfilePath = "config/agents/standard-agent-MK1/standard-agent-MK1.yml";
        logMessage(LogLevel::WARN, "AGENT_PROFILE_PATH not set. Defaulting to: " + agentProfilePath);
    }
    
    const char *agentWorkspaceEnv = std::getenv("AGENT_WORKSPACE");
    if (!agentWorkspaceEnv) {
        fs::path defaultWorkspace = fs::current_path() / "agent_workspace";
        if (!fs::exists(defaultWorkspace)) {
            std::error_code ec;
            fs::create_directories(defaultWorkspace, ec);
            if (ec) {
                logMessage(LogLevel::ERROR, "Failed to create default AGENT_WORKSPACE: " + defaultWorkspace.string(), ec.message());
            } else {
                 logMessage(LogLevel::INFO, "Created default AGENT_WORKSPACE: " + defaultWorkspace.string());
            }
        }
        #ifdef _WIN32
            _putenv_s("AGENT_WORKSPACE", defaultWorkspace.string().c_str());
        #else
            setenv("AGENT_WORKSPACE", defaultWorkspace.string().c_str(), 1); 
        #endif
        logMessage(LogLevel::INFO, "AGENT_WORKSPACE set to default: " + defaultWorkspace.string());
    } else {
         logMessage(LogLevel::INFO, "AGENT_WORKSPACE already set to: " + std::string(agentWorkspaceEnv));
    }

    const std::string host = "0.0.0.0";
    const int port = 7777;

    // Store API clients to manage their lifetime. Agent uses raw pointer.
    std::vector<std::unique_ptr<MiniGemini>> apiClients; 
    std::unique_ptr<Agent> primaryAgent;
    httplib::Server svr;

    try {
        // API Client: Create once, pass by reference. It MUST outlive the Agent.
        auto agentApiClient = std::make_unique<MiniGemini>(apiKey);
        MiniGemini* apiClientRawPtr = agentApiClient.get(); 
        apiClients.push_back(std::move(agentApiClient)); // Store unique_ptr to manage lifetime

        // Agent: Uses the raw pointer to the API client.
        primaryAgent = std::make_unique<Agent>(*apiClientRawPtr); 

        // Register common internal C++ functions to the global ToolRegistry
        // This happens once. loadAgentProfile will look up functions from here by identifier.
        static bool internalToolsRegistered = false;
        if (!internalToolsRegistered) {
            ToolRegistry::getInstance().registerFunction("get_current_time", get_current_time_tool_impl);
            ToolRegistry::getInstance().registerFunction("file", file_tool_impl);
            // ... register other C++ based tools ...
            internalToolsRegistered = true;
            logMessage(LogLevel::INFO, "Common internal C++ functions registered.");
        }

        // Load the agent's profile. This will also load its tools (script-based or internal_function based)
        if (!loadAgentProfile(*primaryAgent, agentProfilePath)) {
            throw std::runtime_error("Failed to initialize primary agent from profile: " + agentProfilePath);
        }
        logMessage(LogLevel::INFO, "Primary agent '" + primaryAgent->getName() + "' initialized successfully from: " + agentProfilePath);

        // Setup HTTP server with the configured agent
        setupHttpServer(svr, *primaryAgent); 
        logMessage(LogLevel::INFO, "HTTP server configured for agent: " + primaryAgent->getName());

        if (!startHttpServer(svr, host, port)) {
            return 1; // Exit if server fails to start
        }

    } catch (const ApiError &e) {
        logMessage(LogLevel::ERROR, "API Error during initialization or runtime", e.what());
        return 1;
    } catch (const std::exception &e) {
        logMessage(LogLevel::ERROR, "Standard Exception during initialization or runtime", e.what());
        return 1;
    } catch (...) {
        logMessage(LogLevel::ERROR, "Unknown error occurred during server setup or run.");
        return 1;
    }

    logMessage(LogLevel::INFO, "Server process ended.");
    // apiClients unique_ptrs will be destroyed here, cleaning up MiniGemini instances.
    // primaryAgent unique_ptr will be destroyed, cleaning up the Agent (and its owned Tools).
    return 0;
}
