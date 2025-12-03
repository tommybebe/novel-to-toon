# Comprehensive Claude Agent SDK for Python Usage Guide

## Table of Contents
1. [Installation and Setup](#installation-and-setup)
2. [Core Concepts and Architecture](#core-concepts-and-architecture)
3. [Creating Agents and Defining Behaviors](#creating-agents-and-defining-behaviors)
4. [Tool Calling and Integrations](#tool-calling-and-integrations)
5. [Conversation Management and State Handling](#conversation-management-and-state-handling)
6. [Streaming Responses](#streaming-responses)
7. [Error Handling and Best Practices](#error-handling-and-best-practices)
8. [Complete Code Examples](#complete-code-examples)
9. [Advanced Features](#advanced-features)
10. [Common Patterns and Use Cases](#common-patterns-and-use-cases)

---

## 1. Installation and Setup

### Prerequisites
- Python 3.10 or higher
- API key from Claude Console (set `ANTHROPIC_API_KEY` environment variable)
- Node.js 18+ (optional, for Claude Code CLI functionality)

### Installation

```bash
pip install claude-agent-sdk
```

The Claude Code CLI is **automatically bundled** with the package—no separate installation required. The SDK will use the bundled CLI by default.

If you prefer a system-wide installation:
```bash
curl -fsSL https://claude.ai/install.sh | bash
```

### Verify Installation

```python
import claude_agent_sdk
print(f"Installed version: {claude_agent_sdk.__version__}")
```

---

## 2. Core Concepts and Architecture

### Two Interaction Modes

The SDK provides two distinct approaches:

#### A. Simple Queries (`query()`)
- **Use case:** One-off, stateless interactions
- **When to use:** When you don't need conversation history
- **Returns:** AsyncIterator of messages
- **Streaming:** Native support

#### B. Session-Based Client (`ClaudeSDKClient`)
- **Use case:** Interactive, multi-turn conversations
- **When to use:** Complex workflows requiring context persistence
- **Features:** Custom tools, hooks, session management
- **Streaming:** Full support with real-time monitoring

### Architecture Components

```
ClaudeSDKClient
├── Session Management (conversation state, context)
├── Tool System (Read, Write, Bash, Custom Tools)
├── MCP Integration (Model Context Protocol servers)
├── Hooks (PreToolUse, PostToolUse for validation/feedback)
├── Permissions (allowed_tools, permission modes)
└── Streaming (async iterators for real-time responses)
```

---

## 3. Creating Agents and Defining Behaviors

### Basic Query (Simplest Approach)

```python
import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions

async def simple_agent():
    """Basic agent that responds to a single prompt"""
    options = ClaudeAgentOptions(
        system_prompt="You are a helpful Python expert",
        cwd="/home/user/project"
    )

    async for message in query(
        prompt="Explain the concept of async/await in Python",
        options=options
    ):
        print(message)

asyncio.run(simple_agent())
```

### Session-Based Agent with ClaudeSDKClient

```python
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions
import asyncio

async def session_agent():
    """Multi-turn agent with conversation history"""
    options = ClaudeAgentOptions(
        system_prompt="You are an expert code reviewer",
        permission_mode='acceptEdits',
        cwd="/home/user/project"
    )

    async with ClaudeSDKClient(options=options) as client:
        # First turn
        await client.query("Review this Python file for style issues")

        # Receive response
        async for message in client.receive_response():
            print(f"Claude: {message}")

        # Second turn - Claude remembers context
        await client.query("Now refactor the code for better performance")

        # Receive second response
        async for message in client.receive_response():
            print(f"Claude: {message}")

asyncio.run(session_agent())
```

---

## 4. Tool Calling and Integrations

### Built-in Tools

The SDK provides default tools:
- **Read**: Read file contents
- **Write**: Create or modify files
- **Bash**: Execute shell commands
- **Search**: Web search capability

### Controlling Tool Access

```python
options = ClaudeAgentOptions(
    allowed_tools=["Read", "Write", "Bash"],  # Whitelist specific tools
    permission_mode='acceptEdits',  # Auto-accept file edits
)
```

### Creating Custom Tools with @tool Decorator

```python
from claude_agent_sdk import tool, create_sdk_mcp_server, ClaudeAgentOptions, query
import asyncio

# Define a custom tool
@tool(
    name="calculator",
    description="Perform mathematical operations",
    input_schema={"operation": str, "a": float, "b": float}
)
async def calculator_tool(args):
    """Execute a math operation"""
    operation = args.get("operation")
    a = args.get("a")
    b = args.get("b")

    if operation == "add":
        result = a + b
    elif operation == "subtract":
        result = a - b
    elif operation == "multiply":
        result = a * b
    elif operation == "divide":
        result = a / b if b != 0 else "Error: Division by zero"
    else:
        result = "Unknown operation"

    return {
        "content": [
            {"type": "text", "text": f"Result: {result}"}
        ]
    }

# Create MCP server with custom tool
server = create_sdk_mcp_server(
    name="math-tools",
    version="1.0.0",
    tools=[calculator_tool]
)

async def use_custom_tools():
    """Use custom tools in a query"""
    options = ClaudeAgentOptions(
        mcp_servers={"math": server},
        allowed_tools=["mcp__math__calculator"],  # Format: mcp__{server_name}__{tool_name}
    )

    async for message in query(
        prompt="What is 42 times 7?",
        options=options
    ):
        print(message)

asyncio.run(use_custom_tools())
```

### Multiple Custom Tools

```python
@tool("fetch_api", "Fetch data from an API", {"url": str})
async def fetch_tool(args):
    # Implementation
    return {"content": [{"type": "text", "text": "API Response"}]}

@tool("parse_json", "Parse JSON data", {"data": str})
async def parse_tool(args):
    # Implementation
    return {"content": [{"type": "text", "text": "Parsed data"}]}

# Combine multiple tools in one server
server = create_sdk_mcp_server(
    name="api-tools",
    version="1.0.0",
    tools=[fetch_tool, parse_tool]
)

options = ClaudeAgentOptions(
    mcp_servers={"api": server},
    allowed_tools=[
        "mcp__api__fetch_api",
        "mcp__api__parse_json"
    ]
)
```

---

## 5. Conversation Management and State Handling

### Session Creation and Resumption

```python
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions
import asyncio

async def session_example():
    """Demonstrate session creation and state management"""
    options = ClaudeAgentOptions(
        system_prompt="You are a helpful assistant with memory",
    )

    # Create a new session
    async with ClaudeSDKClient(options=options) as client:
        # Turn 1
        await client.query("Remember: I love Python programming")
        async for msg in client.receive_response():
            print(f"Turn 1: {msg}")

        # Turn 2 - Claude remembers context
        await client.query("What do I love?")
        async for msg in client.receive_response():
            print(f"Turn 2: {msg}")

asyncio.run(session_example())
```

### Managing Session State

```python
async def session_state_management():
    """Manage multiple sessions and state"""
    options = ClaudeAgentOptions()

    async with ClaudeSDKClient(options=options) as client:
        # Check current session
        session_id = client.session_id
        print(f"Current session: {session_id}")

        # Clear state and start fresh
        await client.disconnect()
        await client.connect()
        print(f"New session after reconnect: {client.session_id}")

        # Resume specific session
        await client.query(prompt="Some prompt", session_id="specific_session_id")

asyncio.run(session_state_management())
```

### Monitoring Conversation Progress

```python
from claude_agent_sdk import (
    ClaudeSDKClient,
    ClaudeAgentOptions,
    AssistantMessage,
    ToolUseBlock,
    ToolResultBlock,
    TextBlock
)
import asyncio

async def monitor_conversation():
    """Monitor real-time progress during execution"""
    options = ClaudeAgentOptions(
        allowed_tools=["Write", "Bash"],
        permission_mode="acceptEdits"
    )

    async with ClaudeSDKClient(options=options) as client:
        await client.query("Create a Python REST API with FastAPI")

        # Monitor messages in real-time
        async for message in client.receive_messages():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, ToolUseBlock):
                        print(f"[TOOL] {block.name}: {block.input}")
                    elif isinstance(block, ToolResultBlock):
                        print(f"[RESULT] Tool execution completed")
                    elif isinstance(block, TextBlock):
                        print(f"[TEXT] {block.text[:100]}...")

asyncio.run(monitor_conversation())
```

---

## 6. Streaming Responses

### Basic Streaming with query()

```python
from claude_agent_sdk import query
import asyncio

async def basic_streaming():
    """Stream responses from a simple query"""
    async for message in query(prompt="Write a Python function to sort a list"):
        print(f"Received: {message}")

asyncio.run(basic_streaming())
```

### Streaming with ClaudeSDKClient

```python
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions
import asyncio

async def client_streaming():
    """Stream multi-turn conversation responses"""
    options = ClaudeAgentOptions()

    async with ClaudeSDKClient(options=options) as client:
        # Query 1
        await client.query("Explain web sockets")

        # Receive and stream response 1
        async for message in client.receive_response():
            print(f"Message 1: {message}")

        # Query 2
        await client.query("How do they compare to HTTP?")

        # Receive and stream response 2
        async for message in client.receive_response():
            print(f"Message 2: {message}")

asyncio.run(client_streaming())
```

### Handling Streaming Events

```python
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions
import asyncio

async def handle_streaming_events():
    """Process different types of streaming events"""
    options = ClaudeAgentOptions(allowed_tools=["Write", "Bash"])

    async with ClaudeSDKClient(options=options) as client:
        await client.query("Create a test file and run it")

        # Process all messages including tool calls
        async for message in client.receive_messages():
            print(f"Event type: {type(message).__name__}")
            print(f"Content: {message}")

asyncio.run(handle_streaming_events())
```

---

## 7. Error Handling and Best Practices

### Exception Hierarchy

```python
from claude_agent_sdk import (
    ClaudeSDKError,
    CLINotFoundError,
    ProcessError,
    CLIJSONDecodeError
)
import asyncio

async def error_handling_example():
    """Handle various error types"""
    try:
        from claude_agent_sdk import query
        async for message in query(prompt="Test"):
            print(message)

    except CLINotFoundError as e:
        print(f"CLI not found: {e}")
        print("Install Claude Code CLI: curl -fsSL https://claude.ai/install.sh | bash")

    except ProcessError as e:
        print(f"Process error: {e}")
        print(f"Exit code: {e.exit_code}")
        print(f"Error output: {e.stderr}")

    except CLIJSONDecodeError as e:
        print(f"JSON decode error: {e}")

    except ClaudeSDKError as e:
        print(f"SDK error: {e}")

    except Exception as e:
        print(f"Unexpected error: {e}")

asyncio.run(error_handling_example())
```

### Robust Error Handling with Anthropic Errors

```python
from claude_agent_sdk import query
import anthropic
import asyncio
import time

async def robust_error_handling():
    """Handle API errors with retry logic"""
    max_retries = 3
    retry_count = 0

    while retry_count < max_retries:
        try:
            async for message in query(prompt="What is 2 + 2?"):
                print(message)
            break  # Success

        except anthropic.RateLimitError:
            retry_count += 1
            wait_time = 2 ** retry_count  # Exponential backoff
            print(f"Rate limited. Retrying in {wait_time} seconds...")
            await asyncio.sleep(wait_time)

        except anthropic.APIError as e:
            print(f"API error: {e.status_code} - {e.message}")
            raise

        except Exception as e:
            print(f"Error: {e}")
            raise

asyncio.run(robust_error_handling())
```

### Safety Hooks for Error Prevention

```python
from claude_agent_sdk import (
    ClaudeSDKClient,
    ClaudeAgentOptions,
    HookMatcher
)
import asyncio

async def check_bash_safety(input_data, tool_use_id, context):
    """Prevent dangerous bash commands"""
    tool_name = input_data.get("tool_name")
    tool_input = input_data.get("tool_input", {})

    if tool_name != "Bash":
        return {}

    command = tool_input.get("command", "")

    # Block dangerous patterns
    block_patterns = [
        "rm -rf /",
        "dd if=/dev/zero",
        ":(){:|:&};:",  # fork bomb
        "nc -l",  # netcat listener
    ]

    for pattern in block_patterns:
        if pattern in command:
            return {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": f"Dangerous command pattern blocked: {pattern}",
                }
            }

    return {}

async def agent_with_safety():
    """Agent with pre-execution safety checks"""
    options = ClaudeAgentOptions(
        allowed_tools=["Bash"],
        hooks={
            "PreToolUse": [
                HookMatcher(matcher="Bash", hooks=[check_bash_safety]),
            ],
        }
    )

    async with ClaudeSDKClient(options=options) as client:
        await client.query("Delete all files")  # Will be blocked

asyncio.run(agent_with_safety())
```

---

## 8. Complete Code Examples

### Example 1: Code Review Agent

```python
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions
import asyncio

async def code_review_agent():
    """Automated code reviewer"""
    options = ClaudeAgentOptions(
        system_prompt="""You are an expert code reviewer.
        Review code for:
        - Code quality and style
        - Performance issues
        - Security vulnerabilities
        - Test coverage
        Provide specific, actionable feedback.""",
        allowed_tools=["Read", "Write", "Bash"],
        permission_mode="acceptEdits",
        cwd="/home/user/project"
    )

    async with ClaudeSDKClient(options=options) as client:
        await client.query("Review all Python files in src/ directory for quality")

        # Stream the review
        async for message in client.receive_response():
            print(message)

asyncio.run(code_review_agent())
```

### Example 2: Data Analysis Agent

```python
from claude_agent_sdk import (
    tool,
    create_sdk_mcp_server,
    ClaudeSDKClient,
    ClaudeAgentOptions
)
import asyncio
import json

@tool(
    "load_csv",
    "Load and analyze CSV data",
    {"file_path": str}
)
async def load_csv(args):
    """Load CSV file"""
    file_path = args.get("file_path")
    # In real implementation, actually load CSV
    return {
        "content": [{"type": "text", "text": f"Loaded {file_path}"}]
    }

@tool(
    "compute_stats",
    "Compute statistical metrics",
    {"data": str, "metric": str}
)
async def compute_stats(args):
    """Compute statistics"""
    # In real implementation, compute actual stats
    return {
        "content": [{"type": "text", "text": "Stats computed"}]
    }

async def data_analyst():
    """Data analysis agent"""
    server = create_sdk_mcp_server(
        name="data-tools",
        version="1.0.0",
        tools=[load_csv, compute_stats]
    )

    options = ClaudeAgentOptions(
        system_prompt="You are a data analyst",
        mcp_servers={"data": server},
        allowed_tools=[
            "mcp__data__load_csv",
            "mcp__data__compute_stats",
            "Read",
            "Write"
        ]
    )

    async with ClaudeSDKClient(options=options) as client:
        await client.query("Analyze sales.csv and generate a report")
        async for message in client.receive_response():
            print(message)

asyncio.run(data_analyst())
```

### Example 3: Document Generation Workflow

```python
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions
import asyncio

async def document_generator():
    """Multi-step document generation"""
    options = ClaudeAgentOptions(
        system_prompt="""You are a technical writer. Create clear,
        well-structured documentation with examples.""",
        allowed_tools=["Read", "Write", "Bash"],
        permission_mode="acceptEdits"
    )

    steps = [
        "Read all source code files",
        "Extract key classes and functions",
        "Create API documentation with examples",
        "Generate a comprehensive README"
    ]

    async with ClaudeSDKClient(options=options) as client:
        for step in steps:
            print(f"\n--- Step: {step} ---")
            await client.query(step)

            async for message in client.receive_response():
                print(message)

asyncio.run(document_generator())
```

---

## 9. Advanced Features

### Prompt Caching (Automatic)

The SDK automatically implements prompt caching to:
- Reduce latency for repeated queries
- Lower API costs
- Improve throughput

```python
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions
import asyncio

async def prompt_caching_example():
    """Leverage automatic prompt caching"""
    # Large context that benefits from caching
    large_context = "..." * 1000  # Large documentation

    options = ClaudeAgentOptions(
        system_prompt=f"Reference documentation:\n{large_context}\n\nAnswer questions about this.",
    )

    # First query - creates cache
    async with ClaudeSDKClient(options=options) as client:
        await client.query("Question 1 about the documentation?")
        async for msg in client.receive_response():
            print(msg)

        # Second query - uses cache (faster, cheaper)
        await client.query("Question 2 about the documentation?")
        async for msg in client.receive_response():
            print(msg)

asyncio.run(prompt_caching_example())
```

### Context Compaction

The SDK automatically handles:
- Summarizing old conversations when context grows large
- Maintaining essential information
- Preventing token limit issues

```python
options = ClaudeAgentOptions(
    # SDK handles context compaction automatically
    # No explicit configuration needed
)
```

### Permission Modes

```python
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions
import asyncio

async def permission_example():
    """Different permission modes for different use cases"""

    # Mode 1: Ask before any action
    options_ask = ClaudeAgentOptions(permission_mode='ask')

    # Mode 2: Auto-accept file edits
    options_auto = ClaudeAgentOptions(permission_mode='acceptEdits')

    # Mode 3: Full autonomy (use with caution!)
    options_auto_all = ClaudeAgentOptions(permission_mode='acceptAll')

    # Mode 4: Read-only (safe for analysis)
    options_read_only = ClaudeAgentOptions(
        allowed_tools=["Read"],  # No Write or Bash
    )

asyncio.run(permission_example())
```

---

## 10. Common Patterns and Use Cases

### Pattern 1: Iterative Refinement

```python
async def iterative_refinement():
    """Refine outputs through multiple iterations"""
    options = ClaudeAgentOptions(
        system_prompt="Improve code quality on each iteration"
    )

    async with ClaudeSDKClient(options=options) as client:
        prompts = [
            "Write a function to parse CSV",
            "Add error handling",
            "Add type hints",
            "Add docstrings and comments"
        ]

        for prompt in prompts:
            await client.query(prompt)
            async for msg in client.receive_response():
                print(msg)
```

### Pattern 2: Multi-Agent Orchestration

```python
async def multi_agent_workflow():
    """Coordinate multiple specialized agents"""

    # Agent 1: Research
    research_options = ClaudeAgentOptions(
        system_prompt="You are a researcher. Find and summarize information.",
        allowed_tools=["Read", "Search"]
    )

    # Agent 2: Summarize
    summary_options = ClaudeAgentOptions(
        system_prompt="Summarize information concisely",
        allowed_tools=["Write"]
    )

    # Agent 3: Review
    review_options = ClaudeAgentOptions(
        system_prompt="Review for accuracy and clarity",
        allowed_tools=["Read"]
    )
```

### Pattern 3: Context Gathering and Action

```python
async def gather_and_act():
    """Gather context, then take action"""
    options = ClaudeAgentOptions(
        allowed_tools=["Read", "Write", "Bash", "Search"]
    )

    async with ClaudeSDKClient(options=options) as client:
        # Step 1: Gather context
        await client.query("Analyze the current codebase structure")
        async for msg in client.receive_response():
            print(f"[Analysis] {msg}")

        # Step 2: Take action based on context
        await client.query("Refactor the code based on your analysis")
        async for msg in client.receive_response():
            print(f"[Refactoring] {msg}")
```

### Use Case: Research Assistant

```python
async def research_assistant():
    """Research a topic and generate a report"""
    options = ClaudeAgentOptions(
        system_prompt="""You are a research assistant.
        1. Search for information about the topic
        2. Gather sources and data
        3. Synthesize findings
        4. Generate a comprehensive report""",
        allowed_tools=["Search", "Read", "Write"],
        permission_mode="acceptEdits"
    )

    async with ClaudeSDKClient(options=options) as client:
        await client.query("Research the latest developments in quantum computing and write a report")
        async for msg in client.receive_response():
            print(msg)
```

### Use Case: Code Generation and Testing

```python
async def code_generator():
    """Generate code and validate with tests"""
    options = ClaudeAgentOptions(
        system_prompt="Generate well-tested Python code",
        allowed_tools=["Write", "Bash", "Read"],
        permission_mode="acceptEdits"
    )

    async with ClaudeSDKClient(options=options) as client:
        await client.query("Create a Python function to calculate fibonacci numbers with unit tests")
        async for msg in client.receive_response():
            print(msg)
```

---

## API Reference Summary

### ClaudeAgentOptions

```python
ClaudeAgentOptions(
    system_prompt: str = None,          # System instructions
    permission_mode: str = 'ask',       # 'ask', 'acceptEdits', 'acceptAll'
    allowed_tools: List[str] = None,    # Whitelist of tools
    cwd: str = None,                    # Working directory
    mcp_servers: Dict[str, Any] = None, # Custom MCP servers
    hooks: Dict[str, List] = None,      # PreToolUse, PostToolUse hooks
    setting_sources: List[str] = None,  # Load from CLAUDE.md
)
```

### ClaudeSDKClient Methods

```python
await client.query(prompt: str, session_id: str = "default")
async for msg in client.receive_messages()  # All messages
async for msg in client.receive_response()  # Response messages
await client.interrupt()                    # Stop execution
await client.connect()                      # Connect to session
await client.disconnect()                   # Disconnect session
```

### Tool Decorator

```python
@tool(
    name: str,                    # Tool name
    description: str,             # Tool description
    input_schema: Dict[str, type] # Input parameters
)
async def tool_function(args):
    return {"content": [{"type": "text", "text": "result"}]}
```

---

## Resources

**Official Documentation:**
- [Python API Reference](https://docs.claude.com/en/docs/agent-sdk/python)
- [Agent SDK Overview](https://platform.claude.com/docs/en/agent-sdk/overview)
- [Session Management](https://platform.claude.com/docs/en/agent-sdk/sessions)

**GitHub Repository:**
- [Claude Agent SDK for Python](https://github.com/anthropics/claude-agent-sdk-python)
  - Examples: `examples/quick_start.py`, `examples/streaming_mode.py`
  - Error definitions: `src/claude_agent_sdk/_errors.py`

**Related Guides:**
- [Building Agents with Claude Agent SDK](https://www.anthropic.com/engineering/building-agents-with-the-claude-agent-sdk)
- [Permissions and Safety](https://code.claude.com/docs/en/sdk/sdk-permissions)

---

## Best Practices Summary

1. **Use appropriate interaction mode**: `query()` for simple tasks, `ClaudeSDKClient` for complex workflows
2. **Implement safety hooks**: Block dangerous operations at the PreToolUse stage
3. **Leverage automatic features**: Prompt caching and context compaction happen automatically
4. **Handle errors gracefully**: Catch specific exception types and implement retry logic
5. **Use custom tools wisely**: In-process MCP servers are faster than subprocess-based alternatives
6. **Manage sessions properly**: Clear state when needed, resume sessions for continuity
7. **Document context**: Use CLAUDE.md or .claude/CLAUDE.md for project-level instructions
8. **Monitor streaming**: Use `receive_messages()` for detailed event tracking
9. **Control permissions**: Start restrictive, expand only as needed
10. **Test thoroughly**: Verify agent behavior with edge cases and error conditions
