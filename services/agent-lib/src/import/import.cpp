#include "Agent.hpp"
#include "Tool.hpp"
#include "ToolRegistry.hpp" // For ToolRegistry
#include "Utils.hpp"        // For executeScriptTool, logMessage
#include "StreamingProtocol.hpp" // For context feeds
#include "Relic.hpp"        // For relics
#include "InternalTools.hpp" // For InternalTools
#include <filesystem>                 // For path manipulation (C++17)
#include <fstream>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>
#include <vector>
#include <yaml-cpp/yaml.h>


namespace fs = std::filesystem;

// Forward declarations
bool loadAgentProfile(Agent &agentToConfigure, const std::string &yamlPath);

std::map<std::string, Tool *>
loadToolsFromFile(const std::string &toolYamlPath,
                  Agent &agentForLoggingContext,
                  const fs::path &toolFileBaseDir);

void autoImportStdManifests(Agent &agentToConfigure, const fs::path &projectRoot);

std::string Agent::hotReloadConfig(const std::string &yamlPath) {
  logMessage(LogLevel::INFO, "Hot reloading agent profile: " + yamlPath,
             "Agent: " + getName());
  if (loadAgentProfile(*this, yamlPath)) {
    return "Hot reload successful.";
  } else {
    return "Hot reload failed.";
  }
}

std::string Agent::hotReloadConfigTool(const Json::Value &params) {
  logMessage(LogLevel::INFO, "Hot reloading agent profile via tool call",
             "Agent: " + getName());
  if (params.isMember("yaml_path") && params["yaml_path"].isString()) {
    return hotReloadConfig(params["yaml_path"].asString());
  } else {
    return "Invalid parameters for hot reload.";
  }
}


// Forward declaration for the new helper (removed duplicate)
// std::map<std::string, Tool *>
// loadToolsFromFile(const std::string &toolYamlPath,
//                   Agent &agentForLoggingContext,
//                   const fs::path &toolFileBaseDir);

// Helper to expand environment variables
std::string expandEnvironmentVariables(const std::string &inputStr,
                                       const Agent &agentContext) {
  std::string result = inputStr;
  size_t pos = 0;

  // 1. Expand agent's environment variables first: ${VAR_NAME} or $VAR_NAME
  // from agent.getEnvironmentVariables()
  const auto &agentEnvVars = agentContext.getEnvironmentVariables();
  for (const auto &pair : agentEnvVars) {
    std::string placeholder = "${" + pair.first + "}";
    size_t N = placeholder.length();
    for (pos = result.find(placeholder); pos != std::string::npos;
         pos = result.find(placeholder, pos)) {
      result.replace(pos, N, pair.second);
      pos +=
          pair.second
              .length(); // Adjust pos to continue search after the replacement
    }
    // Simple $VAR version (less specific, might conflict with system env vars
    // if names overlap) For now, prioritizing ${VAR_NAME} for agent vars to be
    // explicit.
  }

  // 2. Expand system environment variables: $SYS_VAR or ${SYS_VAR}
  pos = 0;
  while ((pos = result.find('$', pos)) != std::string::npos) {
    if (pos + 1 < result.length()) {
      size_t endPos;
      std::string varName;
      bool isBracketed = (result[pos + 1] == '{');

      if (isBracketed) { // ${SYS_VAR}
        endPos = result.find('}', pos + 2);
        if (endPos != std::string::npos) {
          varName = result.substr(pos + 2, endPos - (pos + 2));
        } else {
          pos += 2;
          continue; // Malformed
        }
      } else { // $SYS_VAR (simple variable name)
        endPos = pos + 1;
        while (endPos < result.length() &&
               (std::isalnum(result[endPos]) || result[endPos] == '_')) {
          endPos++;
        }
        varName = result.substr(pos + 1, endPos - (pos + 1));
        endPos--; // Adjust endPos to point to the last char of varName
      }

      if (!varName.empty()) {
        // Check if it's an agent variable first (already handled if using
        // ${...})
        bool agentVarFound = false;
        if (!isBracketed) { // For $VAR_NAME style, check agent env again
          for (const auto &pair : agentEnvVars) {
            if (pair.first == varName) {
              result.replace(pos, (endPos + 1) - pos, pair.second);
              pos += pair.second.length();
              agentVarFound = true;
              break;
            }
          }
        }

        if (!agentVarFound) {
          const char *envVal = std::getenv(varName.c_str());
          if (envVal) {
            result.replace(pos, (endPos + 1) - pos, envVal);
            pos += strlen(envVal);
          } else {
            logMessage(LogLevel::WARN,
                       "Environment variable not found for expansion: " +
                           varName,
                       "Context: " + agentContext.getName());
            result.replace(pos, (endPos + 1) - pos, "");
          }
        }
      } else {
        pos++;
      }
    } else {
      break;
    }
  }
  return result;
}

