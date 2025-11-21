# insurance/views.py
from types import SimpleNamespace

from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, View
from django.shortcuts import redirect
from django.http import HttpResponseForbidden, HttpResponseServerError
from .model.insurance_policy import InsurancePolicy
from .model.claim import Claim
from .forms import InsurancePolicyForm
import requests


class InsurancePolicyListView(ListView):
    model = InsurancePolicy
    template_name = 'policy_list.html'
    context_object_name = 'policies'
    paginate_by = 20


class InsurancePolicyDetailView(DetailView):
    model = InsurancePolicy
    template_name = 'policy_detail.html'
    context_object_name = 'policy'


class InsurancePolicyCreateView(CreateView):
    model = InsurancePolicy
    form_class = InsurancePolicyForm
    template_name = 'policy_form.html'
    success_url = reverse_lazy('policy_list')


class InsurancePolicyUpdateView(UpdateView):
    model = InsurancePolicy
    form_class = InsurancePolicyForm
    template_name = 'policy_form.html'
    success_url = reverse_lazy('policy_list')


class InsurancePolicyDeleteView(View):
    def post(self, request, pk):
        form_id = request.POST.get('id')
        if not form_id or str(pk) != str(form_id):
            return HttpResponseForbidden("Invalid ID for deletion")

        url = f"http://localhost:8000/api/policies/{pk}/"
        response = requests.delete(url)

        if response.status_code not in (200, 204):
            return HttpResponseServerError("Failed to delete policy via API")

        return redirect(reverse_lazy('policy_list'))


class ClaimsByCustomerListView(ListView):
    template_name = 'claims_by_customer.html'
    context_object_name = 'claims'

    def get_claims_from_api(self, customer_id):
        """
        Робимо GET на API і конвертуємо JSON у прості об'єкти.
        """
        url = f"http://localhost:8000/api/claims/find_by_customer"
        params = {'customer_id': customer_id}
        try:
            response = requests.get(url, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()  # список dict
                print(data)
                claims = []
                for c in data:
                    claims.append(SimpleNamespace(**c))
                return claims
        except requests.RequestException:
            pass
        return []

    def get_queryset(self):
        pk = self.kwargs.get('pk')
        if not pk:
            return []

        try:
            customer_id = int(pk)
        except (TypeError, ValueError):
            return []

        return self.get_claims_from_api(customer_id)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['customer'] = {'id': self.kwargs.get('pk')}  # щоб твій шаблон {% if customer %} працював
        return ctx