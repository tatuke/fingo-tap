import json
import os
import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path

from ..interfaces.multistep_task import (
    SessionManager, TaskContext, TaskStep, TaskStatus, StepStatus
)

class InMemorySessionManager(SessionManager):
    """内存会话管理器实现"""
    
    def __init__(self):
        self._sessions: Dict[str, TaskContext] = {}
    
    def create_session(self, user_prompt: str, system_info: str, custom_prompt: str) -> TaskContext:
        """创建新的任务会话"""
        task_id = str(uuid.uuid4())
        context = TaskContext(
            task_id=task_id,
            user_prompt=user_prompt,
            system_info=system_info,
            custom_prompt=custom_prompt,
            status=TaskStatus.PENDING,
            created_at=datetime.now()
        )
        self._sessions[task_id] = context
        return context
    
    def save_session(self, context: TaskContext) -> None:
        """保存会话状态"""
        self._sessions[context.task_id] = context
    
    def load_session(self, task_id: str) -> Optional[TaskContext]:
        """加载会话状态"""
        return self._sessions.get(task_id)
    
    def list_sessions(self) -> List[TaskContext]:
        """列出所有会话"""
        return list(self._sessions.values())
    
    def delete_session(self, task_id: str) -> bool:
        """删除会话"""
        if task_id in self._sessions:
            del self._sessions[task_id]
            return True
        return False

class FileSessionManager(SessionManager):
    """文件会话管理器实现"""
    
    def __init__(self, session_dir: str = "./sessions"):
        self.session_dir = Path(session_dir)
        self.session_dir.mkdir(exist_ok=True)
    
    def _get_session_file(self, task_id: str) -> Path:
        """获取会话文件路径"""
        return self.session_dir / f"{task_id}.json"
    
    def _serialize_context(self, context: TaskContext) -> Dict[str, Any]:
        """序列化任务上下文"""
        return {
            "task_id": context.task_id,
            "user_prompt": context.user_prompt,
            "system_info": context.system_info,
            "custom_prompt": context.custom_prompt,
            "status": context.status.value,
            "current_step_index": context.current_step_index,
            "created_at": context.created_at.isoformat() if context.created_at else None,
            "started_at": context.started_at.isoformat() if context.started_at else None,
            "completed_at": context.completed_at.isoformat() if context.completed_at else None,
            "metadata": context.metadata,
            "steps": [
                {
                    "id": step.id,
                    "name": step.name,
                    "description": step.description,
                    "command": step.command,
                    "estimated_time": getattr(step, "estimated_time", 5),
                    "status": step.status.value,
                    "result": step.result,
                    "error": step.error,
                    "created_at": step.created_at.isoformat() if step.created_at else None,
                    "started_at": step.started_at.isoformat() if step.started_at else None,
                    "completed_at": step.completed_at.isoformat() if step.completed_at else None,
                    "dependencies": step.dependencies
                }
                for step in context.steps
            ]
        }
    
    def _deserialize_context(self, data: Dict[str, Any]) -> TaskContext:
        """反序列化任务上下文"""
        steps = [
            TaskStep(
                id=str(step_data["id"]),
                name=step_data["name"],
                description=step_data["description"],
                command=step_data.get("command"),
                estimated_time=step_data.get("estimated_time", 5),
                status=StepStatus(step_data["status"]),
                result=step_data.get("result"),
                error=step_data.get("error"),
                created_at=datetime.fromisoformat(step_data["created_at"]) if step_data.get("created_at") else None,
                started_at=datetime.fromisoformat(step_data["started_at"]) if step_data.get("started_at") else None,
                completed_at=datetime.fromisoformat(step_data["completed_at"]) if step_data.get("completed_at") else None,
                dependencies=[str(d) for d in step_data.get("dependencies", [])]
            )
            for step_data in data.get("steps", [])
        ]
        
        return TaskContext(
            task_id=data["task_id"],
            user_prompt=data["user_prompt"],
            system_info=data["system_info"],
            custom_prompt=data["custom_prompt"],
            status=TaskStatus(data["status"]),
            steps=steps,
            current_step_index=data.get("current_step_index", 0),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            started_at=datetime.fromisoformat(data["started_at"]) if data.get("started_at") else None,
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
            metadata=data.get("metadata", {})
        )
    
    def create_session(self, user_prompt: str, system_info: str, custom_prompt: str) -> TaskContext:
        """创建新的任务会话"""
        task_id = str(uuid.uuid4())
        context = TaskContext(
            task_id=task_id,
            user_prompt=user_prompt,
            system_info=system_info,
            custom_prompt=custom_prompt,
            status=TaskStatus.PENDING,
            created_at=datetime.now()
        )
        self.save_session(context)
        return context
    
    def save_session(self, context: TaskContext) -> None:
        """保存会话状态"""
        session_file = self._get_session_file(context.task_id)
        data = self._serialize_context(context)
        
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def load_session(self, task_id: str) -> Optional[TaskContext]:
        """加载会话状态"""
        session_file = self._get_session_file(task_id)
        
        if not session_file.exists():
            return None
        
        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return self._deserialize_context(data)
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"Error loading session {task_id}: {e}")
            return None
    
    def list_sessions(self) -> List[TaskContext]:
        """列出所有会话"""
        sessions = []
        
        for session_file in self.session_dir.glob("*.json"):
            task_id = session_file.stem
            context = self.load_session(task_id)
            if context:
                sessions.append(context)
        
        return sorted(sessions, key=lambda x: x.created_at or datetime.min, reverse=True)
    
    def delete_session(self, task_id: str) -> bool:
        """删除会话"""
        session_file = self._get_session_file(task_id)
        
        if session_file.exists():
            try:
                session_file.unlink()
                return True
            except OSError as e:
                print(f"Error deleting session {task_id}: {e}")
                return False
        
        return False
    
    def cleanup_old_sessions(self, max_age_days: int = 30) -> int:
        """清理旧会话文件
        
        Args:
            max_age_days: 最大保留天数
            
        Returns:
            删除的会话数量
        """
        cutoff_time = datetime.now().timestamp() - (max_age_days * 24 * 3600)
        deleted_count = 0
        
        for session_file in self.session_dir.glob("*.json"):
            if session_file.stat().st_mtime < cutoff_time:
                try:
                    session_file.unlink()
                    deleted_count += 1
                except OSError:
                    pass
        
        return deleted_count
