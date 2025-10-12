#ifndef JSON_H_
#define JSON_H_

#include <string>
#include <vector>
#include <map>
#include <sstream>
#include <cstdlib>
#include <stdexcept>
#include <cassert>

namespace json {

// Forward declarations
class Value;
typedef std::map<std::string, Value> Object;
typedef std::vector<Value> Array;

// JSON value types
enum ValueType {
    NULL_VALUE,
    BOOL_VALUE,
    NUMBER_VALUE,
    STRING_VALUE,
    ARRAY_VALUE,
    OBJECT_VALUE
};

class Value {
private:
    ValueType type_;
    bool bool_value_;
    double number_value_;
    std::string string_value_;
    Array array_value_;
    Object object_value_;

public:
    // Constructors
    Value() : type_(NULL_VALUE), bool_value_(false), number_value_(0) {}
    
    // Type-specific constructors
    Value(bool value) : type_(BOOL_VALUE), bool_value_(value), number_value_(0) {}
    Value(int value) : type_(NUMBER_VALUE), bool_value_(false), number_value_(value) {}
    Value(double value) : type_(NUMBER_VALUE), bool_value_(false), number_value_(value) {}
    Value(const char* value) : type_(STRING_VALUE), bool_value_(false), number_value_(0), string_value_(value) {}
    Value(const std::string& value) : type_(STRING_VALUE), bool_value_(false), number_value_(0), string_value_(value) {}
    Value(const Array& value) : type_(ARRAY_VALUE), bool_value_(false), number_value_(0), array_value_(value) {}
    Value(const Object& value) : type_(OBJECT_VALUE), bool_value_(false), number_value_(0), object_value_(value) {}

    // Type checking
    bool isNull() const { return type_ == NULL_VALUE; }
    bool isBool() const { return type_ == BOOL_VALUE; }
    bool isNumber() const { return type_ == NUMBER_VALUE; }
    bool isString() const { return type_ == STRING_VALUE; }
    bool isArray() const { return type_ == ARRAY_VALUE; }
    bool isObject() const { return type_ == OBJECT_VALUE; }
    ValueType type() const { return type_; }

    // Value retrieval (with type checking)
    bool asBool() const {
        if (!isBool()) throw std::runtime_error("Value is not a boolean");
        return bool_value_;
    }
    
    double asNumber() const {
        if (!isNumber()) throw std::runtime_error("Value is not a number");
        return number_value_;
    }
    
    int asInt() const {
        if (!isNumber()) throw std::runtime_error("Value is not a number");
        return static_cast<int>(number_value_);
    }
    
    const std::string& asString() const {
        if (!isString()) throw std::runtime_error("Value is not a string");
        return string_value_;
    }
    
    const Array& asArray() const {
        if (!isArray()) throw std::runtime_error("Value is not an array");
        return array_value_;
    }
    
    const Object& asObject() const {
        if (!isObject()) throw std::runtime_error("Value is not an object");
        return object_value_;
    }
    
    // Mutable accessors
    Array& asArray() {
        if (!isArray()) throw std::runtime_error("Value is not an array");
        return array_value_;
    }
    
    Object& asObject() {
        if (!isObject()) throw std::runtime_error("Value is not an object");
        return object_value_;
    }

    // Array/Object element access
    const Value& operator[](size_t index) const {
        if (!isArray()) throw std::runtime_error("Value is not an array");
        if (index >= array_value_.size()) throw std::out_of_range("Array index out of range");
        return array_value_[index];
    }
    
    Value& operator[](size_t index) {
        if (type_ != ARRAY_VALUE) {
            type_ = ARRAY_VALUE;
            array_value_.clear();
        }
        if (index >= array_value_.size()) 
            array_value_.resize(index + 1);
        return array_value_[index];
    }
    
    const Value& operator[](const std::string& key) const {
        if (!isObject()) throw std::runtime_error("Value is not an object");
        Object::const_iterator it = object_value_.find(key);
        if (it == object_value_.end()) throw std::out_of_range("Object key not found");
        return it->second;
    }
    
    Value& operator[](const std::string& key) {
        if (type_ != OBJECT_VALUE) {
            type_ = OBJECT_VALUE;
            object_value_.clear();
        }
        return object_value_[key];
    }

    // Helper methods for object access
    bool has(const std::string& key) const {
        if (!isObject()) return false;
        return object_value_.find(key) != object_value_.end();
    }
    
    // Size information
    size_t size() const {
        if (isArray()) return array_value_.size();
        if (isObject()) return object_value_.size();
        return 0;
    }

