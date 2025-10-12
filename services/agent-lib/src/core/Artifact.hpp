#ifndef ARTIFACT_HPP
#define ARTIFACT_HPP

#include <algorithm>
#include <cstddef>
#include <ctime>
#include <fstream>
#include <iostream>
#include <map>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>
#include <sys/stat.h>

// Forward declaration
class Artifact;
std::ostream &operator<<(std::ostream &os, const Artifact &a);

class Artifact {
public:
    // Artifact states for agent lifecycle management
    enum State {
        STATE_CREATED,
        STATE_LOADED,
        STATE_MODIFIED,
        STATE_PERSISTED,
        STATE_DIRTY,
        STATE_ARCHIVED,
        STATE_ERROR
    };

    // Artifact types for agent classification and handling
    enum Type {
        TYPE_UNKNOWN,
        TYPE_TEXT,
        TYPE_CODE,
        TYPE_CONFIG,
        TYPE_DATA,
        TYPE_BINARY,
        TYPE_DOCUMENT,
        TYPE_TEMPLATE,
        TYPE_SCRIPT,
        TYPE_LOG,
        TYPE_EPHEMERAL
    };

    // Priority levels for agent task scheduling
    enum Priority {
        PRIORITY_LOW = 0,
        PRIORITY_NORMAL = 1,
        PRIORITY_HIGH = 2,
        PRIORITY_CRITICAL = 3
    };

    // Default constructor
    Artifact() : id_(""), name_(""), content_(""), description_(""),
                 state_(STATE_CREATED), type_(TYPE_UNKNOWN), priority_(PRIORITY_NORMAL),
                 created_time_(std::time(0)), modified_time_(std::time(0)),
                 access_count_(0), version_(1), checksum_(0), max_size_(0) {}

    // Constructor with ID and type
    Artifact(const std::string &id, Type type = TYPE_UNKNOWN) 
        : id_(id), name_(id), content_(""), description_(""),
          state_(STATE_CREATED), type_(type), priority_(PRIORITY_NORMAL),
          created_time_(std::time(0)), modified_time_(std::time(0)),
          access_count_(0), version_(1), checksum_(0), max_size_(0) {}

    // Constructor from file
    explicit Artifact(const std::string &filepath, const std::string &id = "") 
        : content_(""), description_(""), state_(STATE_CREATED), 
          priority_(PRIORITY_NORMAL), created_time_(std::time(0)), 
          modified_time_(std::time(0)), access_count_(0), version_(1), 
          checksum_(0), max_size_(0) {
        
        id_ = id.empty() ? generateIdFromPath(filepath) : id;
        name_ = getBasenameFromPath(filepath);
        source_path_ = filepath;
        type_ = detectTypeFromPath(filepath);
        loadFromFile(filepath);
    }

    ~Artifact() {}

    // --- Core accessors ---
    const std::string &getId() const { return id_; }
    const std::string &getName() const { return name_; }
    const std::string &getContent() const { access_count_++; return content_; }
    const std::string &getDescription() const { return description_; }
    const std::string &getSourcePath() const { return source_path_; }
    const std::vector<std::string> &getTags() const { return tags_; }
    const std::map<std::string, std::string> &getMetadata() const { return metadata_; }
    
    State getState() const { return state_; }
    Type getType() const { return type_; }
    Priority getPriority() const { return priority_; }
    
    time_t getCreatedTime() const { return created_time_; }
    time_t getModifiedTime() const { return modified_time_; }
    size_t getAccessCount() const { return access_count_; }
    unsigned int getVersion() const { return version_; }
    unsigned long getChecksum() const { return checksum_; }
    size_t getSize() const { return content_.length(); }
    size_t getMaxSize() const { return max_size_; }

    // --- Agent-friendly state queries ---
    bool isValid() const { return !id_.empty() && state_ != STATE_ERROR; }
    bool isDirty() const { return state_ == STATE_DIRTY || state_ == STATE_MODIFIED; }
    bool isEphemeral() const { return type_ == TYPE_EPHEMERAL; }
    bool isArchived() const { return state_ == STATE_ARCHIVED; }
    bool hasError() const { return state_ == STATE_ERROR; }
    bool isEmpty() const { return content_.empty(); }
    bool hasSource() const { return !source_path_.empty(); }
    bool exceedsMaxSize() const { return max_size_ > 0 && getSize() > max_size_; }

