from types import SimpleNamespace
import requests
from django.views.generic import TemplateView

API_ROOT = "http://localhost:8000/api"
TIMEOUT = 5


class HomeView(TemplateView):
    template_name = 'index.html'

    def _auth_headers(self):
        access = getattr(self.request, 'session', {}).get('jwt_access')
        if access:
            return {'Authorization': f'Bearer {access}'}
        return {}

    def get_counts(self):
        counts = {
            'policies_count': 0,
            'customers_count': 0,
            'claims_count': 0,
            'payments_count': 0,
        }
        endpoints = {
            'policies_count': '/policies/',
            'customers_count': '/customers/',
            'claims_count': '/claims/',
            'payments_count': '/payments/',
        }
        for key, path in endpoints.items():
            try:
                r = requests.get(f"{API_ROOT}{path}", timeout=TIMEOUT, headers=self._auth_headers())
                if r.status_code == 200 and isinstance(r.json(), list):
                    counts[key] = len(r.json())
            except requests.RequestException:
                pass
        return counts

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(self.get_counts())
        return ctx
