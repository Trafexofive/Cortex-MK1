#include <iostream>
#include <string>
#include <filesystem>
#include <map>
#include <vector>
#include <sstream>
// std::any is C++17 and later
#include <any>

template <typename T>
class Variable {
private:
    std::string key;
    T value;

public:
    Variable(const std::string& k, const T& val) : key(k), value(val) {}

    std::string getKey() const { return key; }
    T getValue() const { return value; }
};


class NamespaceVariables {
private:
    std::map<std::string, NamespaceVariables*> namespaces;
    std::map<std::string, Variable<std::any>> variables;  // Use std::any to store any type

public:
    // Access a namespace (creates it if it doesn't exist)
    NamespaceVariables& operator[](const std::string& ns) {
        if (namespaces.find(ns) == namespaces.end()) {
            namespaces[ns] = new NamespaceVariables();
        }
        return *namespaces[ns];
    }

    // Set a variable within the current namespace
    template <typename T>
    void set(const std::string& key, const T& value) {
        variables[key] = Variable<std::any>(key, value);
    }

    // Get a variable within the current namespace
    template <typename T>
    T get(const std::string& key) const {
        try {
            return std::any_cast<T>(variables.at(key).getValue());
        } catch (const std::bad_any_cast& e) {
            std::cerr << "Error: Invalid type cast for key: " << key << std::endl;
            throw; // Re-throw the exception or handle it differently
        }
    }


    // Helper function to print all variables in a namespace (and sub-namespaces)
    void print(const std::string& prefix = "") const {
        for (const auto& var : variables) {
            std::cout << prefix << var.first << ": ";
            try { // Attempt to print common types
                std::cout << std::any_cast<std::string>(var.second.getValue()) << std::endl;
            } catch(...) {
                try { std::cout << std::any_cast<int>(var.second.getValue()) << std::endl; }
                catch(...) {
                    try { std::cout << std::any_cast<bool>(var.second.getValue()) << std::endl; }
                    catch(...) {
                        try { std::cout << std::any_cast<std::filesystem::path>(var.second.getValue()) << std::endl; }
                        catch(...) { std::cout << "[Unprintable Type]" << std::endl; }
                    }
                }
            }
        }
        for (const auto& ns : namespaces) {
            std::cout << prefix << ns.first << ":" << std::endl;
            ns.second->print(prefix + "  ");
        }
    }


};




int main() {
    NamespaceVariables vars;

    vars["global"]["configs"]["agents"]["standard"].set("name", "Standard Agent");
    vars["agent-1"]["state"]["input"].set("value", 123);
    vars["global"]["configs"]["port"].set("number", 8080);
    vars["global"]["configs"]["path"].set<std::filesystem::path>("value", "data/config.json");


    vars.print();


    std::cout << "Agent name: " << vars["global"]["configs"]["agents"]["standard"].get<std::string>("name") << std::endl;
    std::cout << "Port number: " << vars["global"]["configs"]["port"].get<int>("number") << std::endl;

    // Example demonstrating error handling:
    try {
        std::string portNumber = vars["global"]["configs"]["port"].get<std::string>("number"); // Incorrect type
    } catch (const std::bad_any_cast& e) {
        std::cerr << "Caught exception: " << e.what() << std::endl;
    }


    return 0;
}
