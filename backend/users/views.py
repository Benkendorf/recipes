from rest_framework import filters, mixins, viewsets

from djoser.views import UserViewSet

from .models import CustomUser
from .serializers import CustomUserCreateSerializer

#class CustomUserCreateViewset(UserViewSet):




"""
class UserViewset(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all().order_by('username')
    serializer_class = UserSerializer
"""
