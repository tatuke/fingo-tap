from importlib.resources import files
import os
from open_codex.interfaces.llm_agent import LLMAgent


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
                            api_base=os.getenv("API_BASE"),
                            api_key=os.getenv("API_KEY"))
    # print(f"Script directory: {script_dir}")
    # print(f"Dotenv path: {dotenv_path}")
    # print(f"Model name: {os.environ['MODEL_NAME']}")
    # print(f"File exists? {os.path.exists(dotenv_path)}")
    
    @staticmethod
    def read_file(file_path: str) -> str:
        with open(file_path, 'r') as file:
            content = file.read()
        return content
