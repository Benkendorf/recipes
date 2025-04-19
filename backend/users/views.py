import logging

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView

from djoser.views import UserViewSet

from .models import CustomUser, Subscription
from .serializers import AvatarSerializer, CustomUserCreateSerializer, UserSerializer

from recipes.serializers import SubscriptionSerializer


class CustomUserViewSet(UserViewSet):
    queryset = CustomUser.objects.all().order_by('username')
    serializer_class = UserSerializer
    permission_classes = [AllowAny,]

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


class SubcriptionAPIView(APIView):
    permission_classes = [IsAuthenticated,]
    http_method_names = ['get', 'post', 'head', 'delete']

    def get(self, request):
        subs = CustomUser.objects.filter(
            followers__subscriber=request.user
        ).distinct()

        logging.debug(subs)

        serializer = SubscriptionSerializer(data=subs)
        logging.debug(serializer.initial_data)
        serializer.is_valid()
        logging.debug(serializer.data)
        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    def post(self, request, pk):
        if self.request.user.pk == pk or Subscription.objects.filter(
            subscriber=self.request.user,
            subscribed_to=CustomUser.objects.get(pk=pk)
        ).exists():
            return Response(
                status=status.HTTP_400_BAD_REQUEST
            )
        else:
            new_sub = Subscription.objects.create(
                subscriber=self.request.user,
                subscribed_to=CustomUser.objects.get(pk=pk)
            )
            serializer = SubscriptionSerializer(data=new_sub)
            serializer.is_valid()
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )
