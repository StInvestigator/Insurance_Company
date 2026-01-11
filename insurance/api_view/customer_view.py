from rest_framework import viewsets, permissions
from insurance.model.customer import Customer
from ..serializers import (
    CustomerSerializer
)
from rest_framework.decorators import action
from drf_yasg.utils import swagger_auto_schema
from ..repository.unit_of_work import UnitOfWork
from rest_framework.response import Response
from drf_yasg import openapi
from rest_framework import status


class CustomerView(viewsets.ModelViewSet):
    # permission_classes = [permissions.AllowAny]
    serializer_class = CustomerSerializer
    with UnitOfWork() as repo:
        queryset = repo.customers.get_all()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def list(self, request, *args, **kwargs):
        page = int(request.query_params.get('page', 1) or 1)
        page_size = int(request.query_params.get('page_size', 10) or 10)
        if page < 1:
            page = 1
        if page_size < 1:
            page_size = 10
        with UnitOfWork() as repo:
            qs = repo.customers.get_all()
            total = qs.count()
            start = (page - 1) * page_size
            end = start + page_size
            items = list(qs.order_by('id')[start:end])
            serializer = self.serializer_class(items, many=True)
            total_pages = (total + page_size - 1) // page_size if page_size else 1
            return Response({
                'items': serializer.data,
                'total': total,
                'page': page,
                'page_size': page_size,
                'total_pages': total_pages,
            })

    def retrieve(self, request, pk=None, *args, **kwargs):
        with UnitOfWork() as repo:
            policy = repo.customers.get_by_id(pk)
            if not policy:
                return Response({"error": "Policy not found"}, status=status.HTTP_404_NOT_FOUND)
            serializer = self.serializer_class(policy)
            return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            with UnitOfWork() as repo:
                policy = repo.customers.create(**serializer.validated_data)
                return Response(self.serializer_class(policy).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        with UnitOfWork() as repo:
            instance = repo.customers.get_by_id(pk)
            if not instance:
                return Response({"error": "Policy not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.serializer_class(instance, data=request.data, partial=partial)
        if serializer.is_valid():
            with UnitOfWork() as repo:
                updated = repo.customers.update(pk, **serializer.validated_data)
            return Response(self.serializer_class(updated).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, pk=None, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, pk, *args, **kwargs)

    def destroy(self, request, pk=None, *args, **kwargs):
        with UnitOfWork() as repo:
            deleted = repo.customers.delete(pk)
        if deleted:
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({"error": "Policy not found"}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['get'])
    def find_by_tax_number(self, request):
        tax_number = request.query_params.get('tax_number')
        if not tax_number:
            return Response({"error": "Missing tax_number"}, status=status.HTTP_400_BAD_REQUEST)
        with UnitOfWork() as repo:
            customer = repo.customers.find_by_tax_number(tax_number)
            serializer = self.serializer_class(customer)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[permissions.AllowAny])
    def count(self, request):
        with UnitOfWork() as repo:
            return Response({"count": repo.customers.count()})
