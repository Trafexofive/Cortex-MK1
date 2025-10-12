// #include "Agent.hpp" // Your Agent class header
// #include <string>
// #include <vector>
// #include <fstream>
// #include <iostream> // For basic error output in this example
// #include <stdexcept>
//
// // Include yaml-cpp headers
// #include <yaml-cpp/yaml.h>
// #include <yaml-cpp/emitter.h> // For exporting
//                               
// // --- Export Function ---
// // Saves the current configuration OF an Agent object TO a YAML file.
// // Only saves configurable profile aspects, not full runtime state.
// // Returns true on success, false on failure.
// bool saveAgentProfile(const Agent& agentToSave, const std::string& yamlPath) {
//     logMessage(LogLevel::INFO, "Attempting to save agent profile", yamlPath);
//     YAML::Emitter emitter;
//     try {
//         emitter << YAML::BeginMap;
//
//         // Add a version marker (good practice)
//         emitter << YAML::Key << "version" << YAML::Value << "agent-1.1"; // Example version
//
//         // --- Save Core Identity & Configuration ---
//         emitter << YAML::Key << "name" << YAML::Value << agentToSave.getName();
//         emitter << YAML::Key << "description" << YAML::Value << YAML::Literal << agentToSave.getDescription(); // Use Literal for multi-line
//         emitter << YAML::Key << "system_prompt" << YAML::Value << YAML::Literal << agentToSave.getSystemPrompt(); // Use Literal for multi-line
//         emitter << YAML::Key << "iteration_cap" << YAML::Value << agentToSave.getIterationCap(); // Assuming getter exists
//
//         // --- Save Environment ---
//         // Assuming Agent has a way to get environment variables, e.g., getEnv() returning a map or vector<pair>
//         const auto& envVars = agentToSave.getEnv(); // *** ASSUMPTION: getEnv() exists and returns suitable type ***
//         if (!envVars.empty()) {
//             emitter << YAML::Key << "environment" << YAML::Value << YAML::BeginMap;
//             for (const auto& pair : envVars) {
//                 emitter << YAML::Key << pair.first << YAML::Value << pair.second;
//             }
//             emitter << YAML::EndMap;
//         }
//
//         // --- Save Optional Sections ---
//         // Assuming Agent has getters for these, e.g., getExtraPrompts(), getTasks()
//         const auto& extraPrompts = agentToSave.getExtraPrompts(); // *** ASSUMPTION: getExtraPrompts() exists ***
//         if (!extraPrompts.empty()) {
//             emitter << YAML::Key << "extra_prompts" << YAML::Value << YAML::BeginSeq;
//             for (const auto& prompt : extraPrompts) {
//                 emitter << prompt;
//             }
//             emitter << YAML::EndSeq;
//         }
//         const auto& tasks = agentToSave.getTasks(); // *** ASSUMPTION: getTasks() exists ***
//         if (!tasks.empty()) {
//             emitter << YAML::Key << "tasks" << YAML::Value << YAML::BeginSeq;
//             for (const auto& task : tasks) {
//                 emitter << task;
//             }
//             emitter << YAML::EndSeq;
//         }
//
//         // --- Save Directive ---
//         const auto& directive = agentToSave.getDirective(); // *** ASSUMPTION: getDirective() exists ***
//         emitter << YAML::Key << "directive" << YAML::Value << YAML::BeginMap;
//         // Convert enum back to string
//         std::string typeStr = "NORMAL"; // Default
//         switch (directive.type) {
//             case Agent::DIRECTIVE::Type::BRAINSTORMING: typeStr = "BRAINSTORMING"; break;
//             case Agent::DIRECTIVE::Type::AUTONOMOUS: typeStr = "AUTONOMOUS"; break;
//             case Agent::DIRECTIVE::Type::EXECUTE: typeStr = "EXECUTE"; break;
//             case Agent::DIRECTIVE::Type::REPORT: typeStr = "REPORT"; break;
//             case Agent::DIRECTIVE::Type::NORMAL: // Fallthrough
//             default: typeStr = "NORMAL"; break;
//         }
//         emitter << YAML::Key << "type" << YAML::Value << typeStr;
//         emitter << YAML::Key << "description" << YAML::Value << directive.description;
//         emitter << YAML::Key << "format" << YAML::Value << directive.format;
//         emitter << YAML::EndMap;
//
//         // --- What is NOT saved ---
//         // - Runtime state (iteration, skipFlowIteration, scratchpad)
//         // - History
//         // - Memory state (long/short term)
//         // - Tool definitions/instances (might save *list* of expected tool *names* if needed)
//         // - Sub-agent references/definitions
//
//         emitter << YAML::EndMap;
//
//         // Write to file
//         std::ofstream fout(yamlPath);
//         if (!fout.is_open()) {
//             logMessage(LogLevel::ERROR, "Failed to open file for saving agent profile", yamlPath);
//             return false;
//         }
//         fout << emitter.c_str();
//         fout.close();
//
//         if (!emitter.good()) {
//              logMessage(LogLevel::ERROR, "YAML emitter error after saving agent profile", emitter.GetLastError());
//              return false; // Indicate potential issue even if file write succeeded superficially
//         }
//
//         logMessage(LogLevel::INFO, "Successfully saved agent profile", yamlPath);
//         return true;
//
//     } catch (const YAML::Exception& e) {
//         logMessage(LogLevel::ERROR, "YAML emitter error during agent profile save", yamlPath + ": " + e.what());
//         return false;
//     } catch (const std::exception& e) {
//         logMessage(LogLevel::ERROR, "Generic error saving agent profile", yamlPath + ": " + e.what());
//         return false;
//     }
// }
//
//
