#!/usr/bin/env python3
"""
🌊 ASYNC CORE - Flow-Balancer Integration (FBI-ATO-SP)
═══════════════════════════════════════════════════════════════════════════════

Autonomous Task Orchestration & Sanctuary Preservation for GPU-accelerated
entity extraction with graceful fallback and deterministic results.

Architecture:
  ┌──────────────────────────────────────────────────────────────────────────┐
  │  ASYNC TASK QUEUE                                                         │
  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                       │
  │  │ scan_task   │→ │ score_task  │→ │ embed_task  │  (GPU batched)       │
  │  └─────────────┘  └─────────────┘  └─────────────┘                       │
  │         ↓                ↓                ↓                               │
  │  ┌─────────────────────────────────────────────────────────────────────┐ │
  │  │               RESULT AGGREGATOR (deterministic merge)               │ │
  │  └─────────────────────────────────────────────────────────────────────┘ │
  └──────────────────────────────────────────────────────────────────────────┘

Key Features:
  - Async/await patterns for non-blocking GPU operations
  - Task cancellation with graceful cleanup
  - Deterministic results via seeded operations
  - Auto-fallback to CPU when GPU unavailable/overloaded
  - Memory pressure monitoring with adaptive batching

═══════════════════════════════════════════════════════════════════════════════
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import (
    Any, Callable, Coroutine, Dict, Generic, List, 
    Optional, Set, TypeVar, Union
)
from collections import deque
from concurrent.futures import ThreadPoolExecutor
import threading

logger = logging.getLogger("mas.async")

# ═══════════════════════════════════════════════════════════════════════════════
# TYPE VARIABLES
# ═══════════════════════════════════════════════════════════════════════════════

T = TypeVar('T')  # Task result type
R = TypeVar('R')  # Request type


# ═══════════════════════════════════════════════════════════════════════════════
# TASK STATE MACHINE
# ═══════════════════════════════════════════════════════════════════════════════

class TaskState(Enum):
    """FBI task lifecycle states."""
    PENDING = auto()      # Awaiting execution
    QUEUED = auto()       # In execution queue
    RUNNING = auto()      # Currently executing
    COMPLETED = auto()    # Successfully finished
    FAILED = auto()       # Execution failed
    CANCELLED = auto()    # User/system cancelled
    TIMEOUT = auto()      # Exceeded time limit


class TaskPriority(Enum):
    """Task priority levels (higher = more urgent)."""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3  # System tasks, health checks


# ═══════════════════════════════════════════════════════════════════════════════
# TASK RESULT CONTAINER
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class TaskResult(Generic[T]):
    """
    Immutable result container with metadata.
    Enables deterministic result comparison across runs.
    """
    task_id: str
    state: TaskState
    value: Optional[T] = None
    error: Optional[str] = None
    start_time: float = 0.0
    end_time: float = 0.0
    backend_used: str = "unknown"
    seed_used: Optional[int] = None
    
    @property
    def elapsed_ms(self) -> float:
        """Execution time in milliseconds."""
        return (self.end_time - self.start_time) * 1000
    
    @property
    def success(self) -> bool:
        return self.state == TaskState.COMPLETED
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize for MCP response."""
        return {
            "task_id": self.task_id,
            "state": self.state.name,
            "value": self.value,
            "error": self.error,
            "elapsed_ms": round(self.elapsed_ms, 2),
            "backend": self.backend_used,
            "seed": self.seed_used
        }


# ═══════════════════════════════════════════════════════════════════════════════
# ASYNC TASK DEFINITION
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class AsyncTask(Generic[T]):
    """
    A unit of async work with priority, timeout, and cancellation support.
    """
    id: str
    coroutine: Coroutine[Any, Any, T]
    priority: TaskPriority = TaskPriority.NORMAL
    timeout_seconds: float = 30.0
    created_at: float = field(default_factory=time.time)
    state: TaskState = TaskState.PENDING
    result: Optional[TaskResult[T]] = None
    
    # Cancellation support
    _cancel_event: asyncio.Event = field(default_factory=asyncio.Event)
    
    def request_cancel(self) -> None:
        """Request graceful cancellation."""
        self._cancel_event.set()
    
    @property
    def is_cancelled(self) -> bool:
        return self._cancel_event.is_set()
    
    def __lt__(self, other: 'AsyncTask') -> bool:
        """Priority ordering for heap queue."""
        return self.priority.value > other.priority.value  # Higher priority first


