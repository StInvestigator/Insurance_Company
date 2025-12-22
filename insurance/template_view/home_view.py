from types import SimpleNamespace
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
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

    def _fetch_count(self, key, path):
        try:
            r = requests.get(f"{API_ROOT}{path}", timeout=TIMEOUT, headers=self._auth_headers())
            if r.status_code == 200 and isinstance(r.json(), dict):
                return key, int(r.json().get('count', '0'))
        except requests.RequestException:
            pass
        return key, 0

    def get_counts(self):
        r = requests.get(f"{API_ROOT}/analytics/counts/", timeout=TIMEOUT, headers=self._auth_headers())
        r.raise_for_status()
        if r.status_code == 200 and isinstance(r.json(), dict):
            data = r.json()
            return {
                'policies_count': int(data.get('policies_count', 0)),
                'customers_count': int(data.get('customers_count', 0)),
                'claims_count': int(data.get('claims_count', 0)),
                'payments_count': int(data.get('payments_count', 0)),
            }
        return {
            'policies_count': 0,
            'customers_count': 0,
            'claims_count': 0,
            'payments_count': 0,
        }

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(self.get_counts())
        return ctx
