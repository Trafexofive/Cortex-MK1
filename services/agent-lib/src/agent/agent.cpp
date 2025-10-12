// src/agent.cpp
#include "Agent.hpp" // Adjust path as necessary
#include <algorithm>        // For std::remove_if, std::find_if
#include <chrono>           // For time functions in generateTimestamp
#include <cstdlib>          // For std::getenv
#include <fstream>          // For file operations
#include <iomanip>          // For std::put_time in generateTimestamp
#include <iostream>         // For std::cout, std::cin, std::cerr
#include <sstream>          // For std::stringstream

// --- End Logging ---
Agent::Agent(LLMClient &apiRef, const std::string &agentNameVal)
    : api(apiRef), agentName(agentNameVal), currentIteration(0),
      iterationLimit(10), skipNextFlowIteration(false) {

  logMessage(LogLevel::DEBUG, "Agent instance created", "Name: " + agentName);
  internalFunctionDescriptions["call_subagent"] =
      "[Use -internal- type instead of tool or script] Allows talking to a "
      "registered sub-agent using text input, Very essential in the "
      "CHIMERA_ECOSYS (delegating, access to specialized agents ...). "
      "Parameters: "
      "{\"agent_name\": \"string\", \"prompt\": \"string\"}";
  internalFunctionDescriptions["add_env_var"] =
      "[Use -internal- type instead of tool or script] Adds or updates an "
      "environment variable for the agent. Parameters: {\"key\": \"string\", "
      "\"value\": \"string\"}";
}

Agent::~Agent() {

  for (auto &pair : registeredTools) {
    delete pair.second;
  }
  registeredTools.clear();
  saveHistory();
}

// --- Configuration Setters (Implementations) ---
void Agent::setName(const std::string &newName) { agentName = newName; }
void Agent::setDescription(const std::string &newDescription) {
  agentDescription = newDescription;
}

void Agent::setSystemPrompt(const std::string &prompt) {
  systemPrompt = prompt;
}

void Agent::setSchema(const std::string &schema) { llmResponseSchema = schema; }
void Agent::setExample(const std::string &example) {
  llmResponseExample = example;
}

void Agent::setIterationCap(int cap) { iterationLimit = (cap > 0) ? cap : 10; }

void Agent::setDirective(const AgentDirective &dir) { currentDirective = dir; }
void Agent::addTask(const std::string &task) { tasks.push_back(task); }
void Agent::addInitialCommand(const std::string &command) {
  initialCommands.push_back(command);
}

// --- Tool Management (Implementations) ---
void Agent::addTool(Tool *tool) {
  if (!tool) {
    logMessage(LogLevel::WARN, "Attempted to add a null tool.");
    return;
  }
  const std::string &toolNameStr = tool->getName(); // Use local var for clarity
  if (toolNameStr.empty()) {
    logMessage(LogLevel::WARN, "Attempted to add a tool with an empty name.");
    delete tool;
    return;
  }
  if (registeredTools.count(toolNameStr) ||
      internalFunctionDescriptions.count(toolNameStr)) {
    logMessage(LogLevel::WARN,
               "Agent '" + agentName +
                   "': Tool/internal function name conflict for '" +
                   toolNameStr + "'. Ignoring new tool.");
    delete tool;
  } else {
    registeredTools[toolNameStr] = tool;
    logMessage(LogLevel::INFO, "Agent '" + agentName + "' registered tool: '" +
                                   toolNameStr + "'");
  }
}

void Agent::removeTool(const std::string &toolNameKey) { // Renamed for clarity
  auto it = registeredTools.find(toolNameKey);
  if (it != registeredTools.end()) {
    delete it->second;
    registeredTools.erase(it);
    logMessage(LogLevel::INFO,
               "Agent '" + agentName + "' removed tool: '" + toolNameKey + "'");
  } else {
    logMessage(LogLevel::WARN,
               "Agent '" + agentName +
                   "' attempted to remove non-existent tool: '" + toolNameKey +
                   "'");
  }
}

Tool *Agent::getTool(const std::string &toolNameKey) const {
  auto it = registeredTools.find(toolNameKey);
  return (it != registeredTools.end()) ? it->second : nullptr;
}