    // --- Mutators with automatic state management ---
    void setName(const std::string &name) { 
        if (name_ != name) {
            name_ = name; 
            touch();
        }
    }
    
    void setContent(const std::string &content) { 
        if (content_ != content) {
            content_ = content; 
            updateChecksum();
            incrementVersion();
            setState(STATE_MODIFIED);
        }
    }
    
    void appendContent(const std::string &content) {
        if (!content.empty()) {
            content_ += content;
            updateChecksum();
            incrementVersion();
            setState(STATE_MODIFIED);
        }
    }
    
    void setDescription(const std::string &desc) { 
        if (description_ != desc) {
            description_ = desc; 
            touch();
        }
    }
    
    void setType(Type type) { 
        if (type_ != type) {
            type_ = type; 
            touch();
        }
    }
    
    void setPriority(Priority priority) { 
        if (priority_ != priority) {
            priority_ = priority; 
            touch();
        }
    }
    
    void setMaxSize(size_t max_size) { max_size_ = max_size; }
    void setSourcePath(const std::string &path) { source_path_ = path; }

    // --- Tag management ---
    void addTag(const std::string &tag) {
        if (!tag.empty() && !hasTag(tag)) {
            tags_.push_back(tag);
            touch();
        }
    }

    void removeTags(const std::string &tag) {
        std::vector<std::string>::iterator new_end =
            std::remove(tags_.begin(), tags_.end(), tag);
        if (new_end != tags_.end()) {
            tags_.erase(new_end, tags_.end());
            touch();
        }
    }

    void clearTags() { 
        if (!tags_.empty()) {
            tags_.clear(); 
            touch();
        }
    }

    bool hasTag(const std::string &tag) const {
        return std::find(tags_.begin(), tags_.end(), tag) != tags_.end();
    }

    // --- Metadata management ---
    void setMetadata(const std::string &key, const std::string &value) {
        if (metadata_[key] != value) {
            metadata_[key] = value;
            touch();
        }
    }

    std::string getMetadata(const std::string &key, const std::string &default_val = "") const {
        std::map<std::string, std::string>::const_iterator it = metadata_.find(key);
        return (it != metadata_.end()) ? it->second : default_val;
    }

    bool hasMetadata(const std::string &key) const {
        return metadata_.find(key) != metadata_.end();
    }

    void removeMetadata(const std::string &key) {
        std::map<std::string, std::string>::iterator it = metadata_.find(key);
        if (it != metadata_.end()) {
            metadata_.erase(it);
            touch();
        }
    }

    // --- Content operations ---
    bool loadFromFile(const std::string &filepath) {
        try {
            std::ifstream file(filepath.c_str());
            if (!file.is_open()) {
                setState(STATE_ERROR);
                return false;
            }

            std::ostringstream buffer;
            buffer << file.rdbuf();
            
            content_ = buffer.str();
            source_path_ = filepath;
            updateChecksum();
            setState(STATE_LOADED);
            
            return true;
        } catch (const std::exception &) {
            setState(STATE_ERROR);
            return false;
        }
    }

    bool saveToFile(const std::string &filepath = "") const {
        std::string path = filepath.empty() ? source_path_ : filepath;
        if (path.empty()) return false;

        try {
            std::ofstream file(path.c_str());
            if (!file.is_open()) return false;
            
            file << content_;
            if (filepath.empty() == false) {
                const_cast<Artifact*>(this)->source_path_ = filepath;
            }
            const_cast<Artifact*>(this)->setState(STATE_PERSISTED);
            
            return true;
        } catch (const std::exception &) {
            const_cast<Artifact*>(this)->setState(STATE_ERROR);
            return false;
        }
    }

    bool backup(const std::string &suffix = ".bak") const {
        if (source_path_.empty()) return false;
        return saveToFile(source_path_ + suffix);
    }

    // --- Content analysis ---
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

