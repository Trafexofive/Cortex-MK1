#pragma once

#include <string>
#include <json/json.h> // For Json::Value
#include <chrono>
#include <iomanip>
#include <iostream>

// Function to execute a simple command and get its output (if not already in a global scope)
// int executeCommand(const std::string &command, std::string &output);


// Logging Enum & Function Prototype
enum class LogLevel {
  TOOL_CALL,
  INFO,
  TOOL_RESULT,
  DEBUG,
  WARN,
  ERROR,
  PROMPT
};

void logMessage(LogLevel level, const std::string &message) ;
void logMessage(LogLevel level, const std::string &message,
                const std::string &details) ;

// Function to execute a script (inline or from file) with specified runtime and parameters
std::string executeScriptTool(const std::string& scriptPathOrContent,
                              const std::string& runtime,
                              const Json::Value& params,
                              bool isContentInline);
