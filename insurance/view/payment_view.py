from rest_framework import viewsets

from insurance.model.payment import Payment
from ..serializers import (
    PaymentSerializer,
)
from ..repository.unit_of_work import UnitOfWork


class PaymentView(viewsets.ModelViewSet):
    with UnitOfWork() as repo:
        queryset = repo.payments.get_all()
    serializer_class = PaymentSerializer