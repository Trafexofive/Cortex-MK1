// agent-bin - Interactive CLI for Agent-Lib with streaming and modern manifests
#include "Agent.hpp"
#include "MiniGemini.hpp"
#include "Import.hpp"
#include "ToolRegistry.hpp"
#include "InternalTools.hpp"
#include "StreamingProtocol.hpp"
#include "Relic.hpp"
#include <iostream>
#include <string>
#include <cstdlib>
#include <signal.h>
#include <unistd.h>

// ANSI colors
#define RESET   "\033[0m"
#define BOLD    "\033[1m"
#define DIM     "\033[2m"
#define RED     "\033[31m"
#define GREEN   "\033[32m"
#define YELLOW  "\033[33m"
#define BLUE    "\033[34m"
#define MAGENTA "\033[35m"
#define CYAN    "\033[36m"

bool running = true;

void signalHandler(int signum) {
    std::cout << "\n" << YELLOW << "Caught signal " << signum << ". Exiting gracefully..." << RESET << std::endl;
    running = false;
}

void printBanner() {
    std::cout << BOLD << CYAN;
    std::cout << R"(
╔══════════════════════════════════════════════════════════════╗
║              CORTEX PRIME - AGENT-LIB CLI v1.2               ║
║              Streaming Protocol • Modern Manifests           ║
╚══════════════════════════════════════════════════════════════╝
)" << RESET << "\n";
}

void printHelp() {
    std::cout << BOLD << "Commands:" << RESET << "\n";
    std::cout << "  " << GREEN << "/load <path>" << RESET << "     - Load agent manifest\n";
    std::cout << "  " << GREEN << "/reload" << RESET << "          - Reload current manifest\n";
    std::cout << "  " << GREEN << "/stream on|off" << RESET << "  - Toggle streaming mode\n";
    std::cout << "  " << GREEN << "/tools" << RESET << "           - List available tools\n";
    std::cout << "  " << GREEN << "/relics" << RESET << "          - List available relics\n";
    std::cout << "  " << GREEN << "/context <cmd>" << RESET << "  - Manage context feeds (add|remove|list|refresh)\n";
    std::cout << "  " << GREEN << "/info" << RESET << "            - Show agent information\n";
    std::cout << "  " << GREEN << "/clear" << RESET << "           - Clear conversation\n";
    std::cout << "  " << GREEN << "/help" << RESET << "            - Show this help\n";
    std::cout << "  " << GREEN << "/quit or /exit" << RESET << " - Exit CLI\n";
    std::cout << "\n";
}

void registerInternalTools() {
    auto& registry = ToolRegistry::getInstance();
    registry.registerFunction("system_clock", InternalTools::systemClock);
    registry.registerFunction("agent_metadata", InternalTools::agentMetadata);
    registry.registerFunction("context_feed_manager", InternalTools::contextFeedManager);
    registry.registerFunction("variable_manager", InternalTools::variableManager);
    registry.registerFunction("file_operations", InternalTools::fileOperations);
    registry.registerFunction("environment_info", InternalTools::environmentInfo);
    registry.registerFunction("random_generator", InternalTools::randomGenerator);
    registry.registerFunction("base64_codec", InternalTools::base64Codec);
    registry.registerFunction("json_operations", InternalTools::jsonOperations);
}

void listTools(const Agent& agent) {
    auto tools = agent.getRegisteredTools();
    std::cout << BOLD << "Registered Tools (" << tools.size() << "):" << RESET << "\n";
    if (tools.empty()) {
        std::cout << DIM << "  (no tools loaded)" << RESET << "\n";
    } else {
        for (const auto& [name, tool] : tools) {
            std::cout << "  • " << CYAN << name << RESET << " - " << tool->getDescription() << "\n";
        }
    }
}

void showAgentInfo(const Agent& agent) {
    std::cout << BOLD << "Agent Information:" << RESET << "\n";
    std::cout << "  Name: " << CYAN << agent.getName() << RESET << "\n";
    std::cout << "  Description: " << agent.getDescription() << "\n";
    std::cout << "  Iteration Cap: " << agent.getIterationCap() << "\n";
    std::cout << "  Streaming: " << (agent.isStreamingEnabled() ? GREEN "Enabled" : RED "Disabled") << RESET << "\n";
    std::cout << "  Tools: " << agent.getRegisteredTools().size() << "\n";
}