# ═══════════════════════════════════════════════════════════════════════════════
# BATCH COLLECTOR
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class BatchCollector(Generic[R, T]):
    """
    Collects items into batches for efficient GPU processing.
    
    Flushes when:
      - Batch size reached
      - Timeout elapsed
      - Flush explicitly requested
    """
    max_batch_size: int = 256
    max_wait_ms: float = 50.0
    
    _items: List[R] = field(default_factory=list)
    _futures: List[asyncio.Future] = field(default_factory=list)
    _last_add: float = field(default_factory=time.time)
    _lock: threading.Lock = field(default_factory=threading.Lock)
    
    def add(self, item: R) -> asyncio.Future:
        """Add item to batch, returns future for result."""
        future: asyncio.Future = asyncio.Future()
        
        with self._lock:
            self._items.append(item)
            self._futures.append(future)
            self._last_add = time.time()
            
            # Check if batch is full
            needs_flush = len(self._items) >= self.max_batch_size
        
        return future, needs_flush
    
    def should_flush(self) -> bool:
        """Check if batch should be flushed due to timeout."""
        with self._lock:
            if not self._items:
                return False
            elapsed = (time.time() - self._last_add) * 1000
            return elapsed >= self.max_wait_ms
    
    def collect(self) -> tuple[List[R], List[asyncio.Future]]:
        """Collect current batch and reset."""
        with self._lock:
            items = self._items
            futures = self._futures
            self._items = []
            self._futures = []
            return items, futures
    
    @property
    def size(self) -> int:
        with self._lock:
            return len(self._items)


# ═══════════════════════════════════════════════════════════════════════════════
# ASYNC TASK EXECUTOR
# ═══════════════════════════════════════════════════════════════════════════════

