import sys
import argparse
import subprocess
import os
import platform
import traceback
import logging
from dotenv import load_dotenv
from importlib.resources import files
from open_codex.agent_builder import AgentBuilder
from open_codex.storage_builder import recordcontext,get_db,get_database_url
from open_codex.interfaces.llm_agent import LLMAgent
from open_codex.session.session_manager import FileSessionManager, InMemorySessionManager
from open_codex.executors.multistep_executor import MultiStepTaskExecutor
from open_codex.interfaces.multistep_task import TaskStatus, StepStatus
from contextlib import contextmanager
from importlib.resources import as_file
GREEN = "\033[92m"
RED = "\033[91m"
BLUE = "\033[94m"
RESET = "\033[0m"
try:
    import colorama
    colorama.init()
except Exception:
    pass

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
        return msvcrt.getch().decode("utf-8", errors="ignore")
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

def get_multistep_action():
    print(f"{BLUE}Multi-step task options:{RESET}")
    print(f"{BLUE}[n] Next step  [p] Pause  [r] Resume  [s] Status  [q] Quit{RESET}")
    print(f"{BLUE}Press key: ", end="", flush=True)
    choice = get_keypress().lower()
    return choice

def run_user_action(choice: str, command: str):
    extend_content = None
    if choice == "c":
        print(f"{GREEN}Copying command to clipboard...{RESET}")
        if platform.system() == "Darwin":  # macOS
            result = subprocess.run(
                "pbcopy",
                universal_newlines=True,
                input=command,
                capture_output=True,
                text=True,
            )
        elif platform.system() == "Linux":  # Linux
            result = subprocess.run(
                "xclip -selection clipboard",
                universal_newlines=True,
                input=command,
                shell=True,
                capture_output=True,
                text=True,
            )
        elif platform.system() == "Windows":  # Win
            result = subprocess.run(
                "clip",
                universal_newlines=True,
                input=command,
                shell=True,
                capture_output=True,
                text=True,
            )
        extend_content = f"returncode={result.returncode}\nstdout={result.stdout}\nstderr={result.stderr}"
        print(f"{GREEN}Command copied to clipboard!{RESET}")
    elif choice == "e":
        print(f"{GREEN}Executing command...{RESET}")
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
        )
        extend_content = f"returncode={result.returncode}\nstdout={result.stdout}\nstderr={result.stderr}"
    else: 
        print(f"{RED}Aborting...{RESET}")
        sys.exit(1)
        # write down to database
    with get_db_session() as db:
        db.add(recordcontext(choice=choice, command=command, extend_content=extend_content))
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

def run_multistep_task(agent: LLMAgent, user_prompt: str, custom_prompt: str, system_info: str, session_manager, dry_run: bool = False):
    """运行多步骤任务"""
    executor = MultiStepTaskExecutor(agent, session_manager, dry_run=dry_run)
    
    # 创建新的任务会话
    context = session_manager.create_session(user_prompt, system_info, custom_prompt)
    context.metadata['dry_run'] = dry_run
    
    print(f"{GREEN}Starting multi-step task: {context.task_id}{RESET}")
    print(f"{BLUE}Task: {user_prompt}{RESET}")
    
    try:
        # 分解任务
        steps = executor.decompose_task(user_prompt, context)
        context.steps = steps
        session_manager.save_session(context)
        
        print(f"{BLUE}Task decomposed into {len(steps)} steps:{RESET}")
        for i, step in enumerate(steps, 1):
            print(f"{BLUE}  {i}. {step.name}: {step.description}{RESET}")
        
        # 交互式执行
        while context.current_step_index < len(context.steps):
            current_step = context.steps[context.current_step_index]
            
            print(f"\n{BLUE}Current step ({context.current_step_index + 1}/{len(context.steps)}): {current_step.name}{RESET}")
            print(f"{BLUE}Description: {current_step.description}{RESET}")
            
            action = get_multistep_action()
            
            if action == 'n':
                print(f"{GREEN}Executing step...{RESET}")
                prev_index = context.current_step_index
                context = executor.execute_next_step(context)
                executed_step = context.steps[prev_index]
                if executed_step.status == StepStatus.COMPLETED:
                    print(f"{GREEN}Step completed successfully!{RESET}")
                    if executed_step.result:
                        print(f"{GREEN}Result: {executed_step.result}{RESET}")
                elif executed_step.status == StepStatus.FAILED:
                    print(f"{RED}Step failed: {executed_step.error}{RESET}")
                    if not executor.handle_step_failure(executed_step, context):
                        print(f"{RED}Critical step failed. Task aborted.{RESET}")
                        break
                        
            elif action == 'p':  # Pause
                context = executor.pause_task(context)
                print(f"{BLUE}Task paused. You can resume later with task ID: {context.task_id}{RESET}")
                break
                
            elif action == 'r':  # Resume (if paused)
                context = executor.resume_task(context)
                print(f"{GREEN}Task resumed.{RESET}")
                
            elif action == 's':  # Status
                progress = executor.get_task_progress(context)
                print(f"{BLUE}Task Progress:{RESET}")
                print(f"{BLUE}  Status: {progress['status']}{RESET}")
                print(f"{BLUE}  Progress: {progress['completed_steps']}/{progress['total_steps']} ({progress['progress_percentage']}%){RESET}")
                print(f"{BLUE}  Failed steps: {progress['failed_steps']}{RESET}")
                if progress['estimated_remaining_time']:
                    print(f"{BLUE}  Estimated remaining time: {progress['estimated_remaining_time']}{RESET}")
                    
            elif action == 'q':  # Quit
                context = executor.cancel_task(context)
                print(f"{RED}Task cancelled.{RESET}")
                break
                
            else:
                print(f"{RED}Invalid option. Please try again.{RESET}")
        
        # 检查最终状态
        if context.status == TaskStatus.COMPLETED:
            print(f"{GREEN}\nTask completed successfully!{RESET}")
        elif context.status == TaskStatus.FAILED:
            print(f"{RED}\nTask failed.{RESET}")
        elif context.status == TaskStatus.CANCELLED:
            print(f"{BLUE}\nTask was cancelled.{RESET}")
            
        return context
        
    except Exception as e:
        print(f"{RED}Error during multi-step execution: {e}{RESET}")
        context = executor.cancel_task(context)
        return context

