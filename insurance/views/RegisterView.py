from ..serializers import (
    RegisterSerializer
)

from rest_framework import generics, permissions

# Generic CRUD контролери

class RegisterView(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer




