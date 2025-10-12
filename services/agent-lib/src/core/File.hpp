#ifndef FILE_HPP
#define FILE_HPP

#include <algorithm>
#include <cstddef>
#include <ctime>     // For timestamp functionality
#include <fstream>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>
#include <sys/stat.h> // For file metadata

// Forward declaration
class File;
std::ostream &operator<<(std::ostream &os, const File &f);

class File {
public:
    // File states for agent processing
    enum FileState {
        STATE_UNLOADED,
        STATE_LOADED,
        STATE_MODIFIED,
        STATE_DIRTY,
        STATE_ERROR
    };

    // File types for agent classification
    enum FileType {
        TYPE_UNKNOWN,
        TYPE_TEXT,
        TYPE_CONFIG,
        TYPE_BINARY,
        TYPE_SCRIPT,
        TYPE_DOCUMENT,
        TYPE_IMAGE,
        TYPE_DATA
    };

    // Default constructor
    File() : path_(""), content_(""), description_(""), 
             state_(STATE_UNLOADED), type_(TYPE_UNKNOWN),
             last_modified_(0), file_size_(0), checksum_(0) {}

    // Constructor with path
    explicit File(const std::string &filePath) 
        : path_(filePath), content_(""), description_(""),
          state_(STATE_UNLOADED), type_(TYPE_UNKNOWN),
          last_modified_(0), file_size_(0), checksum_(0) {
        load();
    }

    ~File() {}

    // --- Core getters ---
    const std::string &getPath() const { return path_; }
    const std::string &getContent() const { return content_; }
    const std::string &getDescription() const { return description_; }
    const std::vector<std::string> &getTags() const { return tags_; }
    FileState getState() const { return state_; }
    FileType getType() const { return type_; }
    time_t getLastModified() const { return last_modified_; }
    size_t getFileSize() const { return file_size_; }
    unsigned long getChecksum() const { return checksum_; }

    // --- Agent-friendly accessors ---
    bool isLoaded() const { return state_ != STATE_UNLOADED; }
    bool isDirty() const { return state_ == STATE_DIRTY || state_ == STATE_MODIFIED; }
    bool hasError() const { return state_ == STATE_ERROR; }
    bool exists() const { return fileExists(path_); }
    
    std::string getBasename() const {
        size_t pos = path_.find_last_of("/\\");
        return (pos == std::string::npos) ? path_ : path_.substr(pos + 1);
    }
    
    std::string getExtension() const {
        std::string basename = getBasename();
        size_t pos = basename.find_last_of('.');
        return (pos == std::string::npos) ? "" : basename.substr(pos + 1);
    }

    // --- Setters with state tracking ---
    void setContent(const std::string &content) { 
        if (content_ != content) {
            content_ = content; 
            state_ = STATE_MODIFIED;
            updateChecksum();
        }
    }
    
    void setDescription(const std::string &desc) { description_ = desc; }
    void setTags(const std::vector<std::string> &tags) { tags_ = tags; }
    void setType(FileType type) { type_ = type; }

    // --- Tag management ---
    void addTag(const std::string &tag) {
        if (std::find(tags_.begin(), tags_.end(), tag) == tags_.end()) {
            tags_.push_back(tag);
        }
    }

    void removeTag(const std::string &tag) {
        std::vector<std::string>::iterator new_end =
            std::remove(tags_.begin(), tags_.end(), tag);
        tags_.erase(new_end, tags_.end());
    }

    bool hasTag(const std::string &tag) const {
        return std::find(tags_.begin(), tags_.end(), tag) != tags_.end();
    }

    // --- File operations with better error handling ---
    bool load() {
        if (path_.empty()) {
            state_ = STATE_ERROR;
            return false;
        }

        try {
            std::ifstream fileStream(path_.c_str());
            if (!fileStream.is_open()) {
                state_ = STATE_ERROR;
                return false;
            }

            // Get file metadata
            updateFileMetadata();

            // Read content
            std::ostringstream ss;
            ss << fileStream.rdbuf();
            content_ = ss.str();
            
            // Auto-detect file type
            detectFileType();
            
            // Update state and checksum
            state_ = STATE_LOADED;
            updateChecksum();
            
            return true;
        } catch (const std::exception &) {
            state_ = STATE_ERROR;
            return false;
        }
    }

    bool save() {
        if (path_.empty()) {
            state_ = STATE_ERROR;
            return false;
        }
        return saveAs(path_);
    }

    bool saveAs(const std::string &newPath) {
        try {
            std::ofstream outFile(newPath.c_str());
            if (!outFile.is_open()) {
                state_ = STATE_ERROR;
                return false;
            }
            outFile << content_;
            
            // Update internal state
            path_ = newPath;
            state_ = STATE_LOADED;
            updateFileMetadata();
            
            return true;
        } catch (const std::exception &) {
            state_ = STATE_ERROR;
            return false;
        }
    }

    // --- Agent utility methods ---
    bool backup(const std::string &suffix = ".bak") const {
        if (path_.empty() || !exists()) return false;
        
        std::string backupPath = path_ + suffix;
        std::ifstream src(path_.c_str());
        std::ofstream dst(backupPath.c_str());
        
        if (!src.is_open() || !dst.is_open()) return false;
        
        dst << src.rdbuf();
        return true;
    }

