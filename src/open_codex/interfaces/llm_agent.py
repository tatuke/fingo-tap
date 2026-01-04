from abc import ABC, abstractmethod
from typing import Optional, List
from .multistep_task import TaskContext, TaskStep

class LLMAgent(ABC):
    @abstractmethod
    def one_shot_mode(self, user_input: str) -> str:
        """单次对话模式
        
        Args:
            user_input: 用户输入
            
        Returns:
            AI回复
        """
        pass
    
    @abstractmethod
    def decompose_task(self, user_input: str, context: Optional[TaskContext] = None) -> List[TaskStep]:
        """将用户输入分解为多个执行步骤
        
        Args:
            user_input: 用户输入的任务描述
            context: 可选的任务上下文
            
        Returns:
            分解后的步骤列表
        """
        pass
    
    @abstractmethod
    def execute_step(self, step: TaskStep, context: TaskContext) -> str:
        """执行单个任务步骤
        
        Args:
            step: 要执行的步骤
            context: 任务上下文
            
        Returns:
            步骤执行的结果字符串
        """
        pass
    
    @abstractmethod
    def generate_step_prompt(self, step: TaskStep, context: TaskContext) -> str:
        """为特定步骤生成提示词
        
        Args:
            step: 当前步骤
            context: 任务上下文
            
        Returns:
            生成的提示词
        """
        pass
    
    @abstractmethod
    def validate_step_result(self, step: TaskStep, result: str, context: TaskContext) -> bool:
        """验证步骤执行结果
        
        Args:
            step: 执行完成的步骤
            result: 步骤执行结果字符串
            context: 任务上下文
            
        Returns:
            验证是否通过
        """
        pass
    
    @abstractmethod
    def handle_step_error(self, step: TaskStep, error: Exception, context: TaskContext) -> Optional[str]:
        """处理步骤执行错误
        
        Args:
            step: 出错的步骤
            error: 错误信息
            context: 任务上下文
            
        Returns:
            恢复建议或结果字符串，如不可恢复返回 None
        """
        pass
    