    // --- Search and manipulation ---
    bool contains(const std::string &needle) const {
        return content_.find(needle) != std::string::npos;
    }

    std::vector<size_t> findAll(const std::string &needle) const {
        std::vector<size_t> positions;
        size_t pos = 0;
        
        while ((pos = content_.find(needle, pos)) != std::string::npos) {
            positions.push_back(pos);
            pos += needle.length();
        }
        return positions;
    }

    size_t replace(const std::string &from, const std::string &to) {
        if (from.empty()) return 0;
        
        size_t count = 0;
        size_t pos = 0;
        
        while ((pos = content_.find(from, pos)) != std::string::npos) {
            content_.replace(pos, from.length(), to);
            pos += to.length();
            count++;
        }
        
        if (count > 0) {
            updateChecksum();
            incrementVersion();
            setState(STATE_MODIFIED);
        }
        
        return count;
    }

    // --- Agent lifecycle management ---
    void archive() { setState(STATE_ARCHIVED); }
    void restore() { setState(isDirty() ? STATE_MODIFIED : STATE_LOADED); }
    void markClean() { setState(STATE_PERSISTED); }
    void markDirty() { setState(STATE_DIRTY); }
    void reset() { 
        content_.clear(); 
        tags_.clear(); 
        metadata_.clear();
        setState(STATE_CREATED);
        version_ = 1;
        updateChecksum();
    }

    // --- Serialization for agent communication ---
    std::string toJson() const {
        std::ostringstream json;
        json << "{"
             << "\"id\":\"" << escapeJson(id_) << "\","
             << "\"name\":\"" << escapeJson(name_) << "\","
             << "\"description\":\"" << escapeJson(description_) << "\","
             << "\"state\":" << static_cast<int>(state_) << ","
             << "\"type\":" << static_cast<int>(type_) << ","
             << "\"priority\":" << static_cast<int>(priority_) << ","
             << "\"size\":" << getSize() << ","
             << "\"version\":" << version_ << ","
             << "\"created\":" << created_time_ << ","
             << "\"modified\":" << modified_time_ << ","
             << "\"access_count\":" << access_count_ << ","
             << "\"checksum\":" << checksum_ << ","
             << "\"has_source\":" << (hasSource() ? "true" : "false") << ","
             << "\"tags\":[";
        
        for (size_t i = 0; i < tags_.size(); ++i) {
            json << "\"" << escapeJson(tags_[i]) << "\"";
            if (i < tags_.size() - 1) json << ",";
        }
        
        json << "],\"metadata\":{";
        std::map<std::string, std::string>::const_iterator it = metadata_.begin();
        while (it != metadata_.end()) {
            json << "\"" << escapeJson(it->first) << "\":\"" 
                 << escapeJson(it->second) << "\"";
            ++it;
            if (it != metadata_.end()) json << ",";
        }
        json << "}}";
        
        return json.str();
    }

    // Clone artifact with new ID
    Artifact clone(const std::string &new_id = "") const {
        Artifact copy;
        copy.id_ = new_id.empty() ? (id_ + "_copy") : new_id;
        copy.name_ = name_ + "_copy";
        copy.content_ = content_;
        copy.description_ = description_;
        copy.tags_ = tags_;
        copy.metadata_ = metadata_;
        copy.type_ = type_;
        copy.priority_ = priority_;
        copy.created_time_ = std::time(0);
        copy.modified_time_ = copy.created_time_;
        copy.state_ = STATE_CREATED;
        copy.version_ = 1;
        copy.max_size_ = max_size_;
        copy.updateChecksum();
        
        return copy;
    }

    // Friend function
    friend std::ostream &operator<<(std::ostream &os, const Artifact &a);

private:
    // Core identity and content
    std::string id_;
    std::string name_;
    std::string content_;
    std::string description_;
    std::string source_path_;
    
    // Classification and metadata
    std::vector<std::string> tags_;
    std::map<std::string, std::string> metadata_;
    State state_;
    Type type_;
    Priority priority_;
    
    // Lifecycle tracking
    time_t created_time_;
    time_t modified_time_;
    mutable size_t access_count_;
    unsigned int version_;
    unsigned long checksum_;
    size_t max_size_;

