#include "StreamingProtocol.hpp"
#include "Utils.hpp"
#include <regex>
#include <sstream>
#include <algorithm>

namespace StreamingProtocol {

Parser::Parser(ActionExecutor executor) 
    : actionExecutor(executor) {
}

void Parser::setTokenCallback(TokenCallback callback) {
    tokenCallback = callback;
}

void Parser::setActionExecutor(ActionExecutor executor) {
    actionExecutor = executor;
}

void Parser::parseToken(const std::string& token, bool isFinal) {
    buffer += token;
    processBuffer();
    
    if (isFinal) {
        // Flush any remaining content
        if (state == ParserState::IN_THOUGHT && !currentThought.empty()) {
            handleThought();
        }
        if (state == ParserState::IN_RESPONSE && !currentResponse.empty()) {
            handleResponse();
        }
        
        // FALLBACK: If LLM didn't use protocol format and we have unprocessed buffer,
        // treat it as a plain text response
        if (state == ParserState::IDLE && !buffer.empty()) {
            logMessage(LogLevel::WARN, "LLM response did not use streaming protocol format", 
                      "Treating as plain text response");
            
            if (tokenCallback) {
                TokenEvent event;
                event.type = TokenEvent::Type::RESPONSE;
                event.content = buffer;
                event.metadata["is_final"] = "true";
                event.metadata["fallback"] = "true";
                emitToken(event);
            }
            
            buffer.clear();
        }
    }
}

void Parser::processBuffer() {
    // Strip markdown code block markers from buffer before processing
    // Look for ```xml or ``` at start of buffer or on newlines
    size_t pos = 0;
    while ((pos = buffer.find("```", pos)) != std::string::npos) {
        // Check if this is start of line or buffer
        bool isLineStart = (pos == 0) || (buffer[pos-1] == '\n');
        
        if (isLineStart) {
            // Find end of this line
            size_t lineEnd = buffer.find('\n', pos);
            if (lineEnd != std::string::npos) {
                // Remove the entire line containing ```
                buffer.erase(pos, lineEnd - pos + 1);
                continue; // Don't increment pos, check same position again
            } else {
                // ``` at end of buffer without newline - might be incomplete
                // Only remove if we have ``` followed by more content
                if (pos + 3 < buffer.length()) {
                    buffer.erase(pos, 3);
                } else {
                    break; // Wait for more data
                }
            }
        } else {
            pos++;
        }
    }
    
    while (!buffer.empty()) {
        bool processed = false;
        
        // Check for tag transitions
        if (state == ParserState::IDLE || state == ParserState::IN_THOUGHT) {
            if (detectTagStart("thought")) {
                state = ParserState::IN_THOUGHT;
                processed = true;
            }
        }
        
        if (detectTagStart("action")) {
            if (state == ParserState::IN_THOUGHT) {
                // Action embedded in thought - emit current thought first
                handleThought();
            }
            state = ParserState::IN_ACTION;
            processed = true;
        }
        
        if (detectTagStart("response")) {
            if (state == ParserState::IN_THOUGHT) {
                handleThought();
            }
            state = ParserState::IN_RESPONSE;
            processed = true;
        }
        
        if (detectTagStart("context_feed")) {
            state = ParserState::IN_CONTEXT_FEED;
            processed = true;
        }
        
        // Check for tag endings
        if (state == ParserState::IN_THOUGHT && detectTagEnd("thought")) {
            handleThought();
            state = ParserState::IDLE;
            processed = true;
        }
        
        if (state == ParserState::IN_ACTION && detectTagEnd("action")) {
            handleAction();
            state = (currentThought.empty()) ? ParserState::IDLE : ParserState::IN_THOUGHT;
            processed = true;
        }
        
        if (state == ParserState::IN_RESPONSE && detectTagEnd("response")) {
            handleResponse();
            state = ParserState::IDLE;
            processed = true;
        }
        
        if (state == ParserState::IN_CONTEXT_FEED && detectTagEnd("context_feed")) {
            handleContextFeed();
            state = ParserState::IDLE;
            processed = true;
        }
        
        if (!processed) {
            // Accumulate content
            if (!buffer.empty()) {
                char c = buffer[0];
                buffer.erase(0, 1);
                
                switch (state) {
                    case ParserState::IN_THOUGHT:
                        currentThought += c;
                        // Stream thought in chunks (every 10 characters or on buffer empty)
                        // This reduces callback spam and terminal rendering artifacts
                        if (currentThought.length() - lastEmittedThoughtPos >= 10 || buffer.empty() || c == '\n') {
                            if (tokenCallback && currentThought.length() > lastEmittedThoughtPos) {
                                TokenEvent event;
                                event.type = TokenEvent::Type::THOUGHT;
                                event.content = currentThought.substr(lastEmittedThoughtPos);
                                lastEmittedThoughtPos = currentThought.length();
                                emitToken(event);
                            }
                        }
                        break;
                    case ParserState::IN_ACTION:
                        currentAction += c;
                        break;
                    case ParserState::IN_RESPONSE:
                        currentResponse += c;
                        // Buffer response, don't stream yet (need to resolve variables first)
                        break;
                    case ParserState::IN_CONTEXT_FEED:
                        currentContextFeed += c;
                        break;
                    default:
                        // Discard content outside of tags
                        break;
                }
            } else {
                break;
            }
        }
    }
}

bool Parser::detectTagStart(const std::string& tagName) {
    std::string openTag = "<" + tagName;
    size_t pos = buffer.find(openTag);
    
    if (pos != std::string::npos) {
        // Find the end of the opening tag
        size_t endPos = buffer.find('>', pos);
        if (endPos != std::string::npos) {
            // Extract attributes if present
            std::string tagContent = buffer.substr(pos, endPos - pos + 1);
            size_t attrStart = pos + openTag.length();
            if (attrStart < endPos) {
                std::string attrString = buffer.substr(attrStart, endPos - attrStart);
                currentAttributes = parseAttributes(attrString);
            } else {
                currentAttributes.clear();
            }
            
            buffer.erase(0, endPos + 1);
            return true;
        }
    }
    
    return false;
}

bool Parser::detectTagEnd(const std::string& tagName) {
    std::string closeTag = "</" + tagName + ">";
    size_t pos = buffer.find(closeTag);
    
    if (pos != std::string::npos) {
        buffer.erase(0, pos + closeTag.length());
        return true;
    }
    
    return false;
}

std::map<std::string, std::string> Parser::parseAttributes(const std::string& attrString) {
    std::map<std::string, std::string> attrs;
    
    // Simple attribute parser: key="value" or key='value'
    std::regex attrRegex(R"((\w+)\s*=\s*[\"']([^\"']*)[\"'])");
    std::sregex_iterator iter(attrString.begin(), attrString.end(), attrRegex);
    std::sregex_iterator end;
    
    while (iter != end) {
        std::smatch match = *iter;
        attrs[match[1].str()] = match[2].str();
        ++iter;
    }
    
    return attrs;
}

void Parser::handleThought() {
    // Emit any remaining thought content that wasn't sent yet
    if (tokenCallback && currentThought.length() > lastEmittedThoughtPos) {
        TokenEvent event;
        event.type = TokenEvent::Type::THOUGHT;
        event.content = currentThought.substr(lastEmittedThoughtPos);
        emitToken(event);
    }
    
    // Clear thought and reset tracking
    currentThought.clear();
    lastEmittedThoughtPos = 0;
}

void Parser::handleAction() {
    try {
        auto action = parseAction(currentAction, currentAttributes);
        if (action) {
            action->embeddedInThought = !currentThought.empty();
            
            if (tokenCallback) {
                TokenEvent event;
                event.type = TokenEvent::Type::ACTION_START;
                event.action = action;
                event.metadata["action_id"] = action->id;
                event.metadata["action_name"] = action->name;
                emitToken(event);
            }
            
            // Execute if dependencies are met
            if (canExecuteAction(*action)) {
                executeAction(action);
            } else {
                pendingActions.push_back(action);
            }
        }
    } catch (const std::exception& e) {
        logMessage(LogLevel::ERROR, "Failed to parse action", e.what());
        if (tokenCallback) {
            TokenEvent event;
            event.type = TokenEvent::Type::ERROR;
            event.content = std::string("Action parse error: ") + e.what();
            emitToken(event);
        }
    }
    
    currentAction.clear();
    currentAttributes.clear();
}

void Parser::handleResponse() {
    // Resolve variables in response content
    std::string resolvedContent = resolveVariables(currentResponse);
    
    // Check if response is final (default true)
    bool isFinal = true;
    if (currentAttributes.count("final")) {
        std::string finalAttr = currentAttributes["final"];
        isFinal = (finalAttr != "false" && finalAttr != "0");
    }
    
    // Emit resolved response
    if (tokenCallback && !resolvedContent.empty()) {
        TokenEvent event;
        event.type = TokenEvent::Type::RESPONSE;
        event.content = resolvedContent;
        event.metadata["is_final"] = isFinal ? "true" : "false";
        emitToken(event);
    }
    
    // Store final status for agent loop control
    if (isFinal) {
        logMessage(LogLevel::DEBUG, "Final response received", "");
    } else {
        logMessage(LogLevel::DEBUG, "Non-final response", "Agent will continue");
    }
    
    currentResponse.clear();
    currentAttributes.clear();
}

void Parser::handleContextFeed() {
    try {
        std::string feedId = currentAttributes["id"];
        if (!feedId.empty()) {
            ContextFeed feed;
            feed.id = feedId;
            feed.content = currentContextFeed;
            addContextFeed(feed);
            
            if (tokenCallback) {
                TokenEvent event;
                event.type = TokenEvent::Type::CONTEXT_FEED;
                event.metadata["feed_id"] = feedId;
                event.content = currentContextFeed;
                emitToken(event);
            }
        }
    } catch (const std::exception& e) {
        logMessage(LogLevel::ERROR, "Failed to process context feed", e.what());
    }
    
    currentContextFeed.clear();
    currentAttributes.clear();
}

// Clean JSON by removing comments and fixing common issues
std::string Parser::cleanJSON(const std::string& rawJSON) {
    std::string cleaned = rawJSON;
    
    // 1. Remove single-line comments (// ...)
    std::regex singleComment(R"(//[^\n]*)");
    cleaned = std::regex_replace(cleaned, singleComment, "");
    
    // 2. Remove multi-line comments (/* ... */)
    std::regex multiComment(R"(/\*.*?\*/)");
    cleaned = std::regex_replace(cleaned, multiComment, "");
    
    // 3. Remove trailing commas before } or ]
    std::regex trailingComma(R"(,\s*([\]}]))");
    cleaned = std::regex_replace(cleaned, trailingComma, "$1");
    
    // 4. Trim whitespace
    size_t start = cleaned.find_first_not_of(" \t\n\r");
    size_t end = cleaned.find_last_not_of(" \t\n\r");
    if (start != std::string::npos && end != std::string::npos) {
        cleaned = cleaned.substr(start, end - start + 1);
    }
    
    return cleaned;
}

std::shared_ptr<ParsedAction> Parser::parseAction(const std::string& jsonStr,
                                                   const std::map<std::string, std::string>& attrs) {
    auto action = std::make_shared<ParsedAction>();
    
    // Parse attributes
    if (attrs.count("id")) action->id = attrs.at("id");
    if (attrs.count("type")) action->type = parseType(attrs.at("type"));
    if (attrs.count("mode")) action->mode = parseMode(attrs.at("mode"));
    
    // Clean JSON first to remove comments and fix common issues
    std::string cleanedJSON = cleanJSON(jsonStr);
    
    // Parse JSON body
    Json::CharReaderBuilder readerBuilder;
    Json::Value root;
    std::string errs;
    std::istringstream stream(cleanedJSON);
    
    if (!Json::parseFromStream(readerBuilder, stream, &root, &errs)) {
        // Enhanced error message with original and cleaned JSON
        std::stringstream errorMsg;
        errorMsg << "Failed to parse action JSON: " << errs << "\n";
        errorMsg << "Cleaned JSON (first 200 chars): " << cleanedJSON.substr(0, 200);
        
        logMessage(LogLevel::ERROR, "Failed to parse action", errorMsg.str());
        throw std::runtime_error("Failed to parse action JSON: " + errs);
    }
    
    if (root.isMember("name")) action->name = root["name"].asString();
    if (root.isMember("parameters")) action->parameters = root["parameters"];
    if (root.isMember("output_key")) action->outputKey = root["output_key"].asString();
    
    if (root.isMember("depends_on") && root["depends_on"].isArray()) {
        for (const auto& dep : root["depends_on"]) {
            if (dep.isString()) {
                action->dependsOn.push_back(dep.asString());
            }
        }
    }
    
    if (root.isMember("timeout")) action->timeout = root["timeout"].asInt();
    if (root.isMember("retry_count")) action->retryCount = root["retry_count"].asInt();
    if (root.isMember("skip_on_error")) action->skipOnError = root["skip_on_error"].asBool();
    
    // Resolve variable references in parameters
    action->parameters = resolveVariables(action->parameters);
    
    return action;
}

bool Parser::canExecuteAction(const ParsedAction& action) const {
    for (const auto& depId : action.dependsOn) {
        if (!actionCompleted.count(depId) || !actionCompleted.at(depId)) {
            return false;
        }
    }
    return true;
}

void Parser::executeAction(std::shared_ptr<ParsedAction> action) {
    if (!actionExecutor) {
        logMessage(LogLevel::WARN, "No action executor configured", "Action: " + action->name);
        actionCompleted[action->id] = false;
        return;
    }
    
    // Handle internal actions specially
    if (action->type == ActionType::INTERNAL) {
        bool success = executeInternalAction(*action);
        actionCompleted[action->id] = true;
        
        if (tokenCallback) {
            TokenEvent event;
            event.type = TokenEvent::Type::ACTION_COMPLETE;
            event.action = action;
            event.metadata["action_id"] = action->id;
            event.metadata["type"] = "internal";
            event.metadata["success"] = success ? "true" : "false";
            emitToken(event);
        }
        return;
    }
    
    try {
        Json::Value result = actionExecutor(*action);
        
        // Store result by both output_key and action id
        if (!action->outputKey.empty()) {
            actionResults[action->outputKey] = result;
            logMessage(LogLevel::DEBUG, "Stored action result", 
                      "Key: " + action->outputKey + ", Action: " + action->id);
        }
        actionResults[action->id] = result;
        actionCompleted[action->id] = true;
        
        if (tokenCallback) {
            TokenEvent event;
            event.type = TokenEvent::Type::ACTION_COMPLETE;
            event.action = action;
            event.metadata["action_id"] = action->id;
            event.metadata["output_key"] = action->outputKey;
            event.metadata["success"] = "true";
            emitToken(event);
        }
        
        // Check if any pending actions can now execute
        auto it = pendingActions.begin();
        while (it != pendingActions.end()) {
            if (canExecuteAction(**it)) {
                auto pendingAction = *it;
                it = pendingActions.erase(it);
                executeAction(pendingAction);
            } else {
                ++it;
            }
        }
        
    } catch (const std::exception& e) {
        logMessage(LogLevel::ERROR, "Action execution failed", 
                  "Action: " + action->name + ", Error: " + e.what());
        
        actionCompleted[action->id] = !action->skipOnError;
        
        if (tokenCallback) {
            TokenEvent event;
            event.type = TokenEvent::Type::ERROR;
            event.content = std::string("Action failed: ") + e.what();
            event.metadata["action_id"] = action->id;
            event.metadata["skip_on_error"] = action->skipOnError ? "true" : "false";
            emitToken(event);
        }
    }
}

bool Parser::executeInternalAction(const ParsedAction& action) {
    logMessage(LogLevel::DEBUG, "Executing internal action", "Name: " + action.name);
    
    if (action.name == "add_context_feed") {
        // Add a new context feed dynamically
        if (!action.parameters.isMember("id")) {
            logMessage(LogLevel::ERROR, "add_context_feed missing 'id' parameter", "");
            return false;
        }
        
        ContextFeed feed;
        feed.id = action.parameters["id"].asString();
        
        if (action.parameters.isMember("type")) {
            feed.type = action.parameters["type"].asString();
        }
        if (action.parameters.isMember("source")) {
            feed.source = action.parameters["source"];
        }
        if (action.parameters.isMember("cache_ttl")) {
            feed.cacheTtl = action.parameters["cache_ttl"].asInt();
        }
        if (action.parameters.isMember("max_tokens")) {
            feed.maxTokens = action.parameters["max_tokens"].asInt();
        }
        
        addContextFeed(feed);
        logMessage(LogLevel::INFO, "Added context feed via internal action", "ID: " + feed.id);
        return true;
    }
    else if (action.name == "remove_context_feed") {
        if (!action.parameters.isMember("id")) {
            logMessage(LogLevel::ERROR, "remove_context_feed missing 'id' parameter", "");
            return false;
        }
        
        std::string feedId = action.parameters["id"].asString();
        contextFeeds.erase(feedId);
        logMessage(LogLevel::INFO, "Removed context feed", "ID: " + feedId);
        return true;
    }
    else if (action.name == "set_variable") {
        if (!action.parameters.isMember("key") || !action.parameters.isMember("value")) {
            logMessage(LogLevel::ERROR, "set_variable missing 'key' or 'value'", "");
            return false;
        }
        
        std::string key = action.parameters["key"].asString();
        actionResults[key] = action.parameters["value"];
        logMessage(LogLevel::DEBUG, "Set variable", "Key: " + key);
        return true;
    }
    else if (action.name == "delete_variable") {
        if (!action.parameters.isMember("key")) {
            logMessage(LogLevel::ERROR, "delete_variable missing 'key' parameter", "");
            return false;
        }
        
        std::string key = action.parameters["key"].asString();
        actionResults.erase(key);
        logMessage(LogLevel::DEBUG, "Deleted variable", "Key: " + key);
        return true;
    }
    else if (action.name == "clear_context") {
        actionResults.clear();
        logMessage(LogLevel::INFO, "Cleared execution context", "");
        return true;
    }
    else {
        logMessage(LogLevel::WARN, "Unknown internal action", "Name: " + action.name);
        return false;
    }
}

std::string Parser::resolveVariables(const std::string& input) const {
    std::string result = input;
    
    // Resolve $variable_name references
    std::regex varRegex(R"(\$(\w+))");
    std::sregex_iterator iter(result.begin(), result.end(), varRegex);
    std::sregex_iterator end;
    
    // Build replacement map first to avoid iterator invalidation
    struct Replacement {
        size_t pos;
        size_t len;
        std::string value;
    };
    std::vector<Replacement> replacements;
    
    while (iter != end) {
        std::smatch match = *iter;
        std::string varName = match[1].str();
        std::string replacement;
        
        // Check action results
        if (actionResults.count(varName)) {
            const Json::Value& value = actionResults.at(varName);
            
            // Handle different JSON types
            if (value.isString()) {
                replacement = value.asString();
            } else if (value.isNumeric()) {
                if (value.isDouble()) {
                    replacement = std::to_string(value.asDouble());
                } else {
                    replacement = std::to_string(value.asInt64());
                }
            } else if (value.isBool()) {
                replacement = value.asBool() ? "true" : "false";
            } else if (value.isNull()) {
                replacement = "null";
            } else {
                // For objects/arrays, serialize to JSON
                Json::StreamWriterBuilder builder;
                builder["indentation"] = "";
                replacement = Json::writeString(builder, value);
            }
        }
        // Check context feeds
        else if (contextFeeds.count(varName)) {
            replacement = contextFeeds.at(varName).content;
        }
        
        if (!replacement.empty()) {
            replacements.push_back({
                static_cast<size_t>(match.position(0)),
                static_cast<size_t>(match.length(0)),
                replacement
            });
        }
        
        ++iter;
    }
    
    // Apply replacements in reverse order to maintain positions
    for (auto it = replacements.rbegin(); it != replacements.rend(); ++it) {
        result.replace(it->pos, it->len, it->value);
    }
    
    return result;
}

Json::Value Parser::resolveVariables(const Json::Value& input) const {
    if (input.isString()) {
        return Json::Value(resolveVariables(input.asString()));
    } else if (input.isArray()) {
        Json::Value result(Json::arrayValue);
        for (const auto& item : input) {
            result.append(resolveVariables(item));
        }
        return result;
    } else if (input.isObject()) {
        Json::Value result(Json::objectValue);
        for (const auto& key : input.getMemberNames()) {
            result[key] = resolveVariables(input[key]);
        }
        return result;
    }
    return input;
}

void Parser::emitToken(const TokenEvent& event) {
    if (tokenCallback) {
        tokenCallback(event);
    }
}

ExecutionMode Parser::parseMode(const std::string& modeStr) {
    if (modeStr == "sync") return ExecutionMode::SYNC;
    if (modeStr == "async") return ExecutionMode::ASYNC;
    if (modeStr == "fire_and_forget") return ExecutionMode::FIRE_AND_FORGET;
    return ExecutionMode::ASYNC; // Default
}

ActionType Parser::parseType(const std::string& typeStr) {
    if (typeStr == "tool") return ActionType::TOOL;
    if (typeStr == "agent") return ActionType::AGENT;
    if (typeStr == "relic") return ActionType::RELIC;
    if (typeStr == "workflow") return ActionType::WORKFLOW;
    if (typeStr == "llm") return ActionType::LLM;
    if (typeStr == "internal") return ActionType::INTERNAL;
    return ActionType::TOOL; // Default
}

void Parser::reset() {
    state = ParserState::IDLE;
    buffer.clear();
    currentThought.clear();
    currentAction.clear();
    currentResponse.clear();
    currentContextFeed.clear();
    currentAttributes.clear();
    actionResults.clear();
    actionCompleted.clear();
    pendingActions.clear();
    lastEmittedThoughtPos = 0;  // Reset thought tracking
}

void Parser::addContextFeed(const ContextFeed& feed) {
    contextFeeds[feed.id] = feed;
}

std::string Parser::getContextFeedValue(const std::string& feedId) const {
    if (contextFeeds.count(feedId)) {
        return contextFeeds.at(feedId).content;
    }
    return "";
}

Json::Value Parser::getActionResult(const std::string& actionId) const {
    if (actionResults.count(actionId)) {
        return actionResults.at(actionId);
    }
    return Json::Value::null;
}

} // namespace StreamingProtocol