    bool hasChangedOnDisk() const {
        if (path_.empty()) return false;
        
        struct stat st;
        if (stat(path_.c_str(), &st) != 0) return false;
        
        return st.st_mtime != last_modified_;
    }

    // Content analysis for agents
    size_t getLineCount() const {
        return std::count(content_.begin(), content_.end(), '\n') + 
               (content_.empty() ? 0 : 1);
    }

    std::vector<std::string> getLines() const {
        std::vector<std::string> lines;
        std::istringstream stream(content_);
        std::string line;
        
        while (std::getline(stream, line)) {
            lines.push_back(line);
        }
        return lines;
    }

    // Search functionality
    bool contains(const std::string &needle) const {
        return content_.find(needle) != std::string::npos;
    }

    std::vector<size_t> findAllOccurrences(const std::string &needle) const {
        std::vector<size_t> positions;
        size_t pos = 0;
        
        while ((pos = content_.find(needle, pos)) != std::string::npos) {
            positions.push_back(pos);
            pos += needle.length();
        }
        return positions;
    }

    // --- Serialization for agent communication ---
    std::string toJson() const {
        std::ostringstream json;
        json << "{"
             << "\"path\":\"" << escapeJson(path_) << "\","
             << "\"description\":\"" << escapeJson(description_) << "\","
             << "\"state\":" << static_cast<int>(state_) << ","
             << "\"type\":" << static_cast<int>(type_) << ","
             << "\"size\":" << file_size_ << ","
             << "\"modified\":" << last_modified_ << ","
             << "\"checksum\":" << checksum_ << ","
             << "\"tags\":[";
        
        for (size_t i = 0; i < tags_.size(); ++i) {
            json << "\"" << escapeJson(tags_[i]) << "\"";
            if (i < tags_.size() - 1) json << ",";
        }
        json << "]}";
        
        return json.str();
    }

    // Friend function
    friend std::ostream &operator<<(std::ostream &os, const File &f);

private:
    // Member variables
    std::string path_;
    std::string content_;
    std::string description_;
    std::vector<std::string> tags_;
    FileState state_;
    FileType type_;
    time_t last_modified_;
    size_t file_size_;
    unsigned long checksum_;

    // Helper methods
    void updateFileMetadata() {
        struct stat st;
        if (stat(path_.c_str(), &st) == 0) {
            last_modified_ = st.st_mtime;
            file_size_ = st.st_size;
        }
    }

    void detectFileType() {
        std::string ext = getExtension();
        std::transform(ext.begin(), ext.end(), ext.begin(), ::tolower);
        
        if (ext == "txt" || ext == "md" || ext == "rst") {
            type_ = TYPE_TEXT;
        } else if (ext == "conf" || ext == "cfg" || ext == "ini" || ext == "yaml" || ext == "json") {
            type_ = TYPE_CONFIG;
        } else if (ext == "sh" || ext == "py" || ext == "pl" || ext == "rb") {
            type_ = TYPE_SCRIPT;
        } else if (ext == "csv" || ext == "xml" || ext == "sql") {
            type_ = TYPE_DATA;
        } else {
            // Check if content is text or binary
            type_ = isTextContent() ? TYPE_TEXT : TYPE_BINARY;
        }
    }

    bool isTextContent() const {
        // Simple heuristic: if content has non-printable chars, it's likely binary
        for (size_t i = 0; i < content_.length(); ++i) {
            unsigned char c = content_[i];
            if (c < 32 && c != '\n' && c != '\r' && c != '\t') {
                return false;
            }
        }
        return true;
    }

    void updateChecksum() {
        // Simple checksum (not cryptographic, just for change detection)
        checksum_ = 0;
        for (size_t i = 0; i < content_.length(); ++i) {
            checksum_ = checksum_ * 31 + static_cast<unsigned char>(content_[i]);
        }
    }

    static bool fileExists(const std::string &path) {
        std::ifstream f(path.c_str());
        return f.good();
    }

    static std::string escapeJson(const std::string &str) {
        std::string escaped;
        for (size_t i = 0; i < str.length(); ++i) {
            char c = str[i];
            switch (c) {
                case '"': escaped += "\\\""; break;
                case '\\': escaped += "\\\\"; break;
                case '\n': escaped += "\\n"; break;
                case '\r': escaped += "\\r"; break;
                case '\t': escaped += "\\t"; break;
                default: escaped += c; break;
            }
        }
        return escaped;
    }
};

// Operator overload implementation
inline std::ostream &operator<<(std::ostream &os, const File &f) {
    const char* stateNames[] = {"UNLOADED", "LOADED", "MODIFIED", "DIRTY", "ERROR"};
    const char* typeNames[] = {"UNKNOWN", "TEXT", "CONFIG", "BINARY", "SCRIPT", "DATA"};
    
    os << "File(path: \"" << f.getPath() << "\""
       << ", state: " << stateNames[f.getState()]
       << ", type: " << typeNames[f.getType()]
       << ", size: " << f.getFileSize() << " bytes";
    
    if (!f.getDescription().empty()) {
        os << ", desc: \"" << f.getDescription() << "\"";
    }
    
    const std::vector<std::string> &tags = f.getTags();
    if (!tags.empty()) {
        os << ", tags: [";
        for (size_t i = 0; i < tags.size(); ++i) {
            os << "\"" << tags[i] << "\"";
            if (i < tags.size() - 1) os << ", ";
        }
        os << "]";
    }
    
    os << ")";
    return os;
}

#endif // FILE_HPP
