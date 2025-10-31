from rest_framework import viewsets, status
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
    with UnitOfWork() as repo:
        queryset = repo.claims.get_all()
    serializer_class = ClaimSerializer

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

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
