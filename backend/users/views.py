import logging

from django.db.models import Count

from djoser.views import UserViewSet
from recipes.serializers import SubscriptionSerializer
from users.serializers import SubscriptionCreateSerializer
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import UserModel, Subscription
from .serializers import AvatarSerializer, UserSerializer


class UserModelViewSet(UserViewSet):
    queryset = UserModel.objects.all().order_by('username')
    serializer_class = UserSerializer
    permission_classes = [AllowAny, ]

    @action(detail=False, methods=['put', 'delete'],
            permission_classes=[IsAuthenticated, ])
    def avatar(self, request):
        user = self.get_instance()
        serializer = AvatarSerializer(data=request.data)
        if request.method == 'PUT':
            serializer.is_valid(raise_exception=True)

            user.avatar = serializer.validated_data['avatar']
            user.save()
            response_serializer = AvatarSerializer(
                data={'avatar': user.avatar}
            )
            response_serializer.is_valid()

            return Response(response_serializer.data)

        user.avatar.delete()
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get', 'head'],
            permission_classes=[IsAuthenticated, ],
            pagination_class=PageNumberPagination)
    def subscription_get(self, request):

        if request.method == 'GET':
            subs = UserModel.objects.filter(
                follows__subscriber=request.user
            ).distinct().order_by('username').annotate(
                recipes_count=Count('recipes'))

            paginator = self.pagination_class()
            page = paginator.paginate_queryset(subs, request)

            serializer = SubscriptionSerializer(
                instance=page,
                many=True,
                context={'request': request}
            )

            return paginator.get_paginated_response(serializer.data)

    @action(detail=False, methods=['post', 'head', 'delete'],
            permission_classes=[IsAuthenticated, ],
            pagination_class=PageNumberPagination)
    def subscription_post_delete(self, request, pk):

        if request.method == 'POST':
            if self.request.user.pk == pk or Subscription.objects.filter(
                subscriber=self.request.user,
                subscribed_to=UserModel.objects.get(pk=pk)
            ).exists():
                return Response(
                    status=status.HTTP_400_BAD_REQUEST
                )
            else:
                serializer = SubscriptionCreateSerializer(
                    data={'subscriber': self.request.user.pk,
                          'subscribed_to': pk}
                )
                serializer.is_valid()
                logging.debug(serializer.errors)
                serializer.save()

                serializer_to_return = SubscriptionSerializer(
                    instance=UserModel.objects.get(pk=pk),
                    context={'request': request}
                )

                return Response(
                    serializer_to_return.data,
                    status=status.HTTP_201_CREATED
                )

        elif request.method == 'DELETE':
            if not Subscription.objects.filter(
                subscriber=self.request.user,
                subscribed_to=UserModel.objects.get(pk=pk)
            ).delete():
                return Response(
                    status=status.HTTP_400_BAD_REQUEST
                )
            else:
                return Response(
                    status=status.HTTP_204_NO_CONTENT
                )
