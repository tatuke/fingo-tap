import sys
import argparse
import subprocess
import os
import platform
import traceback
from dotenv import load_dotenv
from importlib.resources import files
from open_codex.agent_builder import AgentBuilder
from open_codex.storage_builder import recordcontext,get_db,get_database_url
from open_codex.interfaces.llm_agent import LLMAgent
from contextlib import contextmanager
from importlib.resources import as_file
GREEN = "\033[92m"
RED = "\033[91m"
BLUE = "\033[94m"
RESET = "\033[0m"

# Capture single keypress (terminal) from the user
# and returns it as a string. It works on both Windows and Unix systems.
# and before that let's introduce some key words
def load_env():
    home_env = os.path.expanduser("~/open_codex_config/.env")
    if os.path.exists(home_env):
        load_dotenv(home_env)
        print(f"Loaded .env from {home_env}")
        return True
    try:
        with as_file(files("open_codex").joinpath(".env")) as pkg_env:
            if os.path.exists(pkg_env):
                load_dotenv(pkg_env)
                print(f"Loaded .env from package: {pkg_env}")
                return True
    except Exception:
        pass
    print("No .env file found in any known location.")
    return False
    # load_dotenv(dotenv_path=dotenv_path)
def load_custom_prompt() -> str:
    return files("open_codex") \
        .joinpath("custom_prompt.txt") \
        .read_text(encoding="utf-8")

    

# Windows
if sys.platform == "win32":
    import msvcrt
    def get_keypress():
        return msvcrt.getch().decode("utf-8")
# Unix
else:
    import termios, tty
    def get_keypress():
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            key = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return key
    
# sys details
def get_system_info():
    system = platform.system()
    release = platform.release()
    version = platform.version()
    info = f"OSsystem: {system} {release} {version}"
    if system == "Linux":
        try:
            import distro
            info += f"\nDistribution: {distro.name(pretty=True)}"
        except ImportError:
            pass
    return info
# db session exception
@contextmanager
def get_db_session():
    db = next(get_db())
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        print("操作失败，错误详情：")
        traceback.print_exc()
        raise e
    finally:
        db.close()

def get_user_action():
    print(f"{BLUE}What do you want to do with this command?{RESET}")
    print(f"{BLUE}[c] Copy  [e] Execute  [a] Abort{RESET}")
    print(f"{BLUE}Press key: ", end="", flush=True)
    choice = get_keypress().lower()
    return choice

def run_user_action(choice: str, command: str):
    if choice == "c":
        print(f"{GREEN}Copying command to clipboard...{RESET}")
        if platform.system() == "Darwin":  # macOS
            subprocess.run("pbcopy", universal_newlines=True, input=command)
        elif platform.system() == "Linux":  # Linux
            subprocess.run("xclip -selection clipboard", universal_newlines=True, input=command, shell=True)
        elif platform.system() == "Windows":  # Win
            subprocess.run("clip", universal_newlines=True, input=command, shell=True)
        print(f"{GREEN}Command copied to clipboard!{RESET}")
    elif choice == "e":
        print(f"{GREEN}Executing command...{RESET}")
        subprocess.run(command, shell=True)
    else: 
        print(f"{RED}Aborting...{RESET}")
        sys.exit(1)
        # write down to database
    with get_db_session() as db:
        db.add(recordcontext(choice=choice, command=command))
        db.commit()

def print_response(command: str):
    print(f"{BLUE}Command found:\n=====================")
    print(f"{GREEN}{command}{RESET}")
    print(f"{BLUE}====================={RESET}")
    print(f"{RESET}")

def get_agent(args: argparse.Namespace) -> LLMAgent:
    # because needed to load env from every time when mission begin
    env_loaded = load_env()
    if not env_loaded:
        print(f"{RED}No .env file found. check ../src/open-codex/.env exists.{RESET}")

    config_model = os.getenv("OLLAMA_MODEL_NAME", "")
    config_host = os.getenv("OLLAMA_HOST", "")
    
    model = args.model if args.model != "" else config_model
    host = args.ollama_host if args.ollama_host != "" else config_host
    
    if args.ollama:
        print(f"{BLUE}Using Ollama with model: {model}{RESET}")
        return AgentBuilder.get_ollama_agent(model=model, host=host)        
    else:
        # print(f"{BLUE}Using model: phi-4-mini-instruct{RESET}")
        # return AgentBuilder.get_phi_agent()
    # using litellm as default
        print(f"{BLUE}Using model: litellm{RESET}")
        return AgentBuilder.get_litellm_agent()

# regx and add user pre-set condition from custom_prompt.txt when get user_input
# def regx_custom_condition(args: argparse.Namespace) -> LLMAgent:

# kind of diffcult... I'll verify its feasibility in a new project before submitting improvements here. prompt compress hah..20250701
    
def run_one_shot(agent: LLMAgent, user_prompt: str, custom_prompt: str, system_info: str) -> str:
    full_prompt = f"{user_prompt}\n\nSystem info: {system_info}\n\nOther conditions:{custom_prompt}"    
    try:
        return agent.one_shot_mode(full_prompt)
    except ConnectionError:
        print(f"{RED}Could not connect to Model.{RESET}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"{RED}Unexpected error: {e}{RESET}", file=sys.stderr)
        print(f"{RED}Exiting...{RESET}", file=sys.stderr)
        sys.exit(1)

# def run_multiple_shot


def get_help_message():
    return f"""
    {BLUE}Usage examples:{RESET}
    {GREEN}open-codex list all files in current directory
    {GREEN}open-codex --ollama find all python files modified in the last week
    {GREEN}open-codex --ollama --model llama3 "create a tarball of the src directory
    """

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Open Codex is a command line interface for LLMs."
                                     "It can be used to generate shell commands from natural language prompts.",
                                     formatter_class=argparse.RawTextHelpFormatter,
                                     epilog=get_help_message())

    parser.add_argument("prompt", nargs="+", 
                        help="Natural language prompt")
    parser.add_argument("--model", type=str, 
                        help="Model name to use (default: phi4-mini)", default="")
    parser.add_argument("--ollama", action="store_true", 
                        help="Use Ollama for LLM inference, use --model to specify the model" \
                        "if left empty, the config value is used.")
    parser.add_argument("--ollama-host", type=str, default="", 
                        help="Configure the host for the Ollama API. " \
                        "If left empty, the config value is used.")

    return parser.parse_args()

def main():
    args = parse_args()
    agent = get_agent(args)

    # join the prompt arguments into a single string
    prompt = " ".join(args.prompt).strip()
    system_info = get_system_info() 
    custom_prompt = load_custom_prompt()
    response = run_one_shot(agent, prompt, custom_prompt, system_info)
    print_response(response)
    action = get_user_action()
    run_user_action(action, response)

if __name__ == "__main__":
    # We call multiprocessing.freeze_support() because we are using PyInstaller to build a frozen binary.
    # When Python spawns helper processes (e.g., for Hugging Face downloads or resource tracking),
    # it uses sys.executable to start the current executable with special multiprocessing arguments.
    # Without freeze_support(), the frozen app would accidentally rerun the main CLI logic 
    # and crash (e.g., with argparse errors).
    # freeze_support() ensures the subprocess is handled correctly without restarting the full app.
    # This is required on macOS and Windows, where "spawn" is the default multiprocessing method.
    # See: https://pyinstaller.org/en/stable/common-issues-and-pitfalls.html#when-to-call-multiprocessing-freeze-support
    from multiprocessing import freeze_support
    freeze_support()
    main()