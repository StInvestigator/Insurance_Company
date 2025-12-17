from types import SimpleNamespace
from typing import Any, Dict, List

import requests
from django.http import HttpResponseServerError, HttpResponseForbidden
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, TemplateView
from django.views.generic.edit import FormView

from insurance.forms import CustomerForm


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
    return requests.put(f"{API_ROOT}{path}", json=data, timeout=TIMEOUT, headers=_auth_headers_from(request))


def api_delete(request, path: str):
    return requests.delete(f"{API_ROOT}{path}", timeout=TIMEOUT, headers=_auth_headers_from(request))


class CustomerListView(ListView):
    template_name = 'customers/list.html'
    context_object_name = 'customers'

    def get_queryset(self):
        resp = api_get(self.request, '/customers/')
        if resp.status_code == 200:
            return to_objects(resp.json())
        return []


class CustomerDetailView(TemplateView):
    template_name = 'customers/detail.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        pk = self.kwargs.get('pk')
        resp = api_get(self.request, f'/customers/{pk}/')
        if resp.status_code == 200:
            ctx['customer'] = SimpleNamespace(**resp.json())
        else:
            ctx['customer'] = None
        return ctx


class CustomerCreateView(FormView):
    template_name = 'customers/form.html'
    form_class = CustomerForm
    success_url = reverse_lazy('customer_list')

    def form_valid(self, form):
        data = form.cleaned_data
        payload = {
            'full_name': data['full_name'],
            'tax_number': data['tax_number'],
            'date_of_birth': data['date_of_birth'].isoformat(),
            'email': data['email'],
            'phone': data['phone'],
            'address': data['address'],
        }
        resp = api_post(self.request, '/customers/', payload)
        if resp.status_code in (200, 201):
            return super().form_valid(form)
        return self.form_invalid(form)


class CustomerUpdateView(FormView):
    template_name = 'customers/form.html'
    form_class = CustomerForm
    success_url = reverse_lazy('customer_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Передаём instance с текущим pk, чтобы ModelForm корректно обрабатывала
        # уникальные поля (email, tax_number) при обновлении существующего клиента.
        try:
            pk = self.kwargs.get('pk')
            if pk is not None:
                from insurance.model.customer import Customer
                # Важно: получить объект из БД, чтобы instance._state.adding = False,
                # иначе Django воспримет форму как создание и сработают unique-ошибки.
                instance = Customer.objects.filter(pk=pk).first()
                if instance is not None:
                    kwargs['instance'] = instance
        except Exception:
            # В случае любой ошибки просто продолжаем без instance
            pass
        return kwargs

    def get_initial(self):
        pk = self.kwargs.get('pk')
        resp = api_get(f'/customers/{pk}/')
        if resp.status_code == 200:
            data = resp.json()
            return {
                'full_name': data.get('full_name'),
                'tax_number': data.get('tax_number'),
                'date_of_birth': data.get('date_of_birth'),
                'email': data.get('email'),
                'phone': data.get('phone'),
                'address': data.get('address'),
            }
        return {}

    def form_valid(self, form):
        pk = self.kwargs.get('pk')
        data = form.cleaned_data
        payload = {
            'full_name': data['full_name'],
            'tax_number': data['tax_number'],
            'date_of_birth': data['date_of_birth'].isoformat(),
            'email': data['email'],
            'phone': data['phone'],
            'address': data['address'],
        }
        resp = api_put(self.request, f'/customers/{pk}/', payload)
        if resp.status_code in (200, 202):
            return super().form_valid(form)
        return self.form_invalid(form)


class CustomerDeleteView(View):
    def post(self, request, pk):
        form_id = request.POST.get('id')
        if not form_id or str(pk) != str(form_id):
            return HttpResponseForbidden("Invalid ID for deletion")
        resp = api_delete(self.request, f'/customers/{pk}/')
        if resp.status_code not in (200, 204):
            return HttpResponseServerError("Failed to delete customer via API")
        return redirect(reverse_lazy('customer_list'))
