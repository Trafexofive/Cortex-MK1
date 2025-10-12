#pragma once

#include "File.hpp"
#include "MiniGemini.hpp"
#include "Tool.hpp"
#include "Utils.hpp"
#include "StreamingProtocol.hpp"
#include "Relic.hpp"

#include <chrono>
#include <iomanip>
#include <json/json.h>
#include <map>
#include <memory>
#include <stack> // For potential future use, not strictly needed by current regeneration
#include <stdexcept>
#include <string>
#include <vector>
// Forward declarations
namespace Json {
class Value;
}

class MiniGemini;
class Tool;
class File; // Assuming File.hpp defines this
class Relic;

// Typedefs
using FileList = std::vector<File>;
using StringKeyValuePair = std::vector<std::pair<std::string, std::string>>;

// --- Structs for LLM Interaction ---

struct StructuredThought {
  std::string type;
  std::string content;
};

struct ActionInfo {
  std::string action; // name of the action to perform eg, "search",
                      // "calculate", "fetch_data"
  std::string type;   // e.g., "tool", "script", "internal_function",
                      // "http_request", "output", etc.
  Json::Value params;

  double confidence = 1.0;
  std::vector<std::string> warnings;
};

struct ParsedLLMResponse {
  bool success = false;

  std::string status;

  std::vector<StructuredThought> thoughts;
  std::vector<ActionInfo> actions;

  std::string finalResponseField;
  std::string rawTrimmedJson;

  bool stop =
      true; // Indicates if the agent should stop processing further actions
};

class Agent {
public:
  struct AgentDirective {
    enum class Type { BRAINSTORMING, AUTONOMOUS, NORMAL, EXECUTE, REPORT };
    Type type = Type::NORMAL;
    std::string description;
    std::string format;
  };

  using DIRECTIVE = AgentDirective;

  // --- Constructor & Destructor ---
  Agent(LLMClient &apiRef, const std::string &agentName = "defaultAgent");
  ~Agent();

  // --- Configuration Setters ---
  void setName(const std::string &newName);
  void setDescription(const std::string &newDescription);
  void setSystemPrompt(const std::string &prompt);
  void
  setSchema(const std::string &schema); // For LLM Response Schema (as guide)
  void
  setExample(const std::string &example); // For Example LLM Response (as guide)
  void setIterationCap(int cap);
  void setDirective(const AgentDirective &directive);
  void addEnvVar(const std::string &key,
                  const std::string &value)
    { environmentVariables.emplace_back(key, value); }

  void addTask(const std::string &task); // Conceptual task for prompting
  void addInitialCommand(
      const std::string &command); // For commands to run on start via run()

  // setModel implement
  void setModel(const std::string &modelName) { api.setModel(modelName); }
  void setTemperature(double temperature) { api.setTemperature(temperature); }
  void setTokenLimit(int tokenLimit) { api.setMaxTokens(tokenLimit); }
  // --- Tool Management ---
  void addTool(Tool *tool); // Agent takes ownership of this raw pointer
  void removeTool(const std::string &toolName); // Deletes the tool
  Tool *getTool(const std::string &toolName) const;
  std::string hotReloadConfig(const std::string &yamlPath);

  std::string hotReloadConfigTool(const Json::Value &params);
  // agent.getRegisteredTools() returns a map of tool names to Tool* pointers

  std::map<std::string, Tool *> getRegisteredTools() const {
    return registeredTools;
  }
  
  // --- Relic Management ---
  void addRelic(Relic* relic);  // Agent tracks but doesn't own (managed by RelicManager)
  Relic* getRelic(const std::string& relicName) const;
  std::vector<std::string> listRelics() const;

  // --- Core Agent Loop ---
  void reset();
  std::string prompt(const std::string &userInput);
  void run(); // Interactive CLI loop
  
  // --- Streaming Protocol Support ---
  void promptStreaming(const std::string &userInput, 
                      StreamingProtocol::TokenCallback callback);
  void setStreamingEnabled(bool enabled) { streamingEnabled = enabled; }
  bool isStreamingEnabled() const { return streamingEnabled; }
  
