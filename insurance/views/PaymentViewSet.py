from rest_framework import viewsets
from ..models import Payment
from ..serializers import (
    PaymentSerializer,
)


from ..repository.payment_repository import PaymentRepository
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework import status


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    permission_classes = [permissions.AllowAny]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.repo = PaymentRepository()

    def list(self, request):
        policies = self.repo.get_all()
        serializer = PaymentSerializer(policies, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        policy = self.repo.get_by_id(pk)
        if not policy:
            return Response({"error": "Policy not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = PaymentSerializer(policy)
        return Response(serializer.data)

    def create(self, request):
        serializer = PaymentSerializer(data=request.data)
        if serializer.is_valid():
            policy = self.repo.create(serializer.validated_data)
            return Response(PaymentSerializer(policy).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None):
        serializer = PaymentSerializer(data=request.data)
        if serializer.is_valid():
            policy = self.repo.update(pk, **serializer.validated_data)
            if not policy:
                return Response({"error": "Policy not found"}, status=status.HTTP_404_NOT_FOUND)
            return Response(PaymentSerializer(policy).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        deleted = self.repo.delete(pk)
        if deleted:
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({"error": "Policy not found"}, status=status.HTTP_404_NOT_FOUND)