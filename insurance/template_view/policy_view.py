from types import SimpleNamespace
from typing import Any, Dict, List

import requests
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseServerError, HttpResponseForbidden
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, TemplateView
from django.views.generic.edit import FormView

from insurance.forms import InsurancePolicyForm


API_ROOT = "http://localhost:8000/api"
TIMEOUT = 5

def _auth_headers_from(request):
    try:
        token = request.session.get('jwt_access')
        if token:
            return {"Authorization": f"Bearer {token}"}
    except Exception:
        pass
    return {}

def to_objects(items: List[Dict[str, Any]]):
    return [SimpleNamespace(**it) for it in items]


def api_get(request, path: str, params: Dict[str, Any] | None = None):
    return requests.get(f"{API_ROOT}{path}", params=params, timeout=TIMEOUT, headers=_auth_headers_from(request))


def api_post(request, path: str, data: Dict[str, Any]):
    return requests.post(f"{API_ROOT}{path}", json=data, timeout=TIMEOUT, headers=_auth_headers_from(request))


def api_put(request, path: str, data: Dict[str, Any]):
    return requests.put(f"{API_ROOT}{path}", json=data, timeout=TIMEOUT, headers=_auth_headers_from(request))


def api_delete(request, path: str):
    return requests.delete(f"{API_ROOT}{path}", timeout=TIMEOUT, headers=_auth_headers_from(request))


class InsurancePolicyListView(LoginRequiredMixin, ListView):
    template_name = 'policies/list.html'
    context_object_name = 'policies'
    
    def get_queryset(self):
        return []

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        try:
            page = int(self.request.GET.get('page', '1'))
        except ValueError:
            page = 1
        params = {'page': page, 'page_size': 10}
        resp = api_get(self.request, '/policies/', params=params)
        items: List[Dict[str, Any]] = []
        total_pages = 1
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, list):
                items = data
                total_pages = 1
            else:
                items = data.get('items', [])
                total_pages = data.get('total_pages', 1)
        current = max(1, min(page, total_pages))
        has_prev = current > 1
        has_next = current < total_pages
        def _next():
            return current + 1 if has_next else current
        def _prev():
            return current - 1 if has_prev else current
        ctx['policies'] = to_objects(items)
        ctx['is_paginated'] = total_pages > 1
        ctx['paginator'] = SimpleNamespace(num_pages=total_pages)
        ctx['page_obj'] = SimpleNamespace(
            number=current,
            has_previous=has_prev,
            has_next=has_next,
            previous_page_number=_prev,
            next_page_number=_next,
        )
        return ctx


class InsurancePolicyDetailView(LoginRequiredMixin, TemplateView):
    template_name = 'policies/detail.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        pk = self.kwargs.get('pk')
        resp = api_get(self.request, f'/policies/{pk}/')
        if resp.status_code == 200:
            ctx['policy'] = SimpleNamespace(**resp.json())
        else:
            ctx['policy'] = None
        return ctx


class InsurancePolicyCreateView(LoginRequiredMixin, FormView):
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
        resp = api_post(self.request, '/policies/', payload)
        if resp.status_code in (200, 201):
            return super().form_valid(form)
        return self.form_invalid(form)


class InsurancePolicyUpdateView(LoginRequiredMixin, FormView):
    template_name = 'policies/form.html'
    form_class = InsurancePolicyForm
    success_url = reverse_lazy('policy_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        try:
            pk = self.kwargs.get('pk')
            if pk is not None:
                from insurance.model.insurance_policy import InsurancePolicy
                instance = InsurancePolicy.objects.filter(pk=pk).first()
                if instance is not None:
                    kwargs['instance'] = instance
        except Exception:
            pass
        return kwargs

    def get_initial(self):
        pk = self.kwargs.get('pk')
        resp = api_get(self.request, f'/policies/{pk}/')
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
        resp = api_put(self.request, f'/policies/{pk}/', payload)
        if resp.status_code in (200, 202):
            return super().form_valid(form)
        return self.form_invalid(form)


class InsurancePolicyDeleteView(LoginRequiredMixin, View):
    def post(self, request, pk):
        form_id = request.POST.get('id')
        if not form_id or str(pk) != str(form_id):
            return HttpResponseForbidden("Invalid ID for deletion")
        resp = api_delete(self.request, f'/policies/{pk}/')
        if resp.status_code not in (200, 204):
            return HttpResponseServerError("Failed to delete policy via API")
        return redirect(reverse_lazy('policy_list'))