  // Add context feed (v1.1 protocol)
  void addContextFeed(const StreamingProtocol::ContextFeed& feed);
  std::string getContextFeedValue(const std::string& feedId) const;
  std::map<std::string, StreamingProtocol::ContextFeed> getContextFeeds() const { 
    return contextFeeds; 
  }

  // --- Memory & State ---
  void addToHistory(const std::string &role, const std::string &content);
  void addEnvironmentVariable(const std::string &key, const std::string &value);
  void importEnvironmentFile(const std::string &filePath);
  void addExtraSystemPrompt(const std::string &promptFragment);


  // --- Getters ---
  const std::string &getName() const;
  const std::string &getDescription() const;
  const std::string &getSystemPrompt() const;
  const std::string &getSchema() const;
  const std::string &getExample() const;
  int getIterationCap() const;
  const AgentDirective &getDirective() const;
  const std::vector<std::string> &getTasks() const;
  const StringKeyValuePair &getEnvironmentVariables() const;
  const std::string getEnvVar(const std::string &key) const {
    for (const auto &pair : environmentVariables) {
      if (pair.first == key) {
        return pair.second;
      }
    }
    return "";
  }
  const std::vector<std::string> &getExtraSystemPrompts() const;
  const std::vector<std::pair<std::string, std::string>> &getHistory() const;
  // getapi
  LLMClient &getApi() const { return api; }

  // --- Sub-Agent Management ---
  void
  addSubAgent(Agent *subAgentInstance); // Agent does NOT own sub-agent pointers
  Agent *getSubAgent(const std::string &subAgentName) const;
  bool hasSubAgents() const { return !subAgents.empty(); }
  const std::vector<std::pair<std::string, Agent*>>& getSubAgents() const { return subAgents; }

  // --- Manual Operations ---
  std::string manualToolCall(const std::string &toolName,
                             const Json::Value &params);

private:
  // --- Core Members ---
  LLMClient &api;
  std::string agentName;
  std::string agentDescription;
  std::string systemPrompt;

  std::string llmResponseSchema;  // For guiding LLM, not strict validation here
  std::string llmResponseExample; // For guiding LLM

  std::vector<std::pair<std::string, std::string>> conversationHistory;
  int currentIteration;
  int iterationLimit;
  bool skipNextFlowIteration;

  StringKeyValuePair environmentVariables;
  FileList agentFiles; // Consider if this is actively used or can be
                       // deprecated/refactored
  std::vector<std::string> extraSystemPrompts;
  std::vector<std::pair<std::string, Agent *>>
      subAgents; // name -> Agent* (non-owning)

  std::vector<std::string> tasks;
  std::vector<std::string> initialCommands; // Executed by run()

  AgentDirective currentDirective;

  std::map<std::string, Tool *> registeredTools; // Agent owns these Tool*
  std::map<std::string, std::string> internalFunctionDescriptions;
  std::map<std::string, Relic*> registeredRelics; // Agent doesn't own, just references
  
  // Streaming protocol support
  bool streamingEnabled = false;
  std::unique_ptr<StreamingProtocol::Parser> streamingParser;
  std::map<std::string, StreamingProtocol::ContextFeed> contextFeeds;

  // --- Private Helper Methods ---
  std::string buildFullPrompt() const;
  ParsedLLMResponse
  parseStructuredLLMResponse(const std::string &trimmedJsonString);
  std::string processActions(const std::vector<ActionInfo> &actions);
  std::string processSingleAction(const ActionInfo &actionInfo);
  std::string executeApiCall(const std::string &fullPrompt);
  void setSkipNextFlowIteration(bool skip);
  std::string directiveTypeToString(AgentDirective::Type type) const;
  std::vector<ActionInfo> &expandActions(std::vector<ActionInfo> &actions) ;

  // Internal "Tool-Like" Functions (declared as private methods)
  std::string internalPromptAgent(const Json::Value &params);
  std::string internalGetWeather(
      const Json::Value &params); // Example, depends on bash+curl
  std::string
  internalGetCurrentTime(const Json::Value &params); // To be implemented
  std::string internalAddEnvVar(
      const Json::Value &params);

void saveHistory(void);


  // Utility
  std::string generateTimestamp() const;
  void trimLLMResponse(
      std::string &responseText); // Helper to extract JSON from ```json ... ```
};
