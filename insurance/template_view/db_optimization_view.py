# db_optimization_view.py
from django.views.generic import TemplateView
from insurance.parallel_db.optimizer import DatabaseOptimizer

class DatabaseOptimizationDashboardView(TemplateView):
    template_name = 'analytics/db_optimization_dashboard.html'

    def post(self, request, *args, **kwargs):
        num_queries = int(request.POST.get("num_queries", 150))
        num_workers = list(map(int, request.POST.get("num_workers", "1,2,4,8").split(",")))
        batch_sizes = list(map(int, request.POST.get("batch_sizes", "10,25,50").split(",")))

        test_threads = "test_threads" in request.POST
        test_processes = "test_processes" in request.POST

        optimizer = DatabaseOptimizer(num_queries=num_queries)
        results = optimizer.run_experiments(
            num_workers_range=num_workers,
            batch_sizes=batch_sizes,
            test_threads=test_threads,
            test_processes=test_processes
        )

        data = optimizer.find_optimal_config(results)

        context = self.get_context_data(**kwargs)
        context.update(data)

        return self.render_to_response(context)
