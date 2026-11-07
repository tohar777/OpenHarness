
import requests
import os
import time
import json
import sys
from openharness.filesystem import FileSystem
from openharness.toolregistry import ToolRegistry
API_URL = ""
API_KEY = ""
MODEL = ""
DEBUG = ""
def execute_tool_calls(message, messages):
    messages.append(message)

    for tool_call in message.get("tool_calls", []):
        name = tool_call["function"]["name"]
        arguments = json.loads(tool_call["function"]["arguments"])
        if DEBUG == "true":
            print(f"\n[Tool] Calling: {name}")
            print(f"[Tool] Arguments: {arguments}")
        elif DEBUG == "false":
            pass
        else:
            print("[OPENHARNESS] Invalid boolean value!")

        try:
            result = registry.execute(name, arguments)
            output = json.dumps(result, ensure_ascii=False)

            print(f"[Tool] Result: {output}")

        except Exception as e:
            output = json.dumps({"error": str(e)})
            print(f"[Tool] Error: {e}")

        messages.append({
            "role": "tool",
            "tool_call_id": tool_call["id"],
            "content": output
        })

def initialize_tools():
    registry = ToolRegistry()
    fs = FileSystem("./")

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

    return registry
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
    return API_URL, API_KEY, MODEL,DEBUG
    

def typewriter(text, speed=0.01):
    if not text:
        return
    for char in text:
        print(char, end="", flush=True)
        time.sleep(speed)
    print() 

def chat(messages: list) -> dict:
    if not API_KEY:
        raise RuntimeError("Missing OPENROUTER_API_KEY environment variable.")

    response = requests.post(
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
        },
        timeout=120
    )

    if not response.ok:
        raise RuntimeError(
            f"OpenRouter error ({response.status_code}): {response.text}"
        )

    data = response.json()

    if "choices" not in data or not data["choices"]:
        raise RuntimeError(f"Unexpected response: {data}")

    return data["choices"][0]["message"]



def main():
    global registry
    registry = initialize_tools()
    print("OpenHarness v0.1")
    print("----------------")

    messages = []

    while True:
        try:
            userMessage = input("\nYou: ").strip()

            if not userMessage:
                continue

            if userMessage == "/exit":
                print("Goodbye!")
                break

            messages.append({
                "role": "user",
                "content": userMessage
            })

            # Send request
            
            #assistant_message = chat(messages)
            assistant_message = chat(messages)

            if assistant_message.get("tool_calls"):
                execute_tool_calls(assistant_message, messages)
                continue
            # Preserve the complete assistant message,
            # including reasoning_details
            messages.append(assistant_message)

            typewriter(assistant_message.get("content"))

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break

        except EOFError:
            print("\nGoodbye!")
            break

        except requests.RequestException as error:
            print(f"\nNetwork error: {error}")
            if messages and messages[-1]["role"] == "user":
                messages.pop()

        except RuntimeError as error:
            print(f"\nError: {error}")
            if messages and messages[-1]["role"] == "user":
                messages.pop()

if __name__ == "__main__":
    API_URL, API_KEY, MODEL,DEBUG = initCredentials()
    main()