    // Helper methods
    void setState(State new_state) {
        if (state_ != new_state) {
            state_ = new_state;
            touch();
        }
    }

    void touch() {
        modified_time_ = std::time(0);
    }

    void incrementVersion() {
        version_++;
        touch();
    }

    void updateChecksum() {
        checksum_ = 0;
        for (size_t i = 0; i < content_.length(); ++i) {
            checksum_ = checksum_ * 31 + static_cast<unsigned char>(content_[i]);
        }
    }

    static std::string generateIdFromPath(const std::string &path) {
        std::string basename = getBasenameFromPath(path);
        // Simple ID generation - in practice you might want something more robust
        return basename + "_" + std::to_string(std::time(0));
    }

    static std::string getBasenameFromPath(const std::string &path) {
        size_t pos = path.find_last_of("/\\");
        return (pos == std::string::npos) ? path : path.substr(pos + 1);
    }

    static Type detectTypeFromPath(const std::string &path) {
        std::string basename = getBasenameFromPath(path);
        size_t pos = basename.find_last_of('.');
        if (pos == std::string::npos) return TYPE_UNKNOWN;
        
        std::string ext = basename.substr(pos + 1);
        std::transform(ext.begin(), ext.end(), ext.begin(), ::tolower);
        
        if (ext == "cpp" || ext == "c" || ext == "h" || ext == "hpp" || 
            ext == "py" || ext == "sh" || ext == "js") {
            return TYPE_CODE;
        } else if (ext == "conf" || ext == "cfg" || ext == "ini" || 
                   ext == "yaml" || ext == "json" || ext == "xml") {
            return TYPE_CONFIG;
        } else if (ext == "txt" || ext == "md" || ext == "rst") {
            return TYPE_TEXT;
        } else if (ext == "csv" || ext == "tsv" || ext == "sql") {
            return TYPE_DATA;
        } else if (ext == "log") {
            return TYPE_LOG;
        }
        
        return TYPE_UNKNOWN;
    }

    static std::string escapeJson(const std::string &str) {
        std::string escaped;
        escaped.reserve(str.length() * 2);
        
        for (size_t i = 0; i < str.length(); ++i) {
            char c = str[i];
            switch (c) {
                case '"': escaped += "\\\""; break;
                case '\\': escaped += "\\\\"; break;
                case '\n': escaped += "\\n"; break;
                case '\r': escaped += "\\r"; break;
                case '\t': escaped += "\\t"; break;
                case '\b': escaped += "\\b"; break;
                case '\f': escaped += "\\f"; break;
                default: 
                    if (c < 32) {
                        escaped += "\\u";
                        escaped += "0000";
                        // Simple hex conversion for control chars
                    } else {
                        escaped += c;
                    }
                    break;
            }
        }
        return escaped;
    }
};

// Stream operator implementation
inline std::ostream &operator<<(std::ostream &os, const Artifact &a) {
    const char* stateNames[] = {"CREATED", "LOADED", "MODIFIED", "PERSISTED", 
                                "DIRTY", "ARCHIVED", "ERROR"};
    const char* typeNames[] = {"UNKNOWN", "TEXT", "CODE", "CONFIG", "DATA", 
                               "BINARY", "DOCUMENT", "TEMPLATE", "SCRIPT", "LOG", "EPHEMERAL"};
    const char* priorityNames[] = {"LOW", "NORMAL", "HIGH", "CRITICAL"};
    
    os << "Artifact(id: \"" << a.getId() << "\""
       << ", name: \"" << a.getName() << "\""
       << ", state: " << stateNames[a.getState()]
       << ", type: " << typeNames[a.getType()]
       << ", priority: " << priorityNames[a.getPriority()]
       << ", size: " << a.getSize() << " bytes"
       << ", v" << a.getVersion();
    
    if (!a.getDescription().empty()) {
        os << ", desc: \"" << a.getDescription() << "\"";
    }
    
    if (a.hasSource()) {
        os << ", source: \"" << a.getSourcePath() << "\"";
    }
    
    const std::vector<std::string> &tags = a.getTags();
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

#endif // ARTIFACT_HPP
