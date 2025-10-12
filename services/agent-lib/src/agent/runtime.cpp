#include "Agent.hpp" // Your Agent class header

// Utility functions for future use - currently unused
#if 0
// will create the file if it does not exist, will append if it does, needs to
// be clean and error free. relative to the current working directory

static void saveThoughtsToFile(const std::vector<StructuredThought> &thoughts,
                               const std::string &filename) {
  for (const auto &thought : thoughts) {
    // append each thought to the filename
    std::ofstream file(filename, std::ios::app);
    if (file.is_open()) {
      file << "Thought Type: " << thought.type << "\n";
      file << "Content: " << thought.content << "\n";
      file << "------------------------\n";
      file.close();
    } else {
      std::cerr << "Error opening file for writing: " << filename << std::endl;
    }
  }
}

static void saveJsonToFile(const Json::Value &jsonData,
                           const std::string &filename) {
  // will create the file if it does not exist, will append if it does, needs to
  // be clean and error free.
  std::ofstream file(filename, std::ios::app);
  if (file.is_open()) {
    Json::StreamWriterBuilder writer;
    std::string output = Json::writeString(writer, jsonData);
    file << output << std::endl; // Append a newline for readability
    file.close();
  } else {
    std::cerr << "Error opening file for writing: " << filename << std::endl;
  }
}
#endif // Unused functions

static bool saveStringToFile(const std::string &path,
                             const std::string &content,
                             const std::string &mode = "default") {
  // Create directory if it doesn't exist
  size_t lastSlash = path.find_last_of('/');
  if (lastSlash != std::string::npos) {
    std::string dir = path.substr(0, lastSlash);
    // Use system() for C++98 compatibility (mkdir -p handles nested dirs)
    std::string mkdirCmd = "mkdir -p \"" + dir + "\"";
    if (system(mkdirCmd.c_str()) != 0) {
      std::cerr << "Failed to create directory: " << dir << std::endl;
      return false;
    }
  }

  // Determine file mode
  std::ios::openmode fileMode;
  if (mode == "append") {
    fileMode = std::ios::out | std::ios::app;
  } else if (mode == "override" || mode == "default") {
    fileMode = std::ios::out | std::ios::trunc;
  } else if (mode == "safe") {
    // Only write if file doesn't exist
    std::ifstream check(path.c_str());
    if (check.good()) {
      check.close();
      std::cerr << "File exists, safe mode prevents overwrite: " << path
                << std::endl;
      return false;
    }
    check.close();
    fileMode = std::ios::out | std::ios::trunc;
  } else if (mode == "backup") {
    // Create backup if file exists
    std::ifstream check(path.c_str());
    if (check.good()) {
      check.close();
      std::string backupPath = path + ".bak";
      std::string cpCmd = "cp \"" + path + "\" \"" + backupPath + "\"";
      if (system(cpCmd.c_str()) != 0) {
        std::cerr << "Failed to create backup: " << backupPath << std::endl;
        return false;
      }
    }
    check.close();
    fileMode = std::ios::out | std::ios::trunc;
  } else if (mode == "atomic") {
    // Write to temp file, then move
    std::string tempPath = path + ".tmp";
    std::ofstream tempFile(tempPath.c_str(), std::ios::out | std::ios::trunc);
    if (!tempFile.is_open()) {
      std::cerr << "Failed to open temp file: " << tempPath << std::endl;
      return false;
    }
    tempFile << content;
    if (tempFile.fail()) {
      std::cerr << "Failed to write to temp file: " << tempPath << std::endl;
      tempFile.close();
      return false;
    }
    tempFile.close();
    if (tempFile.fail()) {
      std::cerr << "Failed to close temp file: " << tempPath << std::endl;
      return false;
    }
    std::string mvCmd = "mv \"" + tempPath + "\" \"" + path + "\"";
    if (system(mvCmd.c_str()) != 0) {
      std::cerr << "Failed to move temp file to final location" << std::endl;
      return false;
    }
    return true; // Skip normal file writing
  } else if (mode == "timestamp") {
    // Append timestamp to filename
    time_t now = time(0);
    char timestamp[20];
    strftime(timestamp, sizeof(timestamp), "%Y%m%d_%H%M%S", localtime(&now));
    size_t dotPos = path.find_last_of('.');
    std::string timestampPath;
    if (dotPos != std::string::npos) {
      timestampPath =
          path.substr(0, dotPos) + "_" + timestamp + path.substr(dotPos);
    } else {
      timestampPath = path + "_" + timestamp;
    }
    std::ofstream tsFile(timestampPath.c_str(),
                         std::ios::out | std::ios::trunc);
    if (!tsFile.is_open()) {
      std::cerr << "Failed to open timestamped file: " << timestampPath
                << std::endl;
      return false;
    }
    tsFile << content;
    if (tsFile.fail()) {
      std::cerr << "Failed to write to timestamped file: " << timestampPath
                << std::endl;
      tsFile.close();
      return false;
    }
    tsFile.close();
    if (tsFile.fail()) {
      std::cerr << "Failed to close timestamped file: " << timestampPath
                << std::endl;
      return false;
    }
    return true; // Skip normal file writing
  } else if (mode == "unique") {
    // Find unique filename by appending numbers
    std::string uniquePath = path;
    int counter = 1;
    while (true) {
      std::ifstream check(uniquePath.c_str());
      if (!check.good()) {
        check.close();
        break;
      }
      check.close();
      size_t dotPos = path.find_last_of('.');
      if (dotPos != std::string::npos) {
        uniquePath = path.substr(0, dotPos) + "_" + std::to_string(counter) +
                     path.substr(dotPos);
      } else {
        uniquePath = path + "_" + std::to_string(counter);
      }
      counter++;
    }
    std::ofstream uniqueFile(uniquePath.c_str(),
                             std::ios::out | std::ios::trunc);
    if (!uniqueFile.is_open()) {
      std::cerr << "Failed to open unique file: " << uniquePath << std::endl;
      return false;
    }
    uniqueFile << content;
    if (uniqueFile.fail()) {
      std::cerr << "Failed to write to unique file: " << uniquePath
                << std::endl;
      uniqueFile.close();
      return false;
    }
    uniqueFile.close();
    if (uniqueFile.fail()) {
      std::cerr << "Failed to close unique file: " << uniquePath << std::endl;
      return false;
    }
    return true; // Skip normal file writing
  } else {
    std::cerr << "Invalid mode: " << mode
              << " (use: default, override, append, safe, backup, atomic, "
                 "timestamp, unique)"
              << std::endl;
    return false;
  }

  std::ofstream file(path.c_str(), fileMode);
  if (!file.is_open()) {
    std::cerr << "Failed to open file: " << path
              << " (errno: " << strerror(errno) << ")" << std::endl;
    return false;
  }

  file << content;
  if (file.fail()) {
    std::cerr << "Failed to write to file: " << path << std::endl;
    file.close();
    return false;
  }

  file.close();
  if (file.fail()) {
    std::cerr << "Failed to close file: " << path << std::endl;
    return false;
  }

  return true;
}

