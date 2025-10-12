// src/agent/core.cpp
#include "Agent.hpp"
#include "Utils.hpp" // For logMessage, executeScriptTool
#include <ctime>               // For internalGetCurrentTime
#include <iomanip>             // For std::put_time
#include <json/json.h>
#include <sstream> // For std::stringstream in processActions


// std::string


// processActions: Aggregates results from multiple action calls
std::string Agent::processActions(const std::vector<ActionInfo> &actions) {
  if (actions.empty()) {
    return "<action_results status=\"no_actions_requested\"/>\n";
  }

  std::stringstream resultsSs;
  resultsSs << "<action_results>\n";
  for (const auto &action : actions) {
    std::string result =
        processSingleAction(action); // Call the refined single action processor
    resultsSs << "  <action_result action_name=\"" << action.action
              << "\" type=\"" << action.type << "\">\n";

    // Basic XML escaping for the result text to avoid breaking the structure
    std::string escapedResult = result;
    size_t pos = 0;
    while ((pos = escapedResult.find("&", pos)) != std::string::npos) {
      escapedResult.replace(pos, 1, "&");
      pos += 5;
    }
    pos = 0;
    while ((pos = escapedResult.find("<", pos)) != std::string::npos) {
      escapedResult.replace(pos, 1, "<");
      pos += 4;
    }
    pos = 0;
    while ((pos = escapedResult.find(">", pos)) != std::string::npos) {
      escapedResult.replace(pos, 1, ">");
      pos += 4;
    }

    resultsSs << "    <output><![CDATA[" << result
              << "]]></output>\n"; // Use original result for CDATA
    resultsSs << "  </action_result>\n";
  }
  resultsSs << "</action_results>\n";
  return resultsSs.str();
}

// processSingleAction: Handles execution of one action
std::string Agent::processSingleAction(const ActionInfo &actionInfo) {

  logMessage(LogLevel::TOOL_CALL,
             "Agent '" + agentName +
                 "' preparing to execute action: " + actionInfo.action,
             "Type: " + actionInfo.type + ", Confidence: " +
                 std::to_string(actionInfo.confidence) + ", Params: " +
                 actionInfo.params.toStyledString().substr(0, 200) + "...");

  for (const auto &warning : actionInfo.warnings) {
    logMessage(LogLevel::WARN,
               "Agent '" + agentName + "': LLM Warning for action '" +
                   actionInfo.action + "'",
               warning);
  }

  try {
    if (actionInfo.type == "tool" || actionInfo.type == "script") {
      Tool *toolToRun = getTool(actionInfo.action);
      if (toolToRun) {
        std::string result = toolToRun->execute(actionInfo.params);
        logMessage(LogLevel::TOOL_RESULT,
                   "Agent '" + agentName + "' " + actionInfo.type + " '" +
                       actionInfo.action + "' result:",
                   result.substr(0, 500) +
                       (result.length() > 500 ? "..." : ""));
        return result;
      } else {
        logMessage(LogLevel::ERROR,
                   "Agent '" + agentName + "': " + actionInfo.type + " '" +
                       actionInfo.action +
                       "' not found or not registered correctly.");
        return "Error: " + actionInfo.type + " '" + actionInfo.action +
               "' not registered or available.";
      }
    } else if (actionInfo.type == "internal") {
      using InternalFuncPtr = std::string (Agent::*)(const Json::Value &);
      std::map<std::string, InternalFuncPtr> internalFuncMap = {
          {"call_subagent", &Agent::internalPromptAgent},
          {"add_env_var", &Agent::internalAddEnvVar}};

      auto it = internalFuncMap.find(actionInfo.action);

      if (it != internalFuncMap.end()) {
        std::string result = (this->*(it->second))(actionInfo.params);
        logMessage(LogLevel::TOOL_RESULT,
                   "Agent '" + agentName + "' internal'" +
                       actionInfo.action + "' result:",
                   result.substr(0, 500) +
                       (result.length() > 500 ? "..." : ""));
        return result;
      }
      logMessage(LogLevel::ERROR, "Agent '" + agentName +
                                      "': Unknown internal" +
                                      actionInfo.action + "'.");
      return "Error: Unknown internal'" + actionInfo.action + "'.";

    }

    logMessage(LogLevel::ERROR, "Agent '" + agentName +
                                    "': Unsupported action type '" +
                                    actionInfo.type + "' for action '" +
                                    actionInfo.action + "'.");
    return "Error: Unsupported action type '" + actionInfo.type + "'.";

  } catch (const std::exception &e) {
    logMessage(LogLevel::ERROR,
               "Agent '" + agentName + "': Exception during action '" +
                   actionInfo.action + "' execution.",
               e.what());
    return "Error executing action '" + actionInfo.action +
           "': " + std::string(e.what());
  } catch (...) {
    logMessage(LogLevel::ERROR, "Agent '" + agentName +
                                    "': Unknown exception during action '" +
                                    actionInfo.action + "' execution.");
    return "Error: Unknown exception executing action '" + actionInfo.action +
           "'.";
  }
}


