from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from insurance.model.claim import Claim
from ..repository.unit_of_work import UnitOfWork
from ..serializers import (
    ClaimSerializer
)


class ClaimView(viewsets.ModelViewSet):
    # permission_classes = [permissions.AllowAny]
    with UnitOfWork() as repo:
        queryset = repo.claims.get_all()
    serializer_class = ClaimSerializer

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
            qs = repo.claims.get_all()
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

    @swagger_auto_schema(
        method='get',
        manual_parameters=[
            openapi.Parameter(
                'policy_id',
                openapi.IN_QUERY,
                description="ID страхової політики для пошуку",
                type=openapi.TYPE_NUMBER,
                required=True
            )
        ]
    )
    @action(detail=False, methods=['get'])
    def find_by_policy(self, request):
        policy_id = request.query_params.get('policy_id')
        if not policy_id:
            return Response({"error": "Missing policy_id"}, status=status.HTTP_400_BAD_REQUEST)
        with UnitOfWork() as repo:
            claims = repo.claims.find_by_policy(policy_id)
            serializer = self.serializer_class(claims, many=True)
            return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def find_by_customer(self, request):
        customer_id = request.query_params.get('customer_id')
        if not customer_id:
            return Response({"error": "Missing customer_id"}, status=status.HTTP_400_BAD_REQUEST)
        page = int(request.query_params.get('page', 1) or 1)
        page_size = int(request.query_params.get('page_size', 10) or 10)
        if page < 1:
            page = 1
        if page_size < 1:
            page_size = 10
        with UnitOfWork() as repo:
            qs = repo.claims.find_by_customer(customer_id)
            # qs may be a QuerySet or list; ensure QuerySet-like slicing
            try:
                total = qs.count()
                ordered = qs.order_by('id')
            except Exception:
                ordered = list(qs)
                total = len(ordered)
            start = (page - 1) * page_size
            end = start + page_size
            items = ordered[start:end]
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
            return Response({"count": repo.claims.count()})
