# Documentation Index

**Cortex-Prime MK1 Documentation Hub**

Complete documentation for the Cortex-Prime MK1 autonomous AI orchestration platform.

---

## 📚 Quick Navigation

### Getting Started
- [Repository Structure](REPOSITORY_STRUCTURE.md) - Project organization
- [Roadmap](ROADMAP.md) - Development roadmap and milestones
- [Features](FEATURES.md) - Platform capabilities and features

### Core Documentation

#### Manifest System ⭐ NEW
- **[Manifest Schemas](MANIFEST_SCHEMAS.md)** - Complete schema reference for all manifest types
- **[Manifest Quick Reference](MANIFEST_QUICK_REFERENCE.md)** - Fast lookup guide for developers
- [Manifests (Legacy)](manifests.md) - Original manifest documentation

#### Architecture & Design
- [Fractal Design](FRACTAL_DESIGN.md) - Fractal composition architecture
- [Workflow Design](WORKFLOW_DESIGN.md) - Workflow orchestration design
- [Agent Execution Protocol](AGENT_EXECUTION_PROTOCOL.md) - Agent runtime protocol

#### Infrastructure & Integration
- [Infrastructure Guide](INFRASTRUCTURE_GUIDE.md) - Deployment and infrastructure
- [LLM Gateway Integration](LLM_GATEWAY_INTEGRATION.md) - LLM provider integration
- [Streaming Protocol](STREAMING_PROTOCOL.md) - Real-time streaming protocol
- [Streaming Protocol v1.1 Implementation](STREAMING_PROTOCOL_V1.1_IMPLEMENTATION_SUMMARY.md)
- [Streaming Protocol v1.1 Quick Reference](STREAMING_PROTOCOL_V1.1_QUICK_REFERENCE.md)

#### Development
- [Progress](PROGRESS.md) - Development progress tracking
- [Changelog](CHANGELOG.md) - Version history and changes
- [Integration Test Results](INTEGRATION_TEST_RESULTS.md) - Test results

---

## 📖 Documentation by Topic

### Manifest Development

**New to manifests?** Start here:
1. [Manifest Quick Reference](MANIFEST_QUICK_REFERENCE.md) - Templates and common patterns
2. [Manifest Schemas](MANIFEST_SCHEMAS.md) - Complete field reference
3. Standard Library (`std/manifests/`) - Working examples
4. Test Suite (`testing/test_against_manifest/`) - Comprehensive examples

**Manifest Types:**
- **Tool Manifests** - Executable functions/scripts
- **Relic Manifests** - Persistent services (APIs, databases)
- **Agent Manifests** - AI entities with reasoning capabilities
- **Workflow Manifests** - Orchestrated task sequences
- **Monument Manifests** - Complete autonomous systems
- **Amulet Manifests** - Pre-configured templates

### System Architecture

**Understanding the platform:**
- [Fractal Design](FRACTAL_DESIGN.md) - How components compose recursively
- [Agent Execution Protocol](AGENT_EXECUTION_PROTOCOL.md) - How agents execute
- [Workflow Design](WORKFLOW_DESIGN.md) - How workflows orchestrate
- [Streaming Protocol](STREAMING_PROTOCOL.md) - Real-time communication

### Deployment & Operations

**Running in production:**
- [Infrastructure Guide](INFRASTRUCTURE_GUIDE.md) - Docker, Kubernetes, configuration
- [LLM Gateway Integration](LLM_GATEWAY_INTEGRATION.md) - Connecting LLM providers
- Standard Manifests (`std/manifests/`) - Production-ready components

### API & Integration

**Building with Cortex-Prime:**
- [Streaming Protocol](STREAMING_PROTOCOL.md) - WebSocket streaming API
- [Streaming Protocol v1.1 Quick Reference](STREAMING_PROTOCOL_V1.1_QUICK_REFERENCE.md)
- [LLM Gateway Integration](LLM_GATEWAY_INTEGRATION.md) - LLM integration patterns

---

## 🎯 Common Tasks

### Creating a New Tool

