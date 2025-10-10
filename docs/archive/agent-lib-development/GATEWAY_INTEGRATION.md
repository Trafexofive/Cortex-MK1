# LLM Gateway Integration for Agent-Lib

**Status**: ✅ Gateway Running  
**Gateway URL**: http://localhost:8081  
**Providers**: gemini, groq, ollama

## Current Situation

The agent-lib C++ client (`MiniGemini.cpp`) directly calls Gemini APIs, which has issues:
- ❌ HTTP 400 errors with `gemini-1.5-pro` due to API versioning
- ❌ Different systemInstruction formats between v1 and v1beta
- ❌ No automatic failover or retry logic
- ❌ Hardcoded to single provider

## Solution: Use LLM Gateway

The Python LLM Gateway (already running in Docker) properly handles:
- ✅ All Gemini model versions (1.5-pro, 2.0-flash, etc.)
- ✅ Multiple providers (Gemini, Groq, Ollama)
- ✅ Automatic failover
- ✅ Rate limiting
- ✅ Circuit breakers
- ✅ Streaming support

## Gateway API

### Completion Endpoint
```http
POST http://localhost:8081/completion
Content-Type: application/json

{
  "messages": [{"role": "user", "content": "Hello"}],
  "provider": "gemini",
  "model": "gemini-1.5-pro",
  "stream": true/false
}
```

### Response
```json
{
  "content": "Response text here",
  "provider": "gemini",
  "model": "gemini-1.5-pro",
  "usage": {...}
}
```

### Streaming Response
```
data: {"content": "chunk1", "done": false}
data: {"content": "chunk2", "done": false}
data: {"content": "", "done": true}
```

## Implementation Options

### Option 1: Create GatewayClient Class (Recommended)
Create a new `GatewayClient.hpp/cpp` that implements `LLMClient` interface:

```cpp
class GatewayClient : public LLMClient {
public:
    GatewayClient(const std::string& gatewayUrl = "http://localhost:8081");
    
    std::string generate(const std::string& prompt) override;
    void generateStream(const std::string& prompt, StreamCallback callback) override;
    
    void setProvider(const std::string& provider); // gemini, groq, ollama
    void setModel(const std::string& model) override;
    
private:
    std::string m_gatewayUrl;
    std::string m_provider;
    std::string m_model;
    
    std::string performRequest(const std::string& endpoint, const std::string& payload);
};
```

### Option 2: Add Gateway Mode to MiniGemini
Add a flag to MiniGemini to use gateway instead of direct API:

```cpp
class MiniGemini : public LLMClient {
    bool m_useGateway = false;
    std::string m_gatewayUrl = "http://localhost:8081";
    
    void setUseGateway(bool use, const std::string& url = "");
};
```

### Option 3: Environment Variable Override
Simplest - check for `LLM_GATEWAY_URL` env var:

```cpp
MiniGemini::MiniGemini() {
    const char* gatewayUrl = std::getenv("LLM_GATEWAY_URL");
    if (gatewayUrl && gatewayUrl[0] != '\0') {
        m_useGateway = true;
        m_gatewayUrl = gatewayUrl;
    }
}
```

## Quick Fix (Option 3)

The fastest way to make agent-lib work is:

1. Set environment variable:
   ```bash
   export LLM_GATEWAY_URL=http://localhost:8081
   ```

2. Modify `MiniGemini::generate()` to check for gateway URL:
   ```cpp
   std::string MiniGemini::generate(const std::string& prompt) {
       const char* gatewayUrl = std::getenv("LLM_GATEWAY_URL");
       if (gatewayUrl && gatewayUrl[0] != '\0') {
           return generateViaGateway(prompt, gatewayUrl);
       }
       // ... existing direct API code
   }
   ```

3. Same for `generateStream()`

## Benefits

- ✅ Works with ALL Gemini models (no versioning issues)
- ✅ Can switch providers easily (gemini, groq, ollama)
- ✅ Automatic failover if one provider is down
- ✅ Better error handling
- ✅ Production-ready (rate limiting, circuit breakers)
- ✅ No changes to agent manifests needed
- ✅ Can use both gateway and direct API (based on env var)

## Testing

Once implemented:

```bash
# Start gateway (already running)
make up STACK=core

# Set gateway URL
export LLM_GATEWAY_URL=http://localhost:8081

# Run agent-bin
cd services/agent-lib
./agent-bin -l ../../manifests/agents/research_orchestrator/agent.yml
```

Should work perfectly with gemini-1.5-pro!

## Next Steps

1. Implement Option 3 (env var gateway override) - simplest, fastest
2. Test with research_orchestrator agent
3. If works well, can create dedicated GatewayClient class later
4. Update documentation

---

**The Great Work continues...**
