#!/usr/bin/env python3
"""
多步骤任务执行示例

这个示例展示了如何使用多步骤任务功能来执行复杂的任务。
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from agent_builder import AgentBuilder
from multistep_task import TaskContext, TaskStatus
from session_manager import InMemorySessionManager
from multistep_executor import MultiStepTaskExecutor


def example_simple_multistep_task():
    """
    简单的多步骤任务示例
    """
    print("=== 简单多步骤任务示例 ===")
    
    # 创建代理（这里使用模拟的代理，实际使用时需要配置真实的LLM）
    try:
        # 尝试创建Ollama代理
        agent = AgentBuilder.get_ollama_agent(
            model="llama3",
            host="http://localhost:11434"
        )
        print("使用Ollama代理")
    except Exception:
        print("无法连接到Ollama，请确保Ollama服务正在运行")
        return
    
    # 创建会话管理器
    session_manager = AgentBuilder.create_session_manager("memory")
    
    # 创建多步骤执行器
    executor = AgentBuilder.create_multistep_executor(agent, session_manager)
    
    # 定义任务
    task_description = "创建一个简单的Python计算器程序"
    
    print(f"任务: {task_description}")
    print("开始执行多步骤任务...\n")
    
    try:
        # 执行任务
        result = executor.execute_task(task_description)
        
        print(f"\n任务执行完成！")
        print(f"最终状态: {result.status}")
        print(f"完成步骤数: {len(result.completed_steps)}")
        
        if result.status == TaskStatus.COMPLETED:
            print("\n=== 执行步骤回顾 ===")
            for i, step in enumerate(result.completed_steps, 1):
                print(f"{i}. {step.description}")
                if step.result:
                    print(f"   结果: {step.result[:100]}..." if len(step.result) > 100 else f"   结果: {step.result}")
                print()
        
    except Exception as e:
        print(f"任务执行出错: {e}")


def example_interactive_multistep_task():
    """
    交互式多步骤任务示例
    """
    print("\n=== 交互式多步骤任务示例 ===")
    
    # 创建代理
    try:
        agent = AgentBuilder.get_ollama_agent(
            model="llama3",
            host="http://localhost:11434"
        )
    except Exception:
        print("无法连接到Ollama，跳过交互式示例")
        return
    
    # 创建会话管理器
    session_manager = AgentBuilder.create_session_manager("memory")
    
    # 创建多步骤执行器
    executor = AgentBuilder.create_multistep_executor(agent, session_manager)
    
    # 获取用户输入的任务
    task_description = input("请输入要执行的任务描述: ")
    
    if not task_description.strip():
        print("任务描述不能为空")
        return
    
    print(f"\n任务: {task_description}")
    print("开始分解任务...")
    
    try:
        # 首先分解任务
        context = TaskContext(
            task_id="interactive_task",
            task_description=task_description,
            completed_steps=[],
            remaining_steps=[],
            metadata={}
        )
        
        steps = agent.decompose_task(task_description, context)
        print(f"\n任务已分解为 {len(steps)} 个步骤:")
        for i, step in enumerate(steps, 1):
            print(f"{i}. {step.description} (预计 {step.estimated_time} 分钟)")
        
        # 询问用户是否继续
        continue_execution = input("\n是否继续执行这些步骤? (y/n): ")
        if continue_execution.lower() != 'y':
            print("任务已取消")
            return
        
        # 执行任务
        result = executor.execute_task(task_description)
        
        print(f"\n任务执行完成！")
        print(f"最终状态: {result.status}")
        
    except Exception as e:
        print(f"任务执行出错: {e}")


def example_session_management():
    """
    会话管理示例
    """
    print("\n=== 会话管理示例 ===")
    
    # 创建文件会话管理器
    session_manager = AgentBuilder.create_session_manager("file", "./example_sessions")
    
    print("创建了文件会话管理器")
    print(f"会话存储路径: ./example_sessions")
    
    # 列出现有会话
    sessions = session_manager.list_sessions()
    print(f"\n当前会话数量: {len(sessions)}")
    
    if sessions:
        print("现有会话:")
        for session_id in sessions:
            try:
                task = session_manager.load_session(session_id)
                print(f"- {session_id}: {task.task_description} ({task.status})")
            except Exception as e:
                print(f"- {session_id}: 加载失败 ({e})")
    
    # 清理旧会话
    cleaned = session_manager.cleanup_old_sessions(max_age_hours=24)
    if cleaned > 0:
        print(f"\n清理了 {cleaned} 个旧会话")


def main():
    """
    主函数 - 运行所有示例
    """
    print("多步骤任务执行系统示例")
    print("=" * 50)
    
    # 运行示例
    example_simple_multistep_task()
    
    # 询问是否运行交互式示例
    run_interactive = input("\n是否运行交互式示例? (y/n): ")
    if run_interactive.lower() == 'y':
        example_interactive_multistep_task()
    
    # 会话管理示例
    example_session_management()
    
    print("\n所有示例执行完成！")


if __name__ == "__main__":
    main()