from types import SimpleNamespace
from typing import Any, Dict, List

import requests
from django.http import HttpResponseServerError, HttpResponseForbidden
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, TemplateView
from django.views.generic.edit import FormView

from insurance.forms import InsurancePolicyForm


API_ROOT = "http://localhost:8000/api"
TIMEOUT = 5


def to_objects(items: List[Dict[str, Any]]):
    return [SimpleNamespace(**it) for it in items]


def api_get(path: str, params: Dict[str, Any] | None = None):
    return requests.get(f"{API_ROOT}{path}", params=params, timeout=TIMEOUT)


def api_post(path: str, data: Dict[str, Any]):
    return requests.post(f"{API_ROOT}{path}", json=data, timeout=TIMEOUT)


def api_put(path: str, data: Dict[str, Any]):
    return requests.put(f"{API_ROOT}{path}", json=data, timeout=TIMEOUT)


def api_delete(path: str):
    return requests.delete(f"{API_ROOT}{path}", timeout=TIMEOUT)


class InsurancePolicyListView(ListView):
    template_name = 'policies/list.html'
    context_object_name = 'policies'

    def get_queryset(self):
        resp = api_get('/policies/')
        if resp.status_code == 200:
            return to_objects(resp.json())
        return []


class InsurancePolicyDetailView(TemplateView):
    template_name = 'policies/detail.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        pk = self.kwargs.get('pk')
        resp = api_get(f'/policies/{pk}/')
        if resp.status_code == 200:
            ctx['policy'] = SimpleNamespace(**resp.json())
        else:
            ctx['policy'] = None
        return ctx


class InsurancePolicyCreateView(FormView):
    template_name = 'policies/form.html'
    form_class = InsurancePolicyForm
    success_url = reverse_lazy('policy_list')

    def form_valid(self, form):
        data = form.cleaned_data
        payload = {
            'policy_number': data['policy_number'],
            'policy_type': data['policy_type'],
            'start_date': data['start_date'].isoformat(),
            'end_date': data['end_date'].isoformat() if data.get('end_date') else None,
            'premium': str(data['premium']),
            'coverage_amount': str(data['coverage_amount']),
            'customer': data['customer'].id if hasattr(data['customer'], 'id') else data['customer'],
        }
        resp = api_post('/policies/', payload)
        if resp.status_code in (200, 201):
            return super().form_valid(form)
        return self.form_invalid(form)


class InsurancePolicyUpdateView(FormView):
    template_name = 'policies/form.html'
    form_class = InsurancePolicyForm
    success_url = reverse_lazy('policy_list')

    def get_initial(self):
        pk = self.kwargs.get('pk')
        resp = api_get(f'/policies/{pk}/')
        if resp.status_code == 200:
            data = resp.json()
            return {
                'policy_number': data.get('policy_number'),
                'policy_type': data.get('policy_type'),
                'start_date': data.get('start_date'),
                'end_date': data.get('end_date'),
                'premium': data.get('premium'),
                'coverage_amount': data.get('coverage_amount'),
                'customer': data.get('customer'),
            }
        return {}

    def form_valid(self, form):
        pk = self.kwargs.get('pk')
        data = form.cleaned_data
        payload = {
            'policy_number': data['policy_number'],
            'policy_type': data['policy_type'],
            'start_date': data['start_date'].isoformat(),
            'end_date': data['end_date'].isoformat() if data.get('end_date') else None,
            'premium': str(data['premium']),
            'coverage_amount': str(data['coverage_amount']),
            'customer': data['customer'].id if hasattr(data['customer'], 'id') else data['customer'],
        }
        resp = api_put(f'/policies/{pk}/', payload)
        if resp.status_code in (200, 202):
            return super().form_valid(form)
        return self.form_invalid(form)


class InsurancePolicyDeleteView(View):
    def post(self, request, pk):
        form_id = request.POST.get('id')
        if not form_id or str(pk) != str(form_id):
            return HttpResponseForbidden("Invalid ID for deletion")
        resp = api_delete(f'/policies/{pk}/')
        if resp.status_code not in (200, 204):
            return HttpResponseServerError("Failed to delete policy via API")
        return redirect(reverse_lazy('policy_list'))
