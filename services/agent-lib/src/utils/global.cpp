#include "Agent.hpp" // For logMessage (ensure it's declared globally or passed)
#include "Utils.hpp"

#include <algorithm>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <iostream>
#include <sstream>
#include <sys/stat.h>
#include <sys/wait.h>
#include <unistd.h>
#include <vector>

// Assuming executeCommand is already defined as:
// int executeCommand(const std::string &command, std::string &output);
// If not, it needs to be included or defined here.
// For simplicity, let's assume it's available and uses logMessage.
// (If it's in Agent.cpp, it might need to be moved to Utils.cpp or made a
// static member of a utility class) This is a simplified version from your
// Agent.cpp for utility usage.
int executeCommand(const std::string &command, std::string &output) {
  output.clear();
  std::string cmdWithStderr = command + " 2>&1"; // Redirect stderr to stdout
  logMessage(LogLevel::DEBUG, "[executeCommand] Executing:", cmdWithStderr);

  FILE *pipe = popen(cmdWithStderr.c_str(), "r");
  if (!pipe) {
    logMessage(LogLevel::ERROR,
               "[executeCommand] popen() failed for command:", command);
    output = "Error: popen() failed to execute command.";
    return -1; // Indicate failure to open pipe
  }

  char buffer[256];
  while (fgets(buffer, sizeof(buffer), pipe) != nullptr) {
    output += buffer;
  }

  int status = pclose(pipe);
  if (status == -1) {
    logMessage(LogLevel::ERROR,
               "[executeCommand] pclose() failed for command:", command);
    // output might contain partial results, append error.
    output += "\nError: pclose() failed after command execution.";
    return -1; // Indicate pclose failure
  }
  logMessage(LogLevel::DEBUG, "[executeCommand] Finished. Raw Status: " +
                                  std::to_string(status) + ", Exit Code: " +
                                  std::to_string(WEXITSTATUS(status)));
  return WEXITSTATUS(status); // Return the actual exit status of the command
}

std::string executeScriptTool(const std::string &scriptPathOrContent,
                              const std::string &runtime,
                              const Json::Value &params, bool isContentInline) {
  std::string commandToExecute;
  std::string
      tempScriptFilePath; // RAII for temp file would be better in production

  if (isContentInline) {
    char tempTemplate[] = "/tmp/agent_script_XXXXXX";
    int fd = mkstemp(tempTemplate);
    if (fd == -1) {
      std::string errMsg =
          "Error: Could not create temporary script file. Errno: " +
          std::string(strerror(errno));
      logMessage(LogLevel::ERROR, "[ScriptTool] mkstemp failed",
                 strerror(errno));
      return errMsg;
    }
    tempScriptFilePath = tempTemplate; // Store for cleanup

    ssize_t written =
        write(fd, scriptPathOrContent.c_str(), scriptPathOrContent.length());
    if (written != static_cast<ssize_t>(scriptPathOrContent.length())) {
      std::string errMsg =
          "Error: Failed to write to temporary script file. Errno: " +
          std::string(strerror(errno));
      logMessage(LogLevel::ERROR, "[ScriptTool] Write to temp file failed",
                 tempScriptFilePath + ", Errno: " + strerror(errno));
      close(fd);
      remove(tempScriptFilePath.c_str());
      return errMsg;
    }

    if (runtime == "bash" || runtime == "sh" ||
        runtime == "zsh") { // Make shell scripts executable
      if (fchmod(fd, S_IRUSR | S_IWUSR | S_IXUSR) == -1) {
        std::string errMsg = "Error: Failed to set execute permissions on "
                             "temporary script. Errno: " +
                             std::string(strerror(errno));
        logMessage(LogLevel::ERROR, "[ScriptTool] fchmod failed on temp file",
                   tempScriptFilePath + ", Errno: " + strerror(errno));
        close(fd);
        remove(tempScriptFilePath.c_str());
        return errMsg;
      }
    }
    close(fd); // Close after writing and chmod

    // Form the command
    if (runtime == "bash" || runtime == "sh" || runtime == "zsh") {
      commandToExecute = tempScriptFilePath; // Directly executable
    } else if (runtime == "python" || runtime == "python3") {
      commandToExecute = runtime + " " + tempScriptFilePath;
    } else {
      logMessage(LogLevel::ERROR,
                 "[ScriptTool] Unsupported runtime for inline script", runtime);
      remove(tempScriptFilePath.c_str());
      return "Error: Unsupported runtime '" + runtime + "' for inline script.";
    }
  } else { // scriptPathOrContent is an actual file path
    // Path safety should have been checked by the caller
    // (loadAgentProfile/loadToolsFromFile) We assume scriptPathOrContent is a
    // safe, canonical path here.
    if (runtime == "bash" || runtime == "sh" || runtime == "zsh") {
      // Check if script is executable, otherwise prepend interpreter
      struct stat st;
      if (stat(scriptPathOrContent.c_str(), &st) == 0 &&
          (st.st_mode & S_IXUSR)) {
        commandToExecute = scriptPathOrContent;
      } else {
        commandToExecute =
            runtime + " " + scriptPathOrContent; // e.g. "bash scripts/my.sh"
      }
    } else if (runtime == "python" || runtime == "python3") {
      commandToExecute = runtime + " " + scriptPathOrContent;
    } else {
      logMessage(LogLevel::ERROR,
                 "[ScriptTool] Unsupported runtime for file-based script",
                 runtime);
      return "Error: Unsupported runtime '" + runtime + "' for script file.";
    }
  }

  // Parameter Passing: Pass the entire 'params' Json::Value as a single JSON
  // string argument.
  std::string paramsJsonString =
      "{}"; // Default to empty JSON object if no params
  if (params.isObject() && !params.empty()) {
    Json::StreamWriterBuilder writerBuilder;
    writerBuilder["indentation"] = ""; // Compact JSON
    paramsJsonString = Json::writeString(writerBuilder, params);
  }

  // Escape the JSON string for shell command line (critical for security and
  // correctness)
  std::string escapedParamsJsonString = "'"; // Start with single quote
  for (char c : paramsJsonString) {
    if (c == '\'') {
      escapedParamsJsonString +=
          "'\\''"; // Replace ' with '\'', effectively ending the current '
                   // string, adding a literal ', and starting a new ' string
    } else {
      escapedParamsJsonString += c;
    }
  }
  escapedParamsJsonString += "'"; // End with single quote

  commandToExecute += " " + escapedParamsJsonString;

  std::string output;
  logMessage(LogLevel::DEBUG, "[ScriptTool] Attempting to execute command",
             commandToExecute);

  int exitStatus =
      ::executeCommand(commandToExecute, output); // Use global executeCommand

  if (!tempScriptFilePath.empty()) {
    if (remove(tempScriptFilePath.c_str()) != 0) {
      logMessage(LogLevel::WARN,
                 "[ScriptTool] Failed to remove temporary script file",
                 tempScriptFilePath + ", Errno: " + strerror(errno));
    }
  }

  if (exitStatus != 0) {
    logMessage(LogLevel::ERROR,
               "[ScriptTool] Script execution failed (Exit Status: " +
                   std::to_string(exitStatus) + ")",
               "Command: " + commandToExecute);
    // Return the script's output even on failure, as it might contain error
    // details.
    return "Error executing script (Exit Status: " +
           std::to_string(exitStatus) + "):\n" + output;
  }
  logMessage(LogLevel::DEBUG, "[ScriptTool] Script executed successfully.",
             "Command: " + commandToExecute);
  return output;
}

