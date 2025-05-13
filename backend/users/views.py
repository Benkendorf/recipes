import logging

from djoser.views import UserViewSet
from recipes.serializers import SubscriptionSerializer
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import CustomUser, Subscription
from .serializers import AvatarSerializer, UserSerializer


class CustomUserViewSet(UserViewSet):
    queryset = CustomUser.objects.all().order_by('username')
    serializer_class = UserSerializer
    permission_classes = [AllowAny, ]

    @action(detail=False, methods=['put', 'delete'],
            permission_classes=[IsAuthenticated, ])
    def avatar(self, request):
        user = self.get_instance()
        serializer = AvatarSerializer(data=request.data)
        if request.method == 'PUT':
            if serializer.is_valid():
                user.avatar = serializer.validated_data['avatar']
                user.save()
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
    permission_classes = [IsAuthenticated, ]
    pagination_class = PageNumberPagination
    http_method_names = ['get', 'post', 'head', 'delete']

    def get(self, request):
        subs = CustomUser.objects.filter(
            follows__subscriber=request.user
        ).distinct().order_by('username')

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(subs, request)

        serializer = SubscriptionSerializer(
            instance=page,
            many=True,
            context={'request': request}
        )

        return paginator.get_paginated_response(serializer.data)

    def post(self, request, pk):
        if self.request.user.pk == pk or Subscription.objects.filter(
            subscriber=self.request.user,
            subscribed_to=CustomUser.objects.get(pk=pk)
        ).exists():
            return Response(
                status=status.HTTP_400_BAD_REQUEST
            )
        else:
            Subscription.objects.create(
                subscriber=self.request.user,
                subscribed_to=CustomUser.objects.get(pk=pk)
            )
            new_subbed_to = CustomUser.objects.get(pk=pk)
            logging.debug(new_subbed_to)
            serializer = SubscriptionSerializer(
                instance=new_subbed_to,
                context={'request': request}
            )
            logging.debug(serializer.data)
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )

    def delete(self, request, pk):
        if not Subscription.objects.filter(
            subscriber=self.request.user,
            subscribed_to=CustomUser.objects.get(pk=pk)
        ).exists():
            return Response(
                status=status.HTTP_400_BAD_REQUEST
            )
        else:
            existing_cart_item = Subscription.objects.filter(
                subscriber=self.request.user,
                subscribed_to=CustomUser.objects.get(pk=pk)
            )
            existing_cart_item.delete()
            return Response(
                status=status.HTTP_204_NO_CONTENT
            )
