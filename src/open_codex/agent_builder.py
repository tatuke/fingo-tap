from importlib.resources import files
import os
from open_codex.interfaces.llm_agent import LLMAgent
from open_codex.session.session_manager import SessionManager, InMemorySessionManager, FileSessionManager
from open_codex.executors.multistep_executor import MultiStepTaskExecutor




class AgentBuilder:
    
    @staticmethod
    def get_system_prompt() -> str:
        return files("open_codex.resources") \
            .joinpath("prompt.txt") \
            .read_text(encoding="utf-8")
# plan to join the custom_prompt.txt to the system_prompt
    # @staticmethod
    # def get_phi_agent() -> LLMAgent:
    #     from open_codex.agents.phi_4_mini_agent import Phi4MiniAgent
    #     system_prompt = AgentBuilder.get_system_prompt()
    #     return Phi4MiniAgent(system_prompt=system_prompt)
    
    @staticmethod
    def get_ollama_agent(model: str, host: str) -> LLMAgent:
        from open_codex.agents.ollama_agent import OllamaAgent
        system_prompt = AgentBuilder.get_system_prompt()
        return OllamaAgent(system_prompt=system_prompt, 
                           model_name=model,
                           host=host)

    @staticmethod
    def get_litellm_agent() -> LLMAgent:
        from open_codex.agents.litellm_agent import LiteLLMAgent
        system_prompt = AgentBuilder.get_system_prompt()
        return LiteLLMAgent(system_prompt=system_prompt, 
                            model_name=os.getenv("MODEL_NAME"),
                            api_key=os.getenv("API_KEY"))
    # print(f"Script directory: {script_dir}")
    # print(f"Dotenv path: {dotenv_path}")
    # print(f"Model name: {os.environ['MODEL_NAME']}")
    # print(f"File exists? {os.path.exists(dotenv_path)}")
    
    @staticmethod
    def create_session_manager(storage_type: str = "memory", storage_path: str = "./sessions") -> SessionManager:
        """
        Create a session manager for multi-step task execution.
        
        Args:
            storage_type: Type of storage ("memory" or "file")
            storage_path: Path for file-based storage (only used if storage_type is "file")
            
        Returns:
            SessionManager instance
        """
        if storage_type.lower() == "file":
            return FileSessionManager(storage_path)
        else:
            return InMemorySessionManager()
    
    @staticmethod
    def create_multistep_executor(agent: LLMAgent, session_manager: SessionManager) -> MultiStepTaskExecutor:
        """
        Create a multi-step task executor.
        
        Args:
            agent: The LLM agent to use for task execution
            session_manager: The session manager for state persistence
            
        Returns:
            MultiStepTaskExecutor instance
        """
        return MultiStepTaskExecutor(agent, session_manager)
    
    @staticmethod
    def read_file(file_path: str) -> str:
        with open(file_path, 'r') as file:
            content = file.read()
        return content
