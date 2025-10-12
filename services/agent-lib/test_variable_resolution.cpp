#include "StreamingProtocol.hpp"
#include <iostream>
#include <sstream>

using namespace StreamingProtocol;

// Mock action executor that returns a simple JSON value
Json::Value mockActionExecutor(const ParsedAction& action) {
    Json::Value result;
    if (action.name == "calculator") {
        result["result"] = 42; // Simple mock result
        result["operation"] = "add";
    } else if (action.name == "text_analyzer") {
        result["word_count"] = 10;
        result["sentiment"] = "positive";
    } else {
        result["message"] = "Mock action executed: " + action.name;
    }
    return result;
}

void testVariableResolution() {
    std::cout << "=== Testing Variable Resolution ===" << std::endl;
    
    // Create parser with mock executor
    Parser parser(mockActionExecutor);
    
    // Set up a simple test: calculate 2+2, store result, then use it in response
    std::string testInput = R"(
<thought>
Let me calculate 2 + 2.
</thought>

<action type="tool" mode="async" id="calc1">
{
  "name": "calculator",
  "parameters": {"operation": "add", "a": 2, "b": 2},
  "output_key": "sum_result"
}
</action>

<response final="true">
The sum of 2 and 2 is $sum_result.
</response>
)";

    std::cout << "Input:" << std::endl;
    std::cout << testInput << std::endl;
    std::cout << std::endl;
    
    // Process the input
    std::cout << "Processing tokens..." << std::endl;
    parser.parseToken(testInput, true); // true means final token
    
    std::cout << "=== Test Complete ===" << std::endl;
}

int main() {
    testVariableResolution();
    return 0;
}