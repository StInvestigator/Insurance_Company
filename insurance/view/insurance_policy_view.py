from rest_framework import viewsets

from insurance.model.insurance_policy import InsurancePolicy
from ..serializers import (
    InsurancePolicySerializer
)
from ..repository.unit_of_work import UnitOfWork


class InsurancePolicyView(viewsets.ModelViewSet):
    serializer_class = InsurancePolicySerializer
    with UnitOfWork() as repo:
        queryset = repo.policies.get_all()