from rest_framework import viewsets
from ..models import InsurancePolicy
from ..serializers import (
    InsurancePolicySerializer
)

from ..repository.policy_repository import PolicyRepository
from rest_framework.response import Response
from rest_framework import status



class InsurancePolicyViewSet(viewsets.ModelViewSet):

    queryset = InsurancePolicy.objects.all()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.repo = PolicyRepository()

    def list(self, request):
        policies = self.repo.get_all()
        serializer = InsurancePolicySerializer(policies, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        policy = self.repo.get_by_id(pk)
        if not policy:
            return Response({"error": "Policy not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = InsurancePolicySerializer(policy)
        return Response(serializer.data)

    def create(self, request):
        serializer = InsurancePolicySerializer(data=request.data)
        if serializer.is_valid():
            policy = self.repo.create(serializer.validated_data)
            return Response(InsurancePolicySerializer(policy).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None):
        serializer = InsurancePolicySerializer(data=request.data)
        if serializer.is_valid():
            policy = self.repo.update(pk, serializer.validated_data)
            if not policy:
                return Response({"error": "Policy not found"}, status=status.HTTP_404_NOT_FOUND)
            return Response(InsurancePolicySerializer(policy).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        deleted = self.repo.delete(pk)
        if deleted:
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({"error": "Policy not found"}, status=status.HTTP_404_NOT_FOUND)