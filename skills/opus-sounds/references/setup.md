# Connect the live directory

Skill installation and MCP setup are separate. Read access uses the public endpoint and does not require an API key. Do not overwrite a user's existing agent configuration; merge only the requested server entry.

## Claude Code

Run in the intended project:

```sh
claude mcp add --transport http opus-sounds https://opussounds.directory/mcp
```

Check the server with `claude mcp list`, then reload the agent if needed.

## Cursor

Merge this into the project's `.cursor/mcp.json`, or the user's `~/.cursor/mcp.json` for all projects:

```json
{
  "mcpServers": {
    "opus-sounds": {
      "url": "https://opussounds.directory/mcp"
    }
  }
}
```

Reload or enable the server in Cursor's MCP settings.

## Other clients

In a client supporting remote MCP, add `https://opussounds.directory/mcp` as a Streamable HTTP server. Follow that client's configuration format; the Cursor JSON above is not universal. Some clients support MCP without Agent Skills, and some support skills without MCP. The website and public catalog remain usable without either integration.

Verify that read tools such as `search_sounds` and `get_sound` appear. Try: “Find a gentle notification sound under one second.” An installed skill alone does not prove that the server is connected.

Official setup references:

- https://code.claude.com/docs/en/mcp
- https://cursor.com/docs/mcp
- https://github.com/vercel-labs/skills
