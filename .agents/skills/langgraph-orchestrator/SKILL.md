---
name: langgraph-orchestrator
description: >
  Use this skill when building stateful agent workflows with LangGraph.
  Triggers include "use LangGraph", "build a graph workflow", "add
  human-in-the-loop", "create a state machine agent", "chain agents
  together", "build a multi-agent graph", "add checkpointing",
  "create agent with memory", "build a deep agent", or any task
  involving stateful orchestration, cycles, conditional routing,
  subgraphs, or complex agent pipelines beyond simple ReAct agents.
---

# LangGraph Orchestrator Skill

A skill that governs how to **build**, **extend**, and **debug** stateful agent workflows using LangGraph.

**When to use LangGraph vs simple agents:**

| Use Simple Agent (ReAct) | Use LangGraph |
|---|---|
| Single task, linear flow | Multi-step with branching logic |
| No state between steps | State must persist across steps |
| No human approval needed | Human-in-the-loop required |
| One agent, few tools | Multiple agents coordinating |
| No cycles or retries | Retry loops, self-correction |

---

## Operation: BUILD — Creating a LangGraph Workflow

### Core Concepts

**StateGraph** — A graph where nodes are functions and edges define the flow. State is a typed dictionary that flows through the graph.

**Nodes** — Python functions that receive state and return updates. Each node does ONE thing.

**Edges** — Connections between nodes. Can be unconditional (always follow) or conditional (choose based on state).

**State** — A TypedDict that accumulates data as it flows through nodes. Use `Annotated` with reducers for list fields.

### Step 1 — Define State

State is the data contract for your entire graph. Define it upfront.

```python
from typing import Annotated, TypedDict
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    """State that flows through the graph."""
    messages: Annotated[list, add_messages]  # conversation history
    current_step: str                         # tracks progress
    result: str                               # final output
```

**State design rules:**
- Include only fields that nodes need to read or write
- Use `Annotated[list, add_messages]` for message history (appends, not replaces)
- Use plain fields for values that get overwritten
- Keep state flat — avoid deep nesting

### Step 2 — Define Nodes

Each node is a function that takes state and returns a partial state update.

```python
from langchain_core.messages import SystemMessage, HumanMessage
from common.llm import create_llm

llm = create_llm()

def analyze(state: AgentState) -> dict:
    """Analyze the input and determine next action."""
    messages = [
        SystemMessage(content="You are an analyst. Classify the input."),
        *state["messages"],
    ]
    response = llm.invoke(messages)
    return {"messages": [response], "current_step": "analyze"}

def generate_report(state: AgentState) -> dict:
    """Generate a report from the analysis."""
    messages = [
        SystemMessage(content="Generate a concise report from the analysis."),
        *state["messages"],
    ]
    response = llm.invoke(messages)
    return {"messages": [response], "result": response.content}
```

**Node rules:**
- One task per node (the "one task, one agent" principle)
- Return a dict with only the fields being updated
- Never mutate state directly — return updates
- Keep nodes stateless — all state lives in the TypedDict

### Step 3 — Define Edges and Routing

```python
def should_continue(state: AgentState) -> str:
    """Route based on the last message content."""
    last_message = state["messages"][-1]
    if "NEEDS_REVIEW" in last_message.content:
        return "review"
    return "report"
```

### Step 4 — Build the Graph

```python
from langgraph.graph import StateGraph, START, END

# Create the graph
graph = StateGraph(AgentState)

# Add nodes
graph.add_node("analyze", analyze)
graph.add_node("review", human_review)
graph.add_node("report", generate_report)

# Add edges
graph.add_edge(START, "analyze")
graph.add_conditional_edges("analyze", should_continue, {
    "review": "review",
    "report": "report",
})
graph.add_edge("review", "analyze")  # cycle: review → re-analyze
graph.add_edge("report", END)

# Compile
app = graph.compile()
```

### Step 5 — Run the Graph

```python
from langchain_core.messages import HumanMessage

result = app.invoke({
    "messages": [HumanMessage(content="Analyze this log file...")],
    "current_step": "",
    "result": "",
})
print(result["result"])
```

---

## Common Patterns

### Pattern 1 — ReAct Agent with Tools

The simplest LangGraph pattern. Use `create_react_agent` for a single agent with tools.

```python
from langgraph.prebuilt import create_react_agent
from common.llm import create_llm

llm = create_llm()
tools = [search_logs, read_file, run_query]

agent = create_react_agent(llm, tools)
result = agent.invoke({
    "messages": [HumanMessage(content="Find errors in today's logs")]
})
```

### Pattern 2 — Sequential Pipeline

Nodes execute in a fixed order.

```python
graph = StateGraph(PipelineState)
graph.add_node("parse", parse_input)
graph.add_node("validate", validate_data)
graph.add_node("transform", transform_data)
graph.add_node("output", format_output)

graph.add_edge(START, "parse")
graph.add_edge("parse", "validate")
graph.add_edge("validate", "transform")
graph.add_edge("transform", "output")
graph.add_edge("output", END)
```

### Pattern 3 — Conditional Branching

Route to different nodes based on state.

```python
def classify_input(state) -> str:
    """Classify input type for routing."""
    content = state["messages"][-1].content.lower()
    if "bug" in content:
        return "bug_handler"
    elif "feature" in content:
        return "feature_handler"
    return "general_handler"

graph.add_conditional_edges("classifier", classify_input, {
    "bug_handler": "handle_bug",
    "feature_handler": "handle_feature",
    "general_handler": "handle_general",
})
```

### Pattern 4 — Self-Correction Loop

Agent checks its own work and retries if needed.

