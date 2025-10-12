#include "Agent.hpp"
#include "StreamingProtocol.hpp"
#include "ToolRegistry.hpp"
#include <iostream>
#include <sstream>

// Streaming protocol implementation for Agent
void Agent::promptStreaming(const std::string &userInput, 
                           StreamingProtocol::TokenCallback callback) {
    if (!streamingParser) {
        // Initialize streaming parser with action executor
        auto executor = [this](const StreamingProtocol::ParsedAction& action) -> Json::Value {
            // Map streaming protocol actions to agent actions
            ActionInfo agentAction;
            
            // Convert action type
            switch (action.type) {
                case StreamingProtocol::ActionType::TOOL:
                    agentAction.type = "tool";
                    break;
                case StreamingProtocol::ActionType::AGENT:
                    agentAction.type = "internal";
                    agentAction.action = "call_subagent";
                    break;
                case StreamingProtocol::ActionType::RELIC:
                    agentAction.type = "relic";
                    break;
                case StreamingProtocol::ActionType::WORKFLOW:
                    agentAction.type = "workflow";
                    break;
                case StreamingProtocol::ActionType::LLM:
                    agentAction.type = "llm";
                    break;
                case StreamingProtocol::ActionType::INTERNAL:
                    agentAction.type = "internal";
                    break;
            }
            
            agentAction.action = action.name;
            agentAction.params = action.parameters;
            
            // Handle relic actions specially
            if (action.type == StreamingProtocol::ActionType::RELIC) {
                // Extract relic name and endpoint
                std::string relicName = action.name;
                std::string endpointName;
                
                // Check if format is "relic_name.endpoint_name"
                size_t dotPos = relicName.find('.');
                if (dotPos != std::string::npos) {
                    endpointName = relicName.substr(dotPos + 1);
                    relicName = relicName.substr(0, dotPos);
                } else if (action.parameters.isMember("endpoint")) {
                    endpointName = action.parameters["endpoint"].asString();
                }
                
                Relic* relic = getRelic(relicName);
                if (!relic) {
                    Json::Value error;
                    error["error"] = "Relic not found: " + relicName;
                    return error;
                }
                
                if (!relic->isRunning()) {
                    logMessage(LogLevel::INFO, "Starting relic", relicName);
                    if (!relic->start()) {
                        Json::Value error;
                        error["error"] = "Failed to start relic: " + relicName;
                        return error;
                    }
                }
                
                return relic->callEndpoint(endpointName, action.parameters);
            }
            
            // Execute the action using existing agent infrastructure
            std::string resultStr = processSingleAction(agentAction);
            
            // Parse result string to JSON
            Json::CharReaderBuilder readerBuilder;
            Json::Value result;
            std::string errs;
            std::istringstream stream(resultStr);
            
            if (Json::parseFromStream(readerBuilder, stream, &result, &errs)) {
                return result;
            }
            
            // If not valid JSON, return as string
            result["result"] = resultStr;
            return result;
        };
        
        streamingParser = std::make_unique<StreamingProtocol::Parser>(executor);
        streamingParser->setTokenCallback(callback);
        
        // Add any pre-configured context feeds
        for (const auto& feedPair : contextFeeds) {
            streamingParser->addContextFeed(feedPair.second);
        }
    }
    
    // Add user message to history if not empty
    if (!userInput.empty()) {
        addToHistory("user", userInput);
    }
    
    // Iteration loop for non-terminating responses
    currentIteration = 0;  // Start at 0
    bool shouldContinue = true;
    bool receivedFinalResponse = false;
    
    while (shouldContinue && currentIteration < iterationLimit) {
        // Log iteration (display as 1-indexed for humans)
        logMessage(LogLevel::INFO, "Agent '" + agentName + "' Iteration " +
                                   std::to_string(currentIteration + 1) + "/" +
                                   std::to_string(iterationLimit));
        
        // Build prompt with streaming protocol instructions
        std::string fullPrompt = buildFullPrompt();
        
        // Add streaming protocol guide to system prompt if not already present
        std::string streamingGuide = R"(

# ⚠️ CRITICAL: RESPONSE PROTOCOL (MANDATORY) ⚠️

You MUST respond EXACTLY in this XML+JSON format. DO NOT use plain text. DO NOT use other formats.

REQUIRED FORMAT:
<thought>
Your reasoning here
</thought>

<response final="true">
Your answer in Markdown
</response>

NON-TERMINATING RESPONSE (continue working after responding):
<thought>
I'll show the user a progress update.
</thought>

<response final="false">
Here's what I found so far. Let me continue investigating...
</response>

<thought>
Now I'll do more work and give the final answer.
</thought>

<response final="true">
Final answer with complete results.
</response>

FULL EXAMPLE:
<thought>
I need to answer the user's question about mathematics.
</thought>

<response final="true">
The answer is 4.

**Explanation:**
- 2 + 2 = 4

This is basic arithmetic.
</response>

IF YOU NEED TO USE TOOLS, USE THIS FORMAT:
<thought>
I will search for information first.
</thought>

<action type="tool" mode="async" id="search1">
{
  "name": "knowledge_retriever",
  "parameters": {"query": "topic"},
  "output_key": "results"
}
</action>

<response final="false">
Based on my search: $results
</response>

STREAM CONTINUES // SHOWCASE ENDS ...



RULES (MANDATORY):
1. ALWAYS start with <thought> tag
2. ALWAYS end with <response> tag (final="true" or final="false")
3. Use final="false" to continue working after showing progress
4. Use <action> tags for tools/agents/relics
5. Never respond with raw text outside tags
6. Follow XML syntax strictly

Your response MUST be valid XML with these tags.
)";
        
        // if (fullPrompt.find("RESPONSE PROTOCOL") == std::string::npos) {
            fullPrompt += streamingGuide;
        // }
        
        // Reset parser for this iteration
        streamingParser->reset();
        
        // Track if we got a final response in this iteration
        receivedFinalResponse = false;
        
        // Wrap callback to detect final responses
        auto wrappedCallback = [&receivedFinalResponse, &callback](const StreamingProtocol::TokenEvent& event) {
            // Check if this is a final response
            if (event.type == StreamingProtocol::TokenEvent::Type::RESPONSE) {
                if (event.metadata.count("is_final") && event.metadata.at("is_final") == "true") {
                    receivedFinalResponse = true;
                }
            }
            
            // Forward to user callback
            if (callback) {
                callback(event);
            }
        };
        
        // Temporarily set wrapped callback
        streamingParser->setTokenCallback(wrappedCallback);
        
        // Generate streaming response
        logMessage(LogLevel::DEBUG, "Agent '" + agentName + "': Sending prompt to API.",
                   "Length: " + std::to_string(fullPrompt.length()));
        
        api.generateStream(fullPrompt, [this](const std::string& token, bool isFinal) {
            if (streamingParser) {
                streamingParser->parseToken(token, isFinal);
            }
        });
        
        logMessage(LogLevel::DEBUG, "Final response received");
        
        // All actions from this iteration have been parsed and executed by the streaming parser
        // NOW increment the iteration counter (after actions are complete)
        currentIteration++;
        
        // Decide if we should continue
        if (receivedFinalResponse) {
            shouldContinue = false;
        } else {
            // Non-final response - continue iteration
            // Add assistant message to history with all action results
            std::string assistantMessage = "<iteration_" + std::to_string(currentIteration - 1) + ">\n";
            
            // Include action results in context for next iteration
            auto results = streamingParser->getAllResults();
            if (!results.empty()) {
                assistantMessage += "<action_results>\n";
                for (const auto& pair : results) {
                    Json::StreamWriterBuilder writer;
                    writer["indentation"] = "";
                    assistantMessage += "<result key=\"" + pair.first + "\">" +
                                       Json::writeString(writer, pair.second) +
                                       "</result>\n";
                }
                assistantMessage += "</action_results>\n";
            }
            assistantMessage += "</iteration_" + std::to_string(currentIteration - 1) + ">";
            
            addToHistory("assistant", assistantMessage);
            
            logMessage(LogLevel::INFO, "Agent '" + agentName + "': Non-final response detected. Continuing...");
        }
        
        // Restore original callback
        streamingParser->setTokenCallback(callback);
        
        if (currentIteration >= iterationLimit) {
            logMessage(LogLevel::WARN, "Agent '" + agentName + "' reached iteration limit (" +
                                      std::to_string(iterationLimit) + ").");
            shouldContinue = false;
        }
    }
}

