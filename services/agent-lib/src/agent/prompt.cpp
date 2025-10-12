#include "Agent.hpp"
#include "Tool.hpp"
#include "ToolRegistry.hpp" // For ToolRegistry
#include "Utils.hpp"        // For executeScriptTool
#include <ctime>
#include <iomanip>
#include <sstream>

// Helper function for formatting current date/time
static std::string getFormattedDateTime() {
  std::time_t now = std::time(0);
  std::tm *timeinfo = std::localtime(&now);

  std::stringstream ss;
  ss << std::put_time(timeinfo, "%Y-%m-%d %H:%M:%S %Z");
  return ss.str();
}

// --- Private Helper Methods (Implementations) ---
std::string Agent::buildFullPrompt() const {
  std::stringstream promptSs;

  promptSs << "<agent_identity>\n";
  promptSs << "\t<name>" << agentName << "</name>\n";
  if (!agentDescription.empty())
    promptSs << "\t<description>" << agentDescription << "</description>\n";
  promptSs << "</agent_identity>\n\n";


  if (!systemPrompt.empty()) {
    promptSs << "<system_prompt>\n" << systemPrompt << "\n</system_prompt>\n\n";
  }

  // Inject streaming protocol instructions if streaming is enabled
  if (streamingEnabled) {
    promptSs << "<cortex_streaming_protocol>\n";
    promptSs << "═══════════════════════════════════════════════════════════════\n";
    promptSs << "  CRITICAL: MANDATORY OUTPUT FORMAT - STRICTLY ENFORCED - \n";
    promptSs << "═══════════════════════════════════════════════════════════════\n\n";
    
    promptSs << "You MUST respond using ONLY the following XML structure.\n";
    promptSs << "DO NOT use markdown code blocks (```xml or ```).\n";
    promptSs << "DO NOT add any text before or after the XML tags.\n";
    promptSs << "OUTPUT THE TAGS DIRECTLY WITH NO WRAPPING.\n\n";
    
    promptSs << "REQUIRED STRUCTURE:\n\n";
    promptSs << "<thought>\n";
    promptSs << "[Your reasoning process. Break down the problem. Plan your approach.]\n";
    promptSs << "[You can use multiple <thought> blocks to show iterative reasoning.]\n";
    promptSs << "</thought>\n\n";

    
    promptSs << "[OPTIONAL: Use <action> blocks to call tools]\n";
    promptSs << "<action type=\"tool\" mode=\"async\" id=\"unique_id\">";
    promptSs << "{\n";
    promptSs << "  \"name\": \"tool_name\",\n";
    promptSs << "  \"parameters\": { \"key\": \"value\" },\n";
    promptSs << "  \"output_key\": \"variable_name\"\n";
    promptSs << "}\n";
    promptSs << "</action>\n\n";
    promptSs << "***IMPORTANT RULE FOR ACTIONS***:\n";
    promptSs << "The JSON block inside the <action> tag MUST be 100% complete and valid. ";
    promptSs << "Do not leave it unfinished. Ensure all brackets {}, braces [], and quotes \" are correctly closed.\n\n";
    
    promptSs << "<response final=\"true\">\n";
    promptSs << "[Your final answer in Markdown format.]\n";
    promptSs << "[Use $variable_name to reference action results.]\n";
    promptSs << "</response>\n\n";
    
    promptSs << "EXAMPLES:\n\n";
    promptSs << "Example 1 (Simple response):\n";

    promptSs << "<thought>\n";
    promptSs << "The user asked a simple greeting. I should respond warmly.\n";
    promptSs << "</thought>\n\n";

    promptSs << "<thought>\n";
    promptSs << "[another thought]\n";
    promptSs << "</thought>\n\n";

    promptSs << "<response final=\"false\">\n";
    promptSs << "Hello! I'll get started on X while I wait for Y\n";
    promptSs << "</response>\n\n";

    promptSs << "<response final=\"true\">\n";
    promptSs << "Hello! How can I assist you today?\n";
    promptSs << "</response>\n\n";
    
    promptSs << "Example 2 (With tool use):\n";
    promptSs << "<thought>\n";
    promptSs << "User needs research. I'll use the knowledge_retriever tool.\n";
    promptSs << "</thought>\n\n";
    promptSs << "<action type=\"tool\" mode=\"async\" id=\"research_1\">\n";
    promptSs << "{\n";
    promptSs << "  \"name\": \"knowledge_retriever\",\n";
    promptSs << "  \"parameters\": { \"query\": \"quantum computing\", \"depth\": \"thorough\" },\n";
    promptSs << "  \"output_key\": \"research_data\"\n";
    promptSs << "}\n";
    promptSs << "</action>\n\n";
    promptSs << "<thought>\n";
    promptSs << "Now I'll synthesize the research results into a clear answer.\n";
    promptSs << "</thought>\n\n";
    promptSs << "<response final=\"true\">\n";
    promptSs << "Based on the research: $research_data\n\n";
    promptSs << "**Key findings:** Quantum computing uses quantum mechanics...\n";
    promptSs << "</response>\n\n";
    
    promptSs << "REMEMBER:\n";
    promptSs << "• Start IMMEDIATELY with <thought> (no preamble)\n";
    promptSs << "• You can use <thought> blocks multiple times and in any place\n";
    promptSs << "• NO markdown code fences (```) (It will result in the parsing and by consequence your execution to fail)\n";
    promptSs << "• ALWAYS end with <response final=\"true\"> (As it is the only way to put an end to the agent loop (Not even the user can interupt you). This is double edged; meaning it also means that IF Job NOT Finished == KEEP GOING)\n";
    promptSs << "• Multiple <thought> blocks = good (shows reasoning, but more imporantly analysis of the problems at hand, future problems, misconptions and beyond)\n";
    promptSs << "• Do not be rigide in Your Suit (The agentic Suit if you will.), Move with confidence. Forget the Old ways and breath in our XML+JSON bespoke streamed Protocol, where we do not wait for actions to be executed. Take advantage of SYNC, ASYNC, and FIRE AND FORGET\n";
    promptSs << "• Take advantage of The Streaming protocol; smaller modular <action>s is the way to go. Instead of one <action> with a huge json Blob, go multiple <action>s. An attomic approach keeps it purposeful, and under control, in order to get the Job Done.\n";
    promptSs << "═══════════════════════════════════════════════════════════════\n";
    promptSs << " ACTION EXAMPLES:\n";
    promptSs << "</cortex_streaming_protocol>\n\n";
  }


  // Add schema and example if they exist
  if (!llmResponseSchema.empty()) {
    promptSs << "<response_schema_definition>\n"
             << llmResponseSchema << "\n</response_schema_definition>\n\n";
  }

  if (!llmResponseExample.empty()) {
    promptSs << "<response_example>\n"
             << llmResponseExample << "\n</response_example>\n\n";
  }

  // live updated metadata, time,date and weather, etc.
  // in the future we could have external tools here.
  promptSs << "<live_metadata>\n";
  promptSs << "\t<current_datetime>" << getFormattedDateTime()
           << "</current_datetime>\n";
  // TODO: Add weather, system stats, etc. when available
  promptSs << "</live_metadata>\n\n";
  
  // Inject context feeds for runtime context injection
  if (!contextFeeds.empty()) {
    promptSs << "<context_feeds>\n";
    promptSs << "\t<tip>Dynamic context provided at runtime</tip>\n";
    for (const auto& feedPair : contextFeeds) {
      const auto& feed = feedPair.second;
      if (!feed.content.empty()) {
        promptSs << "\t<feed id=\"" << feed.id << "\" type=\"" << feed.type << "\">\n";
        promptSs << "\t\t" << feed.content << "\n";
        promptSs << "\t</feed>\n";
      }
    }
    promptSs << "</context_feeds>\n\n";
  }

  // TODO: add a tool that will register some tools with predefined input, it
  // will execute every time and append to the system prompt


  // TODO: readd the addEnvVar builtin.
  // ${{INTERNAL_ENV_VAR}} | ${{tool_name{"param1": "test value", "param2": true}}} aajust exec to default to name + ~type [OPTIONAL]
  // TODO: add action this-> access. if so action needs a unique id. 
    // promptSs << "\t<tip></tip>\n";
  if (!environmentVariables.empty()) {
    promptSs << "<environment_variables>\n";
    promptSs << "\t<tip>Can be Expanded in action object parameters and in reply section eg. (using ${{}} format; avoiding potential conflicts.)</tip>\n";

    for (const auto &pair : environmentVariables) {
      promptSs << "\t<variable name=\"" << pair.first << "\">" << pair.second
               << "</variable>\n";
    }
    promptSs << "</environment_variables>\n\n";
  }

  if (!subAgents.empty()) {
    promptSs << "<sub_agents_online>\n";
    promptSs << "\t<tip>Safe to assume that if the tool name is the same, the it is actually the same</tip>\n";
    for (const auto &pair : subAgents) {
      promptSs << "\t<sub_agent name=\"" << pair.first << "\"/>\n";
      promptSs << "\t<sub_agent_description>" << pair.second->getDescription()
               << "</sub_agent_description>\n";

      for (const auto &action: pair.second->registeredTools) {
          // TODO: if action.description is already in allAvailableActions, display name only
        if (action.second )
            promptSs << "\t<action_definition name=\"" << action.first << "\"";
                     // << "\">" << pair.second->getDescription()
                     // << "</action_definition>\n";
      }
    }
    promptSs << "</sub_agents_online>\n\n";
  }

  std::map<std::string, std::string> allAvailableActions =
      internalFunctionDescriptions;
  for (const auto &pair : registeredTools) {
    if (pair.second)
      allAvailableActions[pair.first] = pair.second->getDescription();
  }

  if (!allAvailableActions.empty()) {
    promptSs << "<available_actions_reference>\n";
    for (const auto &pair : allAvailableActions) {
      promptSs << "\t<action_definition name=\"" << pair.first << "\">\n";
      promptSs << "\t\t<description_text>" << pair.second
               << "</description_text>\n";
      promptSs << "\t</action_definition>\n";
    }
    promptSs << "</available_actions_reference>\n\n";
  }

  if (!extraSystemPrompts.empty()) {
    promptSs << "<additional_guidance>\n"; // Renamed
    for (const auto &p : extraSystemPrompts)
      promptSs << "\t<instruction>" << p << "</instruction>\n";
    promptSs << "</additional_guidance>\n\n";
  }

  // Full conversation history - CAG not RAG
  // Only truncate on API error (token limit), not preemptively
  if (!conversationHistory.empty()) {
    promptSs << "<conversation_history>\n";
    for (const auto &item : conversationHistory) {
      promptSs << "\t<past_conversation_item>\n";
      promptSs << "\t\t<role>" << item.first << "</role>\n";
      promptSs << "\t\t<content>" << item.second << "</content>\n";
      promptSs << "\t</past_conversation_item>\n";
    }
    promptSs << "</conversation_history>\n\n";
  }

  return promptSs.str();
}