// --- Core Agent Loop (Reset, Run - Implementations) ---
void Agent::reset() {
  conversationHistory.clear();
  // LongTermMemory might persist or be cleared based on deeper design choices
  currentIteration = 0;
  skipNextFlowIteration = false;
  logMessage(LogLevel::DEBUG, "Agent '" + agentName + "' state reset.");
}

void Agent::run() {
  logMessage(LogLevel::INFO,
             "Agent '" + agentName + "' starting interactive loop.");
  logMessage(LogLevel::INFO,
             "Type 'exit' or 'quit' to stop, 'reset' to clear history.");

  std::string userInputText;

  std::vector<std::pair<std::string, std::string>> LOCAL_HISTORY;

  while (true) {
    std::cout << "\nUser (" << agentName << ") > ";
    if (!std::getline(std::cin, userInputText)) {
      logMessage(LogLevel::INFO, "Input stream closed (EOF). Exiting agent '" +
                                     agentName + "'.");
      break;
    }
    userInputText.erase(0, userInputText.find_first_not_of(" \t\r\n"));
    userInputText.erase(userInputText.find_last_not_of(" \t\r\n") + 1);

    if (userInputText == "exit" || userInputText == "quit") {
      logMessage(LogLevel::INFO, "Exit command received. Goodbye from agent '" +
                                     agentName + "'!");
      break;
    } else if (userInputText == "reset") {
      reset();
      logMessage(LogLevel::INFO, "Agent '" + agentName + "' has been reset.");
      continue;
    } else if (userInputText.empty()) {
      continue;
    }
    try {
      std::string agentResponseText = prompt(userInputText);

      LOCAL_HISTORY.push_back({"Master", userInputText});
      LOCAL_HISTORY.push_back({this->agentName, agentResponseText});

      // Render the history, right-sided for the agent's perspective, left-sided
      // for user input

      for (const auto &entry : LOCAL_HISTORY) {
        if (entry.first == "Master") {
          std::cout << "\n" << "-----------------------------------------\n";
          std::cout << "\nAgent (" << agentName << ") > " << entry.second
                    << "\n";
          std::cout << "\n" << "-----------------------------------------\n";
        } else {
          std::cout << "\n" << "-----------------------------------------\n";
          std::cout << "\n" << "Master: " << entry.second << "\n";
          std::cout << "\n" << "-----------------------------------------\n";
        }
      }

      std::cout << "-----------------------------------------" << std::endl;
    } catch (const ApiError &e) { // Specific API error
      logMessage(LogLevel::ERROR,
                 "Agent API error for '" + agentName + "':", e.what());
      std::cout << "\n[Agent Error - API]: " << e.what() << std::endl;
    } catch (const std::runtime_error &e) {
      logMessage(LogLevel::ERROR,
                 "Agent runtime error for '" + agentName + "':", e.what());
      std::cout << "\n[Agent Error - Runtime]: " << e.what() << std::endl;
    } catch (const std::exception &e) {
      logMessage(LogLevel::ERROR,
                 "General exception for agent '" + agentName + "':", e.what());
      std::cout << "\n[Agent Error - General]: " << e.what() << std::endl;
    } catch (...) {
      logMessage(LogLevel::ERROR,
                 "Unknown error in agent '" + agentName + "' run loop.");
      std::cout << "\n[Agent Error - Unknown]: An unexpected error occurred."
                << std::endl;
    }
  }
  logMessage(LogLevel::INFO,
             "Agent '" + agentName + "' interactive loop finished.");
}

#define MAX_HISTORY_CONTENT_LEN 100000

// --- Memory & State (Implementations) ---
void Agent::addToHistory(const std::string &role, const std::string &content) {

  std::string processedContent = content.substr(0, MAX_HISTORY_CONTENT_LEN);
  bool truncated = (content.length() > MAX_HISTORY_CONTENT_LEN);
  if (truncated)
    processedContent += "... (truncated)";
  conversationHistory.push_back({role, processedContent});
}

