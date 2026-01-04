import os
from dotenv import load_dotenv
from importlib.resources import files, as_file
# 加载 .env 文件中的环境变量
def load_env():
    home_env = os.path.expanduser("~/.open_codex.env")
    if os.path.exists(home_env):
        load_dotenv(home_env)
        print(f"Loaded .env from {home_env}")
        return True
    # 4. 查包内自带的 .env（只读，不能写入敏感信息）
    try:
        with as_file(files("open_codex").joinpath(".env")) as pkg_env:
            if os.path.exists(pkg_env):
                load_dotenv(pkg_env)
                print(f"Loaded .env from package: {pkg_env}")
                return True
    except Exception as e:
        pass

    print("No .env file found in any known location.")
    return False

# 数据库连接信息
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "10.37.1.199")
DB_PORT = os.getenv("DB_PORT", "3308")
DB_NAME = os.getenv("DB_NAME")

# llm config
MODEL_NAME = os.getenv("MODEL_NAME")
# APT_BASE = os.getenv("API_BASE")
API_KEY = os.getenv("API_KEY")

# ollama config
OLLAMA_MODEL_NAME = os.getenv("OLLAMA_MODEL_NAME")
OLLAMA_HOST = os.getenv("OLLAMA_HOST")

print(f"{DB_USER},{MODEL_NAME},{OLLAMA_HOST}")
