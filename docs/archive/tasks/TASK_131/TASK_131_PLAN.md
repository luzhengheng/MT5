# RFC-131: 系统功能扩展技术规格书

**Protocol Version**: v4.4  
**Status**: Draft  
**Author**: System Architect  
**Date**: 2024-01-XX  
**Depends On**: RFC-130 (Completed)

---

## 1. 背景 (Context)

### 1.1 前置任务回顾

Task #130 已成功完成，建立了系统的基础架构，包括：
- 核心模块初始化
- 基础数据模型定义
- 配置管理系统

### 1.2 当前任务目标

Task #131 旨在扩展系统功能，实现以下核心能力：
- **服务层抽象**: 建立统一的服务接口规范
- **事件驱动机制**: 实现模块间解耦通信
- **持久化适配器**: 支持多种存储后端

### 1.3 设计原则

遵循 Protocol v4.4 核心原则：
- **单一职责 (SRP)**: 每个模块只负责一个功能域
- **依赖倒置 (DIP)**: 高层模块不依赖低层实现
- **开闭原则 (OCP)**: 对扩展开放，对修改关闭

---

## 2. 架构设计 (Architecture)

### 2.1 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                      Application Layer                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   CLI/API   │  │  Scheduler  │  │   Event Dispatcher  │  │
│  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘  │
└─────────┼────────────────┼────────────────────┼─────────────┘
          │                │                    │
          ▼                ▼                    ▼
┌─────────────────────────────────────────────────────────────┐
│                       Service Layer                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ TaskService │  │ UserService │  │  NotificationService│  │
│  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘  │
└─────────┼────────────────┼────────────────────┼─────────────┘
          │                │                    │
          ▼                ▼                    ▼
┌─────────────────────────────────────────────────────────────┐
│                     Repository Layer                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  TaskRepo   │  │  UserRepo   │  │    EventStore       │  │
│  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘  │
└─────────┼────────────────┼────────────────────┼─────────────┘
          │                │                    │
          ▼                ▼                    ▼
┌─────────────────────────────────────────────────────────────┐
│                    Infrastructure Layer                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   SQLite    │  │ PostgreSQL  │  │       Redis         │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 数据流图

```
User Request
     │
     ▼
┌─────────┐    validate    ┌──────────┐    process    ┌─────────┐
│ Handler │───────────────▶│ Service  │──────────────▶│  Repo   │
└─────────┘                └──────────┘               └─────────┘
     │                          │                          │
     │                          │ emit event               │ persist
     │                          ▼                          ▼
     │                    ┌──────────┐              ┌─────────┐
     │                    │EventBus  │              │   DB    │
     │                    └──────────┘              └─────────┘
     │                          │
     │                          │ notify subscribers
     │                          ▼
     │                    ┌──────────────────┐
     │                    │ Event Handlers   │
     │                    └──────────────────┘
     │
     ▼
Response
```

### 2.3 类图

```
┌────────────────────────────────────────────────────────────────┐
│                        <<interface>>                            │
│                         IRepository<T>                          │
├────────────────────────────────────────────────────────────────┤
│ + find_by_id(id: str) -> Optional[T]                           │
│ + find_all() -> List[T]                                        │
│ + save(entity: T) -> T                                         │
│ + delete(id: str) -> bool                                      │
└────────────────────────────────────────────────────────────────┘
                              △
                              │ implements
          ┌───────────────────┼───────────────────┐
          │                   │                   │
┌─────────┴────────┐ ┌────────┴─────────┐ ┌──────┴───────────┐
│  SQLiteRepository │ │ PostgresRepository│ │  MemoryRepository │
├──────────────────┤ ├──────────────────┤ ├──────────────────┤
│ - connection     │ │ - pool           │ │ - storage: Dict  │
│ - table_name     │ │ - schema         │ │                  │
├──────────────────┤ ├──────────────────┤ ├──────────────────┤
│ + find_by_id()   │ │ + find_by_id()   │ │ + find_by_id()   │
│ + find_all()     │ │ + find_all()     │ │ + find_all()     │
│ + save()         │ │ + save()         │ │ + save()         │
│ + delete()       │ │ + delete()       │ │ + delete()       │
└──────────────────┘ └──────────────────┘ └──────────────────┘

┌────────────────────────────────────────────────────────────────┐
│                           Event                                 │
├────────────────────────────────────────────────────────────────┤
│ + id: str                                                      │
│ + type: str                                                    │
│ + payload: Dict[str, Any]                                      │
│ + timestamp: datetime                                          │
│ + metadata: Dict[str, Any]                                     │
├────────────────────────────────────────────────────────────────┤
│ + to_dict() -> Dict                                            │
│ + from_dict(data: Dict) -> Event                               │
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│                          EventBus                               │
├────────────────────────────────────────────────────────────────┤
│ - subscribers: Dict[str, List[Callable]]                       │
│ - event_store: IEventStore                                     │
├────────────────────────────────────────────────────────────────┤
│ + subscribe(event_type: str, handler: Callable) -> None        │
│ + unsubscribe(event_type: str, handler: Callable) -> None      │
│ + publish(event: Event) -> None                                │
│ + replay(from_timestamp: datetime) -> None                     │
└────────────────────────────────────────────────────────────────┘
```

