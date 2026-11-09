
import json
from contextlib import AsyncExitStack
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class MCPClient:
    def __init__(self):
        self.sessions = {}
        self.exit_stack = AsyncExitStack()

    async def connect_stdio(
        self, name, command, args=None, env=None
    ):
        params = StdioServerParameters(
            command=command,
            args=args or [],
            env=env or None
        )

        read_stream, write_stream = await self.exit_stack.enter_async_context(
            stdio_client(params)
        )

        session = await self.exit_stack.enter_async_context(
            ClientSession(read_stream, write_stream)
        )

        await session.initialize()

        self.sessions[name] = session

        result = await session.list_tools()

        print(f"[MCP] Connected: {name}")

        for tool in result.tools:
            print(f"[MCP] Discovered: {name}_{tool.name}")

        return result.tools

    async def connect_server(
        self, registry, name, command, args=None, env=None
    ):
        tools = await self.connect_stdio(
            name, command, args, env
        )

        session = self.sessions[name]

        for tool in tools:
            async def execute_mcp_tool(arguments, _name=tool.name, _session=session):
                result = await _session.call_tool(_name, arguments)

                if result.isError:
                    raise RuntimeError(
                        f"MCP tool failed: {result.content}"
                    )

                return result.structuredContent or [
                    getattr(block, "text", str(block))
                    for block in result.content
                ]

            registry.register(
                f"{name}_{tool.name}",
                tool.description or f"MCP tool from {name}",
                execute_mcp_tool,
                tool.inputSchema
            )

        return {
            "server": name,
            "tools": [f"{name}_{tool.name}" for tool in tools]
        }

    async def load_config(
        self, registry, config_path="config/mcp.json"
    ):
        path = Path(config_path)

        if not path.exists():
            print(f"[MCP] Config not found: {path}")
            return

        with path.open("r", encoding="utf-8") as file:
            config = json.load(file)

        for name, server in config.get("servers", {}).items():
            if server.get("transport") != "stdio":
                continue

            try:
                result = await self.connect_server(
                    registry,
                    name,
                    server["command"],
                    server.get("args", []),
                    server.get("env", {})
                )

                print(
                    f"[MCP] Registered {len(result['tools'])} "
                    f"tools from {name}"
                )

            except Exception as e:
                print(f"[MCP] Failed to connect to {name}: {e}")

    async def call_tool(
        self, server_name, tool_name, arguments
    ):
        session = self.sessions[server_name]

        result = await session.call_tool(
            tool_name,
            arguments
        )

        if result.isError:
            raise RuntimeError(
                f"MCP tool failed: {result.content}"
            )

        return result.structuredContent or [
            getattr(block, "text", str(block))
            for block in result.content
        ]

    async def disconnect_all(self):
        await self.exit_stack.aclose()
        self.sessions.clear()