void Agent::addEnvironmentVariable(const std::string &key,
                                   const std::string &value) {
  auto it =
      std::find_if(environmentVariables.begin(), environmentVariables.end(),
                   [&key](const auto &pair) { return pair.first == key; });
  if (it != environmentVariables.end()) {
    it->second = value;
    logMessage(LogLevel::DEBUG, "Agent '" + agentName + "': Updated env var.",
               key + "=" + value);
  } else {
    environmentVariables.push_back({key, value});
    logMessage(LogLevel::DEBUG, "Agent '" + agentName + "': Added env var.",
               key + "=" + value);
  }
}

void Agent::importEnvironmentFile(const std::string &filePath) {
  std::ifstream envFile(filePath);
  if (!envFile.is_open()) {
    logMessage(LogLevel::ERROR,
               "Agent '" + agentName + "' could not open env file:", filePath);
    return;
  }
  std::string line;
  int count = 0;
  while (std::getline(envFile, line)) {
    line.erase(0, line.find_first_not_of(" \t"));
    if (line.empty() || line[0] == '#')
      continue;
    size_t eqPos = line.find('=');
    if (eqPos != std::string::npos) {
      std::string key = line.substr(0, eqPos);
      key.erase(key.find_last_not_of(" \t") + 1);
      std::string value = line.substr(eqPos + 1);
      value.erase(0, value.find_first_not_of(" \t"));
      value.erase(value.find_last_not_of(" \t") + 1);
      if (value.length() >= 2 &&
          ((value.front() == '"' && value.back() == '"') ||
           (value.front() == '\'' && value.back() == '\''))) {
        value = value.substr(1, value.length() - 2);
      }
      if (!key.empty()) {
        addEnvironmentVariable(key, value);
        count++;
      }
    }
  }
  envFile.close();
  logMessage(LogLevel::INFO,
             "Agent '" + agentName + "' imported " + std::to_string(count) +
                 " env vars from:",
             filePath);
}

void Agent::addExtraSystemPrompt(const std::string &promptFragment) {
  extraSystemPrompts.push_back(promptFragment);
}

// --- Getters (Implementations) ---
const std::string &Agent::getName() const { return agentName; }
const std::string &Agent::getDescription() const { return agentDescription; }
const std::string &Agent::getSystemPrompt() const { return systemPrompt; }
const std::string &Agent::getSchema() const { return llmResponseSchema; }
const std::string &Agent::getExample() const { return llmResponseExample; }
int Agent::getIterationCap() const { return iterationLimit; }
const Agent::AgentDirective &Agent::getDirective() const {
  return currentDirective;
}
const std::vector<std::string> &Agent::getTasks() const { return tasks; }
const StringKeyValuePair &Agent::getEnvironmentVariables() const {
  return environmentVariables;
}
const std::vector<std::string> &Agent::getExtraSystemPrompts() const {
  return extraSystemPrompts;
}
const std::vector<std::pair<std::string, std::string>> &
Agent::getHistory() const {
  return conversationHistory;
}

// --- Sub-Agent Management
void Agent::addSubAgent(Agent *subAgentInstance) {
  if (!subAgentInstance || subAgentInstance == this) {
    logMessage(LogLevel::WARN,
               "Agent '" + agentName +
                   "': Invalid sub-agent or self-addition attempt.");
    return;
  }
  if (std::find_if(subAgents.begin(), subAgents.end(), [&](const auto &p) {
        return p.first == subAgentInstance->getName();
      }) != subAgents.end()) {
    logMessage(LogLevel::WARN, "Agent '" + agentName +
                                   "' already has sub-agent '" +
                                   subAgentInstance->getName() + "'.");
    return;
  }
  subAgents.push_back({subAgentInstance->getName(), subAgentInstance});
  logMessage(LogLevel::INFO, "Agent '" + agentName +
                                 "' registered sub-agent: '" +
                                 subAgentInstance->getName() + "'");
}

Agent *Agent::getSubAgent(const std::string &subAgentNameKey) const {
  auto it =
      std::find_if(subAgents.begin(), subAgents.end(),
                   [&](const auto &p) { return p.first == subAgentNameKey; });
  return (it != subAgents.end()) ? it->second : nullptr;
}

