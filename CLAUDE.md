# Claude Configuration

This document contains Claude-specific configuration and guidelines for the Novel to Toon project.

## Project Context

This is an agentic workflow application that combines:
- **Claude Agent SDK**: For building intelligent agent behaviors and orchestrating tasks
- **Google Gemini API**: For generating images from text descriptions

## Architecture

The application follows an agent-based architecture where:
1. Claude acts as the orchestration layer, managing the workflow
2. The agent receives novel text descriptions as input
3. The agent processes and structures the request
4. Google's Gemini API generates images based on the processed descriptions

## Environment Configuration

The application requires two environment variables:

- `CLAUDE_CODE_OAUTH_TOKEN`: Authentication token for Claude Code access
- `GOOGLE_API_KEY`: API key for Google's Gemini image generation service

## Agent SDK Integration

The Claude Agent SDK is used to:
- Define agent behaviors and capabilities
- Handle conversation state and context
- Manage tool calling and external integrations
- Structure the workflow between input processing and image generation

## Development Guidelines

When working with Claude on this project:

1. **Agent Design**: Focus on creating clear, purposeful agent behaviors
2. **Error Handling**: Implement robust error handling for both API calls
3. **Token Management**: Be mindful of token usage in agent conversations
4. **Streaming**: Consider using streaming for real-time feedback
5. **Testing**: Test both the agent logic and API integrations independently

## Key Integration Points

- **Input Processing**: Agent interprets and structures novel descriptions
- **API Coordination**: Manages the flow between Claude and Gemini APIs
- **Output Handling**: Processes and presents generated images
- **State Management**: Maintains context throughout the workflow

## Resources

- [Claude Agent SDK Documentation](https://platform.claude.com/docs/en/agent-sdk/python)
- [Google Gemini API Documentation](https://ai.google.dev/gemini-api/docs/image-generation)
- Project guides in `docs/` directory
