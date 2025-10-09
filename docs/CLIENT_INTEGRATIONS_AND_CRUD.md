# Client Integrations & CRUD Operations
## Complete API Design for Cortex-Prime MK1

**Version:** 1.0  
**Status:** Design Specification  
**Author:** PRAETORIAN_CHIMERA  
**Date:** 2025-01-15

---

## Table of Contents

1. [CRUD Design Philosophy](#crud-design-philosophy)
2. [RESTful API Specification](#restful-api-specification)
3. [Web Client Architecture](#web-client-architecture)
4. [CLI Client Design](#cli-client-design)
5. [SDK Libraries](#sdk-libraries)
6. [Real-Time Communication](#real-time-communication)
7. [Implementation Roadmap](#implementation-roadmap)

---

## CRUD Design Philosophy

### Current Gap Analysis

**What Exists:**
- ✅ READ operations via manifest_ingestion API
- ✅ Basic web client (B-Line) for chat
- ✅ Shell script for HTTP calls
- ⚠️ No CREATE operations (upload manifest via API works, but no UI)
- ❌ No UPDATE operations (hot-reload only via filesystem)
- ❌ No DELETE operations
- ❌ No proper CLI tool
- ❌ No SDK libraries

**What's Needed:**
- Full CRUD for all manifest types (Agents, Tools, Relics, Workflows, Monuments)
- Full CRUD for executions (start, monitor, cancel, delete)
- Full CRUD for deployments (Relics/Monuments lifecycle)
- Web UI with manifest editor
- CLI tool (`cortex` command)
- Python/JS SDK libraries

### Design Principles

**RESTful & Resource-Oriented**
- Every entity (manifest, execution, deployment) is a REST resource
- Consistent URL patterns: `/api/v1/{resource}/{id}`
- Standard HTTP methods: GET, POST, PUT, PATCH, DELETE
- Idempotent operations where possible

**Multi-Client Support**
- Same API serves Web UI, CLI, and SDK clients
- Authentication/authorization consistent across clients
- WebSocket for real-time updates

**Declarative Operations**
- Creating a manifest stores the declaration
- Deploying a manifest instantiates it
- Separation of declaration vs. instantiation

---

## RESTful API Specification

### API Versioning Strategy

```
/api/v1/          # Stable, production API
/api/v2/          # Future breaking changes
/api/unstable/    # Experimental features
```

### Complete CRUD Matrix

#### Manifests (Declaration)

**Base Path:** `/api/v1/manifests`

| Resource | Method | Endpoint | Description |
|----------|--------|----------|-------------|
| **Agents** | GET | `/manifests/agents` | List all agent manifests |
| | GET | `/manifests/agents/{name}` | Get specific agent manifest |
| | POST | `/manifests/agents` | Create new agent manifest |
| | PUT | `/manifests/agents/{name}` | Replace agent manifest |
| | PATCH | `/manifests/agents/{name}` | Update agent manifest (partial) |
| | DELETE | `/manifests/agents/{name}` | Delete agent manifest |
| **Tools** | GET | `/manifests/tools` | List all tool manifests |
| | GET | `/manifests/tools/{name}` | Get specific tool manifest |
| | POST | `/manifests/tools` | Create new tool manifest |
| | PUT | `/manifests/tools/{name}` | Replace tool manifest |
| | PATCH | `/manifests/tools/{name}` | Update tool manifest |
| | DELETE | `/manifests/tools/{name}` | Delete tool manifest |
| **Relics** | GET | `/manifests/relics` | List all relic manifests |
| | GET | `/manifests/relics/{name}` | Get specific relic manifest |
| | POST | `/manifests/relics` | Create new relic manifest |
| | PUT | `/manifests/relics/{name}` | Replace relic manifest |
| | PATCH | `/manifests/relics/{name}` | Update relic manifest |
| | DELETE | `/manifests/relics/{name}` | Delete relic manifest |
| **Workflows** | GET | `/manifests/workflows` | List all workflow manifests |
| | GET | `/manifests/workflows/{name}` | Get specific workflow manifest |
| | POST | `/manifests/workflows` | Create new workflow manifest |
| | PUT | `/manifests/workflows/{name}` | Replace workflow manifest |
| | PATCH | `/manifests/workflows/{name}` | Update workflow manifest |
| | DELETE | `/manifests/workflows/{name}` | Delete workflow manifest |
| **Monuments** | GET | `/manifests/monuments` | List all monument manifests |
| | GET | `/manifests/monuments/{name}` | Get specific monument manifest |
| | POST | `/manifests/monuments` | Create new monument manifest |
| | PUT | `/manifests/monuments/{name}` | Replace monument manifest |
| | PATCH | `/manifests/monuments/{name}` | Update monument manifest |
| | DELETE | `/manifests/monuments/{name}` | Delete monument manifest |

**Query Parameters:**
- `?state=stable|unstable|experimental` - Filter by state
- `?author={name}` - Filter by author
- `?tags={tag1,tag2}` - Filter by tags
- `?search={query}` - Full-text search
- `?limit=50&offset=0` - Pagination

**Example Requests:**

```bash
# CREATE - Upload new agent manifest
curl -X POST http://localhost:8082/api/v1/manifests/agents \
  -H "Content-Type: application/yaml" \
  --data-binary @manifests/agents/my_agent/agent.yml

# READ - Get agent manifest
curl http://localhost:8082/api/v1/manifests/agents/my_agent

# UPDATE - Patch specific field
curl -X PATCH http://localhost:8082/api/v1/manifests/agents/my_agent \
  -H "Content-Type: application/json" \
  -d '{"cognitive_engine": {"parameters": {"temperature": 0.5}}}'

# DELETE - Remove agent manifest
curl -X DELETE http://localhost:8082/api/v1/manifests/agents/my_agent
```

#### Executions (Runtime)

**Base Path:** `/api/v1/executions`

| Resource | Method | Endpoint | Description |
|----------|--------|----------|-------------|
| **Tool Executions** | POST | `/executions/tools` | Execute a tool |
| | GET | `/executions/tools/{id}` | Get tool execution status |
| | DELETE | `/executions/tools/{id}` | Cancel tool execution |
| **Agent Executions** | POST | `/executions/agents` | Start agent session |
| | GET | `/executions/agents/{id}` | Get agent session |
| | POST | `/executions/agents/{id}/messages` | Send message to agent |
| | DELETE | `/executions/agents/{id}` | End agent session |
| **Workflow Executions** | POST | `/executions/workflows` | Start workflow |
| | GET | `/executions/workflows/{id}` | Get workflow status |
| | POST | `/executions/workflows/{id}/pause` | Pause workflow |
| | POST | `/executions/workflows/{id}/resume` | Resume workflow |
| | DELETE | `/executions/workflows/{id}` | Cancel workflow |
| **Execution History** | GET | `/executions` | List all executions |
| | GET | `/executions/{id}` | Get execution by ID |
| | GET | `/executions/{id}/logs` | Get execution logs |
| | DELETE | `/executions/{id}` | Delete execution record |

**Example Requests:**

```bash
# Execute tool
curl -X POST http://localhost:8083/api/v1/executions/tools \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "calculator",
    "parameters": {"operation": "add", "a": 5, "b": 3}
  }'

# Start agent session
curl -X POST http://localhost:8083/api/v1/executions/agents \
  -d '{
    "agent": "assistant",
    "config": {"temperature": 0.7}
  }'

# Send message to agent
curl -X POST http://localhost:8083/api/v1/executions/agents/abc123/messages \
  -d '{
    "message": "What is the weather today?"
  }'

# Get workflow status
curl http://localhost:8083/api/v1/executions/workflows/xyz789
```

#### Deployments (Infrastructure)

**Base Path:** `/api/v1/deployments`

| Resource | Method | Endpoint | Description |
|----------|--------|----------|-------------|
| **Relics** | POST | `/deployments/relics` | Deploy relic service |
| | GET | `/deployments/relics` | List deployed relics |
| | GET | `/deployments/relics/{name}` | Get relic deployment status |
| | POST | `/deployments/relics/{name}/start` | Start relic |
| | POST | `/deployments/relics/{name}/stop` | Stop relic |
| | POST | `/deployments/relics/{name}/restart` | Restart relic |
| | DELETE | `/deployments/relics/{name}` | Undeploy relic |
| **Monuments** | POST | `/deployments/monuments` | Deploy monument stack |
| | GET | `/deployments/monuments` | List deployed monuments |
| | GET | `/deployments/monuments/{name}` | Get monument status |
| | POST | `/deployments/monuments/{name}/start` | Start monument |
| | POST | `/deployments/monuments/{name}/stop` | Stop monument |
| | POST | `/deployments/monuments/{name}/scale` | Scale monument services |
| | DELETE | `/deployments/monuments/{name}` | Undeploy monument |

**Example Requests:**

```bash
# Deploy relic
curl -X POST http://localhost:8084/api/v1/deployments/relics \
  -d '{
    "relic": "kv_store",
    "environment": "production"
  }'

# Get relic status
curl http://localhost:8084/api/v1/deployments/relics/kv_store

# Deploy monument
curl -X POST http://localhost:8084/api/v1/deployments/monuments \
  -d '{
    "monument": "code_forge",
    "environment": "staging",
    "scale": {
      "ci_runner": 3
    }
  }'

# Scale monument service
curl -X POST http://localhost:8084/api/v1/deployments/monuments/code_forge/scale \
  -d '{
    "service": "ci_runner",
    "replicas": 5
  }'
```

#### System & Registry

**Base Path:** `/api/v1/system`

| Resource | Method | Endpoint | Description |
|----------|--------|----------|-------------|
| **Health** | GET | `/system/health` | Overall system health |
| | GET | `/system/services` | List all services |
| | GET | `/system/services/{name}/health` | Service health |
| **Registry** | GET | `/system/registry/status` | Registry statistics |
| | POST | `/system/registry/sync` | Sync with filesystem |
| | GET | `/system/registry/dependencies` | Dependency graph |
| | POST | `/system/registry/export` | Export registry |
| **Metrics** | GET | `/system/metrics` | Prometheus metrics |
| | GET | `/system/logs` | Aggregated logs |

---

## Web Client Architecture

### Current State: B-Line Chat Client

**Pros:**
- ✅ Simple, functional chat interface
- ✅ WebSocket streaming
- ✅ Voice integration

**Cons:**
- ❌ No manifest management
- ❌ No execution history
- ❌ No deployment controls
- ❌ Hardcoded to single agent

### Proposed: Cortex-Prime Web Console

**Tech Stack:**
- **Framework:** React + TypeScript (or Vue.js)
- **State Management:** Redux Toolkit / Zustand
- **UI Library:** Material-UI / Tailwind CSS
- **WebSocket:** Socket.IO / native WebSocket
- **Code Editor:** Monaco Editor (VS Code editor)
- **Visualization:** D3.js for dependency graphs

**Architecture:**

```
┌─────────────────────────────────────────────────────────────────┐
│                   Cortex-Prime Web Console                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  Navigation                                               │ │
│  │  [Dashboard] [Manifests] [Executions] [Deployments]      │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌─────────────┬──────────────────────────────────────────────┐│
│  │             │                                              ││
│  │  Sidebar    │           Main Content Area                 ││
│  │             │                                              ││
│  │ - Agents    │  ┌────────────────────────────────────────┐ ││
│  │ - Tools     │  │                                        │ ││
│  │ - Relics    │  │   Dynamic Content Based on Route       │ ││
│  │ - Workflows │  │                                        │ ││
│  │ - Monuments │  │   - Manifest Editor                    │ ││
│  │             │  │   - Execution Viewer                   │ ││
│  │ [+ New]     │  │   - Deployment Dashboard               │ ││
│  │             │  │   - Logs & Monitoring                  │ ││
│  │             │  │                                        │ ││
│  └─────────────┘  └────────────────────────────────────────┘ ││
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Page Breakdown

#### 1. Dashboard (/)

**Purpose:** System overview and quick actions

**Components:**
- System health status (all services)
- Recent executions (last 10)
- Active deployments
- Quick action buttons (Execute Agent, Deploy Relic, Create Manifest)
- Metrics charts (CPU, memory, execution count)

**API Calls:**
```javascript
GET /api/v1/system/health
GET /api/v1/executions?limit=10
GET /api/v1/deployments/relics
GET /api/v1/deployments/monuments
GET /api/v1/system/metrics
```

#### 2. Manifests (/manifests)

**Purpose:** Browse, create, edit, delete manifests

**Sub-Routes:**
- `/manifests/agents` - List all agents
- `/manifests/agents/:name` - View/edit agent
- `/manifests/agents/new` - Create new agent
- (Same for tools, relics, workflows, monuments)

**Components:**
- **Manifest List View:**
  - Table/grid of manifests
  - Filters (by type, state, author, tags)
  - Search bar
  - Action buttons (Edit, Delete, Clone, Execute/Deploy)
  
- **Manifest Editor:**
  - Monaco Editor with YAML syntax highlighting
  - Live validation (show errors as you type)
  - Preview pane (rendered manifest structure)
  - Dependency viewer (graph visualization)
  - Version history (future)
  - Save/Cancel/Delete buttons

**API Calls:**
```javascript
// List
GET /api/v1/manifests/agents

// View
GET /api/v1/manifests/agents/assistant

// Create
POST /api/v1/manifests/agents
Body: { name: "new_agent", ... }

// Update
PATCH /api/v1/manifests/agents/assistant
Body: { cognitive_engine: { ... } }

// Delete
DELETE /api/v1/manifests/agents/assistant
```

**Mock UI (React Component):**

```tsx
// ManifestEditor.tsx
import React, { useState, useEffect } from 'react';
import Editor from '@monaco-editor/react';
import { useParams, useNavigate } from 'react-router-dom';
import yaml from 'js-yaml';

interface ManifestEditorProps {
  manifestType: 'agents' | 'tools' | 'relics' | 'workflows' | 'monuments';
}

export const ManifestEditor: React.FC<ManifestEditorProps> = ({ manifestType }) => {
  const { name } = useParams();
  const navigate = useNavigate();
  const [content, setContent] = useState('');
  const [errors, setErrors] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  
  useEffect(() => {
    if (name) {
      // Load existing manifest
      fetch(`/api/v1/manifests/${manifestType}/${name}`)
        .then(res => res.json())
        .then(data => {
          setContent(yaml.dump(data));
        });
    }
  }, [manifestType, name]);
  
  const handleSave = async () => {
    setLoading(true);
    try {
      const manifest = yaml.load(content);
      const method = name ? 'PATCH' : 'POST';
      const url = name 
        ? `/api/v1/manifests/${manifestType}/${name}`
        : `/api/v1/manifests/${manifestType}`;
      
      const response = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(manifest)
      });
      
      if (response.ok) {
        navigate(`/manifests/${manifestType}`);
      } else {
        const error = await response.json();
        setErrors([error.detail]);
      }
    } catch (err) {
      setErrors([err.message]);
    } finally {
      setLoading(false);
    }
  };
  
  const handleValidate = async () => {
    try {
      const manifest = yaml.load(content);
      const response = await fetch('/api/v1/manifests/validate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(manifest)
      });
      
      const result = await response.json();
      setErrors(result.valid ? [] : result.errors);
    } catch (err) {
      setErrors([err.message]);
    }
  };
  
  return (
    <div className="manifest-editor">
      <div className="toolbar">
        <button onClick={handleValidate}>Validate</button>
        <button onClick={handleSave} disabled={loading}>
          {loading ? 'Saving...' : 'Save'}
        </button>
        <button onClick={() => navigate(-1)}>Cancel</button>
      </div>
      
      {errors.length > 0 && (
        <div className="errors">
          {errors.map((err, i) => <div key={i}>{err}</div>)}
        </div>
      )}
      
      <Editor
        height="80vh"
        defaultLanguage="yaml"
        value={content}
        onChange={setContent}
        options={{
          minimap: { enabled: false },
          fontSize: 14,
          tabSize: 2
        }}
      />
    </div>
  );
};
```

#### 3. Executions (/executions)

**Purpose:** Monitor and manage running/past executions

**Sub-Routes:**
- `/executions` - List all executions
- `/executions/:id` - View execution details

**Components:**
- **Execution List:**
  - Table with columns: ID, Type, Entity, Status, Started, Duration
  - Filters (by type, status, date range)
  - Real-time status updates (WebSocket)
  - Action buttons (View Details, Cancel, Retry)

- **Execution Details:**
  - Full execution metadata
  - Live streaming output (for agents)
  - Logs viewer
  - Resource usage charts
  - Cancel/Retry buttons

**WebSocket Integration:**

```javascript
// ExecutionMonitor.tsx
const ws = new WebSocket('ws://localhost:8083/ws/executions');

ws.onmessage = (event) => {
  const update = JSON.parse(event.data);
  // update.execution_id
  // update.status
  // update.output
  
  // Update state/UI
  setExecutions(prev => 
    prev.map(ex => ex.id === update.execution_id 
      ? { ...ex, ...update } 
      : ex
    )
  );
};
```

#### 4. Deployments (/deployments)

**Purpose:** Manage Relic and Monument deployments

**Sub-Routes:**
- `/deployments/relics` - List deployed relics
- `/deployments/relics/:name` - Relic dashboard
- `/deployments/monuments` - List deployed monuments
- `/deployments/monuments/:name` - Monument dashboard

**Components:**
- **Deployment List:**
  - Cards/table of deployed services
  - Status indicators (running, stopped, error)
  - Resource usage (CPU, memory, disk)
  - Action buttons (Start, Stop, Restart, Scale, Undeploy)

- **Relic/Monument Dashboard:**
  - Service overview (all containers)
  - Health checks
  - Logs viewer (tailing logs)
  - Metrics charts
  - Configuration viewer
  - Scale controls (for monuments)
  - Network diagram (service connections)

**Example Component:**

```tsx
// RelicDashboard.tsx
export const RelicDashboard: React.FC = () => {
  const { name } = useParams();
  const [status, setStatus] = useState(null);
  
  useEffect(() => {
    const fetchStatus = async () => {
      const res = await fetch(`/api/v1/deployments/relics/${name}`);
      const data = await res.json();
      setStatus(data);
    };
    
    fetchStatus();
    const interval = setInterval(fetchStatus, 5000); // Poll every 5s
    return () => clearInterval(interval);
  }, [name]);
  
  const handleAction = async (action: 'start' | 'stop' | 'restart') => {
    await fetch(`/api/v1/deployments/relics/${name}/${action}`, {
      method: 'POST'
    });
  };
  
  return (
    <div className="relic-dashboard">
      <h1>{name}</h1>
      <div className="status-badge">{status?.status}</div>
      
      <div className="actions">
        <button onClick={() => handleAction('start')}>Start</button>
        <button onClick={() => handleAction('stop')}>Stop</button>
        <button onClick={() => handleAction('restart')}>Restart</button>
      </div>
      
      <div className="metrics">
        {/* CPU, Memory, Network charts */}
      </div>
      
      <div className="logs">
        <LogsViewer service={name} />
      </div>
    </div>
  );
};
```

### File Structure (React App)

```
services/web_console/
├── package.json
├── tsconfig.json
├── vite.config.ts           # Using Vite for fast dev
├── public/
│   └── index.html
├── src/
│   ├── main.tsx            # Entry point
│   ├── App.tsx             # Root component
│   ├── routes/             # Route definitions
│   │   └── index.tsx
│   ├── pages/              # Page components
│   │   ├── Dashboard.tsx
│   │   ├── ManifestList.tsx
│   │   ├── ManifestEditor.tsx
│   │   ├── ExecutionList.tsx
│   │   ├── ExecutionDetails.tsx
│   │   ├── DeploymentList.tsx
│   │   └── DeploymentDashboard.tsx
│   ├── components/         # Reusable components
│   │   ├── Navbar.tsx
│   │   ├── Sidebar.tsx
│   │   ├── LogsViewer.tsx
│   │   ├── MonacoEditor.tsx
│   │   ├── DependencyGraph.tsx
│   │   └── MetricsChart.tsx
│   ├── hooks/              # Custom hooks
│   │   ├── useWebSocket.ts
│   │   ├── useManifests.ts
│   │   └── useExecutions.ts
│   ├── services/           # API client
│   │   ├── api.ts         # Axios/fetch wrapper
│   │   ├── manifests.ts
│   │   ├── executions.ts
│   │   └── deployments.ts
│   ├── store/              # Redux/Zustand state
│   │   ├── index.ts
│   │   ├── manifestsSlice.ts
│   │   ├── executionsSlice.ts
│   │   └── deploymentsSlice.ts
│   ├── types/              # TypeScript types
│   │   ├── manifest.ts
│   │   ├── execution.ts
│   │   └── deployment.ts
│   └── utils/              # Utilities
│       ├── yaml.ts
│       └── validation.ts
└── Dockerfile              # Container build
```

---

## CLI Client Design

### Proposed: `cortex` CLI Tool

**Tech Stack:**
- **Language:** Python (for ease of integration)
- **Framework:** Click or Typer (modern CLI framework)
- **HTTP Client:** httpx (async support)
- **Output:** Rich (beautiful terminal output)
- **Config:** YAML/TOML config file

**Installation:**

```bash
# Via pip
pip install cortex-prime-cli

# Or via homebrew (future)
brew install cortex-prime/tap/cortex
```

**Configuration:**

```yaml
# ~/.cortex/config.yml
default_profile: local

profiles:
  local:
    api_gateway: http://localhost:8080
    manifest_ingestion: http://localhost:8082
    runtime_executor: http://localhost:8083
    deployment_controller: http://localhost:8084
  
  production:
    api_gateway: https://cortex.example.com
    auth:
      type: bearer
      token_file: ~/.cortex/tokens/prod.token
```

### Command Structure

```bash
cortex [global-options] <command> <subcommand> [options] [args]
```

**Global Options:**
```bash
--profile <name>      # Use specific profile
--api-url <url>       # Override API URL
--format json|yaml|table  # Output format
--verbose             # Verbose logging
--no-color            # Disable colors
```

### Complete Command Tree

```
cortex
├── init                          # Initialize CLI config
├── config
│   ├── list                     # List profiles
│   ├── get <key>                # Get config value
│   └── set <key> <value>        # Set config value
│
├── system
│   ├── health                   # System health check
│   ├── services                 # List services
│   └── metrics                  # Show metrics
│
├── manifests (or m)
│   ├── list [type]              # List manifests
│   ├── get <type> <name>        # Get manifest
│   ├── create <type>            # Create manifest (interactive)
│   ├── edit <type> <name>       # Edit manifest in $EDITOR
│   ├── delete <type> <name>     # Delete manifest
│   ├── validate <file>          # Validate manifest file
│   ├── sync                     # Sync with filesystem
│   └── dependencies <type> <name>  # Show dependencies
│
├── agents (or a)
│   ├── list                     # List agents
│   ├── get <name>               # Get agent
│   ├── create                   # Create agent (interactive wizard)
│   ├── execute <name>           # Execute agent (interactive chat)
│   ├── edit <name>              # Edit agent
│   └── delete <name>            # Delete agent
│
├── tools (or t)
│   ├── list                     # List tools
│   ├── get <name>               # Get tool
│   ├── execute <name> [params]  # Execute tool
│   ├── create                   # Create tool
│   └── delete <name>            # Delete tool
│
├── relics (or r)
│   ├── list                     # List relics
│   ├── get <name>               # Get relic
│   ├── deploy <name>            # Deploy relic
│   ├── start <name>             # Start relic
│   ├── stop <name>              # Stop relic
│   ├── restart <name>           # Restart relic
│   ├── logs <name>              # Tail relic logs
│   ├── status <name>            # Relic status
│   └── undeploy <name>          # Undeploy relic
│
├── monuments (or mon)
│   ├── list                     # List monuments
│   ├── get <name>               # Get monument
│   ├── deploy <name>            # Deploy monument
│   ├── start <name>             # Start monument
│   ├── stop <name>              # Stop monument
│   ├── scale <name> <service> <replicas>  # Scale service
│   ├── logs <name> [service]    # Tail monument logs
│   ├── status <name>            # Monument status
│   └── undeploy <name>          # Undeploy monument
│
├── workflows (or w)
│   ├── list                     # List workflows
│   ├── execute <name> [input]   # Execute workflow
│   ├── status <id>              # Workflow status
│   ├── logs <id>                # Workflow logs
│   ├── pause <id>               # Pause workflow
│   ├── resume <id>              # Resume workflow
│   └── cancel <id>              # Cancel workflow
│
└── executions (or ex)
    ├── list                     # List executions
    ├── get <id>                 # Get execution
    ├── logs <id>                # Execution logs
    ├── cancel <id>              # Cancel execution
    └── delete <id>              # Delete execution record
```

### Example Commands

```bash
# System check
cortex system health

# List all agents
cortex manifests list agents
cortex agents list  # Shortcut

# Create new agent (interactive)
cortex agents create
> Name: my_agent
> Summary: My custom agent
> Author: user@example.com
> Cognitive Engine - Provider: google
> Cognitive Engine - Model: gemini-1.5-pro
> ... (wizard continues)

# Execute agent (interactive chat)
cortex agents execute assistant
> User: What is 42 + 8?
> Assistant: 42 + 8 equals 50.
> User: ^C

# Execute tool with parameters
cortex tools execute calculator --params '{"operation":"add","a":5,"b":3}'

# Deploy relic
cortex relics deploy kv_store

# Monitor relic logs
cortex relics logs kv_store --follow

# Deploy monument
cortex monuments deploy code_forge --env production

# Scale monument service
cortex monuments scale code_forge ci_runner 5

# List recent executions
cortex executions list --limit 10 --status running

# Show dependency graph
cortex manifests dependencies agent assistant
```

### Implementation (Python with Click)

```python
# cortex_cli/main.py
import click
import httpx
from rich.console import Console
from rich.table import Table
import yaml

console = Console()

@click.group()
@click.option('--profile', default='local', help='Profile to use')
@click.option('--api-url', help='Override API URL')
@click.pass_context
def cli(ctx, profile, api_url):
    """Cortex-Prime MK1 CLI - Sovereign AI Orchestration"""
    ctx.ensure_object(dict)
    
    # Load config
    config = load_config()
    profile_config = config['profiles'][profile]
    
    ctx.obj['api_url'] = api_url or profile_config.get('api_gateway')
    ctx.obj['client'] = httpx.Client(base_url=ctx.obj['api_url'])

# System commands
@cli.group()
def system():
    """System management commands"""
    pass

@system.command()
@click.pass_context
def health(ctx):
    """Check system health"""
    client = ctx.obj['client']
    response = client.get('/api/v1/system/health')
    data = response.json()
    
    table = Table(title="System Health")
    table.add_column("Service", style="cyan")
    table.add_column("Status", style="green")
    
    for service, status in data['services'].items():
        table.add_row(service, status['status'])
    
    console.print(table)

# Agent commands
@cli.group()
def agents():
    """Agent management commands"""
    pass

@agents.command()
@click.pass_context
def list(ctx):
    """List all agents"""
    client = ctx.obj['client']
    response = client.get('/api/v1/manifests/agents')
    agents = response.json()
    
    table = Table(title="Agents")
    table.add_column("Name", style="cyan")
    table.add_column("State", style="yellow")
    table.add_column("Author", style="green")
    
    for agent in agents:
        table.add_row(agent['name'], agent['state'], agent['author'])
    
    console.print(table)

@agents.command()
@click.argument('name')
@click.pass_context
def execute(ctx, name):
    """Execute agent in interactive mode"""
    client = ctx.obj['client']
    
    # Start agent session
    response = client.post('/api/v1/executions/agents', json={'agent': name})
    session = response.json()
    session_id = session['execution_id']
    
    console.print(f"[green]Started agent session: {session_id}[/green]")
    console.print("[yellow]Type 'exit' to end session[/yellow]\n")
    
    while True:
        user_input = console.input("[bold blue]You:[/bold blue] ")
        
        if user_input.lower() in ['exit', 'quit']:
            break
        
        # Send message
        response = client.post(
            f'/api/v1/executions/agents/{session_id}/messages',
            json={'message': user_input}
        )
        
        result = response.json()
        console.print(f"[bold green]Agent:[/bold green] {result['response']}\n")
    
    # End session
    client.delete(f'/api/v1/executions/agents/{session_id}')
    console.print("[yellow]Session ended[/yellow]")

# Tool commands
@cli.group()
def tools():
    """Tool management commands"""
    pass

@tools.command()
@click.argument('name')
@click.option('--params', help='Tool parameters (JSON)')
@click.pass_context
def execute(ctx, name, params):
    """Execute a tool"""
    client = ctx.obj['client']
    
    parameters = yaml.safe_load(params) if params else {}
    
    with console.status(f"[bold green]Executing tool {name}..."):
        response = client.post(
            '/api/v1/executions/tools',
            json={'tool': name, 'parameters': parameters}
        )
    
    result = response.json()
    console.print(f"[green]Result:[/green] {result['output']}")

# Relic commands
@cli.group()
def relics():
    """Relic deployment commands"""
    pass

@relics.command()
@click.argument('name')
@click.pass_context
def deploy(ctx, name):
    """Deploy a relic"""
    client = ctx.obj['client']
    
    with console.status(f"[bold green]Deploying relic {name}..."):
        response = client.post(
            '/api/v1/deployments/relics',
            json={'relic': name}
        )
    
    result = response.json()
    console.print(f"[green]Relic {name} deployed successfully[/green]")

@relics.command()
@click.argument('name')
@click.option('--follow', '-f', is_flag=True, help='Follow logs')
@click.pass_context
def logs(ctx, name, follow):
    """View relic logs"""
    client = ctx.obj['client']
    
    if follow:
        # WebSocket streaming
        import websocket
        ws_url = ctx.obj['api_url'].replace('http', 'ws')
        ws = websocket.create_connection(f"{ws_url}/api/v1/deployments/relics/{name}/logs/stream")
        
        console.print(f"[yellow]Tailing logs for {name} (Ctrl+C to stop)...[/yellow]\n")
        
        try:
            while True:
                log_line = ws.recv()
                console.print(log_line)
        except KeyboardInterrupt:
            ws.close()
    else:
        # One-time fetch
        response = client.get(f'/api/v1/deployments/relics/{name}/logs')
        logs = response.json()
        
        for line in logs['logs']:
            console.print(line)

if __name__ == '__main__':
    cli()
```

### CLI Package Structure

```
cortex_cli/
├── setup.py
├── pyproject.toml
├── README.md
├── cortex_cli/
│   ├── __init__.py
│   ├── main.py              # Main CLI entry point
│   ├── config.py            # Config management
│   ├── api/                 # API client
│   │   ├── __init__.py
│   │   ├── client.py        # Base HTTP client
│   │   ├── manifests.py     # Manifest operations
│   │   ├── executions.py    # Execution operations
│   │   └── deployments.py   # Deployment operations
│   ├── commands/            # Command groups
│   │   ├── __init__.py
│   │   ├── system.py
│   │   ├── manifests.py
│   │   ├── agents.py
│   │   ├── tools.py
│   │   ├── relics.py
│   │   ├── monuments.py
│   │   ├── workflows.py
│   │   └── executions.py
│   ├── utils/               # Utilities
│   │   ├── formatting.py    # Rich output formatting
│   │   ├── validation.py    # Input validation
│   │   └── yaml_helpers.py  # YAML processing
│   └── templates/           # Manifest templates
│       ├── agent.yml.j2
│       ├── tool.yml.j2
│       └── relic.yml.j2
└── tests/
    └── test_commands.py
```

---

## SDK Libraries

### Python SDK

**Installation:**
```bash
pip install cortex-prime-sdk
```

**Usage:**

```python
from cortex_prime import CortexClient

# Initialize client
client = CortexClient(api_url="http://localhost:8080")

# Manifests
agents = client.manifests.agents.list()
agent = client.manifests.agents.get("assistant")
client.manifests.agents.create({
    "name": "my_agent",
    "kind": "Agent",
    # ...
})
client.manifests.agents.update("my_agent", {"state": "stable"})
client.manifests.agents.delete("my_agent")

# Executions
execution = client.executions.agents.create("assistant")
response = execution.send_message("Hello!")
print(response.text)
execution.close()

# Deployments
deployment = client.deployments.relics.deploy("kv_store")
status = deployment.status()
deployment.stop()
deployment.start()
deployment.undeploy()
```

### JavaScript/TypeScript SDK

**Installation:**
```bash
npm install @cortex-prime/sdk
```

**Usage:**

```typescript
import { CortexClient } from '@cortex-prime/sdk';

// Initialize client
const client = new CortexClient({ apiUrl: 'http://localhost:8080' });

// Manifests
const agents = await client.manifests.agents.list();
const agent = await client.manifests.agents.get('assistant');
await client.manifests.agents.create({
  name: 'my_agent',
  kind: 'Agent',
  // ...
});

// Executions with streaming
const execution = await client.executions.agents.create('assistant');
execution.on('message', (msg) => {
  console.log('Agent:', msg.text);
});
execution.sendMessage('Hello!');

// Deployments
const deployment = await client.deployments.relics.deploy('kv_store');
const status = await deployment.status();
await deployment.stop();
```

---

## Real-Time Communication

### WebSocket Endpoints

```
WS /api/v1/ws/executions              # All execution updates
WS /api/v1/ws/executions/{id}         # Specific execution
WS /api/v1/ws/deployments             # All deployment updates
WS /api/v1/ws/deployments/{name}/logs # Live logs
WS /api/v1/ws/system/metrics          # Live metrics
```

### Event Format

```json
{
  "type": "execution.status",
  "timestamp": "2025-01-15T10:30:00Z",
  "data": {
    "execution_id": "abc123",
    "status": "running",
    "progress": 45,
    "output": "Processing step 3..."
  }
}
```

---

## Implementation Roadmap

### Phase 1: Core CRUD API (2 weeks)
- [ ] Enhance manifest_ingestion service with PUT/PATCH/DELETE
- [ ] Add filesystem persistence for manifest changes
- [ ] Implement proper error handling and validation
- [ ] Add pagination and filtering to list endpoints
- [ ] Create OpenAPI documentation

### Phase 2: Web Console MVP (3 weeks)
- [ ] Set up React + TypeScript + Vite project
- [ ] Implement Dashboard page
- [ ] Implement Manifest List + Editor pages
- [ ] Implement Execution List + Details pages
- [ ] Add WebSocket integration for real-time updates

### Phase 3: CLI Tool (2 weeks)
- [ ] Create Python CLI with Click
- [ ] Implement all command groups
- [ ] Add interactive wizards (agent create, etc.)
- [ ] Add Rich formatting
- [ ] Package and publish to PyPI

### Phase 4: SDK Libraries (2 weeks)
- [ ] Create Python SDK
- [ ] Create TypeScript SDK
- [ ] Add comprehensive documentation
- [ ] Publish to package registries

### Phase 5: Advanced Features (4 weeks)
- [ ] Deployment management (Relics/Monuments)
- [ ] Advanced monitoring and metrics
- [ ] Role-based access control
- [ ] Audit logging
- [ ] Backup/restore functionality

---

## Conclusion

This comprehensive client integration strategy provides multiple ways to interact with Cortex-Prime:

1. **Web Console** - Rich UI for visual management
2. **CLI Tool** - Fast, scriptable command-line interface
3. **SDK Libraries** - Programmatic access for automation
4. **WebSocket API** - Real-time updates and streaming

All clients interact with the same RESTful API, ensuring consistency and maintainability. The phased roadmap allows for incremental development while delivering value early.

**Priority:** Start with Phase 1 (CRUD API) as foundation, then Phase 2 (Web Console MVP) for immediate usability.

---

**Status:** Ready for Implementation  
**Estimated Effort:** 13 weeks for full completion  
**Dependencies:** MANIFEST_INTERACTION_MODEL.md (Deployment Controller service)
