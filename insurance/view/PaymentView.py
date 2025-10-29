from rest_framework import viewsets

from insurance.model.Payment import Payment
from ..serializers import (
    PaymentSerializer,
)


class PaymentView(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer