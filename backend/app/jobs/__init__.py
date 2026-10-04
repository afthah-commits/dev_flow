from typing import Callable, Dict, Any, Optional

JobHandler = Callable[[Dict[str, Any]], None]

class JobRegistry:
    def __init__(self):
        self._handlers: Dict[str, JobHandler] = {}

    def register(self, job_type: str, handler: JobHandler):
        self._handlers[job_type] = handler

    def get(self, job_type: str) -> Optional[JobHandler]:
        return self._handlers.get(job_type)

    def list_job_types(self):
        return list(self._handlers.keys())

job_registry = JobRegistry()

def register_job(job_type: str):
    def decorator(func: JobHandler):
        job_registry.register(job_type, func)
        return func
    return decorator

# Import handlers so they get registered
from app.jobs import handlers