---

## 3. 实现细节 (Implementation Details)

### 3.1 项目结构

```
/project_root/
├── src/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── entities.py          # 领域实体
│   │   ├── events.py            # 事件定义
│   │   └── exceptions.py        # 自定义异常
│   ├── services/
│   │   ├── __init__.py
│   │   ├── base.py              # 服务基类
│   │   └── task_service.py      # 任务服务
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── interfaces.py        # 仓储接口
│   │   ├── memory.py            # 内存实现
│   │   └── sqlite.py            # SQLite实现
│   ├── infrastructure/
│   │   ├── __init__.py
│   │   ├── event_bus.py         # 事件总线
│   │   └── config.py            # 配置管理
│   └── main.py                  # 入口文件
├── tests/
│   ├── __init__.py
│   ├── test_entities.py
│   ├── test_services.py
│   ├── test_repositories.py
│   └── test_event_bus.py
├── requirements.txt
└── README.md
```

### 3.2 核心模块实现

#### 3.2.1 领域实体 (`/project_root/src/core/entities.py`)

```python
"""
领域实体定义模块

本模块定义系统核心的领域实体，遵循DDD(领域驱动设计)原则。
所有实体都是不可变的数据类，确保线程安全和状态一致性。

Protocol v4.4 Compliance:
- 使用dataclass确保数据完整性
- 实现__post_init__进行业务规则验证
- 提供工厂方法简化对象创建
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from uuid import uuid4


class TaskStatus(Enum):
    """
    任务状态枚举
    
    状态转换规则:
    PENDING -> IN_PROGRESS -> COMPLETED
                          -> FAILED
    PENDING -> CANCELLED
    """
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    
    def can_transition_to(self, target: TaskStatus) -> bool:
        """
        检查状态转换是否合法
        
        Args:
            target: 目标状态
            
        Returns:
            bool: 转换是否允许
        """
        valid_transitions = {
            TaskStatus.PENDING: {TaskStatus.IN_PROGRESS, TaskStatus.CANCELLED},
            TaskStatus.IN_PROGRESS: {TaskStatus.COMPLETED, TaskStatus.FAILED},
            TaskStatus.COMPLETED: set(),
            TaskStatus.FAILED: {TaskStatus.PENDING},  # 允许重试
            TaskStatus.CANCELLED: set(),
        }
        return target in valid_transitions.get(self, set())


class Priority(Enum):
    """任务优先级"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass(frozen=True)
class TaskId:
    """
    任务ID值对象
    
    使用值对象封装ID，提供类型安全和验证逻辑。
    frozen=True确保ID创建后不可修改。
    """
    value: str
    
    def __post_init__(self):
        if not self.value or len(self.value) < 8:
            raise ValueError("TaskId must be at least 8 characters")
    
    @classmethod
    def generate(cls) -> TaskId:
        """生成新的唯一ID"""
        return cls(value=str(uuid4()))
    
    def __str__(self) -> str:
        return self.value


@dataclass
class Task:
    """
    任务实体
    
    核心业务实体，包含任务的所有属性和行为。
    遵循富领域模型原则，业务逻辑封装在实体内部。
    
    Attributes:
        id: 任务唯一标识
        title: 任务标题
        description: 任务描述
        status: 当前状态
        priority: 优先级
        created_at: 创建时间
        updated_at: 最后更新时间
        due_date: 截止日期
        tags: 标签列表
        metadata: 扩展元数据
    """
    id: TaskId
    title: str
    description: str = ""
    status: TaskStatus = TaskStatus.PENDING
    priority: Priority = Priority.MEDIUM
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    due_date: Optional[datetime] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """创建后验证"""
        self._validate()
    
    def _validate(self) -> None:
        """
        业务规则验证
        
        Raises:
            ValueError: 当业务规则被违反时
        """
        if not self.title or len(self.title.strip()) == 0:
            raise ValueError("Task title cannot be empty")
        
        if len(self.title) > 200:
            raise ValueError("Task title cannot exceed 200 characters")
        
        if self.due_date and self.due_date < self.created_at:
            raise ValueError("Due date cannot be before creation date")
    
    def start(self) -> Task:
        """
        开始任务
        
        Returns:
            Task: 更新后的任务实例
            
        Raises:
            InvalidStateTransitionError: 当状态转换非法时
        """
        if not self.status.can_transition_to(TaskStatus.IN_PROGRESS):
            raise InvalidStateTransitionError(
                f"Cannot start task in {self.status.value} status"
            )
        
        return Task(
            id=self.id,
            title=self.title,
            description=self.description,
            status=TaskStatus.IN_PROGRESS,
            priority=self.priority,
            created_at=self.created_at,
            updated_at=datetime.utcnow(),
            due_date=self.due_date,
            tags=self.tags.copy(),
            metadata=self.metadata.copy()
        )
    
    def complete(self) -> Task:
        """
        完成任务
        
        Returns:
            Task: 更新后的任务实例
        """
        if not self.status.can_transition_to(TaskStatus.COMPLETED):
            raise InvalidStateTransitionError(
                f"Cannot complete task in {self.status.value} status"
            )
        
        return Task(
            id=self.id,
            title=self.title,
            description=self.description,
            status=TaskStatus.COMPLETED,
            priority=self.priority,
            created_at=self.created_at,
            updated_at=datetime.utcnow(),
            due_date=self.due_date,
            tags=self.tags.copy(),
            metadata={**self.metadata, "completed_at": datetime.utcnow().isoformat()}
        )
    
    def fail(self, reason: str) -> Task:
        """
        标记任务失败
        
        Args:
            reason: 失败原因
            
        Returns:
            Task: 更新后的任务实例
        """
        if not self.status.can_transition_to(TaskStatus.FAILED):
            raise InvalidStateTransitionError(
                f"Cannot fail task in {self.status.value} status"
            )
        
        return Task(
            id=self.id,
            title=self.title,
            description=self.description,
            status=TaskStatus.FAILED,
            priority=self.priority,
            created_at=self.created_at,
            updated_at=datetime.utcnow(),
            due_date=self.due_date,
            tags=self.tags.copy(),
            metadata={**self.metadata, "failure_reason": reason}
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        序列化为字典
        
        Returns:
            Dict: 任务的字典表示
        """
        return {
            "id": str(self.id),
            "title": self.title,
            "description": self.description,
            "status": self.status.value,
            "priority": self.priority.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "tags": self.tags,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Task:
        """
        从字典反序列化
        
        Args:
            data: 字典数据
            
        Returns:
            Task: 任务实例
        """
        return cls(
            id=TaskId(data["id"]),
            title=data["title"],
            description=data.get("description", ""),
            status=TaskStatus(data["status"]),
            priority=Priority(data["priority"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            due_date=datetime.fromisoformat(data["due_date"]) if data.get("due_date") else None,
            tags=data.get("tags", []),
            metadata=data.get("metadata", {})
        )
    
    @classmethod
    def create(
        cls,
        title: str,
        description: str = "",
        priority: Priority = Priority.MEDIUM,
        due_date: Optional[datetime] = None,
        tags: Optional[List[str]] = None
    ) -> Task:
        """
        工厂方法：创建新任务
        
        Args:
            title: 任务标题
            description: 任务描述
            priority: 优先级
            due_date: 截止日期
            tags: 标签列表
            
        Returns:
            Task: 新创建的任务实例
        """
        return cls(
            id=TaskId.generate(),
            title=title,
            description=description,
            priority=priority,
            due_date=due_date,
            tags=tags or []
        )


class InvalidStateTransitionError(Exception):
    """非法状态转换异常"""
    pass
```