// Implementation for internalGetCurrentTime
std::string Agent::internalGetCurrentTime(const Json::Value &params) {
  (void)params;
  logMessage(LogLevel::DEBUG,
             "Agent '" + agentName + "' executing internal: get_current_time");
  auto now = std::chrono::system_clock::now();
  std::time_t now_c = std::chrono::system_clock::to_time_t(now);
  std::tm now_tm_buf;

  std::tm *now_tm = localtime_r(&now_c, &now_tm_buf);

  if (now_tm) {
    std::stringstream ss;
    // ISO 8601 like format, common for APIs
    ss << std::put_time(now_tm, "%Y-%m-%dT%H:%M:%S%Z");
    return ss.str();
  } else {
    return "Error: Could not retrieve current time.";
  }
}

std::string
staticAgentCall(std::vector<std::string> tasks,
                Agent &TargetAgent) { // primitive relic Implementation
  std::string result;

  return result;
}

/**
 * @brief Makes a "static" call to a target Agent instance with a list of tasks.
 * This function simulates a higher-level command or a primitive "Relic"
 * interaction that directs another agent. It's intended to be called by an
 * orchestrating agent or a system component to delegate a bundle of tasks to a
 * target agent.
 *
 * @param tasks A vector of strings, where each string is a task or instruction.
 * @param targetAgent A reference to the Agent instance to be prompted.
 * @param callingAgentName Optional: Name of the entity making the call, for
 * logging.
 * @return std::string The consolidated final response from the targetAgent
 * after processing tasks.
 */
std::string
staticAgentCall(const std::vector<std::string> &tasks, Agent &targetAgent,
                const std::string &callingAgentName = "StaticCaller") {
  if (tasks.empty()) {
    logMessage(LogLevel::WARN, // Using global LogLevel
               "[" + callingAgentName + " -> staticAgentCall]",
               "No tasks provided to target agent: " + targetAgent.getName());
    return "Error: No tasks provided for agent '" + targetAgent.getName() +
           "'.";
  }

  std::stringstream combinedPromptSs;
  combinedPromptSs
      << "ATTENTION " << targetAgent.getName()
      << ": You have received a direct command assignment from '"
      << callingAgentName
      << "'. Please process the following tasks sequentially and provide a "
         "consolidated final report or outcome. Your standard iterative "
         "thinking process is expected.\n\nTasks:\n";
  for (size_t i = 0; i < tasks.size(); ++i) {
    combinedPromptSs << (i + 1) << ". " << tasks[i] << "\n";
  }
  combinedPromptSs << "\nReport on all outcomes.";
  std::string combinedPrompt = combinedPromptSs.str();

  logMessage(LogLevel::INFO, "[" + callingAgentName + " -> staticAgentCall]",
             "Prompting target agent '" + targetAgent.getName() + "' with " +
                 std::to_string(tasks.size()) + " task(s).");
  logMessage(LogLevel::DEBUG, "[" + callingAgentName + " -> staticAgentCall]",
             "Combined prompt for '" + targetAgent.getName() +
                 "': " + combinedPrompt.substr(0, 250) +
                 (combinedPrompt.length() > 250 ? "..." : ""));

  std::string result;
  try {
    result = targetAgent.prompt(combinedPrompt);

    logMessage(LogLevel::INFO, "[" + callingAgentName + " -> staticAgentCall]",
               "Received response from target agent '" + targetAgent.getName() +
                   "'.");
    logMessage(LogLevel::DEBUG, "[" + callingAgentName + " -> staticAgentCall]",
               "Response from '" + targetAgent.getName() +
                   "': " + result.substr(0, 250) +
                   (result.length() > 250 ? "..." : ""));

  } catch (const ApiError &e) {
    logMessage(LogLevel::ERROR, "[" + callingAgentName + " -> staticAgentCall]",
               "API Error while prompting target agent '" +
                   targetAgent.getName() + "': " + e.what());
    result = "Error: API interaction with agent '" + targetAgent.getName() +
             "' failed: " + e.what();
  } catch (const std::exception &e) {
    logMessage(LogLevel::ERROR, "[" + callingAgentName + " -> staticAgentCall]",
               "Standard Exception while prompting target agent '" +
                   targetAgent.getName() + "': " + e.what());
    result = "Error: Exception while interacting with agent '" +
             targetAgent.getName() + "': " + e.what();
  } catch (...) {
    logMessage(LogLevel::ERROR, "[" + callingAgentName + " -> staticAgentCall]",
               "Unknown error while prompting target agent '" +
                   targetAgent.getName() + "'.");
    result = "Error: Unknown error occurred while interacting with agent '" +
             targetAgent.getName() + "'.";
  }

  return result;
}
