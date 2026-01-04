from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class StepStatus(Enum):
    """步骤状态枚举"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

@dataclass
class TaskStep:
    """任务步骤数据类"""
    id: str
    name: str
    description: str
    command: Optional[str] = None
    estimated_time: int = 5
    status: StepStatus = StepStatus.PENDING
    result: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    dependencies: List[str] = None  # 依赖的步骤ID列表
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.dependencies is None:
            self.dependencies = []

@dataclass
class TaskContext:
    """任务上下文数据类"""
    task_id: str
    user_prompt: str
    system_info: str
    custom_prompt: str
    status: TaskStatus = TaskStatus.PENDING
    steps: List[TaskStep] = None
    current_step_index: int = 0
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.steps is None:
            self.steps = []
        if self.metadata is None:
            self.metadata = {}

class MultiStepTask(ABC):
    """多步骤任务抽象基类"""
    
    @abstractmethod
    def decompose_task(self, user_prompt: str, context: TaskContext) -> List[TaskStep]:
        """将用户输入分解为多个步骤
        
        Args:
            user_prompt: 用户输入的任务描述
            context: 任务上下文
            
        Returns:
            分解后的步骤列表
        """
        pass
    
    @abstractmethod
    def execute_step(self, step: TaskStep, context: TaskContext) -> TaskStep:
        """执行单个步骤
        
        Args:
            step: 要执行的步骤
            context: 任务上下文
            
        Returns:
            更新后的步骤对象
        """
        pass
    
    @abstractmethod
    def can_execute_step(self, step: TaskStep, context: TaskContext) -> bool:
        """检查步骤是否可以执行（依赖是否满足）
        
        Args:
            step: 要检查的步骤
            context: 任务上下文
            
        Returns:
            是否可以执行
        """
        pass
    
    @abstractmethod
    def handle_step_failure(self, step: TaskStep, context: TaskContext) -> bool:
        """处理步骤执行失败
        
        Args:
            step: 失败的步骤
            context: 任务上下文
            
        Returns:
            是否应该继续执行后续步骤
        """
        pass

class SessionManager(ABC):
    """会话管理器抽象基类"""
    
    @abstractmethod
    def create_session(self, user_prompt: str, system_info: str, custom_prompt: str) -> TaskContext:
        """创建新的任务会话
        
        Args:
            user_prompt: 用户输入
            system_info: 系统信息
            custom_prompt: 自定义提示
            
        Returns:
            任务上下文
        """
        pass
    
    @abstractmethod
    def save_session(self, context: TaskContext) -> None:
        """保存会话状态
        
        Args:
            context: 任务上下文
        """
        pass
    
    @abstractmethod
    def load_session(self, task_id: str) -> Optional[TaskContext]:
        """加载会话状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务上下文，如果不存在则返回None
        """
        pass
    
    @abstractmethod
    def list_sessions(self) -> List[TaskContext]:
        """列出所有会话
        
        Returns:
            会话列表
        """
        pass
    
    @abstractmethod
    def delete_session(self, task_id: str) -> bool:
        """删除会话
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否删除成功
        """
        pass

class TaskExecutor(ABC):
    """任务执行器抽象基类"""
    
    @abstractmethod
    def execute_task(self, context: TaskContext) -> TaskContext:
        """执行完整任务
        
        Args:
            context: 任务上下文
            
        Returns:
            更新后的任务上下文
        """
        pass
    
    @abstractmethod
    def execute_next_step(self, context: TaskContext) -> TaskContext:
        """执行下一个步骤
        
        Args:
            context: 任务上下文
            
        Returns:
            更新后的任务上下文
        """
        pass
    
    @abstractmethod
    def pause_task(self, context: TaskContext) -> TaskContext:
        """暂停任务执行
        
        Args:
            context: 任务上下文
            
        Returns:
            更新后的任务上下文
        """
        pass
    
    @abstractmethod
    def resume_task(self, context: TaskContext) -> TaskContext:
        """恢复任务执行
        
        Args:
            context: 任务上下文
            
        Returns:
            更新后的任务上下文
        """
        pass
    
    @abstractmethod
    def cancel_task(self, context: TaskContext) -> TaskContext:
        """取消任务执行
        
        Args:
            context: 任务上下文
            
        Returns:
            更新后的任务上下文
        """
        pass
