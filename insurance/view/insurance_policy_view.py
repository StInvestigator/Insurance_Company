from rest_framework import viewsets

from insurance.model.insurance_policy import InsurancePolicy
from ..serializers import (
    InsurancePolicySerializer
)


class InsurancePolicyView(viewsets.ModelViewSet):
    serializer_class = InsurancePolicySerializer
    queryset = InsurancePolicy.objects.all()