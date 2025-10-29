from rest_framework import viewsets
from .models import Customer, InsurancePolicy, Claim, Payment
from .serializers import (
    CustomerSerializer,
    InsurancePolicySerializer,
    ClaimSerializer,
    PaymentSerializer
)

# Generic CRUD контролери

class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer


class InsurancePolicyViewSet(viewsets.ModelViewSet):
    queryset = InsurancePolicy.objects.all()
    serializer_class = InsurancePolicySerializer


class ClaimViewSet(viewsets.ModelViewSet):
    queryset = Claim.objects.all()
    serializer_class = ClaimSerializer


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
