from typing import List, cast
from llama_cpp import CreateCompletionResponse, Llama
from open_codex.interfaces.llm_agent import LLMAgent
import contextlib
import os
import sys


class AgentPhi4Mini(LLMAgent):
    def __init__(self, system_prompt: str):
        # suppress the stderr output from llama_cpp
        # this is a workaround for the llama_cpp library
        # which prints a lot of warnings and errors to stderr
        # when loading the model
        # this is a temporary solution until the library is fixed
        with AgentPhi4Mini.suppress_stderr():
            self.llm: Llama = Llama.from_pretrained( # type: ignore
                repo_id="lmstudio-community/Phi-4-mini-instruct-GGUF",
                filename="Phi-4-mini-instruct-Q3_K_L.gguf",
                additional_files=[],  
            )
        self.system_prompt = system_prompt

    def one_shot_mode(self, user_input: str) -> str:
        chat_history = [{"role": "system", "content": self.system_prompt}]
        chat_history.append({"role": "user", "content": user_input})
        full_prompt = self.format_chat(chat_history)
        output_raw = self.llm(prompt=full_prompt, max_tokens=100, temperature=0.2, stream=False)
        
        # unfortuntely llama_cpp has a union type for the output
        output = cast(CreateCompletionResponse, output_raw)
        
        assistant_reply : str = output["choices"][0]["text"].strip() 
        return assistant_reply 
        
    
    def format_chat(self, messages: List[dict[str, str]]) -> str:
        chat_prompt = ""
        for msg in messages:
            role_tag = "user" if msg["role"] == "user" else "assistant"
            chat_prompt += f"<|{role_tag}|>\n{msg['content']}\n"
        chat_prompt += "<|assistant|>\n"
        return chat_prompt
    
    @contextlib.contextmanager
    @staticmethod
    def suppress_stderr():
        with open(os.devnull, 'w') as devnull:
            old_stderr = sys.stderr
            sys.stderr = devnull
            try:
                yield
            finally:
                sys.stderr = old_stderr
