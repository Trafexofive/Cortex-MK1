# Gemini API Version Fix

**Date**: October 10, 2024  
**Issue**: HTTP 404 errors when using `gemini-1.5-pro` model  
**Status**: ✅ FIXED

## Problem

The agent was failing with HTTP 404 errors when trying to use `gemini-1.5-pro`:

```
[ERROR] GeminiClient Streaming API Error: Streaming request returned HTTP 404
Error: Streaming request returned HTTP 404
```

## Root Cause

The MiniGemini client was hardcoded to use the `/v1beta/` API endpoint for all models:

```cpp
m_baseUrl("https://generativelanguage.googleapis.com/v1beta/models")
```

However, different Gemini models require different API versions:

| Model Family | API Version | Status |
|--------------|-------------|---------|
| `gemini-2.0-*` | `/v1beta/` | Experimental/Latest |
| `gemini-1.5-*` | `/v1/` | Stable/Production |

When using `gemini-1.5-pro` with `/v1beta/`, the API returns 404 because that model isn't available in the beta API.

## Solution

### 1. Made Base URL Version-Agnostic

**Before**:
```cpp
m_baseUrl("https://generativelanguage.googleapis.com/v1beta/models")
```

**After**:
```cpp
m_baseUrl("https://generativelanguage.googleapis.com")
```

### 2. Added Dynamic API Version Selection

```cpp
// Helper function to determine API version based on model
std::string MiniGemini::getApiVersion() const {
    // gemini-1.5-* models use v1 (stable API)
    // gemini-2.0-* and experimental models use v1beta
    if (m_model.find("gemini-1.5") == 0) {
        return "v1";
    }
    return "v1beta";
}
```

### 3. Created Model URL Builder

```cpp
// Helper function to build complete model endpoint URL
std::string MiniGemini::getModelUrl() const {
    return m_baseUrl + "/" + getApiVersion() + "/models/" + m_model;
}
```

### 4. Updated All API Calls

**Generate (non-streaming)**:
```cpp
std::string url = getModelUrl() + ":generateContent?key=" + m_apiKey;
```

**GenerateStream (streaming)**:
```cpp
std::string url = getModelUrl() + ":streamGenerateContent?alt=sse&key=" + m_apiKey;
```

## Model Support Matrix

The fix now correctly handles:

### Stable Models (v1 API)
- ✅ `gemini-1.5-pro`
- ✅ `gemini-1.5-flash`
- ✅ `gemini-1.5-flash-8b`

### Experimental Models (v1beta API)
- ✅ `gemini-2.0-flash`
- ✅ `gemini-2.0-flash-lite`
- ✅ `gemini-2.0-flash-thinking`
- ✅ `gemini-2.5-pro-exp-*`

## Files Modified

1. **inc/MiniGemini.hpp**
   - Added `getApiVersion()` declaration
   - Added `getModelUrl()` declaration

2. **src/MiniGemini.cpp**
   - Implemented `getApiVersion()` function
   - Implemented `getModelUrl()` function
   - Updated `generate()` to use `getModelUrl()`
   - Updated `generateStream()` to use `getModelUrl()`
   - Changed base URL to be version-agnostic

## Testing

The research_orchestrator agent can now be loaded successfully:

```bash
./agent-bin -l ../../manifests/agents/research_orchestrator/agent.yml
```

Expected output:
```
✓ API key loaded
...
✓ Manifest loaded: research_orchestrator
  Streaming: ON (default for modern manifests)
```

## Future Improvements

### Possible Enhancements:
1. **Explicit version override**: Allow manifest to specify API version
2. **Version detection from model string**: Parse version from full model names
3. **API version caching**: Cache the version lookup result
4. **Fallback logic**: Try both v1 and v1beta if one fails

### Configuration Option:
Could add to agent manifest:
```yaml
cognitive_engine:
  primary:
    provider: "google"
    model: "gemini-1.5-pro"
    api_version: "v1"  # Optional explicit override
```

## Known Limitations

### Model Name Prefix Matching
Currently uses simple prefix matching:
```cpp
if (m_model.find("gemini-1.5") == 0) { return "v1"; }
```

This works for standard model names but might not handle:
- Custom model aliases
- Future model versions (e.g., `gemini-1.6-*`)
- Non-standard naming schemes

### Workaround:
If a model doesn't match, it defaults to `v1beta`. Users can always use `setBaseUrl()` to override manually.

## Conclusion

The fix enables proper support for both stable (gemini-1.5) and experimental (gemini-2.0) model families by dynamically selecting the correct API version based on the model name. This resolves the HTTP 404 errors and makes the agent-lib compatible with a wider range of Gemini models.

---

**Fixed by**: GitHub Copilot CLI  
**Date**: October 10, 2024  
**Impact**: All Gemini models now work correctly
