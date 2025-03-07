from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Favorites, Ingredient, Recipe, ShoppingCart, Tag
from users.serializers import UserSerializer

User = get_user_model()


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = Tag


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = Ingredient


class RecipeSerializer(serializers.ModelSerializer):
    author = UserSerializer()
    tags = TagSerializer(many=True)
    ingredients = IngredientSerializer(many=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        fields = '__all__'
        model = Recipe

    def get_is_favorited(self, obj):
        return Favorites.objects.get(
            recipe=obj,
            list_owner=self.context['request'].user
        ).exists()

    def get_is_in_shopping_cart(self, obj):
        return ShoppingCart.objects.get(
            recipe=obj,
            cart_owner=self.context['request'].user
        ).exists()
