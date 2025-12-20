from typing import List, Dict, Any
from dataclasses import dataclass, asdict
from insurance.parallel_db.parallel_executor import ParallelDBExecutor, ExecutionMetrics
from insurance.parallel_db.query_generator import generate_test_queries


@dataclass
class ExperimentResult:
    num_workers: int
    batch_size: int
    use_processes: bool
    metrics: ExecutionMetrics
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            'num_workers': self.num_workers,
            'batch_size': self.batch_size,
            'use_processes': self.use_processes,
            'total_time': self.metrics.total_time,
            'avg_time_per_query': self.metrics.avg_time_per_query,
            'min_time': self.metrics.min_time,
            'max_time': self.metrics.max_time,
            'success_count': self.metrics.success_count,
            'error_count': self.metrics.error_count,
            'cpu_usage_percent': self.metrics.cpu_usage_percent,
            'memory_usage_mb': self.metrics.memory_usage_mb,
            'total_queries': self.metrics.total_queries,
        }
        return result


class DatabaseOptimizer:
    def __init__(self, num_queries: int = 150):
        self.num_queries = num_queries
        self.queries = generate_test_queries(num_queries)
    
    def run_experiments(
        self,
        num_workers_range: List[int] = None,
        batch_sizes: List[int] = None,
        test_threads: bool = True,
        test_processes: bool = False
    ) -> List[ExperimentResult]:
        if num_workers_range is None:
            num_workers_range = [1, 2, 4, 8, 16]
        
        if batch_sizes is None:
            batch_sizes = [None, 10, 25, 50, 100]
        
        results = []
        
        if test_threads:
            for num_workers in num_workers_range:
                for batch_size in batch_sizes:
                    executor = ParallelDBExecutor(use_processes=False)
                    metrics = executor.execute_queries(
                        queries=self.queries,
                        max_workers=num_workers,
                        batch_size=batch_size
                    )
                    result = ExperimentResult(
                        num_workers=num_workers,
                        batch_size=batch_size or self.num_queries,
                        use_processes=False,
                        metrics=metrics
                    )
                    results.append(result)
        
        if test_processes:
            for num_workers in num_workers_range:
                for batch_size in batch_sizes:
                    executor = ParallelDBExecutor(use_processes=True)
                    metrics = executor.execute_queries(
                        queries=self.queries,
                        max_workers=num_workers,
                        batch_size=batch_size
                    )
                    result = ExperimentResult(
                        num_workers=num_workers,
                        batch_size=batch_size or self.num_queries,
                        use_processes=True,
                        metrics=metrics
                    )
                    results.append(result)
        
        return results
    
    def find_optimal_config(self, results: List[ExperimentResult]) -> Dict[str, Any]:
        if not results:
            return {}
        
        best_result = min(results, key=lambda r: r.metrics.total_time)
        
        by_workers = {}
        for result in results:
            key = result.num_workers
            if key not in by_workers:
                by_workers[key] = []
            by_workers[key].append(result)
        
        avg_times_by_workers = {
            workers: sum(r.metrics.total_time for r in results_list) / len(results_list)
            for workers, results_list in by_workers.items()
        }
        
        return {
            'optimal_config': {
                'num_workers': best_result.num_workers,
                'batch_size': best_result.batch_size,
                'use_processes': best_result.use_processes,
                'total_time': best_result.metrics.total_time,
            },
            'all_results': [r.to_dict() for r in results],
            'avg_time_by_workers': avg_times_by_workers,
            'best_result': best_result.to_dict(),
        }

