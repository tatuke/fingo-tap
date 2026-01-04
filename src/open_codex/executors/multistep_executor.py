import uuid
import re
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..interfaces.multistep_task import (
    TaskExecutor, MultiStepTask, TaskContext, TaskStep, 
    TaskStatus, StepStatus
)
from ..interfaces.llm_agent import LLMAgent
from ..session.session_manager import SessionManager
from ..storage_builder import get_db_session, recordcontext

class MultiStepTaskExecutor(TaskExecutor, MultiStepTask):
    """多步骤任务执行器实现"""
    
    def __init__(self, agent: LLMAgent, session_manager: SessionManager, dry_run: bool = False):
        self.agent = agent
        self.session_manager = session_manager
        self.max_retries = 3
        self.step_timeout = 300  # 5分钟超时
        self.dry_run = dry_run
    
    def decompose_task(self, user_prompt: str, context: TaskContext) -> List[TaskStep]:
        """将用户输入分解为多个步骤"""
        try:
            # 使用LLM代理进行任务分解
            steps = self.agent.decompose_task(user_prompt, context)
            
            # 防护：确保返回的是TaskStep对象列表
            validated_steps = []
            for i, step in enumerate(steps):
                if isinstance(step, str):
                    # 如果是字符串，转换为TaskStep对象
                    step = TaskStep(
                        id=f"step_{i+1}_{uuid.uuid4().hex[:8]}",
                        name=f"步骤 {i+1}",
                        description=step,
                        command=step,
                        status=StepStatus.PENDING,
                        created_at=datetime.now()
                    )
                elif isinstance(step, TaskStep):
                    # 为TaskStep对象分配唯一ID（如果没有的话）
                    if not step.id:
                        step.id = f"step_{i+1}_{uuid.uuid4().hex[:8]}"
                    if not step.created_at:
                        step.created_at = datetime.now()
                else:
                    # 其他类型，跳过
                    continue
                
                validated_steps.append(step)
            
            return validated_steps if validated_steps else [TaskStep(
                id=f"default_{uuid.uuid4().hex[:8]}",
                name="执行用户任务",
                description=user_prompt,
                command=user_prompt,
                status=StepStatus.PENDING,
                created_at=datetime.now()
            )]
        except Exception as e:
            # 如果LLM分解失败，创建一个默认步骤
            return [TaskStep(
                id=f"default_{uuid.uuid4().hex[:8]}",
                name="执行用户任务",
                description=user_prompt,
                command=user_prompt,
                status=StepStatus.PENDING,
                created_at=datetime.now()
            )]
    
    def execute_step(self, step: TaskStep, context: TaskContext) -> TaskStep:
        """执行单个步骤"""
        step.status = StepStatus.IN_PROGRESS
        step.started_at = datetime.now()
        
        try:
            import subprocess, platform
            if step.command:
                if self.dry_run:
                    step.result = f"DRY-RUN:\n命令: {step.command}"
                    step.status = StepStatus.COMPLETED
                    step.completed_at = datetime.now()
                    self._write_step_to_db(step.command, step.result)
                    return step
                if platform.system() == "Windows":
                    proc = subprocess.run([
                            "powershell", "-Command", step.command
                        ], capture_output=True, text=True, timeout=self.step_timeout)
                else:
                    proc = subprocess.run(step.command, shell=True, capture_output=True, text=True, timeout=self.step_timeout)
                step.result = f"returncode={proc.returncode}\nstdout={proc.stdout}\nstderr={proc.stderr}"
                if proc.returncode == 0:
                    step.status = StepStatus.COMPLETED
                else:
                    step.status = StepStatus.FAILED
                    step.error = proc.stderr[:2000]
                step.completed_at = datetime.now()
                self._write_step_to_db(step.command, step.result)
                return step
            else:
                # 使用LLM代理生成命令并执行
                if context.metadata is not None:
                    context.metadata['dry_run'] = self.dry_run
                result = self.agent.execute_step(step, context)
                step.result = result
                # 如果返回中包含命令执行成功/失败，已由代理执行
                if any(k in result for k in ["命令执行成功", "命令执行失败", "命令执行超时", "命令执行异常", "DRY-RUN"]):
                    if "命令执行成功" in result or "DRY-RUN" in result:
                        step.status = StepStatus.COMPLETED
                    else:
                        step.status = StepStatus.FAILED
                        step.error = result[:2000]
                    step.completed_at = datetime.now()
                    cmd_text = self._parse_cmd_from_result(result)
                    self._write_step_to_db(cmd_text, result)
                    return step
                # 否则视为失败
                step.status = StepStatus.FAILED
                step.error = "LLM 未返回可执行命令"
                step.completed_at = datetime.now()
                return step
            
        except Exception as e:
            # 处理执行错误
            step.error = str(e)
            step.status = StepStatus.FAILED
            step.completed_at = datetime.now()
            
            # 尝试错误处理
            try:
                recovery_result = self.agent.handle_step_error(step, e, context)
                if recovery_result:
                    step.result = recovery_result
                return step
            except Exception:
                return step

    def _parse_cmd_from_result(self, result: str) -> str:
        try:
            for key in ["命令:", "Command:"]:
                idx = result.find(key)
                if idx != -1:
                    line = result[idx + len(key):].strip().splitlines()[0]
                    return line.strip()
        except Exception:
            pass
        return ""

    def _write_step_to_db(self, command_text: str, extend_content: str) -> None:
        try:
            with get_db_session() as db:
                db.add(recordcontext(choice="step", command=command_text or "", extend_content=extend_content or ""))
        except Exception:
            pass
    
    def can_execute_step(self, step: TaskStep, context: TaskContext) -> bool:
        """检查步骤是否可以执行（依赖是否满足）"""
        if not step.dependencies:
            return True
        
        # 检查所有依赖步骤是否已完成
        completed_steps = {str(s.id) for s in context.steps if hasattr(s, 'status') and hasattr(s, 'id') and s.status == StepStatus.COMPLETED}
        
        for dep_id in step.dependencies:
            if str(dep_id) not in completed_steps:
                return False
        
        return True
    
    def handle_step_failure(self, step: TaskStep, context: TaskContext) -> bool:
        """处理步骤执行失败"""
        # 检查是否有重试机会
        retry_count = context.metadata.get(f"retry_count_{step.id}", 0)
        
        if retry_count < self.max_retries:
            # 增加重试计数
            context.metadata[f"retry_count_{step.id}"] = retry_count + 1
            
            # 重置步骤状态以便重试
            step.status = StepStatus.PENDING
            step.error = None
            step.started_at = None
            step.completed_at = None
            
            return True  # 继续执行
        
        # 超过最大重试次数，检查是否为关键步骤
        is_critical = step.name.lower().find('critical') != -1 or step.name.lower().find('关键') != -1
        
        if is_critical:
            return False  # 停止执行
        
        # 非关键步骤失败，跳过并继续
        step.status = StepStatus.SKIPPED
        return True
    
    def execute_task(self, context: TaskContext) -> TaskContext:
        """执行完整任务"""
        context.status = TaskStatus.IN_PROGRESS
        context.started_at = datetime.now()
        
        try:
            # 如果没有步骤，先进行任务分解
            if not context.steps:
                context.steps = self.decompose_task(context.user_prompt, context)
            
            # 执行所有步骤
            while context.current_step_index < len(context.steps):
                context = self.execute_next_step(context)
                
                # 检查是否应该停止执行
                current_step = context.steps[context.current_step_index - 1] if context.current_step_index > 0 else None
                if current_step and current_step.status == StepStatus.FAILED:
                    if not self.handle_step_failure(current_step, context):
                        context.status = TaskStatus.FAILED
                        break
            
            # 检查任务完成状态
            if context.status == TaskStatus.IN_PROGRESS:
                completed_steps = sum(1 for step in context.steps if hasattr(step, 'status') and step.status == StepStatus.COMPLETED)
                total_steps = len(context.steps)
                
                if completed_steps == total_steps:
                    context.status = TaskStatus.COMPLETED
                elif completed_steps > 0:
                    context.status = TaskStatus.COMPLETED  # 部分完成也算完成
                else:
                    context.status = TaskStatus.FAILED
            
            context.completed_at = datetime.now()
            
        except Exception as e:
            context.status = TaskStatus.FAILED
            context.metadata['error'] = str(e)
            context.completed_at = datetime.now()
        
        # 保存会话状态
        self.session_manager.save_session(context)
        return context
    
    def execute_next_step(self, context: TaskContext) -> TaskContext:
        """执行下一个步骤"""
        if context.current_step_index >= len(context.steps):
            return context
        
        current_step = context.steps[context.current_step_index]
        if hasattr(current_step, 'status') and current_step.status in [StepStatus.SKIPPED, StepStatus.COMPLETED]:
            context.current_step_index += 1
            self.session_manager.save_session(context)
            return context
        
        # 检查是否可以执行当前步骤
        if not self.can_execute_step(current_step, context):
            # 寻找下一个可执行的步骤
            for i in range(context.current_step_index + 1, len(context.steps)):
                if self.can_execute_step(context.steps[i], context):
                    context.current_step_index = i
                    current_step = context.steps[i]
                    break
            else:
                # 没有可执行的步骤
                return context
        
        updated_step = self.execute_step(current_step, context)
        context.steps[context.current_step_index] = updated_step
        if updated_step.status in [StepStatus.COMPLETED, StepStatus.SKIPPED]:
            context.current_step_index += 1
        self.session_manager.save_session(context)
        return context
    
    def pause_task(self, context: TaskContext) -> TaskContext:
        """暂停任务执行"""
        if context.status == TaskStatus.IN_PROGRESS:
            context.metadata['paused_at'] = datetime.now().isoformat()
            context.metadata['was_paused'] = True
            self.session_manager.save_session(context)
        
        return context
    
    def resume_task(self, context: TaskContext) -> TaskContext:
        """恢复任务执行"""
        if context.metadata.get('was_paused'):
            context.metadata['resumed_at'] = datetime.now().isoformat()
            context.metadata['was_paused'] = False
            
            # 继续执行剩余步骤
            return self.execute_task(context)
        
        return context
    
    def cancel_task(self, context: TaskContext) -> TaskContext:
        """取消任务执行"""
        context.status = TaskStatus.CANCELLED
        context.completed_at = datetime.now()
        context.metadata['cancelled_at'] = datetime.now().isoformat()
        
        # 取消所有未完成的步骤
        for step in context.steps:
            # 防护：确保step是TaskStep对象而不是字符串
            if isinstance(step, str):
                continue
            if hasattr(step, 'status') and step.status in [StepStatus.PENDING, StepStatus.IN_PROGRESS]:
                step.status = StepStatus.SKIPPED
        
        self.session_manager.save_session(context)
        return context
    
    def get_task_progress(self, context: TaskContext) -> Dict[str, Any]:
        """获取任务进度信息"""
        total_steps = len(context.steps)
        completed_steps = sum(1 for step in context.steps if hasattr(step, 'status') and step.status == StepStatus.COMPLETED)
        failed_steps = sum(1 for step in context.steps if hasattr(step, 'status') and step.status == StepStatus.FAILED)
        in_progress_steps = sum(1 for step in context.steps if hasattr(step, 'status') and step.status == StepStatus.IN_PROGRESS)
        
        progress_percentage = (completed_steps / total_steps * 100) if total_steps > 0 else 0
        
        return {
            'task_id': context.task_id,
            'status': context.status.value,
            'total_steps': total_steps,
            'completed_steps': completed_steps,
            'failed_steps': failed_steps,
            'in_progress_steps': in_progress_steps,
            'current_step_index': context.current_step_index,
            'progress_percentage': round(progress_percentage, 2),
            'created_at': context.created_at.isoformat() if context.created_at else None,
            'started_at': context.started_at.isoformat() if context.started_at else None,
            'completed_at': context.completed_at.isoformat() if context.completed_at else None,
            'estimated_remaining_time': 1
        }
    # 估算执行时间毫无必要，如果想看，不如直接展示进度条
    # def _estimate_remaining_time(self, context: TaskContext) -> Optional[str]:
    #     """估算剩余执行时间"""
    #     if not context.started_at or context.current_step_index == 0:
    #         return None
        
    #     elapsed_time = (datetime.now() - context.started_at).total_seconds()
    #     completed_steps = sum(1 for step in context.steps[:context.current_step_index] 
    #                         if hasattr(step, 'status') and step.status == StepStatus.COMPLETED)
        
    #     if completed_steps == 0:
    #         return None
        
    #     avg_time_per_step = elapsed_time / completed_steps
    #     remaining_steps = len(context.steps) - context.current_step_index
    #     estimated_seconds = avg_time_per_step * remaining_steps
        
    #     if estimated_seconds < 60:
    #         return f"{int(estimated_seconds)}秒"
    #     elif estimated_seconds < 3600:
    #         return f"{int(estimated_seconds / 60)}分钟"
    #     else:
    #         return f"{int(estimated_seconds / 3600)}小时{int((estimated_seconds % 3600) / 60)}分钟"
