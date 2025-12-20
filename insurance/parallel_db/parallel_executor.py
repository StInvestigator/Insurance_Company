
import time
import psutil
import os
import inspect
import importlib
from typing import List, Dict, Callable, Any, Optional
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from django.db import connection, connections


@dataclass
class ExecutionMetrics:
    total_time: float
    avg_time_per_query: float
    min_time: float
    max_time: float
    success_count: int
    error_count: int
    cpu_usage_percent: float
    memory_usage_mb: float
    num_threads: int
    num_processes: int
    batch_size: int
    total_queries: int


def close_db_connections():
    for conn in connections.all():
        conn.close()


def execute_query_in_thread(query_func: Callable, query_id: int, *args, **kwargs) -> Dict[str, Any]:
    try:
        start_time = time.time()
        result = query_func(*args, **kwargs)
        execution_time = time.time() - start_time
        
        close_db_connections()
        
        return {
            'query_id': query_id,
            'success': True,
            'execution_time': execution_time,
            'result': result,
            'error': None
        }
    except Exception as e:
        execution_time = time.time() - start_time if 'start_time' in locals() else 0
        close_db_connections()
        return {
            'query_id': query_id,
            'success': False,
            'execution_time': execution_time,
            'result': None,
            'error': str(e)
        }


def execute_query_in_process(query_func_pickle: tuple, query_id: int) -> Dict[str, Any]:
    if 'DJANGO_SETTINGS_MODULE' not in os.environ:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'insurance.settings')
    
    import django
    if not django.apps.apps.ready:
        django.setup()
    
    module_path, func_name, args, kwargs = query_func_pickle
    module = importlib.import_module(module_path)
    query_func = getattr(module, func_name)
    
    try:
        start_time = time.time()
        result = query_func(*args, **kwargs)
        execution_time = time.time() - start_time
        
        close_db_connections()
        
        return {
            'query_id': query_id,
            'success': True,
            'execution_time': execution_time,
            'result': result,
            'error': None
        }
    except Exception as e:
        execution_time = time.time() - start_time if 'start_time' in locals() else 0
        close_db_connections()
        return {
            'query_id': query_id,
            'success': False,
            'execution_time': execution_time,
            'result': None,
            'error': str(e)
        }


class ParallelDBExecutor:
    def __init__(self, use_processes: bool = False):
        self.use_processes = use_processes
        self.process = psutil.Process(os.getpid())
    
    def execute_queries(
        self,
        queries: List[Callable],
        max_workers: int = 4,
        batch_size: Optional[int] = None
    ) -> ExecutionMetrics:
        total_queries = len(queries)
        if batch_size is None:
            batch_size = total_queries
        
        cpu_before = self.process.cpu_percent(interval=0.1)
        memory_before = self.process.memory_info().rss / 1024 / 1024
        
        start_time = time.time()
        results = []
        
        for batch_start in range(0, total_queries, batch_size):
            batch_end = min(batch_start + batch_size, total_queries)
            batch_queries = queries[batch_start:batch_end]
            
            if self.use_processes:
                executor = ProcessPoolExecutor(max_workers=max_workers)
                execute_func = execute_query_in_process
            else:
                executor = ThreadPoolExecutor(max_workers=max_workers)
                execute_func = execute_query_in_thread
            
            futures = []
            for idx, query_func in enumerate(batch_queries):
                query_id = batch_start + idx
                if self.use_processes:
                    import inspect
                    module_path = inspect.getmodule(query_func).__name__
                    func_name = query_func.__name__
                    future = executor.submit(execute_func, (module_path, func_name, (), {}), query_id)
                else:
                    future = executor.submit(execute_func, query_func, query_id)
                futures.append(future)
            
            for future in as_completed(futures):
                results.append(future.result())
            
            executor.shutdown(wait=True)
        
        total_time = time.time() - start_time
        
        cpu_after = self.process.cpu_percent(interval=0.1)
        memory_after = self.process.memory_info().rss / 1024 / 1024
        
        execution_times = [r['execution_time'] for r in results if r['success']]
        success_count = sum(1 for r in results if r['success'])
        error_count = total_queries - success_count
        
        if execution_times:
            avg_time = sum(execution_times) / len(execution_times)
            min_time = min(execution_times)
            max_time = max(execution_times)
        else:
            avg_time = min_time = max_time = 0
        
        return ExecutionMetrics(
            total_time=total_time,
            avg_time_per_query=avg_time,
            min_time=min_time,
            max_time=max_time,
            success_count=success_count,
            error_count=error_count,
            cpu_usage_percent=max(cpu_before, cpu_after),
            memory_usage_mb=memory_after - memory_before,
            num_threads=max_workers if not self.use_processes else 0,
            num_processes=max_workers if self.use_processes else 0,
            batch_size=batch_size,
            total_queries=total_queries
        )