// --- Manual Operations (Implementations) ---
std::string Agent::manualToolCall(const std::string &toolName,
                                  const Json::Value &params) {
  logMessage(LogLevel::INFO, "Agent '" + agentName +
                                 "': Manually calling tool '" + toolName + "'");
  ActionInfo ai;
  ai.action = toolName;
  ai.type = "tool"; // Assume registered tool for manual call
  ai.params = params;
  return processSingleAction(ai);
}

std::string Agent::executeApiCall(const std::string &fullPromptText) {
  logMessage(LogLevel::PROMPT,
             "Agent '" + agentName + "': Sending prompt to API.",
             "Length: " + std::to_string(fullPromptText.length()));
  // For extreme debugging: logMessage(LogLevel::DEBUG, "Full prompt text:",
  // fullPromptText);
  try {
    std::string response = api.generate(fullPromptText);
    logMessage(LogLevel::DEBUG,
               "Agent '" + agentName + "': Received API response.",
               "Length: " + std::to_string(response.length()));
    // For extreme debugging: logMessage(LogLevel::DEBUG, "Raw API Response:",
    // response.substr(0, 500));
    return response;
  } catch (const ApiError &e) { // Catch specific ApiError
    logMessage(LogLevel::ERROR,
               "Agent '" + agentName + "': API Error occurred.", e.what());
    Json::Value errorJson;
    errorJson["status"] = "ERROR_INTERNAL_API_CALL_FAILED";
    Json::Value thoughtError;
    thoughtError["type"] = "ERROR_OBSERVATION";
    thoughtError["content"] =
        "The call to the language model API failed: " + std::string(e.what());
    errorJson["thoughts"].append(thoughtError);
    errorJson["actions"] = Json::arrayValue; // Empty array for actions
    errorJson["final_response"] = "I encountered an issue communicating with "
                                  "the language model. The error was: " +
                                  std::string(e.what());
    Json::StreamWriterBuilder writer;
    writer["indentation"] = ""; // Compact error JSON
    return Json::writeString(writer, errorJson);
  } catch (const std::exception &e) { // Catch other standard exceptions
    logMessage(LogLevel::ERROR,
               "Agent '" + agentName + "': Standard exception during API call.",
               e.what());
    Json::Value errorJson; // Construct a similar error JSON
    errorJson["status"] = "ERROR_INTERNAL_STD_EXCEPTION_IN_API_CALL";
    Json::Value thoughtError;
    thoughtError["type"] = "ERROR_OBSERVATION";
    thoughtError["content"] =
        "A standard C++ exception occurred during the API call: " +
        std::string(e.what());
    errorJson["thoughts"].append(thoughtError);
    errorJson["actions"] = Json::arrayValue;
    errorJson["final_response"] =
        "A system error occurred while trying to reach the language model: " +
        std::string(e.what());
    Json::StreamWriterBuilder writer;
    writer["indentation"] = "";
    return Json::writeString(writer, errorJson);
  }
}

void Agent::setSkipNextFlowIteration(bool skip) {
  skipNextFlowIteration = skip;
  if (skip) {
    logMessage(LogLevel::DEBUG, "Agent '" + agentName +
                                    "': Next flow iteration will be skipped.");
  }
}

std::string Agent::directiveTypeToString(AgentDirective::Type type) const {
  switch (type) {
  case AgentDirective::Type::BRAINSTORMING:
    return "BRAINSTORMING";
  case AgentDirective::Type::AUTONOMOUS:
    return "AUTONOMOUS";
  case AgentDirective::Type::NORMAL:
    return "NORMAL";
  case AgentDirective::Type::EXECUTE:
    return "EXECUTE";
  case AgentDirective::Type::REPORT:
    return "REPORT";
  default:
    return "UNKNOWN_DIRECTIVE";
  }
}

std::string Agent::internalAddEnvVar(const Json::Value &params) {
  if (!params.isMember("key") || !params["key"].isString() ||
      !params.isMember("value") || !params["value"].isString()) {
    return "ERR_INVALID_USE [addEnvVar]: Requires string parameters 'key' and "
           "'value'.";
  }
  std::string key = params["key"].asString();
  std::string value = params["value"].asString();
  addEnvironmentVariable(key, value);
  return "Success: Environment variable '" + key + "' set to '" + value + "'.";
}