void Agent::addContextFeed(const StreamingProtocol::ContextFeed& feed) {
    // Copy the feed
    StreamingProtocol::ContextFeed feedCopy = feed;
    
    // Execute the feed source to populate content (on_demand type)
    if (feedCopy.type == "on_demand" && !feedCopy.source.isNull()) {
        try {
            std::string sourceType = feedCopy.source.get("type", "").asString();
            
            if (sourceType == "internal") {
                // Execute internal tool
                std::string action = feedCopy.source.get("action", "").asString();
                Json::Value params = feedCopy.source.get("params", Json::objectValue);
                
                // Use ToolRegistry to execute internal function
                auto& registry = ToolRegistry::getInstance();
                auto func = registry.getFunction(action);
                
                if (func) {
                    std::string result = func(params);
                    
                    // Parse JSON result and extract relevant content
                    Json::CharReaderBuilder readerBuilder;
                    Json::Value resultJson;
                    std::string errs;
                    std::istringstream stream(result);
                    
                    if (Json::parseFromStream(readerBuilder, stream, &resultJson, &errs)) {
                        // For system_clock, extract timestamp
                        if (resultJson.isMember("timestamp")) {
                            feedCopy.content = resultJson["timestamp"].asString();
                        } else {
                            // Use the whole JSON as pretty string
                            Json::StreamWriterBuilder writerBuilder;
                            writerBuilder["indentation"] = "  ";
                            feedCopy.content = Json::writeString(writerBuilder, resultJson);
                        }
                    } else {
                        feedCopy.content = result;
                    }
                    
                    logMessage(LogLevel::DEBUG, "Executed context feed '" + feed.id + "'",
                               "Content: " + feedCopy.content.substr(0, 100) + (feedCopy.content.length() > 100 ? "..." : ""));
                }
            } else if (sourceType == "tool") {
                // Execute regular tool
                std::string toolName = feedCopy.source.get("name", "").asString();
                Json::Value params = feedCopy.source.get("params", Json::objectValue);
                
                auto toolIt = registeredTools.find(toolName);
                if (toolIt != registeredTools.end()) {
                    feedCopy.content = toolIt->second->execute(params);
                }
            }
        } catch (const std::exception& e) {
            logMessage(LogLevel::WARN, "Failed to execute context feed: " + feed.id, e.what());
            feedCopy.content = "";
        }
    }
    
    contextFeeds[feedCopy.id] = feedCopy;
    
    if (streamingParser) {
        streamingParser->addContextFeed(feedCopy);
    }
}

std::string Agent::getContextFeedValue(const std::string& feedId) const {
    if (contextFeeds.count(feedId)) {
        return contextFeeds.at(feedId).content;
    }
    
    if (streamingParser) {
        return streamingParser->getContextFeedValue(feedId);
    }
    
    return "";
}
