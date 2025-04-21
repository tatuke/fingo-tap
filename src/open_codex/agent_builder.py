from importlib.resources import files

from open_codex.agents.phi_4_mini import AgentPhi4Mini
from open_codex.interfaces.llm_agent import LLMAgent

class AgentBuilder:

    @staticmethod
    def get_agent() -> LLMAgent:
        system_prompt = files("open_codex.resources").joinpath("prompt.txt").read_text(encoding="utf-8")
        return AgentPhi4Mini(system_prompt=system_prompt)
    
    @staticmethod
    def read_file(file_path: str) -> str:
        with open(file_path, 'r') as file:
            content = file.read()
        return content