bool loadAgentProfile(Agent &agentToConfigure, const std::string &yamlPath) {
  logMessage(LogLevel::INFO, "Loading agent profile: " + yamlPath,
             "Agent: " + agentToConfigure.getName());
  YAML::Node config;
  fs::path agentYamlFsPath(yamlPath);
  fs::path agentYamlDir = agentYamlFsPath.parent_path();
  fs::path projectRootDir = fs::current_path();
  fs::path allowedScriptsBaseDir =
      projectRootDir / "config" / "scripts"; // More specific
  fs::path allowedToolImportBaseDir = projectRootDir / "config" / "tools";

  try {
    std::ifstream f(agentYamlFsPath.string());
    if (!f.good()) {
      logMessage(LogLevel::ERROR, "Agent profile file not found", yamlPath);
      return false;
    }
    config = YAML::Load(f);
    f.close();
    
    // AUTO-IMPORT std manifests BEFORE user imports
    autoImportStdManifests(agentToConfigure, projectRootDir);

    // Load Sub-agents
    if (config["agents"] && config["agents"].IsSequence()) {
      logMessage(LogLevel::DEBUG, "Loading sub-agents from profile: " + yamlPath);
      for (const auto &subAgentNode : config["agents"]) {
        if (subAgentNode.IsScalar()) {
          std::string subAgentYamlPathStr =
              expandEnvironmentVariables(subAgentNode.as<std::string>(),
                                         agentToConfigure);
          fs::path subAgentYamlPath = agentYamlDir / subAgentYamlPathStr;

          std::error_code ec;
          subAgentYamlPath = fs::weakly_canonical(subAgentYamlPath, ec);
          if (ec) {
            logMessage(LogLevel::ERROR,
                       "Error canonicalizing sub-agent path: " +
                           subAgentYamlPath.string(),
                       ec.message());
            continue;
          }

          if (!fs::exists(subAgentYamlPath)) {
            logMessage(LogLevel::ERROR,
                       "Sub-agent file not found: " + subAgentYamlPath.string());
            continue;
          }

          Agent *subAgent = new Agent(agentToConfigure.getApi());
          if (loadAgentProfile(*subAgent, subAgentYamlPath.string())) {
            agentToConfigure.addSubAgent(subAgent);
            logMessage(LogLevel::INFO,
                       "Loaded sub-agent: " + subAgent->getName());
          } else {
            delete subAgent; // Clean up on failure
          }
        } else {
          logMessage(LogLevel::WARN,
                     "Invalid sub-agent definition in profile: " + yamlPath);
        }
      }
      
      // Auto-register call_subagent tool if sub-agents were loaded
      if (agentToConfigure.hasSubAgents()) {
        Tool* callSubagentTool = new Tool();
        callSubagentTool->setName("call_subagent");
        callSubagentTool->setDescription("Delegate a task to a specialized sub-agent. Available sub-agents: " + 
                                        std::to_string(agentToConfigure.getSubAgents().size()));
        
        // Set callback to InternalTools function
        callSubagentTool->setCallback([](const Json::Value& params) -> std::string {
          return InternalTools::callSubagent(params, nullptr);
        });
        
        agentToConfigure.addTool(callSubagentTool);
        
        logMessage(LogLevel::INFO, "Auto-registered 'call_subagent' tool",
                   "Available sub-agents: " + std::to_string(agentToConfigure.getSubAgents().size()));
      }
    }
// setModel , setTokenLimit, setTemperature grouped 
    // Support modern cognitive_engine format with legacy fallback
    bool modelConfigured = false;
    bool temperatureConfigured = false;
    bool tokenLimitConfigured = false;
    
    // Try modern cognitive_engine first
    if (config["cognitive_engine"] && config["cognitive_engine"].IsMap()) {
      const YAML::Node& cogEngine = config["cognitive_engine"];
      
      // Parse primary provider/model
      if (cogEngine["primary"] && cogEngine["primary"].IsMap()) {
        const YAML::Node& primary = cogEngine["primary"];
        
        if (primary["model"] && primary["model"].IsScalar()) {
          agentToConfigure.setModel(primary["model"].as<std::string>());
          modelConfigured = true;
          logMessage(LogLevel::INFO,
                     "Agent '" + agentToConfigure.getName() +
                         "': Model '" + primary["model"].as<std::string>() +
                         "' (cognitive_engine.primary)");
        }
      }
      
      // Parse parameters
      if (cogEngine["parameters"] && cogEngine["parameters"].IsMap()) {
        const YAML::Node& params = cogEngine["parameters"];
        
        if (params["temperature"] && params["temperature"].IsScalar()) {
          try {
            double temp = params["temperature"].as<double>();
            agentToConfigure.setTemperature(temp);
            temperatureConfigured = true;
            logMessage(LogLevel::INFO,
                       "Agent '" + agentToConfigure.getName() +
                           "': Temperature " + std::to_string(temp) +
                           " (cognitive_engine.parameters)");
          } catch (...) {}
        }
        
        if (params["max_tokens"] && params["max_tokens"].IsScalar()) {
          try {
            int tokens = params["max_tokens"].as<int>();
            agentToConfigure.setTokenLimit(tokens);
            tokenLimitConfigured = true;
            logMessage(LogLevel::INFO,
                       "Agent '" + agentToConfigure.getName() +
                           "': Token limit " + std::to_string(tokens) +
                           " (cognitive_engine.parameters)");
          } catch (...) {}
        }
      }
    }
    
    // Legacy flat format fallback
    if (!modelConfigured && config["model"] && config["model"].IsScalar()) {
      agentToConfigure.setModel(config["model"].as<std::string>());
      modelConfigured = true;
    }
    
    if (!modelConfigured) {
      logMessage(LogLevel::WARN,
                 "Agent profile missing 'model' or 'cognitive_engine.primary.model'. Using default.",
                 yamlPath);
    }
    
    if (!tokenLimitConfigured && config["token_limit"] && config["token_limit"].IsScalar()) {
      try {
        int tokenLimit = config["token_limit"].as<int>();
        agentToConfigure.setTokenLimit(tokenLimit);
        logMessage(LogLevel::DEBUG,
                   "Agent '" + agentToConfigure.getName() +
                       "' token limit set to: " + std::to_string(tokenLimit));
      } catch (const YAML::BadConversion &e) {
        logMessage(LogLevel::WARN,
                   "Failed to parse 'token_limit' for agent " +
                       agentToConfigure.getName(),
                   e.what());
      }
    }
    if (!temperatureConfigured && config["temperature"] && config["temperature"].IsScalar()) {
      try {
        double temperature = config["temperature"].as<double>();
        agentToConfigure.setTemperature(temperature);
        logMessage(LogLevel::DEBUG,
                   "Agent '" + agentToConfigure.getName() +
                       "' temperature set to: " + std::to_string(temperature));
      } catch (const YAML::BadConversion &e) {
        logMessage(LogLevel::WARN,
                   "Failed to parse 'temperature' for agent " +
                       agentToConfigure.getName(),
                   e.what());
      }
    }

    if (config["name"] && config["name"].IsScalar()) {
      agentToConfigure.setName(config["name"].as<std::string>());
    } else {
      logMessage(LogLevel::WARN,
                 "Agent profile missing 'name'. Using default or previous.",
                 yamlPath);
    }

    if (config["description"] && config["description"].IsScalar()) {
      agentToConfigure.setDescription(expandEnvironmentVariables(
          config["description"].as<std::string>(), agentToConfigure));
    }
    // Support both modern 'persona.agent' and legacy 'system_prompt'
    std::string systemPromptPath;
    if (config["persona"] && config["persona"].IsMap() && 
        config["persona"]["agent"] && config["persona"]["agent"].IsScalar()) {
      // Modern manifest format: persona.agent
      systemPromptPath = config["persona"]["agent"].as<std::string>();
    } 

    if (config["persona"] && config["persona"].IsMap() &&
        config["persona"]["system"] && config["persona"]["system"].IsScalar()) {
            // we need to add this to agent system prompt as well, following the:
            //
  // agent: "./system-prompts/zero.md" -- for the agent behavior
  // system: "./system-prompts/demurge.md" -- for the overall system context (main system prompt)
  // user: "./system-prompts/demurge-user.md" -- for the user behavior, preferences, etc.
            // format as referenced in the spec

        }

    
    if (!systemPromptPath.empty()) {
      if (systemPromptPath.size() > 3 &&
          systemPromptPath.substr(systemPromptPath.size() - 3) == ".md") {
        fs::path promptFilePath = agentYamlDir / systemPromptPath;

        std::error_code ec;
        promptFilePath = fs::weakly_canonical(promptFilePath, ec);
        if (ec) {
          logMessage(LogLevel::ERROR,
                     "Error canonicalizing system prompt path: " +
                         promptFilePath.string(),
                     ec.message());
        } else {
          std::ifstream promptFile(promptFilePath);
          if (promptFile.good()) {
            std::string content((std::istreambuf_iterator<char>(promptFile)),
                                std::istreambuf_iterator<char>());
            agentToConfigure.setSystemPrompt(
                expandEnvironmentVariables(content, agentToConfigure));
            logMessage(LogLevel::DEBUG,
                       "Agent '" + agentToConfigure.getName() +
                           "': Loaded system prompt from " + promptFilePath.string());
          } else {
            logMessage(LogLevel::ERROR,
                       "System prompt file not found or not readable: " +
                           promptFilePath.string());
          }
        }
      } else {
        agentToConfigure.setSystemPrompt(
            expandEnvironmentVariables(systemPromptPath, agentToConfigure));
      }
    }
    if (config["schema"] && config["schema"].IsScalar()) {
      agentToConfigure.setSchema(expandEnvironmentVariables(
          config["schema"].as<std::string>(), agentToConfigure));
    }
    if (config["example"] && config["example"].IsScalar()) {
      agentToConfigure.setExample(expandEnvironmentVariables(
          config["example"].as<std::string>(), agentToConfigure));
    }
    if (config["iteration_cap"] && config["iteration_cap"].IsScalar()) {
      try {
        int cap = config["iteration_cap"].as<int>();
        agentToConfigure.setIterationCap(cap);
        logMessage(LogLevel::DEBUG,
                   "Agent '" + agentToConfigure.getName() +
                       "' iteration_cap set to: " + std::to_string(cap));
      } catch (const YAML::BadConversion &e) {
        logMessage(LogLevel::WARN,
                   "Failed to parse 'iteration_cap' for agent " +
                       agentToConfigure.getName(),
                   e.what());
      }
    }
    // Handle modern manifest format: environment.variables and environment.env_file
    if (config["environment"] && config["environment"].IsMap()) {
      // Modern format with nested variables
      if (config["environment"]["variables"] && config["environment"]["variables"].IsMap()) {
        for (const auto &env_it : config["environment"]["variables"]) {
          std::string key = env_it.first.as<std::string>();
          std::string value = expandEnvironmentVariables(
              env_it.second.as<std::string>(), agentToConfigure);
          agentToConfigure.addEnvironmentVariable(key, value);
        }
      }
      // Also handle legacy flat format (direct key-value pairs under environment)
      // Only iterate if it doesn't have the modern 'variables' key
      else {
        bool has_modern_keys = config["environment"]["variables"] || 
                              config["environment"]["env_file"];
        if (!has_modern_keys) {
          for (const auto &env_it : config["environment"]) {
            std::string key = env_it.first.as<std::string>();
            std::string value = expandEnvironmentVariables(
                env_it.second.as<std::string>(), agentToConfigure);
            agentToConfigure.addEnvironmentVariable(key, value);
          }
        }
      }
      // TODO: Handle env_file loading in the future
    }
    if (config["extra_prompts"] && config["extra_prompts"].IsSequence()) {
      for (const auto &item : config["extra_prompts"]) {
        if (item.IsScalar())
          agentToConfigure.addExtraSystemPrompt(expandEnvironmentVariables(
              item.as<std::string>(), agentToConfigure));
      }
    }
    // Tasks are conceptual, not currently used for direct execution logic
    // beyond prompting if (config["tasks"] && config["tasks"].IsSequence()) {
    //     for (const auto& item : config["tasks"]) {
    //          if(item.IsScalar())
    //          agentToConfigure.addTask(expandEnvironmentVariables(item.as<std::string>(),
    //          agentToConfigure));
    //     }
    // }
    if (config["directive"] && config["directive"].IsMap()) {
      Agent::AgentDirective directive;
      if (config["directive"]["type"] &&
          config["directive"]["type"].IsScalar()) {
        std::string typeStr = config["directive"]["type"].as<std::string>();
        if (typeStr == "BRAINSTORMING")
          directive.type = Agent::AgentDirective::Type::BRAINSTORMING;
        else if (typeStr == "AUTONOMOUS")
          directive.type = Agent::AgentDirective::Type::AUTONOMOUS;
        else if (typeStr == "EXECUTE")
          directive.type = Agent::AgentDirective::Type::EXECUTE;
        else if (typeStr == "REPORT")
          directive.type = Agent::AgentDirective::Type::REPORT;
        else
          directive.type = Agent::AgentDirective::Type::NORMAL; // Default
      }
      if (config["directive"]["description"] &&
          config["directive"]["description"].IsScalar()) {
        directive.description = expandEnvironmentVariables(
            config["directive"]["description"].as<std::string>(),
            agentToConfigure);
      }
      if (config["directive"]["format"] &&
          config["directive"]["format"].IsScalar()) {
        directive.format = expandEnvironmentVariables(
            config["directive"]["format"].as<std::string>(), agentToConfigure);
      }
      agentToConfigure.setDirective(directive);
    }

    std::map<std::string, Tool *> resolvedTools;

    if (config["import"] && config["import"].IsMap() &&
        config["import"]["tools"] && config["import"]["tools"].IsSequence()) {
      logMessage(LogLevel::DEBUG, "Agent '" + agentToConfigure.getName() +
                                      "': Processing tool imports...");
      for (const auto &importPathNode : config["import"]["tools"]) {
        if (importPathNode.IsScalar()) {
          std::string relativeToolYamlPathStr = expandEnvironmentVariables(
              importPathNode.as<std::string>(), agentToConfigure);
          fs::path fullToolYamlPath = agentYamlDir / relativeToolYamlPathStr;

          std::error_code ec;
          fullToolYamlPath = fs::weakly_canonical(fullToolYamlPath, ec);
          if (ec) {
            logMessage(LogLevel::ERROR,
                       "Error canonicalizing tool import path: " +
                           fullToolYamlPath.string(),
                       ec.message());
            continue;
          }

          if (!fs::exists(fullToolYamlPath)) {
            logMessage(LogLevel::ERROR, "Agent '" + agentToConfigure.getName() +
                                            "': Tool import file not found: " +
                                            fullToolYamlPath.string() +
                                            ". Skipping import.");
            continue;
          }

          std::map<std::string, Tool *> toolsFromFile =
              loadToolsFromFile(fullToolYamlPath.string(), agentToConfigure,
                                fullToolYamlPath.parent_path());
          for (auto const &[name, toolPtr] : toolsFromFile) {
            if (resolvedTools.count(name)) {
              logMessage(LogLevel::WARN,
                         "Agent '" + agentToConfigure.getName() + "': Tool '" +
                             name + "' from '" + fullToolYamlPath.string() +
                             "' (import) is being overwritten by a subsequent "
                             "import or inline definition.");
              delete resolvedTools[name];
            }
            resolvedTools[name] = toolPtr;
          }
        }
      }
    }

    if (config["tools"] && config["tools"].IsMap()) {
      logMessage(LogLevel::DEBUG, "Agent '" + agentToConfigure.getName() +
                                      "': Processing inline tools...");
      for (const auto &toolNodePair : config["tools"]) {
        std::string yamlToolKey = toolNodePair.first.as<std::string>();
        YAML::Node toolDef = toolNodePair.second;

        if (!toolDef.IsMap()) {
          logMessage(LogLevel::WARN,
                     "Agent '" + agentToConfigure.getName() +
                         "': Skipping non-map tool definition under YAML key '" +
                         yamlToolKey + "'.");
          continue;
        }

        // Use YAML key as name if 'name' field not provided (modern manifest support)
        std::string toolName;
        if (toolDef["name"] && toolDef["name"].IsScalar()) {
          toolName = toolDef["name"].as<std::string>();
        } else {
          toolName = yamlToolKey; // Fallback to YAML key
          logMessage(LogLevel::DEBUG,
                     "Agent '" + agentToConfigure.getName() +
                         "': Using YAML key '" + yamlToolKey +
                         "' as tool name (no explicit 'name' field).");
        }

        // Validate required fields
        if (!toolDef["description"] || !toolDef["description"].IsScalar() ||
            !toolDef["type"] || !toolDef["type"].IsScalar()) {
          logMessage(
              LogLevel::WARN,
              "Agent '" + agentToConfigure.getName() +
                  "': Skipping malformed inline tool '" + toolName +
                  "' (YAML key: '" + yamlToolKey +
                  "'). Missing required fields (description, type).");
          continue;
        }

        std::string toolDescription = expandEnvironmentVariables(
            toolDef["description"].as<std::string>(), agentToConfigure);
        std::string toolType = toolDef["type"].as<std::string>();

        Tool *newTool = new Tool(toolName, toolDescription);
        FunctionalToolCallback callback = nullptr;

        if (toolType == "script") {
          if (!toolDef["runtime"] || !toolDef["runtime"].IsScalar()) {
            logMessage(LogLevel::WARN, "Agent '" + agentToConfigure.getName() +
                                           "': Inline script tool '" +
                                           toolName +
                                           "' missing 'runtime'. Skipping.");
            delete newTool;
            continue;
          }
          std::string runtime =
              toolDef["runtime"].as<std::string>(); // Captured by lambda
          std::string scriptSourceLocation;         // Captured by lambda
          bool isInline = false;                    // Captured by lambda

          if (toolDef["code"] && toolDef["code"].IsScalar()) {
            scriptSourceLocation = expandEnvironmentVariables(
                toolDef["code"].as<std::string>(), agentToConfigure);
            isInline = true;
          } else if (toolDef["path"] && toolDef["path"].IsScalar()) {
            std::string scriptPathStr = expandEnvironmentVariables(
                toolDef["path"].as<std::string>(), agentToConfigure);
            fs::path scriptFullPath = agentYamlDir / scriptPathStr;

            std::error_code ec;
            scriptFullPath = fs::weakly_canonical(scriptFullPath, ec);
            if (ec) {
              logMessage(LogLevel::ERROR,
                         "Error canonicalizing inline script path: " +
                             scriptFullPath.string(),
                         ec.message() + " for tool " + toolName);
              delete newTool;
              continue;
            }

            if (!fs::exists(scriptFullPath)) {
              logMessage(LogLevel::ERROR,
                         "Agent '" + agentToConfigure.getName() +
                             "': Script file for inline tool '" + toolName +
                             "' not found: " + scriptFullPath.string() +
                             ". Skipping.");
              delete newTool;
              continue;
            }
            scriptSourceLocation = scriptFullPath.string();
            isInline = false;
          } else {
            logMessage(LogLevel::WARN,
                       "Agent '" + agentToConfigure.getName() +
                           "': Inline script tool '" + toolName +
                           "' missing 'path' or 'code'. Skipping.");
            delete newTool;
            continue;
          }

          // The callback captures necessary info to call executeScriptTool
          callback = [runtime, scriptSourceLocation, isInline, toolName,
                      agentName = agentToConfigure.getName()](
                         const Json::Value &scriptParams) -> std::string {
            // logMessage(LogLevel::DEBUG, "Agent '" + agentName + "' executing
            // inline-defined script tool via lambda: " + toolName);
            try {
              // scriptParams are the parameters specifically for the *target
              // script*, extracted by the LLM and placed in actionInfo.params.
              return executeScriptTool(scriptSourceLocation, runtime,
                                       scriptParams, isInline);
            } catch (const std::exception &e) {
              logMessage(LogLevel::ERROR,
                         "Exception in inline script tool '" + toolName +
                             "' for agent '" + agentName + "'",
                         e.what());
              return "Error executing script '" + toolName + "': " + e.what();
            }
          };

        } else if (toolType == "internal") {
          if (!toolDef["function_identifier"] ||
              !toolDef["function_identifier"].IsScalar()) {
            logMessage(LogLevel::WARN,
                       "Agent '" + agentToConfigure.getName() +
                           "': Inline internal function tool '" + toolName +
                           "' missing 'function_identifier'. Skipping.");
            delete newTool;
            continue;
          }
          std::string funcId = toolDef["function_identifier"].as<std::string>();
          callback = ToolRegistry::getInstance().getFunction(funcId);
          if (!callback) {
            logMessage(LogLevel::ERROR,
                       "Agent '" + agentToConfigure.getName() +
                           "': Internal function '" + funcId +
                           "' for inline tool '" + toolName +
                           "' not found in registry. Skipping.");
            delete newTool;
            continue;
          }
        } else {
          logMessage(LogLevel::WARN, "Agent '" + agentToConfigure.getName() +
                                         "': Unknown inline tool type '" +
                                         toolType + "' for tool '" + toolName +
                                         "'. Skipping.");
          delete newTool;
          continue;
        }

        newTool->setCallback(callback);
        if (resolvedTools.count(toolName)) {
          logMessage(LogLevel::WARN,
                     "Agent '" + agentToConfigure.getName() +
                         "': Inline tool '" + toolName +
                         "' is overwriting an imported tool definition.");
          delete resolvedTools[toolName];
        }
        resolvedTools[toolName] = newTool;
        logMessage(LogLevel::DEBUG, "Agent '" + agentToConfigure.getName() +
                                        "': Loaded inline tool '" + toolName +
                                        "' with type '" + toolType + "'.");
      }
    }

    for (auto const &[name, toolPtr] : resolvedTools) {
      agentToConfigure.addTool(toolPtr);
    }

    // Load relics (persistent services)
    if (config["import"] && config["import"].IsMap() &&
        config["import"]["relics"] && config["import"]["relics"].IsSequence()) {
      logMessage(LogLevel::DEBUG, "Agent '" + agentToConfigure.getName() +
                                      "': Processing relic imports...");
      
      for (const auto &relicPathNode : config["import"]["relics"]) {
        if (relicPathNode.IsScalar()) {
          std::string relativeRelicPathStr = expandEnvironmentVariables(
              relicPathNode.as<std::string>(), agentToConfigure);
          fs::path fullRelicPath = agentYamlDir / relativeRelicPathStr;
          
          std::error_code ec;
          fullRelicPath = fs::weakly_canonical(fullRelicPath, ec);
          if (ec) {
            logMessage(LogLevel::ERROR,
                       "Error canonicalizing relic import path: " +
                           fullRelicPath.string(),
                       ec.message());
            continue;
          }
          
          if (!fs::exists(fullRelicPath)) {
            logMessage(LogLevel::ERROR, "Agent '" + agentToConfigure.getName() +
                                            "': Relic manifest not found: " +
                                            fullRelicPath.string());
            continue;
          }
          
          // Load relic using RelicManager
          RelicManager& relicMgr = RelicManager::getInstance();
          if (relicMgr.loadRelic(fullRelicPath.string())) {
            // Get the loaded relic
            YAML::Node relicConfig = YAML::LoadFile(fullRelicPath.string());
            std::string relicName = relicConfig["name"].as<std::string>();
            Relic* relic = relicMgr.getRelic(relicName);
            
            if (relic) {
              agentToConfigure.addRelic(relic);
              logMessage(LogLevel::INFO, "Agent '" + agentToConfigure.getName() +
                                            "': Loaded relic '" + relicName + "'");
              
              // Start health monitoring if not already started
              if (!relicMgr.isMonitoring()) {
                relicMgr.startHealthMonitoring();
              }
            }
          }
        }
      }
    }

    // Load context feeds (v1.1 streaming protocol support)
    if (config["context_feeds"] && config["context_feeds"].IsSequence()) {
      logMessage(LogLevel::DEBUG, "Agent '" + agentToConfigure.getName() +
                                      "': Processing context feeds...");
      
      for (const auto &feedNode : config["context_feeds"]) {
        if (!feedNode.IsMap()) continue;
        
        StreamingProtocol::ContextFeed feed;
        
        // Parse feed ID (required)
        if (feedNode["id"] && feedNode["id"].IsScalar()) {
          feed.id = feedNode["id"].as<std::string>();
        } else {
          logMessage(LogLevel::WARN, "Context feed missing 'id', skipping");
          continue;
        }
        
        // Parse feed type (required)
        if (feedNode["type"] && feedNode["type"].IsScalar()) {
          feed.type = feedNode["type"].as<std::string>();
        } else {
          feed.type = "on_demand"; // Default
        }
        
        // Parse source configuration
        if (feedNode["source"] && feedNode["source"].IsMap()) {
          const YAML::Node &sourceNode = feedNode["source"];
          
          // Convert YAML to JSON for source
          Json::Value sourceJson;
          
          if (sourceNode["type"] && sourceNode["type"].IsScalar()) {
            sourceJson["type"] = sourceNode["type"].as<std::string>();
          }
          if (sourceNode["name"] && sourceNode["name"].IsScalar()) {
            sourceJson["name"] = sourceNode["name"].as<std::string>();
          }
          if (sourceNode["action"] && sourceNode["action"].IsScalar()) {
            sourceJson["action"] = sourceNode["action"].as<std::string>();
          }
          
          // Parse params if present
          if (sourceNode["params"] && sourceNode["params"].IsMap()) {
            Json::Value paramsJson;
            for (const auto &param : sourceNode["params"]) {
              std::string key = param.first.as<std::string>();
              if (param.second.IsScalar()) {
                paramsJson[key] = expandEnvironmentVariables(
                    param.second.as<std::string>(), agentToConfigure);
              }
            }
            sourceJson["params"] = paramsJson;
          }
          
          feed.source = sourceJson;
        }
        
        // Parse optional settings
        if (feedNode["cache_ttl"] && feedNode["cache_ttl"].IsScalar()) {
          try {
            feed.cacheTtl = feedNode["cache_ttl"].as<int>();
          } catch (...) {}
        }
        
        if (feedNode["max_tokens"] && feedNode["max_tokens"].IsScalar()) {
          try {
            feed.maxTokens = feedNode["max_tokens"].as<int>();
          } catch (...) {}
        }
        
        // Add feed to agent
        agentToConfigure.addContextFeed(feed);
        logMessage(LogLevel::INFO, "Agent '" + agentToConfigure.getName() +
                                      "': Loaded context feed '" + feed.id +
                                      "' (type: " + feed.type + ")");
      }
    }
    
    // Enable streaming if protocol is requested
    if (config["streaming_protocol"] && config["streaming_protocol"].IsScalar()) {
      bool enableStreaming = config["streaming_protocol"].as<bool>();
      agentToConfigure.setStreamingEnabled(enableStreaming);
      if (enableStreaming) {
        logMessage(LogLevel::INFO, "Agent '" + agentToConfigure.getName() +
                                      "': Streaming protocol enabled");
      }
    }

    logMessage(LogLevel::INFO,
               "Successfully loaded agent profile: " +
                   agentToConfigure.getName(),
               yamlPath);
    return true;

  } catch (const YAML::Exception &e) {
    logMessage(LogLevel::ERROR,
               "YAML parsing error in agent profile: " + yamlPath, e.what());
    return false;
  } catch (const fs::filesystem_error &e) {
    logMessage(LogLevel::ERROR,
               "Filesystem error loading agent profile: " + yamlPath, e.what());
    return false;
  } catch (const std::exception &e) {
    logMessage(LogLevel::ERROR,
               "Generic error loading agent profile: " + yamlPath, e.what());
    return false;
  }
}

