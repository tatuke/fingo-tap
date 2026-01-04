# 多步骤任务执行功能

本文档介绍如何使用新增的多步骤任务执行功能。

## 概述

多步骤任务执行功能允许将复杂的任务分解为多个较小的步骤，并逐步执行。这个功能包括：

- 任务自动分解
- 步骤依赖管理
- 会话状态持久化
- 交互式执行控制
- 错误处理和恢复

## 核心组件

### 1. 多步骤任务接口 (`multistep_task.py`)

定义了多步骤任务系统的核心数据结构和抽象接口：

- `TaskStep`: 表示单个任务步骤
- `TaskContext`: 任务执行上下文
- `MultiStepTask`: 完整的多步骤任务
- `SessionManager`: 会话管理抽象接口
- `TaskExecutor`: 任务执行器抽象接口

### 2. 会话管理器 (`session_manager.py`)

提供任务状态的持久化存储：

- `InMemorySessionManager`: 内存存储（适用于临时任务）
- `FileSessionManager`: 文件存储（适用于需要持久化的任务）

### 3. 多步骤执行器 (`multistep_executor.py`)

负责任务的实际执行：

- 任务分解
- 步骤调度
- 依赖检查
- 错误处理
- 进度跟踪

### 4. 扩展的LLM代理接口

所有LLM代理现在都支持多步骤执行方法：

- `decompose_task()`: 分解任务为步骤
- `execute_step()`: 执行单个步骤
- `validate_step_result()`: 验证步骤结果
- `handle_step_error()`: 处理步骤错误

## 使用方法

### 1. 命令行使用

#### 启用多步骤模式

```bash
python main.py --multistep "创建一个Python计算器程序"
```

#### 选择会话存储类型

```bash
# 使用内存存储（默认）
python main.py --multistep --session-storage memory "任务描述"

# 使用文件存储
python main.py --multistep --session-storage file "任务描述"
```

#### 会话管理

```bash
# 列出所有活动会话
python main.py --list-sessions

# 恢复特定会话
python main.py --resume session_id
```

### 2. 编程接口使用

```python
from agent_builder import AgentBuilder
from multistep_task import TaskContext

# 创建代理
agent = AgentBuilder.get_ollama_agent(
    model="llama3",
    host="http://localhost:11434"
)

# 创建会话管理器
session_manager = AgentBuilder.create_session_manager("file", "./sessions")

# 创建多步骤执行器
executor = AgentBuilder.create_multistep_executor(agent, session_manager)

# 执行任务
task_description = "创建一个Web应用"
result = executor.execute_task(task_description)

print(f"任务状态: {result.status}")
print(f"完成步骤: {len(result.completed_steps)}")
```

### 3. 交互式执行

在多步骤模式下，系统会在每个步骤完成后询问用户下一步操作：

- `n` (next): 继续执行下一步
- `p` (pause): 暂停任务（保存状态）
- `s` (status): 查看当前状态
- `q` (quit): 退出（取消任务）

## 配置选项

### 会话存储配置

```python
# 内存存储（临时）
session_manager = AgentBuilder.create_session_manager("memory")

# 文件存储（持久化）
session_manager = AgentBuilder.create_session_manager("file", "./my_sessions")
```

### 执行器配置

```python
executor = MultiStepTaskExecutor(
    agent=agent,
    session_manager=session_manager,
    max_retries=3,  # 最大重试次数
    timeout_seconds=300  # 步骤超时时间
)
```

## 示例

### 运行示例代码

```bash
# 运行基本示例
python examples/multistep_example.py

# 运行测试
python tests/test_multistep.py
```

### 示例任务

1. **创建Python程序**
   ```bash
   python main.py --multistep "创建一个Python计算器程序，包含基本的加减乘除功能"
   ```

2. **Web开发任务**
   ```bash
   python main.py --multistep "开发一个简单的博客网站，包含文章列表和详情页面"
   ```

3. **数据分析任务**
   ```bash
   python main.py --multistep "分析销售数据，生成月度报告和可视化图表"
   ```

## 错误处理

系统提供多层错误处理机制：

1. **步骤级错误**: 单个步骤失败时，系统会尝试恢复或跳过
2. **任务级错误**: 整个任务失败时，保存当前状态以便后续恢复
3. **会话恢复**: 可以从之前保存的状态恢复执行

## 最佳实践

1. **任务描述**: 提供清晰、具体的任务描述
2. **会话管理**: 对于长期任务使用文件存储
3. **错误处理**: 定期检查任务状态，及时处理错误
4. **资源管理**: 定期清理旧的会话文件

## 故障排除

### 常见问题

1. **LLM连接失败**
   - 检查Ollama服务是否运行
   - 验证模型是否已下载
   - 确认网络连接正常

2. **会话加载失败**
   - 检查会话文件是否存在
   - 验证文件权限
   - 确认JSON格式正确

3. **任务分解失败**
   - 简化任务描述
   - 检查LLM响应格式
   - 尝试重新启动任务

### 调试模式

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# 现在会显示详细的调试信息
```

## 扩展开发

### 自定义会话管理器

```python
from multistep_task import SessionManager

class CustomSessionManager(SessionManager):
    def save_session(self, task: MultiStepTask) -> None:
        # 自定义保存逻辑
        pass
    
    def load_session(self, task_id: str) -> MultiStepTask:
        # 自定义加载逻辑
        pass
```

### 自定义任务执行器

```python
from multistep_task import TaskExecutor

class CustomTaskExecutor(TaskExecutor):
    def execute_task(self, task_description: str) -> MultiStepTask:
        # 自定义执行逻辑
        pass
```

## 性能优化

1. **并行执行**: 对于独立的步骤，可以考虑并行执行
2. **缓存机制**: 缓存常用的任务分解结果
3. **资源限制**: 设置合理的超时和重试限制
4. **会话清理**: 定期清理过期的会话数据

## 版本兼容性

- 新功能完全向后兼容
- 原有的单步骤模式继续正常工作
- 可以在同一个系统中混合使用两种模式

---

更多信息请参考源代码注释和示例文件。