from rest_framework import viewsets

from insurance.model.insurance_policy import InsurancePolicy
from ..serializers import (
    InsurancePolicySerializer
)
from ..repository.unit_of_work import UnitOfWork
from rest_framework import permissions


class InsurancePolicyView(viewsets.ModelViewSet):
    permission_classes = [permissions.AllowAny]
    serializer_class = InsurancePolicySerializer
    with UnitOfWork() as repo:
        queryset = repo.policies.get_all()