std::map<std::string, Tool *>
loadToolsFromFile(const std::string &toolYamlPath,
                  Agent &agentForLoggingContext,
                  const fs::path &toolFileBaseDir) {
  std::map<std::string, Tool *> loadedTools;
  YAML::Node toolsRootNode;
  fs::path projectRootDir = fs::current_path();
  fs::path allowedScriptsBaseDir = projectRootDir / "config" / "scripts";

  logMessage(LogLevel::DEBUG,
             "Agent '" + agentForLoggingContext.getName() +
                 "': Importing tool definitions from: " + toolYamlPath);

  try {
    std::ifstream f(toolYamlPath);
    if (!f.good()) {
      logMessage(LogLevel::ERROR,
                 "Agent '" + agentForLoggingContext.getName() +
                     "': Tool definition file not found: " + toolYamlPath);
      return loadedTools;
    }
    toolsRootNode = YAML::Load(f);
    f.close();
  } catch (const YAML::Exception &e) {
    logMessage(LogLevel::ERROR,
               "Agent '" + agentForLoggingContext.getName() +
                   "': Failed to parse tool YAML file: " + toolYamlPath,
               e.what());
    return loadedTools;
  }

  if (!toolsRootNode.IsMap()) {
    logMessage(LogLevel::ERROR, "Agent '" + agentForLoggingContext.getName() +
                                    "': Root of tool file '" + toolYamlPath +
                                    "' is not a map. Skipping.");
    return loadedTools;
  }

  // Check if this is a modern "kind: Tool" manifest
  if (toolsRootNode["kind"] && toolsRootNode["kind"].IsScalar() &&
      toolsRootNode["kind"].as<std::string>() == "Tool") {
    // Modern Tool manifest format
    logMessage(LogLevel::DEBUG,
               "Agent '" + agentForLoggingContext.getName() +
                   "': Detected modern 'kind: Tool' format in " + toolYamlPath);
    
    if (!toolsRootNode["name"] || !toolsRootNode["name"].IsScalar()) {
      logMessage(LogLevel::ERROR, "Modern tool manifest missing 'name': " + toolYamlPath);
      return loadedTools;
    }
    
    std::string toolName = toolsRootNode["name"].as<std::string>();
    std::string toolDescription = toolsRootNode["description"] && toolsRootNode["description"].IsScalar()
                                  ? toolsRootNode["description"].as<std::string>()
                                  : "No description";
    
    Tool *newTool = new Tool(toolName, toolDescription);
    FunctionalToolCallback callback = nullptr;
    
    // Parse implementation section
    if (toolsRootNode["implementation"] && toolsRootNode["implementation"].IsMap()) {
      const YAML::Node& impl = toolsRootNode["implementation"];
      std::string implType = impl["type"] && impl["type"].IsScalar()
                            ? impl["type"].as<std::string>()
                            : "";
      
      if (implType == "script") {
        std::string runtime = impl["runtime"] && impl["runtime"].IsScalar()
                             ? impl["runtime"].as<std::string>()
                             : "python3";
        std::string entrypoint = impl["entrypoint"] && impl["entrypoint"].IsScalar()
                                ? impl["entrypoint"].as<std::string>()
                                : "";
        
        if (!entrypoint.empty()) {
          // Resolve script path relative to tool.yml directory
          fs::path scriptPath = toolFileBaseDir / entrypoint;
          std::error_code ec;
          scriptPath = fs::weakly_canonical(scriptPath, ec);
          
          if (ec || !fs::exists(scriptPath)) {
            logMessage(LogLevel::ERROR,
                       "Agent '" + agentForLoggingContext.getName() +
                           "': Script for modern tool '" + toolName +
                           "' not found: " + scriptPath.string());
            delete newTool;
            return loadedTools;
          }
          
          std::string scriptLocation = scriptPath.string();
          callback = [runtime, scriptLocation, toolName,
                      agentName = agentForLoggingContext.getName()](
                         const Json::Value &scriptParams) -> std::string {
            try {
              return executeScriptTool(scriptLocation, runtime, scriptParams, false);
            } catch (const std::exception &e) {
              logMessage(LogLevel::ERROR,
                         "Agent '" + agentName + "': Exception in modern tool '" +
                             toolName + "'.", e.what());
              return "Error executing tool '" + toolName + "': " + e.what();
            }
          };
          
          newTool->setCallback(callback);
          loadedTools[toolName] = newTool;
          logMessage(LogLevel::INFO,
                     "Agent '" + agentForLoggingContext.getName() +
                         "': Loaded modern tool '" + toolName + "' from " + toolYamlPath);
        } else {
          logMessage(LogLevel::ERROR, "Modern tool missing entrypoint: " + toolYamlPath);
          delete newTool;
        }
      } else {
        logMessage(LogLevel::WARN, "Unsupported implementation type: " + implType);
        delete newTool;
      }
    } else {
      logMessage(LogLevel::ERROR, "Modern tool missing implementation section: " + toolYamlPath);
      delete newTool;
    }
    
    return loadedTools;
  }

  // Legacy format - iterate categories
  for (const auto &categoryNodePair : toolsRootNode) {
    std::string categoryKey = categoryNodePair.first.as<std::string>();
    YAML::Node categoryToolsMap = categoryNodePair.second;

    if (!categoryToolsMap.IsMap()) {
      logMessage(LogLevel::WARN,
                 "Agent '" + agentForLoggingContext.getName() +
                     "': Expected a map of tools under category '" +
                     categoryKey + "' in " + toolYamlPath +
                     ". Skipping category.");
      continue;
    }

    for (const auto &toolNodePair : categoryToolsMap) {
      std::string yamlToolKey = toolNodePair.first.as<std::string>();
      YAML::Node toolDef = toolNodePair.second;

      if (!toolDef.IsMap() || !toolDef["name"] || !toolDef["name"].IsScalar() ||
          !toolDef["description"] || !toolDef["description"].IsScalar() ||
          !toolDef["type"] || !toolDef["type"].IsScalar()) {
        logMessage(LogLevel::WARN,
                   "Agent '" + agentForLoggingContext.getName() +
                       "': Skipping malformed tool definition in '" +
                       toolYamlPath + "' under YAML key '" + yamlToolKey +
                       "'. Missing required fields (name, description, type).");
        continue;
      }

      std::string toolName = toolDef["name"].as<std::string>();
      std::string toolDescription = expandEnvironmentVariables(
          toolDef["description"].as<std::string>(), agentForLoggingContext);
      std::string toolType = toolDef["type"].as<std::string>();

      Tool *newTool = new Tool(toolName, toolDescription);
      FunctionalToolCallback callback = nullptr;

      if (toolType == "script") {
        if (!toolDef["runtime"] || !toolDef["runtime"].IsScalar()) {
          logMessage(LogLevel::WARN,
                     "Agent '" + agentForLoggingContext.getName() +
                         "': Script tool '" + toolName + "' in '" +
                         toolYamlPath + "' missing 'runtime'. Skipping.");
          delete newTool;
          continue;
        }
        std::string runtime = toolDef["runtime"].as<std::string>(); // Captured
        std::string scriptSourceLocation;                           // Captured
        bool isInline = false;                                      // Captured

        if (toolDef["code"] && toolDef["code"].IsScalar()) {
          scriptSourceLocation = expandEnvironmentVariables(
              toolDef["code"].as<std::string>(), agentForLoggingContext);
          isInline = true;
        } else if (toolDef["path"] && toolDef["path"].IsScalar()) {
          std::string scriptPathStr = expandEnvironmentVariables(
              toolDef["path"].as<std::string>(), agentForLoggingContext);
          fs::path scriptFullPath = toolFileBaseDir / scriptPathStr;

          std::error_code ec;
          scriptFullPath = fs::weakly_canonical(scriptFullPath, ec);
          if (ec) {
            logMessage(LogLevel::ERROR,
                       "Error canonicalizing script path from tool file: " +
                           scriptFullPath.string(),
                       ec.message() + " for tool " + toolName);
            delete newTool;
            continue;
          }

          if (!fs::exists(scriptFullPath)) {
            logMessage(LogLevel::ERROR,
                       "Agent '" + agentForLoggingContext.getName() +
                           "': Script file for tool '" + toolName + "' from '" +
                           toolYamlPath + "' not found: " +
                           scriptFullPath.string() + ". Skipping.");
            delete newTool;
            continue;
          }
          scriptSourceLocation = scriptFullPath.string();
          isInline = false;
        } else {
          logMessage(LogLevel::WARN,
                     "Agent '" + agentForLoggingContext.getName() +
                         "': Script tool '" + toolName + "' in '" +
                         toolYamlPath +
                         "' missing 'path' or 'code'. Skipping.");
          delete newTool;
          continue;
        }

        callback = [runtime, scriptSourceLocation, isInline, toolName,
                    agentName = agentForLoggingContext.getName()](
                       const Json::Value &scriptParams) -> std::string {
          // logMessage(LogLevel::DEBUG, "Agent '" + agentName + "': Executing
          // script tool '" + toolName + "' (defined in separate tool file).");
          try {
            return executeScriptTool(scriptSourceLocation, runtime,
                                     scriptParams, isInline);
          } catch (const std::exception &e) {
            logMessage(LogLevel::ERROR,
                       "Agent '" + agentName + "': Exception in script tool '" +
                           toolName + "' (defined in separate tool file).",
                       e.what());
            return "Error executing script '" + toolName + "': " + e.what();
          }
        };

      } else if (toolType == "internal") {
        if (!toolDef["function_identifier"] ||
            !toolDef["function_identifier"].IsScalar()) {
          logMessage(LogLevel::WARN,
                     "Agent '" + agentForLoggingContext.getName() +
                         "': Internal function tool '" + toolName + "' in '" +
                         toolYamlPath +
                         "' missing 'function_identifier'. Skipping.");
          delete newTool;
          continue;
        }
        std::string funcId = toolDef["function_identifier"].as<std::string>();
        callback = ToolRegistry::getInstance().getFunction(funcId);
        if (!callback) {
          logMessage(LogLevel::ERROR,
                     "Agent '" + agentForLoggingContext.getName() +
                         "': Internal function '" + funcId + "' for tool '" +
                         toolName + "' from '" + toolYamlPath +
                         "' not found in registry. Skipping.");
          delete newTool;
          continue;
        }
      } else {
        logMessage(LogLevel::WARN,
                   "Agent '" + agentForLoggingContext.getName() +
                       "': Unknown tool type '" + toolType + "' for tool '" +
                       toolName + "' in '" + toolYamlPath + "'. Skipping.");
        delete newTool;
        continue;
      }

      newTool->setCallback(callback);
      if (loadedTools.count(toolName)) {
        logMessage(LogLevel::WARN,
                   "Agent '" + agentForLoggingContext.getName() +
                       "': Duplicate tool name '" + toolName +
                       "' within the same tool definition file '" +
                       toolYamlPath + "'. Overwriting.");
        delete loadedTools[toolName];
      }
      loadedTools[toolName] = newTool;
      logMessage(LogLevel::DEBUG, "Agent '" + agentForLoggingContext.getName() +
                                      "': Loaded tool '" + toolName +
                                      "' from file '" + toolYamlPath +
                                      "' with type '" + toolType + "'.");
    }
  }
  logMessage(LogLevel::INFO, "Agent '" + agentForLoggingContext.getName() +
                                 "': Finished importing " +
                                 std::to_string(loadedTools.size()) +
                                 " tool definitions from " + toolYamlPath);
  return loadedTools;
}

