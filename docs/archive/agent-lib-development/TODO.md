### TO-DO: PRIORITY FEATURES (B-LINE → CATHEDRAL)

**Foundational Infrastructure (Do First)**

1. **✅ Manifest Ingestion Pipeline Completion** [COMPLETE]
   - [x] Robust YAML loader for agents/tools/relics from manifests/
   - [x] Schema validation against covenant principles
   - [x] Hot-reload capability without arbiter restart
   - [x] Error handling for malformed manifests
   - [x] Registry synchronization with C++ arbiter core
   - **Tests:** 8/8 passing
   - **Documentation:** services/manifest_ingestion/FEATURES.md

2. **✅ Context Variable System (`variables.hpp` go-live)** [COMPLETE]
   - [x] Implement `$(...)` substitution parser for YAML
   - [x] Runtime variable resolution engine
   - [x] Expose core context vars: $TIMESTAMP, $AGENT_ID, $SESSION_ID, $USER_INTENT
   - [x] Agent state variables: $LAST_RESULT, $ITERATION_COUNT, $CONFIDENCE
   - [x] Integration with manifest loader
   - **Tests:** 17/17 passing
   - **Documentation:** services/manifest_ingestion/FEATURES.md

3. **✅ Streaming Protocol v1.1 Support** [COMPLETE]
   - [x] LLM client streaming API (modelApi.hpp)
   - [x] MiniGemini streaming implementation with SSE
   - [x] StreamingProtocol parser for real-time action execution
   - [x] Agent streaming API (promptStreaming)
   - [x] Context feeds support in manifests
   - [x] Variable resolution ($variable_name)
   - [x] Action dependency resolution
   - [x] Parallel async action execution
   - **Documentation:** STREAMING_PROTOCOL_README.md

4. **✅ Modern Manifest Format v1.0** [COMPLETE]
   - [x] Context feeds configuration
   - [x] streaming_protocol flag
   - [x] v1.0 Sovereign Core Standard support
   - [x] Example manifest with streaming features
   - **Example:** config/agents/streaming-example/agent.yml

5. **🚧 Script Runtime Executor Hardening** [IN PROGRESS]
   - [ ] Container-based sandboxing for Python/Bash tools
   - [ ] Resource limits (CPU, memory, timeout) per execution
   - [ ] Secure I/O redirection and error propagation
   - [ ] Tool result validation and typing
   - [ ] Execution metrics and observability

4. **First Relic Implementation (Reference Pattern)**
   - [ ] Choose initial Relic (notes KB or Factorio config bundle)
   - [ ] Define YAML schema with access_method patterns
   - [ ] Implement arbiter-side Relic loading and registration
   - [ ] Build query interface for agent consumption
   - [ ] Document the pattern for scaling to other Relics

5. **Layered Directive System (MVP)**
   - [ ] Layer 0: Constitutional firmware in C++ agent class
   - [ ] Layer 1: Profile identity from agent YAML base_system_prompt
   - [ ] Layer 2: Dynamic directive overlay (2-3 initial: verbose_mode, rapid_fire, cautious)
   - [ ] Prompt fragment injection mechanism
   - [ ] Tool/Relic access filtering via tags
   - [ ] Directive activation/deactivation API

6. **Memory/State Persistence Layer**
   - [ ] Profile export/import (.agent-name.profile.json)
   - [ ] Conversation state persistence (SQLite or Redis)
   - [ ] OODA loop state tracking across sessions
   - [ ] Learning pattern storage for habitual/preferential agents
   - [ ] Memory pruning and archival strategies

**Secondary Priorities (Post-Foundation)**

- [ ] Implement more sophisticated error handling
- [ ] Add more tools to global tool library
- [ ] Improve agent decision-making heuristics
- [ ] Message bus integration (NATS/RabbitMQ) for async comms
- [ ] Advanced observability (metrics, traces, logs correlation)
- [ ] Multi-agent coordination protocols

---

**Progress:** 4/6 Phase 0 features complete (67%)
**Test Coverage:** 25+ tests, 100% pass rate
**Last Updated:** 2025-01-10
