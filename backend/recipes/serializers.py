import logging

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser

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
    ingredients = RecipeIngredientSerializer(many=True, source='recipe_ingredients')
    image = Base64ImageField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        fields = '__all__'
        model = Recipe

    def get_is_favorited(self, obj):
        if isinstance(self.context['request'].user, AnonymousUser):
            return False
        return Favorites.objects.filter(
            recipe=obj,
            list_owner=self.context['request'].user
        ).exists()

    def get_is_in_shopping_cart(self, obj):
        if isinstance(self.context['request'].user, AnonymousUser):
            return False
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
    ingredients = RecipeIngredientCreateSerializer(many=True)
    image = Base64ImageField()

    class Meta:
        fields = '__all__'
        model = Recipe
    """
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
    """
    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients_data = validated_data.pop('ingredients')

        recipe = Recipe.objects.create(**validated_data)

        for tag in tags:
            RecipeTag.objects.create(tag=tag, recipe=recipe)

        for ingredient_data in ingredients_data:
            ingredient = ingredient_data['ingredient']
            amount = ingredient_data['amount']
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient=ingredient,
                amount=amount
            )

        return recipe

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get('cooking_time',
                                                   instance.cooking_time)
        instance.image = validated_data.get('image', instance.image)

        tags = validated_data.pop('tags')
        ingredients_data = validated_data.pop('ingredients')

        current_tags = RecipeTag.objects.filter(
            recipe=instance
        )
        for tag in current_tags:
            tag.delete()

        current_ingredients = RecipeIngredient.objects.filter(
            recipe=instance
        )
        for ingredient in current_ingredients:
            ingredient.delete()

        for tag in tags:
            RecipeTag.objects.create(tag=tag, recipe=instance)

        for ingredient_data in ingredients_data:
            ingredient = ingredient_data['ingredient']
            amount = ingredient_data['amount']
            RecipeIngredient.objects.create(
                recipe=instance,
                ingredient=ingredient,
                amount=amount
            )

        instance.save()
        return instance

    def to_representation(self, instance):
        return RecipeSerializer(instance, context=self.context).data


class ShortRecipeSerializer(serializers.ModelSerializer):

    class Meta:
        fields = ('id', 'name', 'image', 'cooking_time')
        model = Recipe


class SubscriptionSerializer(UserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        fields = ('email', 'id', 'username', 'first_name', 'last_name', 'is_subscribed', 'avatar', 'recipes', 'recipes_count')
        model = User

    def get_recipes(self, obj):
        recipes_limit = int(self.context['request'].query_params.get('recipes_limit', '-1'))
        recipes_to_serialize = []
        if recipes_limit == -1:
            recipes_to_serialize = Recipe.objects.filter(
                author=obj
            )
        else:
            recipes_to_serialize = Recipe.objects.filter(
                author=obj
            )[:recipes_limit]

        return ShortRecipeSerializer(
            recipes_to_serialize,
            many=True,
            required=False,
        ).data

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(
            author=obj
        ).count()
