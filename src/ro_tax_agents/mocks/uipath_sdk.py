"""Mock implementation of UiPath Python SDK."""

from typing import Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import uuid
from datetime import datetime


class TaskStatus(Enum):
    """UiPath task status."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class MockProcess:
    """Mock UiPath Process."""

    process_id: str
    name: str
    status: TaskStatus = TaskStatus.PENDING
    output: dict = field(default_factory=dict)


@dataclass
class MockTask:
    """Mock UiPath Task for Human-in-the-Loop."""

    task_id: str
    title: str
    data: dict
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[dict] = None


@dataclass
class MockQueueItem:
    """Mock UiPath Queue Item."""

    item_id: str
    queue_name: str
    specific_content: dict
    status: str = "New"
    reference: Optional[str] = None


class MockUiPathSDK:
    """Mock implementation of UiPath Python SDK.

    This class simulates the UiPath Python SDK functionality for development
    and testing purposes. All operations return mock responses.
    """

    def __init__(self) -> None:
        self._processes: dict[str, MockProcess] = {}
        self._tasks: dict[str, MockTask] = {}
        self._queues: dict[str, list[MockQueueItem]] = {}
        self._buckets: dict[str, dict[str, bytes]] = {}

    # Process Operations
    def invoke_process(
        self,
        process_name: str,
        input_arguments: Optional[dict] = None,
        folder_path: str = "Shared",
    ) -> dict[str, Any]:
        """Mock InvokeProcess - starts a UiPath process.

        Args:
            process_name: Name of the process to invoke
            input_arguments: Input arguments for the process
            folder_path: UiPath folder path

        Returns:
            Process execution result
        """
        process_id = str(uuid.uuid4())
        self._processes[process_id] = MockProcess(
            process_id=process_id,
            name=process_name,
            status=TaskStatus.COMPLETED,
            output={"mock_result": f"Process {process_name} completed successfully"},
        )
        return {
            "process_id": process_id,
            "status": "completed",
            "output": self._processes[process_id].output,
        }

    # Task Operations (Human-in-the-Loop)
    def create_task(
        self,
        title: str,
        task_catalog_name: str,
        data: dict,
        priority: str = "Normal",
    ) -> MockTask:
        """Mock CreateTask - creates a human task.

        Args:
            title: Task title
            task_catalog_name: Task catalog name
            data: Task data
            priority: Task priority

        Returns:
            Created task object
        """
        task_id = str(uuid.uuid4())
        task = MockTask(
            task_id=task_id,
            title=title,
            data=data,
            status=TaskStatus.PENDING,
        )
        self._tasks[task_id] = task
        return task

    def get_task_status(self, task_id: str) -> TaskStatus:
        """Get mock task status.

        Args:
            task_id: Task ID to check

        Returns:
            Task status
        """
        task = self._tasks.get(task_id)
        return task.status if task else TaskStatus.FAILED

    def complete_task(self, task_id: str, result: dict) -> bool:
        """Complete a human task with result.

        Args:
            task_id: Task ID to complete
            result: Task result data

        Returns:
            True if successful
        """
        task = self._tasks.get(task_id)
        if task:
            task.status = TaskStatus.COMPLETED
            task.result = result
            return True
        return False

    # Queue Operations
    def add_queue_item(
        self,
        queue_name: str,
        specific_content: dict,
        reference: Optional[str] = None,
    ) -> MockQueueItem:
        """Mock Add Queue Item.

        Args:
            queue_name: Name of the queue
            specific_content: Queue item content
            reference: Optional reference

        Returns:
            Created queue item
        """
        item = MockQueueItem(
            item_id=str(uuid.uuid4()),
            queue_name=queue_name,
            specific_content=specific_content,
            reference=reference,
        )
        if queue_name not in self._queues:
            self._queues[queue_name] = []
        self._queues[queue_name].append(item)
        return item

    def get_queue_items(self, queue_name: str, status: str = "New") -> list[MockQueueItem]:
        """Get queue items by status.

        Args:
            queue_name: Queue name
            status: Status filter

        Returns:
            List of queue items
        """
        items = self._queues.get(queue_name, [])
        return [item for item in items if item.status == status]

    # Bucket Operations
    def upload_to_bucket(
        self,
        bucket_name: str,
        file_name: str,
        content: bytes,
    ) -> str:
        """Mock Upload to Bucket.

        Args:
            bucket_name: Bucket name
            file_name: File name
            content: File content

        Returns:
            Bucket URL
        """
        if bucket_name not in self._buckets:
            self._buckets[bucket_name] = {}
        self._buckets[bucket_name][file_name] = content
        return f"bucket://{bucket_name}/{file_name}"

    def download_from_bucket(
        self,
        bucket_name: str,
        file_name: str,
    ) -> bytes:
        """Mock Download from Bucket.

        Args:
            bucket_name: Bucket name
            file_name: File name

        Returns:
            File content
        """
        return self._buckets.get(bucket_name, {}).get(file_name, b"")

    # Context Grounding (Knowledge Search)
    def context_grounding(
        self,
        query: str,
        index_name: str,
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        """Mock Context Grounding - semantic search.

        Args:
            query: Search query
            index_name: Knowledge index name
            top_k: Number of results

        Returns:
            List of search results
        """
        return [
            {
                "content": f"Mock tax regulation content for: {query}",
                "score": 0.95,
                "metadata": {"source": "Codul Fiscal 2024", "article": "64"},
            },
            {
                "content": f"Related tax procedure for: {query}",
                "score": 0.87,
                "metadata": {"source": "Codul de Procedura Fiscala", "article": "122"},
            },
        ][:top_k]


# Singleton instance
mock_uipath = MockUiPathSDK()