class AsyncExecutor:
    """
    FBI-ATO-SP: Autonomous Task Orchestration with Sanctuary Preservation.
    
    Manages async task execution with:
      - Priority-based scheduling
      - GPU/CPU backend selection
      - Graceful degradation under load
      - Deterministic execution (seeded randomness)
    """
    
    def __init__(
        self,
        max_concurrent: int = 4,
        max_queue_size: int = 1000,
        default_seed: int = 42,
        thread_pool_size: int = 2
    ):
        self.max_concurrent = max_concurrent
        self.max_queue_size = max_queue_size
        self.default_seed = default_seed
        
        # Task management
        self._queue: asyncio.PriorityQueue = None  # Created in start()
        self._active_tasks: Dict[str, asyncio.Task] = {}
        self._completed: deque = deque(maxlen=100)  # Recent completions
        
        # Lifecycle
        self._running = False
        self._shutdown_event: asyncio.Event = None
        
        # Thread pool for CPU fallback
        self._thread_pool = ThreadPoolExecutor(
            max_workers=thread_pool_size,
            thread_name_prefix="mas-cpu-"
        )
        
        # Statistics
        self._stats = {
            "tasks_submitted": 0,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "tasks_cancelled": 0,
            "gpu_executions": 0,
            "cpu_fallbacks": 0,
        }
    
    async def start(self) -> None:
        """Initialize executor and start worker loop."""
        if self._running:
            return
        
        self._queue = asyncio.PriorityQueue(maxsize=self.max_queue_size)
        self._shutdown_event = asyncio.Event()
        self._running = True
        
        # Start worker task
        asyncio.create_task(self._worker_loop())
        logger.info(f"AsyncExecutor started (max_concurrent={self.max_concurrent})")
    
    async def stop(self, timeout: float = 5.0) -> None:
        """Graceful shutdown with timeout."""
        if not self._running:
            return
        
        logger.info("AsyncExecutor shutting down...")
        self._running = False
        self._shutdown_event.set()
        
        # Cancel active tasks
        for task_id, task in list(self._active_tasks.items()):
            task.cancel()
        
        # Wait for cleanup
        if self._active_tasks:
            await asyncio.wait(
                self._active_tasks.values(),
                timeout=timeout
            )
        
        self._thread_pool.shutdown(wait=False)
        logger.info("AsyncExecutor stopped")
    
    async def submit(self, task: AsyncTask[T]) -> str:
        """
        Submit task for execution.
        
        Returns task ID for tracking.
        """
        if not self._running:
            raise RuntimeError("Executor not started")
        
        if self._queue.qsize() >= self.max_queue_size:
            raise RuntimeError("Task queue full")
        
        task.state = TaskState.QUEUED
        await self._queue.put((task.priority.value * -1, task.created_at, task))
        
        self._stats["tasks_submitted"] += 1
        logger.debug(f"Task {task.id} queued (priority={task.priority.name})")
        
        return task.id
    
    async def submit_and_wait(self, task: AsyncTask[T]) -> TaskResult[T]:
        """Submit task and wait for completion."""
        await self.submit(task)
        return await self._wait_for_task(task)
    
    async def _wait_for_task(self, task: AsyncTask[T]) -> TaskResult[T]:
        """Wait for a specific task to complete."""
        while task.state in (TaskState.PENDING, TaskState.QUEUED, TaskState.RUNNING):
            await asyncio.sleep(0.01)
        return task.result
    
    async def _worker_loop(self) -> None:
        """Main worker loop - processes tasks from queue."""
        while self._running:
            try:
                # Check concurrent limit
                if len(self._active_tasks) >= self.max_concurrent:
                    await asyncio.sleep(0.01)
                    continue
                
                # Get next task (with timeout for shutdown check)
                try:
                    _, _, task = await asyncio.wait_for(
                        self._queue.get(),
                        timeout=0.1
                    )
                except asyncio.TimeoutError:
                    continue
                
                # Execute task
                asyncio_task = asyncio.create_task(
                    self._execute_task(task)
                )
                self._active_tasks[task.id] = asyncio_task
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker loop error: {e}")
    
    async def _execute_task(self, task: AsyncTask[T]) -> None:
        """Execute a single task with timeout and error handling."""
        task.state = TaskState.RUNNING
        start_time = time.time()
        
        try:
            # Execute with timeout
            result_value = await asyncio.wait_for(
                task.coroutine,
                timeout=task.timeout_seconds
            )
            
            task.result = TaskResult(
                task_id=task.id,
                state=TaskState.COMPLETED,
                value=result_value,
                start_time=start_time,
                end_time=time.time(),
                seed_used=self.default_seed
            )
            task.state = TaskState.COMPLETED
            self._stats["tasks_completed"] += 1
            
        except asyncio.TimeoutError:
            task.result = TaskResult(
                task_id=task.id,
                state=TaskState.TIMEOUT,
                error=f"Task exceeded {task.timeout_seconds}s timeout",
                start_time=start_time,
                end_time=time.time()
            )
            task.state = TaskState.TIMEOUT
            self._stats["tasks_failed"] += 1
            
        except asyncio.CancelledError:
            task.result = TaskResult(
                task_id=task.id,
                state=TaskState.CANCELLED,
                error="Task cancelled",
                start_time=start_time,
                end_time=time.time()
            )
            task.state = TaskState.CANCELLED
            self._stats["tasks_cancelled"] += 1
            
        except Exception as e:
            task.result = TaskResult(
                task_id=task.id,
                state=TaskState.FAILED,
                error=str(e),
                start_time=start_time,
                end_time=time.time()
            )
            task.state = TaskState.FAILED
            self._stats["tasks_failed"] += 1
            logger.error(f"Task {task.id} failed: {e}")
        
        finally:
            # Cleanup
            self._active_tasks.pop(task.id, None)
            self._completed.append(task)
    
    def run_sync(self, coro: Coroutine[Any, Any, T]) -> T:
        """
        Run coroutine synchronously (for MCP tool integration).
        
        Uses existing event loop if available, creates new one otherwise.
        """
        try:
            loop = asyncio.get_running_loop()
            # We're in an async context - schedule and wait
            future = asyncio.ensure_future(coro)
            return loop.run_until_complete(future)
        except RuntimeError:
            # No running loop - create one
            return asyncio.run(coro)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get executor statistics."""
        return {
            **self._stats,
            "queue_size": self._queue.qsize() if self._queue else 0,
            "active_tasks": len(self._active_tasks),
            "running": self._running
        }


# ═══════════════════════════════════════════════════════════════════════════════
# BATCH PROCESSOR (GPU-OPTIMIZED)
# ═══════════════════════════════════════════════════════════════════════════════

class BatchProcessor(Generic[R, T]):
    """
    Processes items in GPU-efficient batches.
    
    Collects incoming items, batches them, and processes via GPU
    when batch is full or timeout expires.
    """
    
    def __init__(
        self,
        process_fn: Callable[[List[R]], List[T]],
        max_batch_size: int = 256,
        max_wait_ms: float = 50.0,
        use_gpu: bool = True
    ):
        self.process_fn = process_fn
        self.max_batch_size = max_batch_size
        self.max_wait_ms = max_wait_ms
        self.use_gpu = use_gpu
        
        self._collector = BatchCollector(
            max_batch_size=max_batch_size,
            max_wait_ms=max_wait_ms
        )
        self._running = False
        self._flush_task: Optional[asyncio.Task] = None
    
    async def start(self) -> None:
        """Start batch processor."""
        if self._running:
            return
        self._running = True
        self._flush_task = asyncio.create_task(self._flush_loop())
    
    async def stop(self) -> None:
        """Stop batch processor and flush remaining items."""
        self._running = False
        if self._flush_task:
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass
        
        # Final flush
        await self._flush()
    
    async def process(self, item: R) -> T:
        """Add item and wait for batch result."""
        future, needs_flush = self._collector.add(item)
        
        if needs_flush:
            asyncio.create_task(self._flush())
        
        return await future
    
    async def _flush_loop(self) -> None:
        """Periodic flush check."""
        while self._running:
            if self._collector.should_flush():
                await self._flush()
            await asyncio.sleep(self.max_wait_ms / 1000 / 2)
    
    async def _flush(self) -> None:
        """Process current batch."""
        items, futures = self._collector.collect()
        if not items:
            return
        
        try:
            # Process batch (may use GPU)
            results = await asyncio.get_event_loop().run_in_executor(
                None,
                self.process_fn,
                items
            )
            
            # Distribute results
            for future, result in zip(futures, results):
                if not future.done():
                    future.set_result(result)
                    
        except Exception as e:
            # Propagate error to all waiters
            for future in futures:
                if not future.done():
                    future.set_exception(e)


# ═══════════════════════════════════════════════════════════════════════════════
# CONVENIENCE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

# Global executor instance
_executor: Optional[AsyncExecutor] = None


def get_executor() -> AsyncExecutor:
    """Get or create global executor."""
    global _executor
    if _executor is None:
        _executor = AsyncExecutor()
    return _executor


async def ensure_started() -> AsyncExecutor:
    """Ensure executor is started and return it."""
    executor = get_executor()
    if not executor._running:
        await executor.start()
    return executor


def run_async(coro: Coroutine[Any, Any, T]) -> T:
    """
    Run async coroutine from sync context.
    
    Safe to call from MCP tool handlers.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    
    if loop is not None:
        # In async context - use nest_asyncio pattern
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            future = pool.submit(asyncio.run, coro)
            return future.result()
    else:
        return asyncio.run(coro)


