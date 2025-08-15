# services/task_queue.py
import asyncio
import threading
import queue
import logging
from datetime import datetime
from typing import Callable, Any, Dict, List
from dataclasses import dataclass
from enum import Enum
import uuid

class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class Task:
    task_id: str
    func: Callable
    args: tuple
    kwargs: dict
    status: TaskStatus
    created_at: datetime
    started_at: datetime = None
    completed_at: datetime = None
    result: Any = None
    error: str = None

class TaskQueue:
    """Simple background task queue for KrishiMitra"""
    
    def __init__(self, max_workers: int = 3):
        self.max_workers = max_workers
        self.task_queue = queue.Queue()
        self.tasks: Dict[str, Task] = {}
        self.workers: List[threading.Thread] = []
        self.running = False
        self.logger = logging.getLogger(__name__)
    
    async def start(self):
        """Start the task queue"""
        if self.running:
            return
        
        self.running = True
        self.logger.info("Task queue started")
        
        # Start worker threads
        for i in range(self.max_workers):
            worker = threading.Thread(target=self._worker, name=f"TaskWorker-{i}")
            worker.daemon = True
            worker.start()
            self.workers.append(worker)
        
        # Start periodic cleanup
        asyncio.create_task(self._periodic_cleanup())
        
        # Run periodic tasks
        await self._run_periodic_tasks()
    
    async def stop(self):
        """Stop the task queue"""
        self.running = False
        
        # Signal all workers to stop
        for _ in range(self.max_workers):
            self.task_queue.put(None)
        
        # Wait for workers to finish
        for worker in self.workers:
            worker.join(timeout=5)
        
        self.workers.clear()
        self.logger.info("Task queue stopped")
    
    def add_task(self, func: Callable, *args, **kwargs) -> str:
        """Add a task to the queue"""
        task_id = str(uuid.uuid4())
        
        task = Task(
            task_id=task_id,
            func=func,
            args=args,
            kwargs=kwargs,
            status=TaskStatus.PENDING,
            created_at=datetime.now()
        )
        
        self.tasks[task_id] = task
        self.task_queue.put(task)
        
        return task_id
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get task status"""
        task = self.tasks.get(task_id)
        if not task:
            return {"error": "Task not found"}
        
        return {
            "task_id": task.task_id,
            "status": task.status.value,
            "created_at": task.created_at.isoformat(),
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "result": task.result,
            "error": task.error
        }
    
    def _worker(self):
        """Worker thread function"""
        while self.running:
            try:
                task = self.task_queue.get(timeout=1)
                
                if task is None:  # Shutdown signal
                    break
                
                # Execute task
                task.status = TaskStatus.RUNNING
                task.started_at = datetime.now()
                
                try:
                    result = task.func(*task.args, **task.kwargs)
                    task.result = result
                    task.status = TaskStatus.COMPLETED
                except Exception as e:
                    task.error = str(e)
                    task.status = TaskStatus.FAILED
                    self.logger.error(f"Task {task.task_id} failed: {str(e)}")
                
                task.completed_at = datetime.now()
                self.task_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Worker error: {str(e)}")
    
    async def _periodic_cleanup(self):
        """Clean up old completed tasks"""
        while self.running:
            try:
                await asyncio.sleep(3600)  # Run every hour
                
<<<<<<< HEAD
                from datetime import timedelta
                cutoff_time = datetime.now() - timedelta(hours=24)
=======
                cutoff_time = datetime.now().replace(hour=datetime.now().hour - 24)
>>>>>>> 5cb95f1756f99b9b6a413434887e60db00428edf
                
                # Remove old completed tasks
                old_tasks = [
                    task_id for task_id, task in self.tasks.items()
                    if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]
                    and task.completed_at and task.completed_at < cutoff_time
                ]
                
                for task_id in old_tasks:
                    del self.tasks[task_id]
                
                if old_tasks:
                    self.logger.info(f"Cleaned up {len(old_tasks)} old tasks")
                    
            except Exception as e:
                self.logger.error(f"Cleanup error: {str(e)}")
    
    async def _run_periodic_tasks(self):
        """Run periodic background tasks"""
        try:
            # Clean up old notifications
            from services.notification_service import notification_service
            notification_service.cleanup_old_notifications(days=30)
            
            # Clean up old cache entries
            from services.offline_cache import offline_cache
            offline_cache.clear_expired()
            
            self.logger.info(f"Periodic tasks completed at {datetime.now()}")
            
        except Exception as e:
            self.logger.error(f"Periodic tasks error: {str(e)}")

# Background task functions
def send_notification_task(user_id: str, title: str, message: str, notification_type: str):
    """Background task to send notification"""
    try:
        from services.notification_service import notification_service, NotificationType
        notification_service.create_notification(
            user_id=user_id,
            title=title,
            message=message,
            notification_type=NotificationType(notification_type)
        )
    except Exception as e:
        logging.error(f"Notification task error: {str(e)}")

def process_image_task(image_path: str, user_id: str):
    """Background task to process uploaded images"""
    try:
        from services.enhanced_gemini import enhanced_gemini
        from services.user_profiles import user_profile_service
        
        # Analyze image
        analysis = enhanced_gemini.analyze_image(image_path)
        
        # Record interaction
        user_profile_service.record_interaction(
            user_id=user_id,
            interaction_type="image_analysis",
            query=f"Image analysis: {image_path}",
            response=str(analysis),
            confidence_score=0.8,
            data_sources=["gemini_vision"]
        )
        
    except Exception as e:
        logging.error(f"Image processing task error: {str(e)}")

def market_monitoring_task():
    """Background task to monitor market changes"""
    try:
        from services.real_market_api import real_market_api
        from services.notification_service import notification_service
        
        # This would monitor price changes and send alerts
        # Implementation depends on specific market monitoring requirements
        
    except Exception as e:
        logging.error(f"Market monitoring task error: {str(e)}")

# Global task queue
task_queue = TaskQueue()