# insurance/views.py
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, View
from django.shortcuts import redirect
from django.http import HttpResponseForbidden, HttpResponseServerError
from .model.insurance_policy import InsurancePolicy
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
