# insurance/views.py
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, View
from django.shortcuts import get_object_or_404, redirect, render
from django.http import HttpResponseForbidden
from .model.insurance_policy import InsurancePolicy
from .forms import InsurancePolicyForm

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
    """
    Отримує POST з полем 'id' (або стандартний pk з URL) і видаляє запис.
    Ми перевіряємо що id збігається з URL (додаткова перевірка для безпеки).
    """
    def post(self, request, pk):
        # При бажанні додай перевірку прав: if not request.user.is_authenticated: return HttpResponseForbidden()
        policy = get_object_or_404(InsurancePolicy, pk=pk)
        form_id = request.POST.get('id')
        if not form_id or str(policy.pk) != str(form_id):
            # Невласний id — забороняємо видалення
            return HttpResponseForbidden("Invalid ID for deletion")
        policy.delete()
        return redirect(reverse_lazy('policy_list'))