    // String representation
    std::string toString(bool pretty = false, int indent = 0) const {
        std::ostringstream os;
        
        switch (type_) {
            case NULL_VALUE:
                os << "null";
                break;
                
            case BOOL_VALUE:
                os << (bool_value_ ? "true" : "false");
                break;
                
            case NUMBER_VALUE:
                os << number_value_;
                break;
                
            case STRING_VALUE:
                os << '"';
                for (size_t i = 0; i < string_value_.length(); ++i) {
                    char c = string_value_[i];
                    switch (c) {
                        case '"':  os << "\\\""; break;
                        case '\\': os << "\\\\"; break;
                        case '\b': os << "\\b"; break;
                        case '\f': os << "\\f"; break;
                        case '\n': os << "\\n"; break;
                        case '\r': os << "\\r"; break;
                        case '\t': os << "\\t"; break;
                        default:
                            if (c < 32) {
                                os << "\\u" 
                                   << std::hex << std::uppercase
                                   << static_cast<int>(c)
                                   << std::dec << std::nouppercase;
                            } else {
                                os << c;
                            }
                    }
                }
                os << '"';
                break;
                
            case ARRAY_VALUE: {
                os << '[';
                
                if (pretty && !array_value_.empty()) {
                    os << '\n';
                }
                
                for (size_t i = 0; i < array_value_.size(); ++i) {
                    if (pretty) {
                        for (int j = 0; j < indent + 2; ++j) os << ' ';
                    }
                    
                    os << array_value_[i].toString(pretty, indent + 2);
                    
                    if (i < array_value_.size() - 1) {
                        os << ',';
                    }
                    
                    if (pretty) {
                        os << '\n';
                    }
                }
                
                if (pretty && !array_value_.empty()) {
                    for (int j = 0; j < indent; ++j) os << ' ';
                }
                
                os << ']';
                break;
            }
            
            case OBJECT_VALUE: {
                os << '{';
                
                if (pretty && !object_value_.empty()) {
                    os << '\n';
                }
                
                Object::const_iterator it = object_value_.begin();
                for (size_t i = 0; it != object_value_.end(); ++it, ++i) {
                    if (pretty) {
                        for (int j = 0; j < indent + 2; ++j) os << ' ';
                    }
                    
                    os << '"' << it->first << "\":";
                    
                    if (pretty) {
                        os << ' ';
                    }
                    
                    os << it->second.toString(pretty, indent + 2);
                    
                    if (i < object_value_.size() - 1) {
                        os << ',';
                    }
                    
                    if (pretty) {
                        os << '\n';
                    }
                }
                
                if (pretty && !object_value_.empty()) {
                    for (int j = 0; j < indent; ++j) os << ' ';
                }
                
                os << '}';
                break;
            }
        }
        
        return os.str();
    }
};

// Parsing functions
namespace parser {
    // Simple tokenizer for JSON parsing
    class Tokenizer {
    private:
        const std::string& input_;
        size_t pos_;

        void skipWhitespace() {
            while (pos_ < input_.length() && isspace(input_[pos_]))
                ++pos_;
        }

    public:
        Tokenizer(const std::string& input) : input_(input), pos_(0) {}

        bool hasMore() const {
            return pos_ < input_.length();
        }

        char peek() {
            skipWhitespace();
            if (!hasMore()) return '\0';
            return input_[pos_];
        }

        char next() {
            skipWhitespace();
            if (!hasMore()) return '\0';
            return input_[pos_++];
        }

        std::string readString() {
            // Assume the opening quote has been consumed
            std::string result;
            bool escape = false;

            while (hasMore()) {
                char c = input_[pos_++];
                
                if (escape) {
                    escape = false;
                    switch (c) {
                        case '"': result += '"'; break;
                        case '\\': result += '\\'; break;
                        case '/': result += '/'; break;
                        case 'b': result += '\b'; break;
                        case 'f': result += '\f'; break;
                        case 'n': result += '\n'; break;
                        case 'r': result += '\r'; break;
                        case 't': result += '\t'; break;
                        case 'u': {
                            // Handle \uXXXX escape sequences
                            if (pos_ + 4 > input_.length()) {
                                throw std::runtime_error("Invalid \\u escape sequence");
                            }
                            std::string hex = input_.substr(pos_, 4);
                            pos_ += 4;
                            
                            // Convert hex to int and then to char
                            int value = 0;
                            for (int i = 0; i < 4; ++i) {
                                value = value * 16;
                                char h = hex[i];
                                if (h >= '0' && h <= '9') value += (h - '0');
                                else if (h >= 'A' && h <= 'F') value += (h - 'A' + 10);
                                else if (h >= 'a' && h <= 'f') value += (h - 'a' + 10);
                                else throw std::runtime_error("Invalid hex character in \\u escape");
                            }
                            
                            // This is a simplification - proper UTF-8 handling would be more complex
                            if (value < 128) {
                                result += static_cast<char>(value);
                            } else {
                                // Just for basic handling, more comprehensive UTF-8 would be needed
                                result += '?';
                            }
                            break;
                        }
                        default:
                            result += c;
                    }
                } else if (c == '\\') {
                    escape = true;
                } else if (c == '"') {
                    // End of string
                    break;
                } else {
                    result += c;
                }
            }
            
            return result;
        }

