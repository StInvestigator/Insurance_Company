from rest_framework import viewsets
from ..models import Customer, InsurancePolicy, Claim, Payment
from ..serializers import (
    CustomerSerializer,
    InsurancePolicySerializer,
    ClaimSerializer,
    PaymentSerializer,
    RegisterSerializer
)

from ..repository.policy_repository import PolicyRepository
from ..repository.customer_repository import CustomerRepository
from ..repository.claim_repository import ClaimRepository
from ..repository.payment_repository import PaymentRepository
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import generics, permissions
from django.contrib.auth.models import User
from rest_framework import status



class ClaimViewSet(viewsets.ModelViewSet):
    queryset = Claim.objects.all()

    queryset = Claim.objects.all()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.repo = ClaimRepository()

    def list(self, request):
        policies = self.repo.get_all()
        serializer = ClaimSerializer(policies, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        policy = self.repo.get_by_id(pk)
        if not policy:
            return Response({"error": "Policy not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = ClaimSerializer(policy)
        return Response(serializer.data)

    def create(self, request):
        serializer = ClaimSerializer(data=request.data)
        if serializer.is_valid():
            policy = self.repo.create(serializer.validated_data)
            return Response(ClaimSerializer(policy).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None):
        serializer = ClaimSerializer(data=request.data)
        if serializer.is_valid():
            policy = self.repo.update(pk, serializer.validated_data)
            if not policy:
                return Response({"error": "Policy not found"}, status=status.HTTP_404_NOT_FOUND)
            return Response(ClaimSerializer(policy).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        deleted = self.repo.delete(pk)
        if deleted:
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({"error": "Policy not found"}, status=status.HTTP_404_NOT_FOUND)