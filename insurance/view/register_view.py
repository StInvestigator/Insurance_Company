from ..serializers import (
    RegisterSerializer
)
from ..repository.unit_of_work import UnitOfWork
from rest_framework import generics, permissions

class RegisterView(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer




