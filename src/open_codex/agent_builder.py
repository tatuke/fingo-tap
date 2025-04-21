
from open_codex.agents.phi_4_mini import AgentPhi4Mini
from open_codex.interfaces.llm_agent import LLMAgent

class AgentBuilder:

    @staticmethod
    def get_agent() -> LLMAgent:
        prompt = AgentBuilder.read_file("src/open_codex/resources/prompt.txt")
        return AgentPhi4Mini(system_prompt=prompt)
    
    @staticmethod
    def read_file(file_path: str) -> str:
        with open(file_path, 'r') as file:
            content = file.read()
        return content
