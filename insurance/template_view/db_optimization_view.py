from django.views.generic import TemplateView
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json
import requests
from urllib.parse import urljoin


class DatabaseOptimizationDashboardView(TemplateView):
    template_name = 'analytics/db_optimization_dashboard.html'
    
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        return ctx


@csrf_exempt
@require_http_methods(["POST"])
def run_optimization_experiment(request):
    try:
        data = json.loads(request.body)
        
        api_url = urljoin(request.build_absolute_uri('/'), '/api/analytics/db-optimization/')
        response = requests.post(api_url, json=data, timeout=300)
        
        if response.status_code == 200:
            return JsonResponse(response.json())
        else:
            return JsonResponse(
                {'error': f'API returned status {response.status_code}'},
                status=response.status_code
            )
    except Exception as e:
        return JsonResponse(
            {'error': str(e)},
            status=500
        )

