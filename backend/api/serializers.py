import base64

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from djoser.serializers import UserCreateSerializer
from recipes.constants import COOKING_TIME_MIN_VALUE
from recipes.models import (Favorites, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from rest_framework import serializers
from users.models import Subscription

User = get_user_model()


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField(required=False)

    class Meta:
        fields = ('id', 'email', 'username', 'first_name',
                  'last_name', 'is_subscribed', 'avatar')
        model = User

    def get_is_subscribed(self, obj):

        return (self.context["request"].user.is_authenticated
                and self.context['request'].user.followers.filter(
                    subscribed_to=obj).exists())


class UserCreateSerializer(UserCreateSerializer):
    class Meta(UserCreateSerializer.Meta):
        model = User
        fields = UserCreateSerializer.Meta.fields + ('username',)


class AvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField()

    class Meta:
        fields = ('avatar',)
        model = User


class SubscriptionCreateSerializer(serializers.ModelSerializer):

    class Meta:
        fields = ('subscriber', 'subscribed_to')
        model = Subscription

    def validate(self, data):
        if data['subscriber'] == data['subscribed_to']:
            raise serializers.ValidationError('Нельзя подписаться'
                                              ' на самого себя!')
        return data


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = Tag


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        fields = '__all__'
        model = Ingredient


class RecipeIngredientSerializer(serializers. ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        source='ingredient.id', read_only=True)

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

    amount = serializers.IntegerField(min_value=1)

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
        read_only_fields = ['__all__', ]
        model = Recipe

    def get_is_favorited(self, obj):
        return (self.context["request"].user.is_authenticated
                and self.context['request'].user.favorites.filter(
                    recipe=obj).exists())

    def get_is_in_shopping_cart(self, obj):
        return (self.context["request"].user.is_authenticated
                and self.context['request'].user.shoppingcart.filter(
                    recipe=obj).exists())


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

    def validate(self, data):
        if 'tags' not in data:
            raise serializers.ValidationError({'tags': 'Обязательное поле.'})
        if 'ingredients' not in data:
            raise serializers.ValidationError({'ingredients':
                                               'Обязательное поле.'})
        if len(data['tags']) != len(set(data['tags'])):
            raise serializers.ValidationError('Тэги должны быть уникальны.')

        just_ings = [dic['ingredient'] for dic in data['ingredients']]
        if len(just_ings) != len(set(just_ings)):
            raise serializers.ValidationError('Ингредиенты'
                                              ' должны быть уникальны.')

        return data

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients_data = validated_data.pop('ingredients')

        recipe = Recipe.objects.create(**validated_data)

        recipe.tags.set(tags)

        self.recipe_ing_bulk_create(ingredients_data, recipe)

        return recipe

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags')
        ingredients_data = validated_data.pop('ingredients')

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
        )[:recipes_limit if recipes_limit != -1 else None]

        return ShortRecipeSerializer(
            recipes_to_serialize,
            many=True,
            required=False,
        ).data


class ShoppingCartSerializer(serializers.ModelSerializer):

    class Meta:
        fields = ('owner', 'recipe')
        model = ShoppingCart

    def validate(self, data):
        if ('request' in self.context
            and not self.context['request'].user.shoppingcart_recipes(
                recipe=get_object_or_404(Recipe, pk=data['pk'])).exists()):
            raise serializers.ValidationError('Нельзя добавить'
                                              ' уже добавленный рецепт!')
        return data


class FavoritesSerializer(serializers.ModelSerializer):

    class Meta:
        fields = ('owner', 'recipe')
        model = Favorites

    def validate(self, data):
        if ('request' in self.context
            and not self.context['request'].user.favorites_recipes(
                recipe=get_object_or_404(Recipe, pk=data['pk'])).exists()):
            raise serializers.ValidationError('Нельзя добавить'
                                              ' уже добавленный рецепт!')
        return data
