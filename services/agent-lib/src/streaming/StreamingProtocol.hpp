#pragma once

#include <json/json.h>
#include <string>
#include <vector>
#include <map>
#include <memory>
#include <functional>

/**
 * ==============================================================================
 * STREAMING EXECUTION PROTOCOL v1.1 - C++ Implementation
 * ==============================================================================
 * 
 * Implements the Cortex-Prime streaming protocol for real-time action execution
 * as the LLM generates its response.
 * 
 * Protocol Format:
 * - <thought>...</thought>           - Reasoning that streams to user
 * - <action type="..." mode="..." id="...">JSON</action> - Actions to execute
 * - <response final="true">...</response> - Final answer to user
 * - <context_feed id="...">...</context_feed> - Dynamic context injection
 * 
 * Execution Modes:
 * - sync: Wait for completion before continuing
 * - async: Run in background, continue parsing
 * - fire_and_forget: Start execution, don't track result
 * 
 * Action Types:
 * - tool: Stateless function/tool
 * - agent: Sub-agent delegation
 * - relic: Persistent service (database, cache, API)
 * - workflow: Multi-step pipeline
 * - llm: LLM call for sub-tasks
 * - internal: Modify agent environment (add context feeds, etc.)
 * 
 * See: docs/streaming/STREAMING_PROTOCOL.md for full specification
 */

namespace StreamingProtocol {

// Parser states
enum class ParserState {
    IDLE,
    IN_THOUGHT,
    IN_ACTION,
    IN_RESPONSE,
    IN_CONTEXT_FEED
};

// Execution modes
enum class ExecutionMode {
    SYNC,
    ASYNC,
    FIRE_AND_FORGET
};

// Action types
enum class ActionType {
    TOOL,
    AGENT,
    RELIC,
    WORKFLOW,
    LLM,
    INTERNAL
};

// Parsed action structure
struct ParsedAction {
    std::string id;
    ActionType type;
    ExecutionMode mode;
    std::string name;
    Json::Value parameters;
    std::string outputKey;
    std::vector<std::string> dependsOn;
    bool embeddedInThought = false;
    
    // For error handling
    int timeout = 30;
    int retryCount = 0;
    bool skipOnError = false;
};

// Parsed response structure
struct ParsedResponse {
    std::string content;
    bool isFinal = true;  // If false, agent continues after response
};

// Context feed structure
struct ContextFeed {
    std::string id;
    std::string type;  // on_demand, periodic, internal, etc.
    Json::Value source;
    std::string content;
    int cacheTtl = 0;
    int maxTokens = 0;
};

// Token event for streaming output
struct TokenEvent {
    enum class Type {
        THOUGHT,
        ACTION_START,
        ACTION_COMPLETE,
        RESPONSE,
        CONTEXT_FEED,
        ERROR
    } type;
    
    std::string content;
    std::shared_ptr<ParsedAction> action;
    std::map<std::string, std::string> metadata;
};

// Action executor callback
// Returns: Result as JSON value, or throws on error
using ActionExecutor = std::function<Json::Value(const ParsedAction&)>;

// Token callback for real-time output
using TokenCallback = std::function<void(const TokenEvent&)>;

/**
 * Streaming Protocol Parser
 * 
 * Parses LLM output in real-time, executing actions as soon as they're complete.
 */
class Parser {
public:
    Parser(ActionExecutor executor = nullptr);
    
    // Parse a token from the LLM stream
    void parseToken(const std::string& token, bool isFinal);
    
    // Set callback for token events
    void setTokenCallback(TokenCallback callback);
    
    // Set action executor
    void setActionExecutor(ActionExecutor executor);
    
    // Get current parser state
    ParserState getState() const { return state; }
    
    // Get action results
    Json::Value getActionResult(const std::string& actionId) const;
    
    // Get all action results
    std::map<std::string, Json::Value> getAllResults() const { return actionResults; }
    
    // Reset parser state
    void reset();
    
    // Add context feed
    void addContextFeed(const ContextFeed& feed);
    
    // Get context feed value
    std::string getContextFeedValue(const std::string& feedId) const;
    
    // Execute internal action (add_context_feed, set_variable, etc.)
    bool executeInternalAction(const ParsedAction& action);

private:
    ParserState state = ParserState::IDLE;
    std::string buffer;
    std::string currentThought;
    std::string currentAction;
    std::string currentResponse;
    std::string currentContextFeed;
    
    // Track last emitted thought position for chunked streaming
    size_t lastEmittedThoughtPos = 0;
    
    std::map<std::string, std::string> currentAttributes;
    
    ActionExecutor actionExecutor;
    TokenCallback tokenCallback;
    
    // Action execution tracking
    std::map<std::string, Json::Value> actionResults;
    std::map<std::string, bool> actionCompleted;
    std::vector<std::shared_ptr<ParsedAction>> pendingActions;
    
    // Context feeds
    std::map<std::string, ContextFeed> contextFeeds;
    
    // Helper methods
    void processBuffer();
    bool detectTagStart(const std::string& tagName);
    bool detectTagEnd(const std::string& tagName);
    std::map<std::string, std::string> parseAttributes(const std::string& attrString);
    
    void handleThought();
    void handleAction();
    void handleResponse();
    void handleContextFeed();
    
    std::string cleanJSON(const std::string& rawJSON);  // New: JSON cleaning
    std::shared_ptr<ParsedAction> parseAction(const std::string& jsonStr, 
                                              const std::map<std::string, std::string>& attrs);
    
    void executeAction(std::shared_ptr<ParsedAction> action);
    bool canExecuteAction(const ParsedAction& action) const;
    
    std::string resolveVariables(const std::string& input) const;
    Json::Value resolveVariables(const Json::Value& input) const;
    
    void emitToken(const TokenEvent& event);
    
    ExecutionMode parseMode(const std::string& modeStr);
    ActionType parseType(const std::string& typeStr);
};

} // namespace StreamingProtocol
