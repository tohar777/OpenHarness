
import requests
import os
import time
import json
import sys
import asyncio
import httpx
from plugins.loader import loadPlugins
from openharness.system_config import systemprompt
from openharness.filesystem import FileSystem
from openharness.toolregistry import ToolRegistry
from openharness.shellexecution import ShellExecution
from openharness.mcp_client import MCPClient
from openharness.websearch import WebSearch
from openharness.skills import SkillManager
from openharness.tui import OpenHarnessTUI
API_URL = ""
API_KEY = ""
MODEL = ""
DEBUG = ""

async def agent(userMessage, messages):
    messages.append({
        "role": "user",
        "content": userMessage
    })

    while True:
        assistant_message = await chat(messages)

        if assistant_message.get("tool_calls"):
            await execute_tool_calls(
                assistant_message,
                messages
            )
            continue

        messages.append(assistant_message)

        return assistant_message.get("content", "")

async def execute_tool_calls(message, messages):
    messages.append(message)

    for tool_call in message.get("tool_calls", []):
        name = tool_call["function"]["name"]
        arguments = json.loads(tool_call["function"]["arguments"])

        if DEBUG == "true":
            print(f"\n[Tool] Calling: {name}")
            print(f"[Tool] Arguments: {arguments}")

        try:
            result = await registry.execute(name, arguments)
            output = json.dumps(result, ensure_ascii=False, default=str)

            if DEBUG == "true":
                print(f"[Tool] Result: {output}")

        except Exception as e:
            output = json.dumps({"error": str(e)})
            print(f"[Tool] Error: {e}")

        messages.append({
            "role": "tool",
            "tool_call_id": tool_call["id"],
            "content": output
        })

async def initialize():
    registry = await initialize_tools()

    mcp_client = MCPClient()
    await mcp_client.load_config(
        registry,
        "config/mcp.json"
    )

    return registry, mcp_client


async def initialize_tools():
    registry = ToolRegistry()
    fs = FileSystem("./")
    se = ShellExecution()
    mcp_client = MCPClient()
    ws = WebSearch()
    skill = SkillManager()
    registry.register(
        "skill_catalog",
        "list of available skill in the skills directory",
        skill.get_catalog,
        {
            "type": "object",
            "properties": {},
            "additionalProperties": False
        }
    )
    registry.register(
        "load_skill",
        "load a skill's full instruction when relevant to user",
        skill.load_skill,
        {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Name of the skill to load."
                }
            },
            "required": ["name"],
            "additionalProperties": False
        }
    )
    registry.register(
        "read_file",
        "Read a text file from the workspace.",
        fs.read_file,
        {
            "type": "object",
            "properties": {
                "filename": {"type": "string"}
            },
            "required": ["filename"],
            "additionalProperties": False
        }
    )

    registry.register(
        "shell",
        "Use shell to execute commands like touch or mkdir.",
        se.execute_shell,
        {
            "type": "object",
            "properties": {
                "cmd": {"type": "string"}
            },
            "required": ["cmd"],
            "additionalProperties": False
        }
    )

    registry.register(
        "write_file",
        "Create or modify a text file in the workspace.",
        fs.write_file,
        {
            "type": "object",
            "properties": {
                "filename": {"type": "string"},
                "content": {"type": "string"}
            },
            "required": ["filename", "content"],
            "additionalProperties": False
        }
    )

    registry.register(
        "list_files",
        "List files in the workspace.",
        fs.list_files,
        {
            "type": "object",
            "properties": {},
            "additionalProperties": False
        }
    )
    registry.register(
        "web_search",
        "Search the internet for information. ",
        ws.web_search,
        {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "max_results": {"type": "integer"}
            },
            "required": ["query"],
            "additionalProperties": False
        }
    )
    registry.register(
        "web_fetch",
        "Fetch infomation from the internet",
        ws.web_fetch,
        {
            "type": "object",
            "properties": {
                "url": {"type": "string"},
            },
            "required": ["url"],
            "additionalProperties": False
        }
    )
    loadPlugins(registry)
    # Load MCP servers from config/mcp.json
    await mcp_client.load_config(registry)

    print("[OpenHarness] Tools initialized.")

    return registry,mcp_client
def initCredentials():
    try:
        with open("config/config.json", "r") as config:
                info = json.load(config)
    except:
        pass

    API_URL = info["API_URL"]
    API_KEY = info["API_KEY"]
    MODEL = info["API-MODEL"]
    DEBUG = info["DEBUG"]
    #SYSTEM_PROMPT = info["SYSTEM_PROMPT"]
    return API_URL, API_KEY, MODEL,DEBUG
    

def typewriter(text, speed=0.01):
    if not text:
        return
    for char in text:
        print(char, end="", flush=True)
        time.sleep(speed)
    print() 

async def chat(messages: list) -> dict:
    if not API_KEY:
        raise RuntimeError("Missing OPENROUTER_API_KEY environment variable.")

    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(
            API_URL,
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": MODEL,
                "messages": messages,
                "tools": registry.get_schemas(),
                "tool_choice": "auto",
                "reasoning": {
                    "enabled": True
                }
            }
        )

    if not response.is_success:
        raise RuntimeError(
            f"OpenRouter error ({response.status_code}): {response.text}"
        )

    data = response.json()

    if "choices" not in data or not data["choices"]:
        raise RuntimeError(f"Unexpected response: {data}")

    return data["choices"][0]["message"]


async def main():
    global registry

    registry, mcp_client = await initialize_tools()

    print("OpenHarness v0.5")
    print("----------------")

    messages = [
        {"role": "system", "content": systemprompt()}
    ]

    try:
        app = OpenHarnessTUI(agent, messages)
        await app.run_async()
    finally:
        await mcp_client.disconnect_all()

if __name__ == "__main__":
    API_URL, API_KEY, MODEL,DEBUG = initCredentials()
    asyncio.run(main())
