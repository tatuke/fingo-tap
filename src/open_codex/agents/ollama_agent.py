from typing import List, Dict, Optional
import logging
import ollama
import json

from open_codex.interfaces.llm_agent import LLMAgent
from open_codex.interfaces.multistep_task import TaskContext, TaskStep, StepStatus

# Configure logger
logger = logging.getLogger(__name__)

class OllamaAgent(LLMAgent):
    """
    Agent that connects to Ollama to access local language models 
    using the official Python client.
    """
    
    def __init__(self, 
                 system_prompt: str,
                 model_name: str,
                 host: str,
                 temperature: float = 0.2,
                 max_tokens: int = 500):
        """
        Initialize the Ollama agent.
        
        Args:
            system_prompt: The system prompt to use for generating responses
            model_name: The name of the model to use (default: "llama3")
            host: The host URL of the Ollama API (default: None, uses OLLAMA_HOST env var or http://localhost:11434)
            temperature: The temperature to use for generation (default: 0.2)
            max_tokens: The maximum number of tokens to generate (default: 500)
        """
        self.system_prompt = system_prompt
        self.model_name = model_name
        self.host = host

        self.temperature = temperature
        self.max_tokens = max_tokens
        self._ollama_client = ollama.Client(host=self.host)
    
    def _check_ollama_available(self) -> None:
        """Check if Ollama server is available and the model exists."""
        try:
            # List models to check connection
            models: ollama.ListResponse = self._ollama_client.list()
            
            available_models = [model.model for model in models.models if model.model is not None]
            
            if not available_models:
                logger.error(f"No models found in Ollama. You may need to pull the model with: ollama pull {self.model_name}")
            elif self.model_name not in available_models:
                logger.error(f"Model '{self.model_name}' not found in Ollama. Available models: {', '.join(available_models)}")
                logger.error(f"You can pull the model with: ollama pull {self.model_name}")
                
        except ConnectionError as e:
            logger.error(f"Could not connect to Ollama server.")
            logger.error(
                f"Make sure Ollama is running at {self.host} or install it from https://ollama.com"
            )
            raise ConnectionError(
                f"Could not connect to Ollama server. "
                f"Make sure Ollama is running at {self.host} or install it from https://ollama.com"
            )
    
    def one_shot_mode(self, user_input: str) -> str:
        """
        Generate a one-shot response to the user input.
        
        Args:
            user_input: The user's input prompt
            
        Returns:
            The generated response as a string
        """
        self._check_ollama_available()
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_input}
        ]
        
        response = self._generate_completion(messages)
        return response.strip()
    
    def decompose_task(self, task_description: str, context: TaskContext) -> List[TaskStep]:
        """
        Decompose a complex task into smaller steps.
        
        Args:
            task_description: Description of the task to decompose
            context: Current task context
            
        Returns:
            List of task steps
        """
        # 使用专门的任务分解系统提示词，不使用原始系统提示词
        decomposition_system_prompt = """You are a task decomposition expert. Your job is to break down complex tasks into smaller, manageable steps.

Rules:
1. Always decompose tasks into multiple logical steps when possible
2. Each step should be specific and actionable
3. Consider dependencies between steps
4. For software installation tasks, include steps like: repository setup, package download, installation, verification
5. Return ONLY a valid JSON array, no explanations
6. Each step must have: id, description, dependencies (array), estimated_time (minutes)"""
        
        prompt = f"""Decompose this task into smaller steps:

Task: {task_description}

For installation tasks like this, consider these typical steps:
1. Check system requirements
2. Add repository or download source
3. Update package lists
4. Install dependencies
5. Install main package
6. Configure if needed
7. Verify installation

Return as JSON array:"""
        
        messages = [
            {"role": "system", "content": decomposition_system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        response = self._generate_completion(messages)
        cleaned = self._extract_json_array(response)
        try:
            steps_data = json.loads(cleaned)
            steps = []
            for step_data in steps_data:
                step = TaskStep(
                    id=step_data["id"],
                    description=step_data["description"],
                    dependencies=step_data.get("dependencies", []),
                    estimated_time=step_data.get("estimated_time", 5)
                )
                steps.append(step)
            return steps
        except json.JSONDecodeError:
            # Fallback: create a single step
            return [TaskStep(
                id="step1",
                description=task_description,
                dependencies=[],
                estimated_time=10
            )]
    
    def execute_step(self, step: TaskStep, context: TaskContext) -> str:
        """
        Execute a single step of the task.
        
        Args:
            step: The step to execute
            context: Current task context
            
        Returns:
            Result of the step execution
        """
        import subprocess
        import platform
        
        prompt = self.generate_step_prompt(step, context)
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        # 生成命令
        command = self._generate_completion(messages).strip()
        
        try:
            # 实际执行命令
            if platform.system() == "Windows":
                # Windows使用PowerShell
                result = subprocess.run(
                    ["powershell", "-Command", command],
                    capture_output=True,
                    text=True,
                    timeout=300  # 5分钟超时
                )
            else:
                # Linux/macOS使用bash
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=300  # 5分钟超时
                )
            
            # 返回执行结果
            if result.returncode == 0:
                return f"命令执行成功:\n命令: {command}\n输出: {result.stdout}"
            else:
                return f"命令执行失败:\n命令: {command}\n错误: {result.stderr}\n返回码: {result.returncode}"
                
        except subprocess.TimeoutExpired:
            return f"命令执行超时:\n命令: {command}"
        except Exception as e:
            return f"命令执行异常:\n命令: {command}\n异常: {str(e)}"
    
    def generate_step_prompt(self, step: TaskStep, context: TaskContext) -> str:
        """
        Generate a prompt for executing a specific step.
        
        Args:
            step: The step to generate prompt for
            context: Current task context
            
        Returns:
            Generated prompt
        """
        prompt = f"""Execute the following step:

Step: {step.description}
Step ID: {step.id}

Context:
- Task: {context.user_prompt}
- Current step: {context.current_step_index + 1} of {len(context.steps)}
"""
        
        completed_steps = [step for step in context.steps[:context.current_step_index] if step.status == StepStatus.COMPLETED]
        if completed_steps:
            prompt += "\nPrevious steps completed:\n"
            for completed_step in completed_steps[-3:]:  # Show last 3 steps
                prompt += f"- {completed_step.description}\n"
        
        if step.dependencies:
            prompt += f"\nThis step depends on: {', '.join(step.dependencies)}\n"
        
        prompt += "\nPlease provide a detailed response for this step."
        return prompt
    
    def validate_step_result(self, step: TaskStep, result: str, context: TaskContext) -> bool:
        """
        Validate the result of a step execution.
        
        Args:
            step: The executed step
            result: The result to validate
            context: Current task context
            
        Returns:
            True if the result is valid, False otherwise
        """
        if not result or len(result.strip()) < 10:
            return False
        
        result_lower = result.lower()
        
        # 检查是否是成功执行的结果
        if "命令执行成功" in result:
            return True
        
        # 检查是否是明确的失败
        if any(indicator in result for indicator in ["命令执行失败", "命令执行超时", "命令执行异常"]):
            return False
        
        # 检查常见的错误指示器
        error_indicators = ["error", "failed", "cannot", "unable", "impossible", "permission denied", "not found"]
        error_count = sum(1 for indicator in error_indicators if indicator in result_lower)
        
        # 如果错误指示器太多，认为执行失败
        return error_count <= 1
    
    def handle_step_error(self, step: TaskStep, error: str, context: TaskContext) -> Optional[str]:
        """
        Handle errors that occur during step execution.
        
        Args:
            step: The step that failed
            error: The error message
            context: Current task context
            
        Returns:
            Recovery suggestion or None if no recovery is possible
        """
        prompt = f"""An error occurred while executing a step. Please provide a recovery suggestion:

Step: {step.description}
Error: {error}

Context:
- Task: {context.user_prompt}
- Completed steps: {len([s for s in context.steps if s.status == StepStatus.COMPLETED])}

Please suggest how to recover from this error or if the step should be skipped."""
        
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        try:
            return self._generate_completion(messages)
        except Exception:
            return None

    def _generate_completion(self, messages: List[Dict[str, str]]) -> str:
        """
        Generate a completion using the Ollama API.
        
        Args:
            messages: The conversation history as a list of message dictionaries
            
        Returns:
            The generated text response
        """
        try:
            
            response = ollama.chat(
                model=self.model_name,
                messages=messages,
                options={
                    "temperature": self.temperature,
                    "num_predict": self.max_tokens,
                }
            )
            
            if "message" in response and "content" in response["message"]:
                return response["message"]["content"]
            else:
                raise ValueError(f"Unexpected response format from Ollama API: {response}")
                
        except Exception as e:
            raise ConnectionError(f"Error communicating with Ollama: {str(e)}")
            # some model call himself "human friendly" including extra markdown mark
            
    def _extract_json_array(self, text: str) -> str:
        import re
        s = text.strip()
        m = re.search(r"```(?:json|JSON)?\n([\s\S]*?)\n```", s)
        if m:
            s = m.group(1).strip()
        if "[" in s and "]" in s:
            start = s.find("[")
            end = s.rfind("]")
            if start != -1 and end != -1 and end > start:
                return s[start:end+1].strip()
        return s
