/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   import.main.cpp                                    :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: mlamkadm <mlamkadm@student.42.fr>          +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2025/05/13 16:05:39 by mlamkadm          #+#    #+#             */
/*   Updated: 2025/05/13 16:05:39 by mlamkadm         ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

#include "Import.hpp"
#include "Agent.hpp"
#include "Groq.hpp"
#include "MiniGemini.hpp"
#include "Tool.hpp"
#include "modelApi.hpp" // For ApiError
#include "json/json.h"      // For Json::Value used by tools
#include <curl/curl.h>      // For curl_global_init/cleanup
#include <memory>           // For Tool pointers (optional but good practice)
#include <stdexcept>
#include <string>
#include <vector>

// #include "externals/file.cpp" // For file operations
// #include "externals/bash.cpp" // For bash command execution

void commandHandler(const std::string &command) {
  std::vector<std::string> commandArgs;
  std::istringstream iss(command);
  std::string arg;

  while (iss >> arg) {
    commandArgs.push_back(arg);
  }
}

int CLI(Agent &agent, const std::string &confPath =
                          "/home/mlamkadm/ai-repos/agents/agent-lib/config/"
                          "agents/standard-agent-MK1/DEMURGE.yml") {
  if (!loadAgentProfile(agent, confPath)) {
    std::cerr << "Failed to load agent profile from: " << confPath << std::endl;
    return 1;
  }

  std::cout << "Agent Name after load: " << agent.getName() << std::endl;

  std::vector<std::string> replies;
  std::string userInput;

  while (true) {
#define CLEAR_SCREEN "\033[2J\033[1;1H"
#define RESET_COLOR "\033[0m"

#define DB_LINE_VERT "═"

    std::cout << "╔════════════════════════════════════════╗\n";
    std::getline(std::cin, userInput);
    std::cout << "║                                        ║\n";
    std::cout << "╚════════════════════════════════════════╝\n";
    if (userInput == "/exit" || userInput == "/quit")
      break;
    else if (userInput == "/clear") {
      agent.reset();
      continue;
    } else if (userInput.empty()) {
      std::cout << "Please enter a valid command." << std::endl;
      continue;
    }

    try {
      std::string response = agent.prompt(userInput);
      replies.push_back("User: " + userInput);
      replies.push_back("Agent: " + response);
    } catch (const ApiError &e) {
      std::cerr << "API Error: " << e.what() << std::endl;
      replies.push_back("Error: " + std::string(e.what()));
      std::string response = agent.prompt(userInput);
      replies.push_back("User: " + userInput);
      replies.push_back("Agent: " + response);
    } catch (const std::exception &e) {
      std::cerr << "Exception: " << e.what() << std::endl;
      replies.push_back("Exception: " + std::string(e.what()));
      std::string response = agent.prompt(userInput);
      replies.push_back("User: " + userInput);
      replies.push_back("Agent: " + response);
    } catch (...) {
      std::cerr << "An unknown error occurred." << std::endl;
      replies.push_back("Unknown Error");
      std::string response = agent.prompt(userInput);
      replies.push_back("User: " + userInput);
      replies.push_back("Agent: " + response);
    }
  }

  return 0; // Return success code
}

int main(int ac, char **av) {

  MiniGemini llmClient;

  Agent DEMURGE(llmClient);

  if (ac > 1) {
    std::string confPath = av[1];
    return CLI(DEMURGE, confPath);
  } else {
    std::string defaultConfPath =
        "/home/mlamkadm/ai-repos/agents/agent-lib/config/agents/"
        "standard-agent-MK1/DEMURGE.yml";
    return CLI(DEMURGE, defaultConfPath);
  }
}

// draft -h page :
// // -h, --help: Show this help message
// // -v, --version: Show version information
// // // -c, --config <file>: Specify a configuration file
// // // -l, --list: List available agents
// // // -a, --agent <name>: Specify an agent to use
// // // -t, --tool <name>: Specify a tool to use
// // // -i, --input <text>: Provide input text for the agent
// // // -o, --output <file>: Specify an output file for the agent's response
// // // --verbose: Enable verbose output
// // // --quiet: Suppress output
// // // --debug: Enable debug mode
// // // --no-color: Disable colored output
// // // --config-dir <dir>: Specify a directory for configuration files
// // // --data-dir <dir>: Specify a directory for data files
// // // --cache-dir <dir>: Specify a directory for cache files
// // // --log-file <file>: Specify a file for logging output
// // // --log-level <level>: Set the logging level (e.g., debug, info, warning,
// error)
// // // --timeout <seconds>: Set a timeout for operations
// // // --retry <count>: Set the number of retries for failed operations
// // // --no-cache: Disable caching
// // // --no-ssl: Disable SSL verification
// // // --proxy <url>: Specify a proxy server to use
// // // --user-agent <string>: Set a custom user agent string
