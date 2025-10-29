from rest_framework import viewsets
from insurance.model.Customer import Customer
from ..serializers import (
    CustomerSerializer
)
from ..repository.customer_repository import CustomerRepository
from rest_framework.response import Response
from rest_framework import status


class CustomerView(viewsets.ModelViewSet):
    serializer_class = CustomerSerializer
    queryset = Customer.objects.all()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.repo = CustomerRepository()

    def list(self, request, *args, **kwargs):
        policies = self.repo.get_all()
        serializer = self.serializer_class(policies, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None, *args, **kwargs):
        policy = self.repo.get_by_id(pk)
        if not policy:
            return Response({"error": "Policy not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = self.serializer_class(policy)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            policy = self.repo.create(**serializer.validated_data)
            return Response(self.serializer_class(policy).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        partial = kwargs.pop('partial', False)
        if serializer.is_valid() or partial:
            policy = self.repo.update(pk, **serializer.validated_data)
            if not policy:
                return Response({"error": "Policy not found"}, status=status.HTTP_404_NOT_FOUND)
            return Response(self.serializer_class(policy).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None, *args, **kwargs):
        deleted = self.repo.delete(pk)
        if deleted:
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({"error": "Policy not found"}, status=status.HTTP_404_NOT_FOUND)