void showHelp(const char* progName) {
    std::cout << BOLD << "Usage: " << RESET << progName << " [OPTIONS]\n\n";
    std::cout << BOLD << "OPTIONS:\n" << RESET;
    std::cout << "  " << GREEN << "-h, --help" << RESET << "              Show this help message\n";
    std::cout << "  " << GREEN << "-v, --version" << RESET << "           Show version information\n";
    std::cout << "  " << GREEN << "-l, --load" << RESET << " <path>       Load agent manifest on startup\n";
    std::cout << "  " << GREEN << "-s, --stream" << RESET << "            Enable streaming mode by default\n";
    std::cout << "  " << GREEN << "-t, --test" << RESET << "              Test/validate manifest and exit\n";
    std::cout << "\n" << BOLD << "EXAMPLES:\n" << RESET;
    std::cout << "  " << progName << "                                    # Interactive mode\n";
    std::cout << "  " << progName << " -l config/agents/sage/agent.yml    # Load agent on start\n";
    std::cout << "  " << progName << " -l sage/agent.yml -s               # Load with streaming\n";
    std::cout << "  " << progName << " -l sage/agent.yml --test           # Validate manifest only\n";
    std::cout << "  " << progName << " --help                             # Show this help\n";
}

void showVersion() {
    std::cout << BOLD << "CORTEX PRIME - Agent-Lib CLI\n" << RESET;
    std::cout << "Version: " << CYAN << "1.2.0" << RESET << "\n";
    std::cout << "Streaming Protocol: " << GREEN << "Enabled" << RESET << "\n";
    std::cout << "Modern Manifests: " << GREEN << "Supported" << RESET << "\n";
    std::cout << "Build: " << __DATE__ << " " << __TIME__ << "\n";
}

