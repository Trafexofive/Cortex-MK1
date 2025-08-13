# PROTO-SCHEMA.md

> NOTES:
> 
> - [x] we need to take into account that the `build_tool` action is a long-running. We need to ensure that the agent can handle this without blocking the user. (very hard, most agents can barely handle long-running tasks, not us though) 
> - [x] I see this as a good opportunity to add a feature that Ive wanted to add for a while: **asynchronous actions**. This will allow the agent to dispatch long-running tasks without blocking the user. The agent can return a task ID immediately, and the user can check the status of the task later.
> - [ ] Bit unrelated, But we need to add a new build.tool.yml (will be in the root of the local tool dir) (this should be pluggable as well as have a default implementations/helopers for building (yaml to dockerfile, fancy way to add dependencies, etc) and running the build (docker build, docker run, etc). This will allow us to have a standard way of building and running tools. Of course, not all tools will need this, but it will be useful for tools that require a build step (e.g. C++ tools, etc) and have a lot of dependencies (relics and monuments).
> - [x] Smartly handle long-running tasks by dispatching them as asynchronous actions. 
> - [x] internal vars for task management, such as 'task_id', 'result', ...
> - [x] How the env and context expand to include knowledge relics and security levels.
> - [x] a new depends on option for actions, as well as a new `execution` field to indicate if the action is synchronous or asynchronous.
> - [x] the ability to for the agent to do sub-tasks/sub-actions, such as kicking off a long-running task and then returning a task ID immediately. The primary action can be ASYNC, this shouldnt affect the type (ASYNC/SYNC) of the action, but rather the execution mode. So even though the action is ASYNC, It will still wait for the action to complete before returning the response.
> - [x] Add a new display field to the action, which will be used to display the action in the UI. This will be useful for actions that are long-running and need to be displayed in the UI. But for normal actions (the llm/agent is seeing the result), this will be null. Useful for action that pretty print ... This will be client Agnostic, It will be rendered on our clients (TUI, frontend, etc) and maybe will be even used to display the action in a user-friendly way. 
> - [ ] action exec in toughts, so the agent can decide how to execute the action based on the context and the action itself. This will allow the agent to be more flexible and adaptive in its execution.
> - [ ] we need to talk about expansion, how the env and context expand to include knowledge relics and security levels. This will allow the agent to have a more dynamic and flexible context, which can be used to make better decisions and execute actions more effectively.
> - [ ] we need to give the agents, a trap-card ability, for now they will be just simple actions that can be executed by the agent, but in the future they will be able to do more complex things, such as executing other actions, or even modifying the agent itself. This will allow the agent to be more flexible and adaptive in its execution. they can add the actions to a retgistry, then execute them, append them agent context every iteration, useful for dynamic data/context, such as the current time, or the current user, or the current task, etc. This will allow the agent to be more flexible and adaptive in its execution. Premove that RROOOOOKS!
> - [ ] we need to add better resonnoing capabilities to the agents, so they can make better decisions and execute actions more effectively. This will allow the agent to be more flexible and adaptive in its execution. For example, the agent can use the context to decide which action to execute, or which tool to use, or even which agent to delegate the task to. for now lets say that the agent chooses how much to think, or if more thinking is needed, or if it can just execute the action. This will allow the agent to be more flexible and adaptive in its execution.
> - [ ] we might even decouple the resonnoing from the core loop (we would have 2 loops, once the thinking with action exec is dont then the agent gets started on the main loop, this), we probably want add this now, im still thinking about how to do ASYNC, thinking (might, apply the same logic as the actions, so the agent can dispatch a thinking task and then return a task ID immediately, and the user can check the status of the task later. This will allow the agent to be more flexible and adaptive in its execution.), Oh I see, we dont need to decouple the resonnoing from the core loop, we can add the pre-thinking step to the core loop, so the agent can think before executing the action (should be able disabled from the yml, this extends to all other core agent/tool functionality, so the agent can think before executing the action, or even before executing the core loop, this will allow the agent to be more flexible and adaptive in its execution. ). cool, so the agent can do some data retrieval, then think about the data, then execute the action, or even execute the core loop. This will allow the agent to be more flexible and adaptive in its execution.

---

## Master Schema v2.0

This version incorporates asynchronous operations, context management, action dependencies, and richer metadata for UI display.

```json
{
  "status": "string (Enum: SUCCESS | EXECUTING | ERROR | TASK_STARTED)",
  "context": {
    "knowledge_relics": ["string (ID of a knowledge source)"], // how will this look like in the config/my_agent/knowledge/. ?? We need to think about everything
    "security_level": "string (e.g., 'user', 'admin', 'system')", // to remove
    "variables": {
      "string (variable_name)": "any (JSON serializable value)"
    }
  },
  "thoughts": [
    {
      "type": "string (Enum: PLAN | OBSERVATION | ...)",
      "content": "string"
    }
  ],
  "actions": [
    {
      "action_id": "string (Optional, unique ID for this action instance)",
      "action": "string (Name of the tool or internal function)",
      "type": "string (Enum: tool | internal | relic | monument<D-h>)",
      "params": "object",
      "execution": "string (Enum: SYNC | ASYNC)",
      "depends_on": "string (Optional, action_id of a prerequisite action)",
      "display": {
        "type": "string (e.g., 'progress_bar', 'status_message')",
        "label": "string (UI display text)",
        "estimated_duration_seconds": "integer"
      },
      "sub_actions": [
        "..."
      ]
    }
  ],
  "stop": "boolean",
  "response": "string | null"
}
```

---

## Prototype Examples

### Prototype 1: Kicking off an Async Task
*This is the foundational example of an asynchronous, long-running task.*
```json
{
  "status": "TASK_STARTED",
  "context": {
    "knowledge_relics": ["relic_id_project_docs_v4"],
    "security_level": "user"
  },
  "thoughts": [
    {
      "type": "PLAN",
      "content": "The Master has requested a compilation. This is a long-running task. I will dispatch it as an asynchronous action using the 'build_tool' and immediately return a task ID so the Master is not blocked."
    },
    {
      "type": "DECISION",
      "content": "Using 'build_tool' with 'target: //main:app' as an ASYNC action."
    }
  ],
  "actions": [
    {
      "action_id": "build-main-app-123",
      "action": "build_tool",
      "type": "tool",
      "params": {
        "target": "//main:app",
        "config": "release"
      },
      "execution": "ASYNC"
    }
  ],
  "stop": true,
  "response": "Compilation task started. You can check the status using the task ID: build-main-app-123"
}
```

### Prototype 2: Checking Task Status
*This schema shows how an agent could check the status of a previously dispatched asynchronous task.*
```json
{
  "status": "EXECUTING",
  "thoughts": [
    {
      "type": "PLAN",
      "content": "The Master wants to know the status of the compilation task. I will use the 'task_manager' tool with the 'get_status' operation and the task ID I received earlier."
    }
  ],
  "actions": [
    {
      "action": "task_manager",
      "type": "tool",
      "params": {
        "operation": "get_status",
        "task_id": "build-main-app-123"
      },
      "execution": "SYNC"
    }
  ],
  "stop": false,
  "response": null
}
```

### Prototype 3: Action with Dependencies
*This schema demonstrates how an action could depend on the successful completion of another. The `search_documentation` action will only run if the `doc_update_task` action succeeds.*
```json
{
  "status": "EXECUTING",
  "thoughts": [
    {
      "type": "PLAN",
      "content": "To answer the Master's query, I first need to ensure my local documentation is up-to-date, then I can search it. I will chain these actions using the 'depends_on' field."
    }
  ],
  "actions": [
    {
      "action_id": "doc_update_task",
      "action": "git_tool",
      "type": "tool",
      "params": {
        "operation": "pull",
        "repo": "docs_repository"
      },
      "execution": "ASYNC"
    },
    {
      "action_id": "search_docs_task",
      "action": "search_tool",
      "type": "tool",
      "params": {
        "query": "How to configure the new logging service?",
        "path": "./local_docs"
      },
      "execution": "SYNC",
      "depends_on": "doc_update_task"
    }
  ],
  "stop": false,
  "response": null
}
```

### Prototype 4: Action with UI Display Hint
*This schema shows an action that provides a hint for how a user interface could display its progress.*
```json
{
  "status": "EXECUTING",
  "thoughts": [
    {
      "type": "PLAN",
      "content": "The Master has approved the deployment. I will start the deployment process and provide progress updates suitable for a UI."
    }
  ],
  "actions": [
    {
      "action_id": "deploy-prod-gateway-456",
      "action": "deploy_tool",
      "type": "tool",
      "params": {
        "target": "production",
        "service": "api_gateway"
      },
      "execution": "ASYNC",
      "display": {
        "type": "progress_bar",
        "label": "Deploying api_gateway to production...",
        "estimated_duration_seconds": 120
      }
    }
  ],
  "stop": true,
  "response": "Deployment to production has been initiated. Task ID: deploy-prod-gateway-456. You can monitor the progress."
}
```

### Prototype 5: Internal Variables and Context Expansion
*This schema illustrates an agent using the result of a previous asynchronous task (referenced by an internal variable) as input for a subsequent action. It also shows the `context` block being used to specify knowledge sources and security constraints for the operation.*
```json
{
  "status": "EXECUTING",
  "context": {
    "knowledge_relics": ["relic_id_project_docs_v4", "relic_id_coding_best_practices"],
    "security_level": "user",
    "variables": {
      "last_build_id": "build-main-app-123"
    }
  },
  "thoughts": [
    {
      "type": "PLAN",
      "content": "The build is complete. Now I need to analyze the build output for warnings. I will use the 'static_analyzer' tool and pass it the 'task_id' of the build, which I have stored as an internal variable 'last_build_id'."
    },
    {
      "type": "ASSUMPTION",
      "content": "I am assuming the 'static_analyzer' tool can retrieve the build logs using the task ID."
    }
  ],
  "actions": [
    {
      "action": "static_analyzer",
      "type": "tool",
      "params": {
        "source_task_id": "${{variables.last_build_id}}",
        "ruleset": "strict"
      },
      "execution": "SYNC"
    }
  ],
  "stop": false,
  "response": null
}
```

### Prototype 6: Sub-Actions and Execution Clarification
*This prototype clarifies the idea of a primary action that dispatches sub-actions. The main action `enrich_and_report` is synchronous from the Master's perspective, but it internally orchestrates asynchronous sub-actions. The agent will wait for all sub-actions to complete before considering the primary action done.*
```json
{
  "status": "EXECUTING",
  "thoughts": [
    {
      "type": "PLAN",
      "content": "The Master wants a full report on the new pull request. I will define a primary action 'enrich_and_report' that encapsulates fetching the PR data, running tests, and generating a summary. I will wait for all these steps to complete before responding."
    }
  ],
  "actions": [
    {
      "action_id": "pr_report_main",
      "action": "enrich_and_report",
      "type": "internal", 
      "execution": "SYNC",
      "description": "Fetches PR data, runs tests, and generates a summary report.",
      "sub_actions": [
        {
          "action_id": "fetch_pr",
          "action": "github_tool",
          "type": "tool",
          "params": { "operation": "get_pr_details", "pr_number": 123 },
          "execution": "ASYNC"
        },
        {
          "action_id": "run_unit_tests",
          "action": "build_tool",
          "type": "tool",
          "params": { "target": "//...:test" },
          "execution": "ASYNC",
          "depends_on": "fetch_pr"
        },
        {
          "action_id": "generate_summary",
          "action": "summarizer_tool",
          "type": "tool",
          "params": {
            "source_task_id": "run_unit_tests",
            "context_task_id": "fetch_pr"
          },
          "execution": "SYNC",
          "depends_on": "run_unit_tests"
        }
      ]
    }
  ],
  "stop": false,
  "response": null
}
```