// --- Utility Functions ---

#define DEBUG_LOG_LEVEL LogLevel::INFO
// new logMessage function that takes into account LogLevel, will only display
// if the log level above or equal to DEBUG_LOG_LEVEL

void logMessage(LogLevel level, const std::string &message,
                const std::string &details) {

  if (level < DEBUG_LOG_LEVEL) {
    return; 
  }

  // return;

  auto nowChrono = std::chrono::system_clock::now();
  auto nowTimeT = std::chrono::system_clock::to_time_t(nowChrono);
  std::tm nowTmLocalBuf;

  std::tm *nowTm = localtime_r(&nowTimeT, &nowTmLocalBuf);

  char timeBuffer[20];

  if (nowTm) { // Check if localtime_r/s succeeded
    std::strftime(timeBuffer, sizeof(timeBuffer), "%H:%M:%S", nowTm);
  } else {
    std::strncpy(timeBuffer, "NO_TIME", sizeof(timeBuffer) - 1);
    timeBuffer[sizeof(timeBuffer) - 1] = '\0';
  }

  std::string prefix;
  std::string colorStart = "";
  std::string colorEnd = "\033[0m"; // ANSI Reset

  switch (level) {
  case LogLevel::DEBUG:
    prefix = "[DEBUG] ";
    colorStart = "\033[36m";
    break;
  case LogLevel::INFO:
    prefix = "[INFO]  ";
    colorStart = "\033[32m";
    break;
  case LogLevel::WARN:
    prefix = "[WARN]  ";
    colorStart = "\033[33m";
    break;
  case LogLevel::ERROR:
    prefix = "[ERROR] ";
    colorStart = "\033[1;31m";
    break;
  case LogLevel::TOOL_CALL:
    prefix = "[TOOL CALL] ";
    colorStart = "\033[1;35m";
    break;
  case LogLevel::TOOL_RESULT:
    prefix = "[TOOL RESULT] ";
    colorStart = "\033[35m";
    break;
  case LogLevel::PROMPT:
    prefix = "[PROMPT] ";
    colorStart = "\033[34m";
    break;
  }

  std::ostream &outStream =
      (level == LogLevel::ERROR || level == LogLevel::WARN) ? std::cerr
                                                            : std::cout;
  outStream << colorStart << std::string(timeBuffer) << " " << prefix << message
            << colorEnd << std::endl;
  if (!details.empty()) {
    const size_t MAX_DETAIL_LEN = 100500;

    std::string truncatedDetails = details.substr(0, MAX_DETAIL_LEN);
    if (details.length() > MAX_DETAIL_LEN)
      truncatedDetails += "... (truncated)";
    outStream << colorStart << "  " << truncatedDetails << colorEnd
              << std::endl;
  }
}

// log message 2 params overload
void logMessage(LogLevel level, const std::string &message) {
  logMessage(level, message, "");
}
