from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from djoser.views import UserViewSet

from .models import CustomUser
from .serializers import AvatarSerializer, CustomUserCreateSerializer, UserSerializer


class CustomUserViewSet(UserViewSet):
    queryset = CustomUser.objects.all().order_by('username')
    serializer_class = UserSerializer

    @action(detail=False, methods=['put', 'delete'], permission_classes=[IsAuthenticated,])
    def avatar(self, request):
        #self.get_object = self.get_instance
        user = self.get_instance()
        serializer = AvatarSerializer(data=request.data)
        if request.method == 'PUT':
            if serializer.is_valid():
                user.avatar = serializer.validated_data['avatar']
                user.save()
                #serializer.save()
                response_serializer = AvatarSerializer(
                    data={'avatar': user.avatar}
                )
                response_serializer.is_valid()
                return Response(response_serializer.data)
            else:
                return Response(serializer.errors,
                                status=status.HTTP_400_BAD_REQUEST)
        else:
            user.avatar.delete()
            user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