1. Read: [Manifest Quick Reference](MANIFEST_QUICK_REFERENCE.md#tool-quick-template)
2. Copy template from quick reference
3. Review: [Manifest Schemas](MANIFEST_SCHEMAS.md#tool-manifest-schema)
4. See example: `std/manifests/tools/calculator/`
5. Test and validate

### Creating a New Agent

1. Read: [Manifest Quick Reference](MANIFEST_QUICK_REFERENCE.md#agent-quick-template)
2. Review: [Agent Execution Protocol](AGENT_EXECUTION_PROTOCOL.md)
3. Study: [Manifest Schemas](MANIFEST_SCHEMAS.md#agent-manifest-schema)
4. See example: `std/manifests/agents/assistant/`
5. Define persona in system prompt file
6. Configure cognitive engine
7. Import tools/relics as needed

### Building a Monument

1. Read: [Fractal Design](FRACTAL_DESIGN.md)
2. Review: [Manifest Quick Reference](MANIFEST_QUICK_REFERENCE.md#monument-quick-template)
3. Study: [Manifest Schemas](MANIFEST_SCHEMAS.md#monument-manifest-schema)
4. See examples:
   - Simple: `std/manifests/monuments/blog_platform/`
   - Complex: `testing/test_against_manifest/monuments/complex/data_analytics_platform/`
   - Specialized: `testing/test_against_manifest/monuments/specialized/knowledge_base/`
5. Compose infrastructure, intelligence, and automation layers

### Deploying to Production

1. Read: [Infrastructure Guide](INFRASTRUCTURE_GUIDE.md)
2. Configure: Environment variables and secrets
3. Review: [LLM Gateway Integration](LLM_GATEWAY_INTEGRATION.md)
4. Deploy: Using Docker Compose or Kubernetes
5. Monitor: Health checks and metrics

---

## 📂 External Resources

### Standard Library
- **Location:** `std/manifests/`
- **Purpose:** Production-ready foundation manifests
- **Docs:** `std/manifests/README.md`, `std/manifests/CATALOG.md`

### Test Suite
- **Location:** `testing/test_against_manifest/`
- **Purpose:** Comprehensive validation and examples
- **Docs:** `testing/test_against_manifest/README.md`

### Main Repository
- **Root:** `/home/mlamkadm/repos/Cortex-Prime-MK1`
- **Documentation:** `/docs` (this directory)
- **Services:** `/services`
- **Infrastructure:** `/infra`

---

## 📝 Document Status

### Current (v1.0+)
- ✅ Manifest Schemas - **Complete**
- ✅ Manifest Quick Reference - **Complete**
- ✅ Streaming Protocol v1.1 - **Complete**
- ✅ Infrastructure Guide - **Complete**
- ✅ LLM Gateway Integration - **Complete**

### Legacy/Historical
- 📄 manifests.md - Original manifest documentation (superseded by MANIFEST_SCHEMAS.md)
- 📄 tmp-feedback_*.md - Temporary feedback documents

### Active Development
- 🔄 Features - Updated regularly
- 🔄 Changelog - Updated per release
- 🔄 Progress - Updated as development progresses

---

## 🔍 Finding Information

### By Role

**Developer Creating Manifests:**
1. [Manifest Quick Reference](MANIFEST_QUICK_REFERENCE.md)
2. [Manifest Schemas](MANIFEST_SCHEMAS.md)
3. Standard Library examples (`std/manifests/`)

**System Architect:**
1. [Fractal Design](FRACTAL_DESIGN.md)
2. [Infrastructure Guide](INFRASTRUCTURE_GUIDE.md)
3. [Workflow Design](WORKFLOW_DESIGN.md)

**DevOps Engineer:**
1. [Infrastructure Guide](INFRASTRUCTURE_GUIDE.md)
2. [LLM Gateway Integration](LLM_GATEWAY_INTEGRATION.md)
3. [Repository Structure](REPOSITORY_STRUCTURE.md)

**API Developer:**
1. [Streaming Protocol](STREAMING_PROTOCOL.md)
2. [Streaming Protocol v1.1 Quick Reference](STREAMING_PROTOCOL_V1.1_QUICK_REFERENCE.md)
3. [LLM Gateway Integration](LLM_GATEWAY_INTEGRATION.md)

---

## 📊 Documentation Statistics

- **Total Documents:** 20+
- **Schema Docs:** 2 (complete reference + quick guide)
- **Protocol Docs:** 3 (streaming protocol v1.0 + v1.1)
- **Architecture Docs:** 3 (fractal, workflow, agent)
- **Integration Docs:** 2 (infrastructure, LLM gateway)
- **Management Docs:** 4 (roadmap, progress, changelog, features)

---

## 🆘 Getting Help

1. **Quick Questions:** Check [Manifest Quick Reference](MANIFEST_QUICK_REFERENCE.md)
2. **Schema Details:** See [Manifest Schemas](MANIFEST_SCHEMAS.md)
3. **Examples:** Browse `std/manifests/` and `testing/test_against_manifest/`
4. **Architecture:** Read [Fractal Design](FRACTAL_DESIGN.md)
5. **Deployment:** Consult [Infrastructure Guide](INFRASTRUCTURE_GUIDE.md)

---

## 🔄 Recent Updates

### January 2025
- ✅ Added comprehensive manifest schema documentation
- ✅ Created manifest quick reference guide
- ✅ Established standard library (`std/manifests/`)
- ✅ Built complete test suite with monuments
- ✅ Documented all manifest types with examples

### October 2024
- ✅ Streaming Protocol v1.1 implementation
- ✅ Infrastructure guide updates
- ✅ LLM gateway integration documentation
- ✅ Repository structure documentation

---

## 📌 Key Concepts

### Manifests
YAML files that declare components (tools, relics, agents, workflows, monuments). Follow v1.0 Sovereign Core Standard.

### Fractal Composition
Components can contain sub-components recursively. Agents can have local tools, sub-agents, relics, and workflows.

### Relative Path Imports
All imports use relative file paths. No magic globals or registries required.

### Context Feeds
Dynamic data injection into agents from tools, relics, or other agents. Can be on-demand or periodic.

### Monuments
Complete autonomous systems composed of infrastructure (relics), intelligence (agents), and automation (workflows).

---

**Documentation Version:** 1.0.0  
**Platform Version:** Cortex-Prime MK1 v1.0  
**Last Updated:** January 2025  
**Maintainer:** Cortex-Prime Team
