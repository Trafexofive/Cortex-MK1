#include <iostream>
#include "MiniGemini.hpp"

int main() {
    MiniGemini api;
    
    std::cout << "Testing streaming..." << std::endl;
    
    try {
        api.generateStream("Say 'test' in one word", [](const std::string& token, bool isFinal) {
            if (!token.empty()) {
                std::cout << "Token: [" << token << "]" << std::endl;
            }
            if (isFinal) {
                std::cout << "Stream finished" << std::endl;
            }
        });
    } catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << std::endl;
        return 1;
    }
    
    return 0;
}