#### 3.2.2 事件定义 (`/project_root/src/core/events.py`)

```python
"""
事件定义模块

定义系统中所有领域事件，支持事件溯源和CQRS模式。
事件是不可变的，一旦创建就不能修改。

Protocol v4.4 Compliance:
- 事件命名遵循过去时态 (TaskCreated, not CreateTask)
- 每个事件携带完整的上下文信息
- 支持事件版本控制
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional, Type, TypeVar
from uuid import uuid4
from abc import ABC, abstractmethod


T = TypeVar('T', bound='DomainEvent')


@dataclass(frozen=True)
class EventMetadata:
    """
    事件元数据
    
    包含事件的追踪和审计信息。
    """
    correlation_id: str  # 关联ID，用于追踪请求链
    causation_id: Optional[str] = None  # 因果ID，指向触发此事件的事件
    user_id: Optional[str] = None  # 操作用户
    source: str = "system"  # 事件来源
    version: int = 1  # 事件版本


@dataclass(frozen=True)
class DomainEvent(ABC):
    """
    领域事件基类
    
    所有领域事件必须继承此类。
    frozen=True确保事件不可变性。
    """
    event_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: EventMetadata = field(default_factory=lambda: EventMetadata(
        correlation_id=str(uuid4())
    ))
    
    @property
    @abstractmethod
    def event_type(self) -> str:
        """事件类型标识"""
        pass
    
    @property
    @abstractmethod
    def aggregate_id(self) -> str:
        """聚合根ID"""
        pass
    
    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典"""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "aggregate_id": self.aggregate_id,
            "timestamp": self.timestamp.isoformat(),
            "metadata": {
                "correlation_id": self.metadata.correlation_id,
                "causation_id": self.metadata.causation_id,
                "user_id": self.metadata.user_id,
                "source": self.metadata.source,
                "version": self.metadata.version
            },
            "payload": self._get_payload()
        }
    
    @abstractmethod
    def _get_payload(self) -> Dict[str, Any]:
        """获取事件载荷"""
        pass


@dataclass(frozen=True)
class TaskCreated(DomainEvent):
    """
    任务创建事件
    
    当新任务被创建时触发。
    """
    task_id: str = ""
    title: str = ""
    description: str = ""
    priority: int = 2
    due_date: Optional[str] = None
    tags: tuple = field(default_factory=tuple)
    
    @property
    def event_type(self) -> str:
        return "task.created"
    
    @property
    def aggregate_id(self) -> str:
        return self.task_id
    
    def _get_payload(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "title": self.title,
            "description": self.description,
            "priority": self.priority,
            "due_date": self.due_date,
            "tags": list(self.tags)
        }


@dataclass(frozen=True)
class TaskStarted(DomainEvent):
    """任务开始事件"""
    task_id: str = ""
    started_at: str = ""
    
    @property
    def event_type(self) -> str:
        return "task.started"
    
    @property
    def aggregate_id(self) -> str:
        return self.task_id
    
    def _get_payload(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "started_at": self.started_at
        }


@dataclass(frozen=True)
class TaskCompleted(DomainEvent):
    """任务完成事件"""
    task_id: str = ""
    completed_at: str = ""
    duration_seconds: Optional[float] = None
    
    @property
    def event_type(self) -> str:
        return "task.completed"
    
    @property
    def aggregate_id(self) -> str:
        return self.task_id
    
    def _get_payload(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "completed_at": self.completed_at,
            "duration_seconds": self.duration_seconds
        }


@dataclass(frozen=True)
class TaskFailed(DomainEvent):
    """任务失败事件"""
    task_id: str = ""
    reason: str = ""
    failed_at: str = ""
    retry_count: int = 0
    
    @property
    def event_type(self) -> str:
        return "task.failed"
    
    @property
    def aggregate_id(self) -> str:
        return self.task_id
    
    def _get_payload(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "reason": self.reason,
            "failed_at": self.failed_at,
            "retry_count": self.retry_count
        }


# 事件类型注册表
EVENT_REGISTRY: Dict[str, Type[DomainEvent]] = {
    "task.created": TaskCreated,
    "task.started": TaskStarted,
    "task.completed": TaskCompleted,
    "task.failed": TaskFailed,
}


def deserialize_event(data: Dict[str, Any]) -> DomainEvent:
    """
    反序列化事件
    
    Args:
        data: 事件字典数据
        
    Returns:
        DomainEvent: 事件实例
        
    Raises:
        ValueError: 未知事件类型
    """
    event_type = data.get("event_type")
    if event_type not in EVENT_REGISTRY:
        raise ValueError(f"Unknown event type: {event_type}")
    
    event_class = EVENT_REGISTRY[event_type]
    metadata = EventMetadata(**data["metadata"])
    
    return event_class(
        event_id=data["event_id"],
        timestamp=datetime.fromisoformat(data["timestamp"]),
        metadata=metadata,
        **data["payload"]
    )
```

