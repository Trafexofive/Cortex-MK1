# Auto-Load Manifests Feature

The manifest ingestion service now supports auto-loading manifests on startup.

## Configuration

Edit `/manifests/autoload.yml` to specify which manifests should be loaded automatically when the stack starts.

## Usage

```yaml
# manifests/autoload.yml
tools:
  - "../test_against_manifest/tools/simple/calculator/tool.yml"
  - "tools/sys_info/tool.yml"

relics:
  - "../test_against_manifest/relics/simple/kv_store/relic.yml"

agents:
  - "../test_against_manifest/agents/simple/assistant/agent.yml"
  - "../test_against_manifest/agents/complex/data_processor/agent.yml"

workflows:
  - "../test_against_manifest/workflows/simple/data_pipeline/workflow.yml"
```

## Settings

In `services/manifest_ingestion/settings.yml`:

```yaml
performance:
  preload:
    auto_load:
      enabled: true  # Enable/disable auto-load
      manifest_list_file: "/app/manifests/autoload.yml"  # Path to autoload file
      fail_on_error: false  # Continue even if some manifests fail
      load_dependencies: true  # Auto-load imported dependencies
```

## Features

- **Automatic dependency resolution**: Imported manifests are loaded automatically
- **Relative path support**: Paths resolved from manifests/ directory
- **Error tolerance**: Failed loads don't stop startup (configurable)
- **Load order**: Manifests loaded in specified order
- **Circular dependency detection**: Prevents infinite loops

## Startup Flow

1. Service starts
2. Auto-load reads `autoload.yml`
3. Resolves all manifest paths
4. Loads each manifest (and its dependencies)
5. Logs summary of loaded manifests
6. Continues with hot-reload setup

## Example Output

```
🚀 Starting Manifest Ingestion Service...
📋 Auto-loading manifests from /app/manifests/autoload.yml
Loading tool: ../test_against_manifest/tools/simple/calculator/tool.yml
Loading tool: ../test_against_manifest/tools/simple/text_analyzer/tool.yml
Loading relic: ../test_against_manifest/relics/simple/kv_store/relic.yml
Loading agent: ../test_against_manifest/agents/simple/assistant/agent.yml
Loading agent: ../test_against_manifest/agents/complex/data_processor/agent.yml
✅ Auto-loaded 5 manifests: {'tools': 2, 'relics': 1, 'agents': 2, 'workflows': 0, 'failed': 0}
✅ Manifest Ingestion Service ready
```