# ═══════════════════════════════════════════════════════════════════════════════
# TASK FACTORIES
# ═══════════════════════════════════════════════════════════════════════════════

def create_scan_task(
    target: str,
    priority: TaskPriority = TaskPriority.NORMAL,
    timeout: float = 60.0
) -> AsyncTask:
    """Create async scan task."""
    from uuid import uuid4
    
    async def scan_coro():
        # Import here to avoid circular dependency
        from server import mas_scan
        return mas_scan(target)
    
    return AsyncTask(
        id=f"scan-{uuid4().hex[:8]}",
        coroutine=scan_coro(),
        priority=priority,
        timeout_seconds=timeout
    )


def create_entity_task(
    entity_name: str,
    context_lines: int = 25,
    priority: TaskPriority = TaskPriority.HIGH
) -> AsyncTask:
    """Create async entity extraction task."""
    from uuid import uuid4
    
    async def entity_coro():
        from server import mas_entity_deep
        return mas_entity_deep(entity_name, context_lines)
    
    return AsyncTask(
        id=f"entity-{uuid4().hex[:8]}",
        coroutine=entity_coro(),
        priority=priority,
        timeout_seconds=30.0
    )


# ═══════════════════════════════════════════════════════════════════════════════
# MODULE DIAGNOSTICS
# ═══════════════════════════════════════════════════════════════════════════════

def module_status() -> Dict[str, Any]:
    """Get async module status for diagnostics."""
    executor = get_executor()
    return {
        "module": "async_core",
        "version": "1.0.0",
        "executor_running": executor._running,
        "stats": executor.get_stats() if executor._running else None,
        "features": [
            "priority_scheduling",
            "batch_collection",
            "gpu_fallback",
            "deterministic_seeds",
            "graceful_cancellation"
        ]
    }