def list_sessions(session_manager):
    """列出所有会话"""
    sessions = session_manager.list_sessions()
    
    if not sessions:
        print(f"{BLUE}No active sessions found.{RESET}")
        return
    
    print(f"{BLUE}Active sessions:{RESET}")
    for session in sessions:
        status_color = GREEN if session.status == TaskStatus.COMPLETED else BLUE if session.status == TaskStatus.IN_PROGRESS else RED
        print(f"{status_color}  {session.task_id}: {session.user_prompt[:50]}... [{session.status.value}]{RESET}")

def resume_session(session_manager, task_id: str):
    """恢复会话"""
    context = session_manager.load_session(task_id)
    
    if not context:
        print(f"{RED}Session {task_id} not found.{RESET}")
        return
    
    print(f"{GREEN}Resuming session: {task_id}{RESET}")
    
    # 这里需要重新创建agent和executor
    # 为简化，暂时返回context，实际使用时需要完整的恢复逻辑
    return context


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
    parser.add_argument("--multistep", action="store_true",
                        help="Enable multi-step task execution mode")
    parser.add_argument("--list-sessions", action="store_true",
                        help="List all active sessions")
    parser.add_argument("--resume", type=str, metavar="TASK_ID",
                        help="Resume a paused session by task ID")
    parser.add_argument("--session-storage", choices=["memory", "file"], default="file",
                        help="Choose session storage type (default: file)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Generate and record commands without executing them")

    return parser.parse_args()

def main():
    args = parse_args()
    
    # 初始化会话管理器
    if args.session_storage == "memory":
        session_manager = InMemorySessionManager()
    else:
        session_manager = FileSessionManager()
    
    # 处理会话相关命令
    if args.list_sessions:
        list_sessions(session_manager)
        return
    
    if args.resume:
        context = session_manager.load_session(args.resume)
        if context:
            agent = get_agent(args)
            executor = MultiStepTaskExecutor(agent, session_manager)
            context = executor.resume_task(context)
            progress = executor.get_task_progress(context)
            print(f"{BLUE}Session info: {context.user_prompt}{RESET}")
            print(f"{BLUE}Status: {progress['status']}{RESET}")
            print(f"{BLUE}Progress: {progress['completed_steps']}/{progress['total_steps']} ({progress['progress_percentage']}%){RESET}")
        return
    
    agent = get_agent(args)
    
    # join the prompt arguments into a single string
    prompt = " ".join(args.prompt).strip()
    system_info = get_system_info() 
    custom_prompt = load_custom_prompt()
    
    if args.multistep:
        # 多步骤模式
        run_multistep_task(agent, prompt, custom_prompt, system_info, session_manager, dry_run=args.dry_run)
    else:
        # 单步骤模式（原有逻辑）
        response = run_one_shot(agent, prompt, custom_prompt, system_info)
        print_response(response)
        action = get_user_action()
        run_user_action(action, response)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
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
