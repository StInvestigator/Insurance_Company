from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from insurance.model.payment import Payment
from ..serializers import (
    PaymentSerializer,
)
from ..repository.unit_of_work import UnitOfWork
from rest_framework import permissions


class PaymentView(viewsets.ModelViewSet):
    # permission_classes = [permissions.AllowAny]
    with UnitOfWork() as repo:
        queryset = repo.payments.get_all()
    serializer_class = PaymentSerializer

    def list(self, request, *args, **kwargs):
        page = int(request.query_params.get('page', 1) or 1)
        page_size = int(request.query_params.get('page_size', 10) or 10)
        if page < 1:
            page = 1
        if page_size < 1:
            page_size = 10
        with UnitOfWork() as repo:
            qs = repo.payments.get_all()
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

    @action(detail=False, methods=['get'], permission_classes=[permissions.AllowAny])
    def count(self, request):
        with UnitOfWork() as repo:
            return Response({"count": repo.payments.count()})