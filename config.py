import os
DATA = """
                {
                    "API_URL" : "https://openrouter.ai/api/v1/chat/completions",
                    "API_KEY" : "sk-or-v1-123abc",
                    "MODEL" : "nvidia/nemotron-3.5-super-vl:free",
                    "DEBUG":"false"
                }
            """
try:
    os.mkdir("config")
    with open("config/config.json", "x") as file:
        file.write(DATA)
except FileExistsError:
    print("Error: config already already exists!")