// struct ActionInfo {
//   std::string action; // name of the action to perform eg, "search",
//                       // "calculate", "fetch_data"
//   std::string type;   // e.g., "tool", "script", "internal_function",
//                       // "http_request", "output", etc.
//   Json::Value params;
//
//   double confidence = 1.0;
//   std::vector<std::string> warnings;
// };

// expand using ${{ENV_VAR}} syntax, in any key of the ActionInfo, expanding
// internal agent class ENV_VARs, this->
//
// using stringkeyvaluepair = std::vector<std::pair<std::string, std::string>>;
// for env vars format
std::vector<ActionInfo> &
Agent::expandActions(std::vector<ActionInfo> &actions) {
  for (auto &action : actions) {
    // Check if params is an object
    if (action.params.isObject()) {
      for (auto &key : action.params.getMemberNames()) {

        if (action.params[key].isString()) {
          std::string value = action.params[key].asString();
          // Check for ${{ENV_VAR}} syntax
          if (value.find("${{") != std::string::npos) {
            size_t startPos = 0;
            while ((startPos = value.find("${{", startPos)) !=
                   std::string::npos) {
              size_t endPos = value.find("}}", startPos);
              if (endPos == std::string::npos)
                break;
              std::string envVar =
                  value.substr(startPos + 3, endPos - startPos - 3);
              std::string envValue = getEnvVar(envVar);
              value.replace(startPos, endPos - startPos + 2, envValue);
              startPos += envValue.length(); // Move past the replaced text
            }
            action.params[key] =
                value; // Update the parameter with expanded value
          }
        }
      }
    }
  }
  return actions;
}

// some for reply section

