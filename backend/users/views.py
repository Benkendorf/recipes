from rest_framework import filters, mixins, viewsets

from .models import CustomUser
from .serializers import UserSerializer


class UserViewset(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all().order_by('name')
    serializer_class = UserSerializer