```python
def check_quality(state) -> str:
    """Evaluate output quality."""
    if state.get("retry_count", 0) >= 3:
        return "accept"  # give up after 3 retries
    if quality_score(state["result"]) < 0.8:
        return "retry"
    return "accept"

graph.add_conditional_edges("checker", check_quality, {
    "retry": "generator",   # loop back
    "accept": "output",
})
```

### Pattern 5 — Human-in-the-Loop

Pause the graph for human approval before continuing.

```python
from langgraph.checkpoint.memory import MemorySaver

# Compile with checkpointing (required for interrupts)
checkpointer = MemorySaver()
app = graph.compile(
    checkpointer=checkpointer,
    interrupt_before=["dangerous_action"],  # pause before this node
)

# Run until interrupt
config = {"configurable": {"thread_id": "user-123"}}
result = app.invoke(input_data, config)
# → Graph pauses before "dangerous_action"

# User reviews, then resume
result = app.invoke(None, config)  # continues from checkpoint
```

**When to use interrupt_before vs interrupt_after:**
- `interrupt_before` — pause BEFORE the node runs (for approval gates)
- `interrupt_after` — pause AFTER the node runs (for review of output)

### Pattern 6 — Multi-Agent Graph

Each node is a different specialist agent.

```python
from langgraph.prebuilt import create_react_agent

# Create specialist agents
researcher = create_react_agent(
    create_llm(), [web_search, read_document],
    prompt="You are a research specialist..."
)
writer = create_react_agent(
    create_llm(temperature=0.7), [write_file, format_text],
    prompt="You are a technical writer..."
)
reviewer = create_react_agent(
    create_llm(), [read_file, check_style],
    prompt="You are a code reviewer..."
)

# Wire into graph
graph = StateGraph(TeamState)
graph.add_node("research", researcher)
graph.add_node("write", writer)
graph.add_node("review", reviewer)

graph.add_edge(START, "research")
graph.add_edge("research", "write")
graph.add_edge("write", "review")
graph.add_conditional_edges("review", needs_revision, {
    "revise": "write",
    "approve": END,
})
```

### Pattern 7 — Subgraphs

Nest one graph inside another for modular design.

```python
# Define inner graph
inner_graph = StateGraph(InnerState)
inner_graph.add_node("step_a", do_a)
inner_graph.add_node("step_b", do_b)
inner_graph.add_edge(START, "step_a")
inner_graph.add_edge("step_a", "step_b")
inner_graph.add_edge("step_b", END)
inner_compiled = inner_graph.compile()

# Use as a node in outer graph
outer_graph = StateGraph(OuterState)
outer_graph.add_node("preprocess", preprocess)
outer_graph.add_node("inner_workflow", inner_compiled)  # subgraph as node
outer_graph.add_node("postprocess", postprocess)
```

---

## Checkpointing and Persistence

### In-Memory (Development)

```python
from langgraph.checkpoint.memory import MemorySaver
checkpointer = MemorySaver()
app = graph.compile(checkpointer=checkpointer)
```

### SQLite (Production — Single Instance)

```python
from langgraph.checkpoint.sqlite import SqliteSaver
checkpointer = SqliteSaver.from_conn_string("checkpoints.db")
app = graph.compile(checkpointer=checkpointer)
```

### Thread Management

Every conversation gets a unique thread_id for state isolation:

```python
config = {"configurable": {"thread_id": "unique-conversation-id"}}
result = app.invoke(input_data, config)
```

---

## Streaming

### Stream Node Outputs

```python
for event in app.stream(input_data, config):
    for node_name, output in event.items():
        print(f"[{node_name}] {output}")
```

### Stream LLM Tokens

```python
for event in app.stream(input_data, config, stream_mode="messages"):
    # event is (message_chunk, metadata)
    print(event[0].content, end="", flush=True)
```

---

## Operation: DEBUG — Diagnosing Graph Issues

### Visualization

```python
# Print the graph structure
print(app.get_graph().draw_mermaid())
```

### Common Issues

| Symptom | Cause | Fix |
|---|---|---|
| Graph runs forever | Missing END edge or broken conditional | Ensure every path reaches END, add recursion limit |
| State not updating | Node returns wrong keys | Return dict with exact TypedDict field names |
| Messages duplicating | Not using `add_messages` reducer | Use `Annotated[list, add_messages]` for message fields |
| Checkpoint errors | No checkpointer configured | Add `MemorySaver()` to `compile()` |
| Human-in-the-loop not pausing | Missing checkpointer | Interrupts require a checkpointer |
| Wrong node executes | Conditional edge returns wrong key | Print routing decisions, verify return values match edge map |

### Recursion Limit

Prevent infinite loops:

```python
app = graph.compile()
result = app.invoke(
    input_data,
    config={"recursion_limit": 25},  # default is 25
)
```

---

## When NOT to Use LangGraph

- **Simple Q&A** — use a direct LLM call
- **Linear pipeline with no branching** — use a simple chain (`prompt | llm | parser`)
- **Single agent with tools** — use `create_react_agent` directly (still LangGraph, but no custom graph needed)
- **No state between calls** — use stateless LangChain chains

**Start with the simplest approach. Escalate to a custom StateGraph only when you need branching, cycles, human-in-the-loop, or multi-agent coordination.**

---

## Post-Build Verification

- [ ] Every path through the graph reaches END
- [ ] State TypedDict includes all fields nodes read/write
- [ ] List fields use `Annotated` with appropriate reducers
- [ ] Conditional edges return values that match the edge map exactly
- [ ] Recursion limit is set to prevent infinite loops
- [ ] Checkpointer is configured if using interrupts or persistence
- [ ] Graph visualization matches intended flow (`draw_mermaid()`)
- [ ] Each node does one thing and returns a partial state update