static std::string generateUUID() {
  std::stringstream ss;
  ss << std::hex << std::uppercase << std::setw(8) << std::setfill('0')
     << rand() % 0xFFFFFFFF; // Random 8 hex digits
  return ss.str();
}

void Agent::saveHistory(void) {

  std::string filename =
      "/home/mlamkadm/ai-repos/agents/agent-lib/rawLogs/agent_history_" +
      generateUUID() + ".xml";

  std::string fullPromptText;

  while (!conversationHistory.empty()) {
    auto entry = conversationHistory.back();
    conversationHistory.pop_back();
    fullPromptText += "<entry>\n";
    fullPromptText += "  <role>" + entry.first + "</role>\n";
    fullPromptText += "  <content>" + entry.second + "</content>\n";
    fullPromptText += "</entry>\n";
  }

  saveStringToFile(filename, fullPromptText);
}

std::string Agent::prompt(const std::string &userInput) {

  if (!userInput.empty()) {
    addToHistory("user", userInput);
  }

  currentIteration = 0;
  std::string finalAgentResponseToUser = "";

  while (currentIteration < iterationLimit) {
    currentIteration++;
    logMessage(LogLevel::INFO, "Agent '" + agentName + "' Iteration " +
                                   std::to_string(currentIteration) + "/" +
                                   std::to_string(iterationLimit));

    std::string fullPromptText = buildFullPrompt();

    std::string llmRawResponse = executeApiCall(fullPromptText);

    std::string trimmedLlmResponse = llmRawResponse;
    trimLLMResponse(trimmedLlmResponse);

    ParsedLLMResponse parsedData =
        parseStructuredLLMResponse(trimmedLlmResponse);

    addToHistory("model", parsedData.rawTrimmedJson);

    if (parsedData.status.find("ERROR") != std::string::npos) {
      logMessage(LogLevel::ERROR,
                 "Agent '" + agentName +
                     "': LLM returned an error status: " + parsedData.status,
                 "Raw trimmed JSON: " +
                     parsedData.rawTrimmedJson.substr(0, 500));
      finalAgentResponseToUser =
          "Agent '" + agentName +
          "' encountered an error while processing your request. "
          "Please check the logs for details and readjust.";
      continue;
    }

    if (parsedData.success == false) {
      logMessage(
          LogLevel::ERROR,
          "Agent '" + agentName +
              "': LLM response parsing failed. Status: " + parsedData.status,
          "Raw trimmed JSON: " + parsedData.rawTrimmedJson.substr(0, 500));
      finalAgentResponseToUser =
          "Agent '" + agentName +
          "' encountered a critical error while processing your request. "
          "Please check the logs for details and readjust.";
      continue;
    }


    // Log thoughts for debugging
    for (const auto &thought : parsedData.thoughts) {
      std::cout << "Thought (" << thought.type << "): " << thought.content
                << std::endl;
    }

    logMessage(LogLevel::DEBUG,
               "Agent '" + agentName + "': LLM Status: " + parsedData.status,
               parsedData.rawTrimmedJson);

    // Process actions if any exist
    if (!parsedData.actions.empty()) {
      logMessage(LogLevel::INFO, "Agent '" + agentName +
                                     "': LLM requires action(s). Processing " +
                                     std::to_string(parsedData.actions.size()) +
                                     " action(s).");

      std::vector<ActionInfo> tmpAction = parsedData.actions;

      expandActions(parsedData.actions);

      std::string actionResultsText = processActions(parsedData.actions);
      addToHistory("action_results", actionResultsText);
    }

    // Check if we should stop processing
    if (parsedData.stop) {
      if (!parsedData.finalResponseField.empty()) {
        finalAgentResponseToUser = parsedData.finalResponseField;
      }
      break;
    }

    // If we've hit iteration limit without stop signal
    if (currentIteration >= iterationLimit) {
      logMessage(LogLevel::WARN, "Agent '" + agentName +
                                     "' reached iteration limit (" +
                                     std::to_string(iterationLimit) + ").");
      if (finalAgentResponseToUser.empty()) {
        finalAgentResponseToUser =
            "Agent '" + agentName + "' has processed the maximum iterations (" +
            std::to_string(iterationLimit) +
            ") for this request. Please try rephrasing or "
            "breaking down the request.";
      }
      break;
    }
  }

#define RESET "\033[0m"
#define RED "\033[31m"

  std::cout << "\n"
            << RED << agentName << ": " << RESET << finalAgentResponseToUser
            << std::endl;

  return finalAgentResponseToUser;
}