#### 3.2.3 仓储接口 (`/project_root/src/repositories/interfaces.py`)

```python
"""
仓储接口定义模块

定义数据访问层的抽象接口，遵循依赖倒置原则。
具体实现（SQLite、PostgreSQL等）在独立模块中提供。

Protocol v4.4 Compliance:
- 使用Protocol类型提供结构化子类型
- 支持泛型以提高类型安全
- 定义清晰的契约和前置/后置条件
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Optional, List, Dict, Any, Callable
from datetime import datetime

from src.core.entities import Task, TaskId
from src.core.events import DomainEvent


# 泛型类型变量
T = TypeVar('T')
ID = TypeVar('ID')


class IRepository(ABC, Generic[T, ID]):
    """
    通用仓储接口
    
    定义CRUD操作的标准契约。所有仓储实现必须遵循此接口。
    
    Type Parameters:
        T: 实体类型
        ID: 标识符类型
    """
    
    @abstractmethod
    def find_by_id(self, id: ID) -> Optional[T]:
        """
        根据ID查找实体
        
        Args:
            id: 实体标识符
            
        Returns:
            Optional[T]: 找到的实体，不存在则返回None
            
        Postcondition:
            - 返回的实体是完整的，包含所有属性
            - 不修改任何状态
        """
        pass
    
    @abstractmethod
    def find_all(self) -> List[T]:
        """
        获取所有实体
        
        Returns:
            List[T]: 实体列表，可能为空
            
        Postcondition:
            - 返回的列表是新创建的，修改不影响仓储
        """
        pass
    
    @abstractmethod
    def save(self, entity: T) -> T:
        """
        保存实体（创建或更新）
        
        Args:
            entity: 要保存的实体
            
        Returns:
            T: 保存后的实体（可能包含生成的字段）
            
        Precondition:
            - entity不为None
            - entity通过业务规则验证
            
        Postcondition:
            - 实体被持久化
            - 返回的实体反映最新状态
        """
        pass
    
    @abstractmethod
    def delete(self, id: ID) -> bool:
        """
        删除实体
        
        Args:
            id: 要删除的实体ID
            
        Returns:
            bool: 删除是否成功
            
        Postcondition:
            - 如果返回True，实体已被删除
            - 如果返回False，实体不存在
        """
        pass
    
    @abstractmethod
    def exists(self, id: ID) -> bool:
        """
        检查实体是否存在
        
        Args:
            id: 实体ID
            
        Returns:
            bool: 是否存在
        """
        pass
    
    @abstractmethod
    def count(self) -> int:
        """
        获取实体总数
        
        Returns:
            int: 实体数量
        """
        pass


class ITaskRepository(IRepository[Task, TaskId]):
    """
    任务仓储接口
    
    扩展通用仓储接口，添加任务特定的查询方法。
    """
    
    @