std::string Agent::internalPromptAgent(const Json::Value &params) {
  if (!params.isMember("agent_name") || !params["agent_name"].isString() ||
      !params.isMember("prompt") || !params["prompt"].isString()) {
    return "Error [promptAgent]: Requires string parameters 'agent_name' and "
           "'prompt'.";
  }

  std::string targetAgentName = params["agent_name"].asString();
  std::string subPromptText = params["prompt"].asString();
  Agent *targetAgent = getSubAgent(targetAgentName);
  if (targetAgent) {
    logMessage(LogLevel::INFO, "Agent '" + agentName +
                                   "' is prompting sub-agent '" +
                                   targetAgentName + "'.");
    try {
      std::string contextualPrompt =
          "CONTEXT: This prompt is from Agent '" + agentName +
          "'. Please process the following request:\n---\n" + subPromptText;
      std::string response = targetAgent->prompt(contextualPrompt);
      logMessage(LogLevel::INFO, "Agent '" + agentName +
                                     "' received response from sub-agent '" +
                                     targetAgentName + "'.");
      return "Response from Agent '" + targetAgentName + "':\n" + response;
    } catch (const std::exception &e) {
      logMessage(LogLevel::ERROR,
                 "Agent '" + agentName + "': Error prompting sub-agent '" +
                     targetAgentName + "'.",
                 e.what());
      return "Error [promptAgent]: Exception while prompting '" +
             targetAgentName + "': " + std::string(e.what());
    }
  }
  logMessage(LogLevel::WARN, "Agent '" + agentName + "': Sub-agent '" +
                                 targetAgentName +
                                 "' not found for prompting.");
  return "Error [promptAgent]: Sub-agent '" + targetAgentName + "' not found.";
}

// --- Utility Implementations ---
std::string Agent::generateTimestamp() const {
  auto nowChrono = std::chrono::system_clock::now();
  auto nowTimeT = std::chrono::system_clock::to_time_t(nowChrono);
  std::tm nowTmLocalBuf;

  std::tm *nowTm = localtime_r(&nowTimeT, &nowTmLocalBuf);

  if (nowTm) {
    std::stringstream ss;
    ss << std::put_time(nowTm, "%Y-%m-%dT%H:%M:%S%Z"); // ISO 8601 like
    return ss.str();
  }
  return "[TIMESTAMP_ERROR]";
}

void Agent::trimLLMResponse(std::string &responseText) {
  // Finds ```json ... ``` or ``` ... ``` and extracts the content.
  size_t startPos = responseText.find("```");
  if (startPos == std::string::npos)
    return;

  // Look for "json" immediately after the first ```
  size_t contentActualStart = startPos + 3;
  if (responseText.length() > startPos + 7 &&
      responseText.substr(startPos + 3, 4) == "json") {
    // Skip "json" and any immediate newline/whitespace
    contentActualStart =
        responseText.find_first_not_of(" \t\r\n", startPos + 7);
    if (contentActualStart ==
        std::string::npos) { // Only ```json and whitespace after
      responseText = "";
      return;
    }
  } else {
    // Skip just ``` and any immediate newline/whitespace
    contentActualStart =
        responseText.find_first_not_of(" \t\r\n", startPos + 3);
    if (contentActualStart ==
        std::string::npos) { // Only ``` and whitespace after
      responseText = "";
      return;
    }
  }

  size_t endPos = responseText.rfind("```");
  if (endPos == std::string::npos || endPos <= contentActualStart)
    return;

  // Content is between contentActualStart and just before endPos
  responseText =
      responseText.substr(contentActualStart, endPos - contentActualStart);
  // Trim any leading/trailing whitespace from the extracted content itself
  responseText.erase(0, responseText.find_first_not_of(" \t\r\n"));
  responseText.erase(responseText.find_last_not_of(" \t\r\n") + 1);

  logMessage(LogLevel::DEBUG,
             "Agent '" + agentName + "': Trimmed LLM response code block.");
}