int main(int argc, char** argv) {
    // Parse CLI arguments FIRST (before any output)
    std::string autoLoadPath = "";
    bool autoStream = false;
    bool testMode = false;
    
    for (int i = 1; i < argc; i++) {
        std::string arg = argv[i];
        
        if (arg == "-h" || arg == "--help") {
            showHelp(argv[0]);
            return 0;
        } else if (arg == "-v" || arg == "--version") {
            showVersion();
            return 0;
        } else if (arg == "-l" || arg == "--load") {
            if (i + 1 < argc) {
                autoLoadPath = argv[++i];
            } else {
                std::cerr << RED << "Error: --load requires a path argument\n" << RESET;
                showHelp(argv[0]);
                return 1;
            }
        } else if (arg == "-s" || arg == "--stream") {
            autoStream = true;
        } else if (arg == "-t" || arg == "--test") {
            testMode = true;
        } else {
            std::cerr << RED << "Error: Unknown option '" << arg << "'\n\n" << RESET;
            showHelp(argv[0]);
            return 1;
        }
    }
    
    // Setup signal handlers
    signal(SIGINT, signalHandler);
    signal(SIGTERM, signalHandler);
    
    printBanner();
    
    // Get API key from environment
    const char* apiKey = std::getenv("GEMINI_API_KEY");
    if (!apiKey || apiKey[0] == '\0') {
        std::cout << YELLOW << "⚠  GEMINI_API_KEY not set. Set it for real LLM calls." << RESET << "\n";
        apiKey = "placeholder-key";
    } else {
        std::cout << GREEN << "✓ API key loaded" << RESET << "\n";
    }
    
    // Register internal tools
    std::cout << DIM << "Registering internal tools..." << RESET << "\n";
    registerInternalTools();
    std::cout << GREEN << "✓ Internal tools registered" << RESET << "\n\n";
    
    // Create LLM client and agent
    MiniGemini gemini(apiKey);
    Agent agent(gemini, "agent");
    
    // Enable streaming by default (modern manifests use streaming protocol)
    agent.setStreamingEnabled(true);
    
    // Auto-load manifest if specified via CLI
    std::string manifestPath;
    if (!autoLoadPath.empty()) {
        manifestPath = autoLoadPath;
        std::cout << "Loading manifest: " << CYAN << manifestPath << RESET << "\n";
        if (loadAgentProfile(agent, manifestPath)) {
            std::cout << GREEN << "✓ Manifest loaded: " << agent.getName() << RESET << "\n";
            
            // If test mode, exit after validation
            if (testMode) {
                std::cout << GREEN << "✓ Successfully loaded agent profile: " << agent.getName() << RESET << "\n";
                std::cout << "  " << manifestPath << "\n";
                return 0;
            }
            
            if (!autoStream) {
                // Only allow disabling if explicitly requested
                std::cout << DIM << "  Streaming: ON (default for modern manifests)" << RESET << "\n";
            }
            std::cout << "\n";
        } else {
            std::cout << RED << "✗ Failed to load manifest" << RESET << "\n\n";
            if (testMode) {
                return 1;
            }
            manifestPath.clear();
        }
    }
    
    // Exit early if test mode without manifest
    if (testMode) {
        std::cerr << RED << "Error: --test requires --load <path>\n" << RESET;
        return 1;
    }
    
    if (manifestPath.empty()) {
        std::cout << DIM << "No manifest loaded. Use " << GREEN << "/load <path>" << DIM << " to load one." << RESET << "\n";
    }
    
    printHelp();
    
    // Main loop
    std::string input;
    while (running) {
        std::cout << BOLD << "\n> " << RESET;
        if (!std::getline(std::cin, input)) {
            break;
        }
        
        if (input.empty()) continue;
        
        // Handle commands
        if (input[0] == '/') {
            if (input == "/quit" || input == "/exit") {
                break;
            }
            else if (input == "/help") {
                printHelp();
            }
            else if (input == "/clear") {
                agent.reset();
                std::cout << GREEN << "✓ Conversation cleared" << RESET << "\n";
            }
            else if (input == "/tools") {
                listTools(agent);
            }
            else if (input == "/relics") {
                std::vector<std::string> relics = agent.listRelics();
                std::cout << BOLD << "Relics (" << relics.size() << "):" << RESET << "\n";
                for (const auto& name : relics) {
                    Relic* relic = agent.getRelic(name);
                    if (relic) {
                        std::string status = relic->isRunning() ? 
                            (relic->isHealthy() ? GREEN "●" RESET : YELLOW "●" RESET) : 
                            RED "●" RESET;
                        std::cout << "  " << status << " " << CYAN << name << RESET 
                                  << " (" << relic->getServiceType() << ")" << DIM 
                                  << " - " << relic->getSummary() << RESET << "\n";
                    }
                }
                if (relics.empty()) {
                    std::cout << DIM << "  No relics loaded" << RESET << "\n";
                }
            }
            else if (input.substr(0, 9) == "/context ") {
                // Context feed management: /context add|remove|list|refresh <args>
                std::string contextCmd = input.substr(9);
                std::istringstream iss(contextCmd);
                std::string action;
                iss >> action;
                
                if (action == "list") {
                    // List all active context feeds
                    auto feeds = agent.getContextFeeds();
                    std::cout << BOLD << "Active Context Feeds (" << feeds.size() << "):" << RESET << "\n";
                    if (feeds.empty()) {
                        std::cout << DIM << "  (no context feeds active)" << RESET << "\n";
                    } else {
                        for (const auto& pair : feeds) {
                            const auto& feed = pair.second;
                            std::cout << "  • " << CYAN << feed.id << RESET;
                            std::cout << " [" << feed.type << "]";
                            if (!feed.content.empty()) {
                                std::string preview = feed.content.substr(0, 50);
                                if (feed.content.length() > 50) preview += "...";
                                std::cout << DIM << " - " << preview << RESET;
                            }
                            std::cout << "\n";
                        }
                    }
                    
                } else if (action == "add") {
                    // Add new context feed: /context add <feed_id> <type> <source>
                    std::string feedId, feedType, source;
                    iss >> feedId >> feedType;
                    std::getline(iss, source);
                    
                    if (feedId.empty() || feedType.empty()) {
                        std::cout << RED << "Usage: /context add <feed_id> <type> <source>" << RESET << "\n";
                        std::cout << "  Types: on_demand, periodic, static\n";
                        std::cout << "  Example: /context add my_feed on_demand system_clock\n";
                    } else {
                        // Create context feed
                        StreamingProtocol::ContextFeed feed;
                        feed.id = feedId;
                        feed.type = feedType;
                        
                        // Parse source
                        if (!source.empty()) {
                            // Simple source: internal tool name
                            source = source.substr(source.find_first_not_of(" \t"));
                            feed.source["type"] = "internal";
                            feed.source["action"] = source;
                            feed.source["params"] = Json::objectValue;
                        }
                        
                        agent.addContextFeed(feed);
                        std::cout << GREEN << "✓ Added context feed: " << feedId << RESET << "\n";
                    }
                    
                } else if (action == "remove") {
                    // Remove context feed: /context remove <feed_id>
                    std::string feedId;
                    iss >> feedId;
                    
                    if (feedId.empty()) {
                        std::cout << RED << "Usage: /context remove <feed_id>" << RESET << "\n";
                    } else {
                        // Would need agent API to remove feeds
                        std::cout << YELLOW << "⚠  Context feed removal not yet implemented in API" << RESET << "\n";
                    }
                    
                } else if (action == "refresh") {
                    // Refresh context feed: /context refresh <feed_id>
                    std::string feedId;
                    iss >> feedId;
                    
                    if (feedId.empty()) {
                        std::cout << RED << "Usage: /context refresh <feed_id>" << RESET << "\n";
                    } else {
                        std::string value = agent.getContextFeedValue(feedId);
                        if (value.empty()) {
                            std::cout << YELLOW << "⚠  Context feed not found: " << feedId << RESET << "\n";
                        } else {
                            std::cout << BOLD << "Context Feed: " << feedId << RESET << "\n";
                            std::cout << value << "\n";
                        }
                    }
                    
                } else {
                    std::cout << RED << "Unknown context action. Use: add|remove|list|refresh" << RESET << "\n";
                }
            }
            else if (input == "/info") {
                showAgentInfo(agent);
            }
            else if (input == "/reload") {
                if (manifestPath.empty()) {
                    std::cout << YELLOW << "No manifest to reload. Use /load first." << RESET << "\n";
                } else {
                    if (loadAgentProfile(agent, manifestPath)) {
                        std::cout << GREEN << "✓ Manifest reloaded" << RESET << "\n";
                    } else {
                        std::cout << RED << "✗ Failed to reload manifest" << RESET << "\n";
                    }
                }
            }
            else if (input.substr(0, 6) == "/load ") {
                manifestPath = input.substr(6);
                std::cout << "Loading: " << CYAN << manifestPath << RESET << "\n";
                if (loadAgentProfile(agent, manifestPath)) {
                    std::cout << GREEN << "✓ Loaded: " << agent.getName() << RESET << "\n";
                } else {
                    std::cout << RED << "✗ Failed to load manifest" << RESET << "\n";
                    manifestPath.clear();
                }
            }
            else if (input.substr(0, 8) == "/stream ") {
                std::string mode = input.substr(8);
                if (mode == "on") {
                    agent.setStreamingEnabled(true);
                    std::cout << GREEN << "✓ Streaming enabled" << RESET << "\n";
                } else if (mode == "off") {
                    agent.setStreamingEnabled(false);
                    std::cout << YELLOW << "⚠  Streaming disabled" << RESET << "\n";
                } else {
                    std::cout << RED << "Invalid mode. Use: /stream on|off" << RESET << "\n";
                }
            }
            else {
                std::cout << RED << "Unknown command. Type /help for available commands." << RESET << "\n";
            }
            continue;
        }
        
        // Process user input
        try {
            if (manifestPath.empty()) {
                std::cout << YELLOW << "⚠  No agent loaded. Use /load <path> first." << RESET << "\n";
                continue;
            }
            
            if (agent.isStreamingEnabled()) {
                // Streaming mode
                std::cout << DIM << "[Streaming...]" << RESET << "\n";
                
                // Buffer for accumulating output to reduce rendering artifacts
                std::string outputBuffer;
                bool needsFlush = false;
                
                agent.promptStreaming(input, [&outputBuffer, &needsFlush](const StreamingProtocol::TokenEvent& event) {
                    switch (event.type) {
                        case StreamingProtocol::TokenEvent::Type::THOUGHT:
                            outputBuffer += MAGENTA + event.content + RESET;
                            needsFlush = true;
                            // Flush on newlines or when buffer gets large
                            if (event.content.find('\n') != std::string::npos || outputBuffer.length() > 200) {
                                std::cout << outputBuffer << std::flush;
                                outputBuffer.clear();
                                needsFlush = false;
                            }
                            break;
                        case StreamingProtocol::TokenEvent::Type::ACTION_START:
                            // Flush any pending output before action
                            if (!outputBuffer.empty()) {
                                std::cout << outputBuffer << std::flush;
                                outputBuffer.clear();
                            }
                            std::cout << "\n" << YELLOW << "[ACTION: " << event.action->name << "]" << RESET << "\n" << std::flush;
                            break;
                        case StreamingProtocol::TokenEvent::Type::ACTION_COMPLETE:
                            std::cout << GREEN << "[DONE]" << RESET << " " << std::flush;
                            break;
                        case StreamingProtocol::TokenEvent::Type::RESPONSE:
                            // Flush any pending thought output before response
                            if (!outputBuffer.empty()) {
                                std::cout << outputBuffer << std::flush;
                                outputBuffer.clear();
                            }
                            std::cout << event.content << std::flush;
                            break;
                        case StreamingProtocol::TokenEvent::Type::ERROR:
                            // Flush pending output first
                            if (!outputBuffer.empty()) {
                                std::cout << outputBuffer << std::flush;
                                outputBuffer.clear();
                            }
                            std::cout << RED << "[ERROR: " << event.content << "]" << RESET << "\n" << std::flush;
                            break;
                        default:
                            break;
                    }
                });
                
                // Final flush of any remaining buffered output
                if (!outputBuffer.empty()) {
                    std::cout << outputBuffer << std::flush;
                }
                
                std::cout << "\n";
            } else {
                // Non-streaming mode
                std::string response = agent.prompt(input);
                std::cout << CYAN << response << RESET << "\n";
            }
            
        } catch (const std::exception& e) {
            std::cout << RED << "Error: " << e.what() << RESET << "\n";
        }
    }
    
    std::cout << "\n" << BOLD << "Goodbye!" << RESET << "\n";
    return 0;
}
