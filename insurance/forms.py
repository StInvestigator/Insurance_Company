# insurance/forms.py
from django import forms
from insurance.model.insurance_policy import InsurancePolicy


class InsurancePolicyForm(forms.ModelForm):
    start_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    end_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))

    class Meta:
        model = InsurancePolicy
        fields = ['policy_number', 'policy_type', 'start_date', 'end_date', 'premium', 'coverage_amount', 'customer']