        std::string readNumber() {
            size_t start = pos_ - 1;  // Include the first digit
            
            // Read digits, dot, exponent, etc.
            while (hasMore() && (
                   isdigit(input_[pos_]) || 
                   input_[pos_] == '.' || 
                   input_[pos_] == 'e' || 
                   input_[pos_] == 'E' || 
                   input_[pos_] == '+' || 
                   input_[pos_] == '-')) {
                ++pos_;
            }
            
            return input_.substr(start, pos_ - start);
        }

        std::string readToken() {
            size_t start = pos_ - 1;
            while (hasMore() && isalpha(input_[pos_])) {
                ++pos_;
            }
            return input_.substr(start, pos_ - start);
        }
        
        void expect(char c) {
            if (next() != c) {
                std::ostringstream msg;
                msg << "Expected '" << c << "' at position " << pos_;
                throw std::runtime_error(msg.str());
            }
        }
    };

    Value parseValue(Tokenizer& tokenizer);

    Value parseObject(Tokenizer& tokenizer) {
        Object obj;
        
        // Empty object?
        if (tokenizer.peek() == '}') {
            tokenizer.next();  // Consume '}'
            return Value(obj);
        }
        
        while (true) {
            // Parse key
            if (tokenizer.next() != '"') {
                throw std::runtime_error("Expected string as object key");
            }
            std::string key = tokenizer.readString();
            
            // Parse colon
            if (tokenizer.next() != ':') {
                throw std::runtime_error("Expected ':' after object key");
            }
            
            // Parse value
            obj[key] = parseValue(tokenizer);
            
            // More items?
            char c = tokenizer.next();
            if (c == '}') {
                break;  // End of object
            }
            else if (c != ',') {
                throw std::runtime_error("Expected ',' or '}' after object value");
            }
        }
        
        return Value(obj);
    }

    Value parseArray(Tokenizer& tokenizer) {
        Array arr;
        
        // Empty array?
        if (tokenizer.peek() == ']') {
            tokenizer.next();  // Consume ']'
            return Value(arr);
        }
        
        while (true) {
            // Parse value
            arr.push_back(parseValue(tokenizer));
            
            // More items?
            char c = tokenizer.next();
            if (c == ']') {
                break;  // End of array
            }
            else if (c != ',') {
                throw std::runtime_error("Expected ',' or ']' after array value");
            }
        }
        
        return Value(arr);
    }

    Value parseValue(Tokenizer& tokenizer) {
        char c = tokenizer.peek();
        
        switch (c) {
            case 'n':
                // null
                tokenizer.next();  // Consume 'n'
                if (tokenizer.readToken() == "ull") {
                    return Value();
                }
                throw std::runtime_error("Invalid token: expected 'null'");
                
            case 't':
                // true
                tokenizer.next();  // Consume 't'
                if (tokenizer.readToken() == "rue") {
                    return Value(true);
                }
                throw std::runtime_error("Invalid token: expected 'true'");
                
            case 'f':
                // false
                tokenizer.next();  // Consume 'f'
                if (tokenizer.readToken() == "alse") {  
                    return Value(false);
                }
                throw std::runtime_error("Invalid token: expected 'false'");
                
            case '"':
                // string
                tokenizer.next();  // Consume '"'
                return Value(tokenizer.readString());
                
            case '{':
                // object
                tokenizer.next();  // Consume '{'
                return parseObject(tokenizer);
                
            case '[':
                // array
                tokenizer.next();  // Consume '['
                return parseArray(tokenizer);
                
            case '-':
            case '0': case '1': case '2': case '3': case '4':
            case '5': case '6': case '7': case '8': case '9':
                // number
                tokenizer.next();  // Consume first digit/sign
                return Value(atof(tokenizer.readNumber().c_str()));
                
            default:
                throw std::runtime_error("Unexpected character in JSON");
        }
    }
    
    Value parse(const std::string& input) {
        Tokenizer tokenizer(input);
        Value result = parseValue(tokenizer);
        
        // Check for trailing data
        if (tokenizer.hasMore()) {
            char c = tokenizer.peek();
            if (!isspace(c)) {
                throw std::runtime_error("Unexpected trailing data in JSON");
            }
        }
        
        return result;
    }
}  // namespace parser

// Helper functions
inline Value parse(const std::string& input) {
    return parser::parse(input);
}

inline Value parseFile(const std::string& filename) {
    std::ifstream file(filename.c_str());
    if (!file.is_open()) {
        throw std::runtime_error("Unable to open file for reading");
    }
    
    std::stringstream buffer;
    buffer << file.rdbuf();
    file.close();
    
    return parse(buffer.str());
}

}  // namespace json

#endif  // JSON_H_
