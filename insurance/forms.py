# insurance/forms.py
from django import forms
from insurance.model.insurance_policy import InsurancePolicy
from insurance.model.customer import Customer
from insurance.model.claim import Claim
from insurance.model.payment import Payment


class InsurancePolicyForm(forms.ModelForm):
    start_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    end_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))

    class Meta:
        model = InsurancePolicy
        fields = ['policy_number', 'policy_type', 'start_date', 'end_date', 'premium', 'coverage_amount', 'customer']


class CustomerForm(forms.ModelForm):
    date_of_birth = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))

    class Meta:
        model = Customer
        fields = ['full_name', 'tax_number', 'date_of_birth', 'email', 'phone', 'address']

    def validate_unique(self):
        # Для обновления клиента игнорируем уникальные проверки на уровне формы
        # для полей email и tax_number — их корректно проверит API/БД, а форма
        # не должна блокировать сохранение текущих значений.
        if self.instance and self.instance.pk:
            exclude = self._get_validation_exclusions()
            exclude.update({'email', 'tax_number'})
            try:
                self.instance.validate_unique(exclude=exclude)
            except forms.ValidationError as e:
                self._update_errors(e)
        else:
            super().validate_unique()


class ClaimForm(forms.ModelForm):
    claim_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))

    class Meta:
        model = Claim
        fields = ['policy', 'claim_date', 'amount', 'description']


class PaymentForm(forms.ModelForm):
    date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))

    class Meta:
        model = Payment
        fields = ['amount', 'date', 'claim']
