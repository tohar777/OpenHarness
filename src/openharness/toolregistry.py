import inspect

class ToolRegistry:

    def __init__(self):
        self.tools = {}

    def register(self, name, description, function, parameters):
        self.tools[name] = {
            "description": description,
            "function": function,
            "parameters": parameters
        }

    def get_schemas(self):
        return [
            {
                "type": "function",
                "function": {
                    "name": name,
                    "description": tool["description"],
                    "parameters": tool["parameters"]
                }
            }
            for name, tool in self.tools.items()
        ]

    

    async def execute(self, name, arguments):
            if name not in self.tools:
                raise ValueError(f"Unknown tool: {name}")

            function = self.tools[name]["function"]
            result = function(**arguments)

            if inspect.isawaitable(result):
                result = await result

            return result
