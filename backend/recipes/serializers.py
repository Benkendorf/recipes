import logging

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from rest_framework import serializers
from users.serializers import Base64ImageField, UserSerializer

from .models import (Favorites, Ingredient, Recipe, RecipeIngredient,
                     ShoppingCart, Tag)

from .constants import COOKING_TIME_MIN_VALUE

User = get_user_model()


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = Tag


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        fields = '__all__'
        model = Ingredient


class RecipeIngredientSerializer(serializers. ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.CharField(source='ingredient.name')
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit')

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeIngredientCreateSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='ingredient'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    author = UserSerializer()
    tags = TagSerializer(many=True)
    ingredients = RecipeIngredientSerializer(
        many=True,
        source='recipe_ingredients'
    )
    image = Base64ImageField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        fields = '__all__'
        model = Recipe

    def get_is_favorited(self, obj):
        if isinstance(self.context['request'].user, AnonymousUser):
            return False
        return self.context['request'].user.favorites.filter(
            recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        if isinstance(self.context['request'].user, AnonymousUser):
            return False
        return self.context['request'].user.shoppingcart.filter(
            recipe=obj).exists()


class RecipeCreateSerializer(serializers.ModelSerializer):
    author = UserSerializer(
        required=False
    )
    tags = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all()
    )
    ingredients = RecipeIngredientCreateSerializer(many=True)
    image = Base64ImageField()
    cooking_time = serializers.IntegerField(min_value=COOKING_TIME_MIN_VALUE)

    class Meta:
        fields = '__all__'
        model = Recipe

    def create(self, validated_data):
        try:
            tags = validated_data.pop('tags')
        except KeyError:
            raise serializers.ValidationError({'tags': 'Обязательное поле.'})

        try:
            ingredients_data = validated_data.pop('ingredients')
        except KeyError:
            raise serializers.ValidationError({'ingredients':
                                               'Обязательное поле.'})

        if len(tags) != len(set(tags)):
            raise serializers.ValidationError('Тэги должны быть уникальны.')

        just_ings = [dic['ingredient'] for dic in ingredients_data]
        if len(just_ings) != len(set(just_ings)):
            raise serializers.ValidationError('Ингредиенты'
                                              ' должны быть уникальны.')

        recipe = Recipe.objects.create(**validated_data)

        recipe.tags.set(tags)

        self.recipe_ing_bulk_create(ingredients_data, recipe)

        return recipe

    def update(self, instance, validated_data):
        try:
            tags = validated_data.pop('tags')
        except KeyError:
            raise serializers.ValidationError({'tags': 'Обязательное поле.'})

        try:
            ingredients_data = validated_data.pop('ingredients')
        except KeyError:
            raise serializers.ValidationError({'ingredients':
                                               'Обязательное поле.'})

        super().update(instance, validated_data)

        instance.tags.set(tags)

        instance.ingredients.clear()
        self.recipe_ing_bulk_create(ingredients_data, instance)

        instance.save()
        return instance

    def to_representation(self, instance):
        return RecipeSerializer(instance, context=self.context).data

    def recipe_ing_bulk_create(self, ingredients_data, recipe):
        RecipeIngredient.objects.bulk_create(
            [RecipeIngredient(ingredient=ing_data['ingredient'],
                              amount=ing_data['amount'],
                              recipe=recipe)
                for ing_data in ingredients_data]
        )


class ShortRecipeSerializer(serializers.ModelSerializer):

    class Meta:
        fields = ('id', 'name', 'image', 'cooking_time')
        model = Recipe


class SubscriptionSerializer(UserSerializer):
    recipes = serializers.SerializerMethodField()

    class Meta:
        fields = ('email', 'id', 'username', 'first_name', 'last_name',
                  'is_subscribed', 'avatar', 'recipes')
        model = User

    def get_recipes(self, obj):
        recipes_limit = int(self.context['request'].query_params.get(
            'recipes_limit', '-1'))
        recipes_to_serialize = obj.recipes.all(
        )[:int(recipes_limit)if recipes_limit != '-1' else None]

        return ShortRecipeSerializer(
            recipes_to_serialize,
            many=True,
            required=False,
        ).data


class ShoppingCartSerializer(serializers.ModelSerializer):

    class Meta:
        fields = ('owner', 'recipe')
        model = ShoppingCart


class FavoritesSerializer(serializers.ModelSerializer):

    class Meta:
        fields = ('owner', 'recipe')
        model = Favorites
