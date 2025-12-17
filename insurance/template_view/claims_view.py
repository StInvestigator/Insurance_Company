from types import SimpleNamespace
from typing import Any, Dict, List

import requests
from django.http import HttpResponseServerError, HttpResponseForbidden
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, TemplateView
from django.views.generic.edit import FormView

from insurance.forms import ClaimForm


API_ROOT = "http://localhost:8000/api"
TIMEOUT = 5


def to_objects(items: List[Dict[str, Any]]):
    return [SimpleNamespace(**it) for it in items]


def _auth_headers_from(request):
    try:
        token = request.session.get('jwt_access')
        if token:
            return {"Authorization": f"Bearer {token}"}
    except Exception:
        pass
    return {}


def api_get(request, path: str, params: Dict[str, Any] | None = None):
    return requests.get(f"{API_ROOT}{path}", params=params, timeout=TIMEOUT, headers=_auth_headers_from(request))


def api_post(request, path: str, data: Dict[str, Any]):
    return requests.post(f"{API_ROOT}{path}", json=data, timeout=TIMEOUT, headers=_auth_headers_from(request))


def api_put(request, path: str, data: Dict[str, Any]):
    return requests.patch(f"{API_ROOT}{path}", json=data, timeout=TIMEOUT, headers=_auth_headers_from(request))


def api_delete(request, path: str):
    return requests.delete(f"{API_ROOT}{path}", timeout=TIMEOUT, headers=_auth_headers_from(request))


class ClaimsByCustomerListView(ListView):
    template_name = 'claims/by_customer.html'
    context_object_name = 'claims'

    def get_queryset(self):
        pk = self.kwargs.get('pk')
        try:
            customer_id = int(pk)
        except (TypeError, ValueError):
            return []
        resp = api_get(self.request, '/claims/find_by_customer', params={'customer_id': customer_id})
        if resp.status_code == 200:
            return to_objects(resp.json())
        return []

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['customer'] = {'id': self.kwargs.get('pk')}
        return ctx


class ClaimListView(ListView):
    template_name = 'claims/list.html'
    context_object_name = 'claims'

    def get_queryset(self):
        resp = api_get(self.request, '/claims/')
        if resp.status_code == 200:
            return to_objects(resp.json())
        return []


class ClaimDetailView(TemplateView):
    template_name = 'claims/detail.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        pk = self.kwargs.get('pk')
        resp = api_get(self.request, f'/claims/{pk}/')
        if resp.status_code == 200:
            ctx['claim'] = SimpleNamespace(**resp.json())
        else:
            ctx['claim'] = None
        return ctx


class ClaimCreateView(FormView):
    template_name = 'claims/form.html'
    form_class = ClaimForm
    success_url = reverse_lazy('claim_list')

    def form_valid(self, form):
        data = form.cleaned_data
        # Преобразуем связанные объекты в id
        payload = {
            'policy': data['policy'].id if hasattr(data['policy'], 'id') else data['policy'],
            'claim_date': data['claim_date'].isoformat(),
            'amount': str(data['amount']),
            'description': data['description'],
        }
        resp = api_post(self.request, '/claims/', payload)
        if resp.status_code in (200, 201):
            return super().form_valid(form)
        return self.form_invalid(form)


class ClaimUpdateView(FormView):
    template_name = 'claims/form.html'
    form_class = ClaimForm
    success_url = reverse_lazy('claim_list')

    def get_initial(self):
        pk = self.kwargs.get('pk')
        resp = api_get(f'/claims/{pk}/')
        if resp.status_code == 200:
            data = resp.json()
            return {
                'policy': data.get('policy'),
                'claim_date': data.get('claim_date'),
                'amount': data.get('amount'),
                'description': data.get('description'),
            }
        return {}

    def form_valid(self, form):
        pk = self.kwargs.get('pk')
        data = form.cleaned_data
        payload = {
            'policy': data['policy'].id if hasattr(data['policy'], 'id') else data['policy'],
            'claim_date': data['claim_date'].isoformat(),
            'amount': str(data['amount']),
            'description': data['description'],
        }
        resp = api_put(self.request, f'/claims/{pk}/', payload)
        if resp.status_code in (200, 202):
            return super().form_valid(form)
        return self.form_invalid(form)


class ClaimDeleteView(View):
    def post(self, request, pk):
        form_id = request.POST.get('id')
        if not form_id or str(pk) != str(form_id):
            return HttpResponseForbidden("Invalid ID for deletion")
        resp = api_delete(self.request, f'/claims/{pk}/')
        if resp.status_code not in (200, 204):
            return HttpResponseServerError("Failed to delete claim via API")
        return redirect(reverse_lazy('claim_list'))