// Auto-import standard manifests from std/manifests before user imports
void autoImportStdManifests(Agent &agentToConfigure, const fs::path &projectRoot) {
  // Check if std/manifests exists
  fs::path stdManifestsPath = projectRoot / "../../std/manifests";
  
  std::error_code ec;
  stdManifestsPath = fs::weakly_canonical(stdManifestsPath, ec);
  if (ec || !fs::exists(stdManifestsPath)) {
    logMessage(LogLevel::DEBUG, "No std/manifests directory found - skipping auto-import",
               "Path: " + stdManifestsPath.string());
    return;
  }
  
  logMessage(LogLevel::DEBUG, "Auto-importing std manifests from: " + stdManifestsPath.string());
  
  // Auto-import std tools
  fs::path stdToolsPath = stdManifestsPath / "tools";
  if (fs::exists(stdToolsPath) && fs::is_directory(stdToolsPath)) {
    for (const auto& entry : fs::directory_iterator(stdToolsPath)) {
      if (entry.is_directory()) {
        fs::path toolManifest = entry.path() / "tool.yml";
        if (fs::exists(toolManifest)) {
          try {
            auto stdTools = loadToolsFromFile(toolManifest.string(), agentToConfigure, entry.path());
            for (auto const &[name, toolPtr] : stdTools) {
              agentToConfigure.addTool(toolPtr);
            }
            logMessage(LogLevel::DEBUG, "Auto-imported std tool: " + entry.path().filename().string());
          } catch (const std::exception& e) {
            logMessage(LogLevel::WARN, "Failed to auto-import std tool: " + entry.path().filename().string(), e.what());
          }
        }
      }
    }
  }
  
  // TODO: Auto-import std agents, relics, etc. as needed
  // For now, tools are the most critical for universal access
}

