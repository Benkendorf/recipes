import logging

from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Favorites, Ingredient, Recipe, RecipeIngredient, RecipeTag, ShoppingCart, Tag
from users.serializers import Base64ImageField, UserSerializer

User = get_user_model()


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = Tag


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        fields = '__all__'
        model = Ingredient


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all()
    )
    amount = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    author = UserSerializer()
    tags = TagSerializer(many=True)
    ingredients = IngredientSerializer(many=True)
    image = Base64ImageField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        fields = '__all__'
        model = Recipe

    def get_is_favorited(self, obj):
        return Favorites.objects.filter(
            recipe=obj,
            list_owner=self.context['request'].user
        ).exists()

    def get_is_in_shopping_cart(self, obj):
        return ShoppingCart.objects.filter(
            recipe=obj,
            cart_owner=self.context['request'].user
        ).exists()


class RecipeCreateSerializer(serializers.ModelSerializer):
    author = UserSerializer(
        required=False
    )
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all()
    )
    ingredients = RecipeIngredientSerializer(many=True)
    image = Base64ImageField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        fields = '__all__'
        model = Recipe

    def get_is_favorited(self, obj):
        return Favorites.objects.filter(
            recipe=obj,
            list_owner=self.context['request'].user
        ).exists()

    def get_is_in_shopping_cart(self, obj):
        return ShoppingCart.objects.filter(
            recipe=obj,
            cart_owner=self.context['request'].user
        ).exists()

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients_data = validated_data.pop('ingredients')

        recipe = Recipe.objects.create(**validated_data)

        for tag in tags:
            RecipeTag.objects.create(tag=tag, recipe=recipe)

        logging.critical(f'INGREDIENTS_DATA: {ingredients_data}')

        for ingredient_data in ingredients_data:
            logging.critical(f'CURRENT INGREDIENT_DATA: {ingredient_data}')
            ingredient = ingredient_data['id']
            logging.critical(f'CURRENT INGREDIENT: {ingredient}')
            amount = ingredient_data['amount']
            logging.critical(f'CURRENT AMOUNT: {amount}')
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient=ingredient,
                amount=amount
            )
            logging.critical('RECIPE_INGREDIENT_CREATE DONE')

        return recipe

    """
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if self.context['request'].method == 'GET':
            ingredients = representation.get('ingredients', [])
            for ingredient in ingredients:
                ingredient['amount'] = RecipeIngredient.objects.get(
                    recipe=instance, ingredient=ingredient['id']).amount
        return representation
    """
