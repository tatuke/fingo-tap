#!/usr/bin/env python3
"""
多步骤任务功能的基本测试

这个测试文件验证多步骤任务系统的核心组件是否正常工作。
"""

import sys
import os
import tempfile
import shutil
from unittest.mock import Mock, MagicMock

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from multistep_task import (
    TaskStep, TaskContext, TaskStatus, StepStatus,
    MultiStepTask, SessionManager, TaskExecutor
)
from session_manager import InMemorySessionManager, FileSessionManager
from multistep_executor import MultiStepTaskExecutor
from interfaces.llm_agent import LLMAgent


class MockLLMAgent(LLMAgent):
    """
    模拟的LLM代理，用于测试
    """
    
    def __init__(self):
        self.call_count = 0
    
    def one_shot_mode(self, user_input: str) -> str:
        self.call_count += 1
        return f"Mock response {self.call_count} for: {user_input[:50]}..."
    
    def decompose_task(self, task_description: str, context: TaskContext) -> list[TaskStep]:
        """模拟任务分解"""
        self.call_count += 1
        return [
            TaskStep(
                id="step1",
                description="分析需求",
                dependencies=[],
                estimated_time=5
            ),
            TaskStep(
                id="step2",
                description="设计方案",
                dependencies=["step1"],
                estimated_time=10
            ),
            TaskStep(
                id="step3",
                description="实现功能",
                dependencies=["step2"],
                estimated_time=15
            )
        ]
    
    def execute_step(self, step: TaskStep, context: TaskContext) -> str:
        """模拟步骤执行"""
        self.call_count += 1
        return f"已完成步骤: {step.description}"
    
    def generate_step_prompt(self, step: TaskStep, context: TaskContext) -> str:
        """生成步骤提示"""
        return f"执行步骤: {step.description}"
    
    def validate_step_result(self, step: TaskStep, result: str, context: TaskContext) -> bool:
        """验证步骤结果"""
        return len(result) > 5  # 简单验证：结果长度大于5
    
    def handle_step_error(self, step: TaskStep, error: str, context: TaskContext) -> str:
        """处理步骤错误"""
        return f"错误处理建议: 重试步骤 {step.description}"


def test_task_step_creation():
    """
    测试TaskStep创建
    """
    print("测试TaskStep创建...")
    
    step = TaskStep(
        id="test_step",
        description="测试步骤",
        dependencies=["dep1", "dep2"],
        estimated_time=10
    )
    
    assert step.id == "test_step"
    assert step.description == "测试步骤"
    assert step.dependencies == ["dep1", "dep2"]
    assert step.estimated_time == 10
    assert step.status == StepStatus.PENDING
    
    print("✓ TaskStep创建测试通过")


def test_task_context_creation():
    """
    测试TaskContext创建
    """
    print("测试TaskContext创建...")
    
    context = TaskContext(
        task_id="test_task",
        task_description="测试任务",
        completed_steps=[],
        remaining_steps=[],
        metadata={"key": "value"}
    )
    
    assert context.task_id == "test_task"
    assert context.task_description == "测试任务"
    assert context.completed_steps == []
    assert context.remaining_steps == []
    assert context.metadata == {"key": "value"}
    
    print("✓ TaskContext创建测试通过")


def test_memory_session_manager():
    """
    测试内存会话管理器
    """
    print("测试内存会话管理器...")
    
    manager = InMemorySessionManager()
    
    # 创建测试任务
    task = MultiStepTask(
        task_id="test_task",
        task_description="测试任务",
        steps=[],
        status=TaskStatus.PENDING
    )
    
    # 保存会话
    manager.save_session(task)
    
    # 加载会话
    loaded_task = manager.load_session("test_task")
    assert loaded_task.task_id == "test_task"
    assert loaded_task.task_description == "测试任务"
    
    # 列出会话
    sessions = manager.list_sessions()
    assert "test_task" in sessions
    
    # 删除会话
    manager.delete_session("test_task")
    sessions = manager.list_sessions()
    assert "test_task" not in sessions
    
    print("✓ 内存会话管理器测试通过")


def test_file_session_manager():
    """
    测试文件会话管理器
    """
    print("测试文件会话管理器...")
    
    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    
    try:
        manager = FileSessionManager(temp_dir)
        
        # 创建测试任务
        task = MultiStepTask(
            task_id="test_file_task",
            task_description="文件测试任务",
            steps=[],
            status=TaskStatus.PENDING
        )
        
        # 保存会话
        manager.save_session(task)
        
        # 验证文件存在
        session_file = os.path.join(temp_dir, "test_file_task.json")
        assert os.path.exists(session_file)
        
        # 加载会话
        loaded_task = manager.load_session("test_file_task")
        assert loaded_task.task_id == "test_file_task"
        assert loaded_task.task_description == "文件测试任务"
        
        # 列出会话
        sessions = manager.list_sessions()
        assert "test_file_task" in sessions
        
        # 删除会话
        manager.delete_session("test_file_task")
        assert not os.path.exists(session_file)
        
        print("✓ 文件会话管理器测试通过")
        
    finally:
        # 清理临时目录
        shutil.rmtree(temp_dir)


def test_multistep_executor():
    """
    测试多步骤执行器
    """
    print("测试多步骤执行器...")
    
    # 创建模拟组件
    agent = MockLLMAgent()
    session_manager = InMemorySessionManager()
    executor = MultiStepTaskExecutor(agent, session_manager)
    
    # 执行任务
    task_description = "创建一个简单的计算器"
    result = executor.execute_task(task_description)
    
    # 验证结果
    assert result.task_description == task_description
    assert result.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.PAUSED]
    assert len(result.steps) > 0
    
    # 验证代理被调用
    assert agent.call_count > 0
    
    print(f"✓ 多步骤执行器测试通过 (状态: {result.status}, 步骤数: {len(result.steps)})")


def test_task_decomposition():
    """
    测试任务分解功能
    """
    print("测试任务分解功能...")
    
    agent = MockLLMAgent()
    context = TaskContext(
        task_id="decomp_test",
        task_description="测试任务分解",
        completed_steps=[],
        remaining_steps=[],
        metadata={}
    )
    
    steps = agent.decompose_task("创建一个Web应用", context)
    
    assert len(steps) == 3
    assert steps[0].id == "step1"
    assert steps[0].description == "分析需求"
    assert steps[1].dependencies == ["step1"]
    assert steps[2].dependencies == ["step2"]
    
    print("✓ 任务分解功能测试通过")


def run_all_tests():
    """
    运行所有测试
    """
    print("开始运行多步骤任务功能测试")
    print("=" * 50)
    
    tests = [
        test_task_step_creation,
        test_task_context_creation,
        test_memory_session_manager,
        test_file_session_manager,
        test_multistep_executor,
        test_task_decomposition
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"✗ {test.__name__} 失败: {e}")
            failed += 1
        print()
    
    print("=" * 50)
    print(f"测试结果: {passed} 通过, {failed} 失败")
    
    if failed == 0:
        print("🎉 所有测试通过！多步骤任务功能正常工作。")
    else:
        print("⚠️  部分测试失败，请检查实现。")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)