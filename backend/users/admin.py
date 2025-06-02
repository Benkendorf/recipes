from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .forms import EmailLoginForm
from .models import Subscription, UserModel

admin.site.login_form = EmailLoginForm


@admin.register(UserModel)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name',
                    'recipes_count', 'subscribers_count')
    search_fields = ('username', 'email', 'first_name', 'last_name')

    @admin.display(description='Количество рецептов')
    def recipes_count(self, obj):
        return obj.recipes.count()

    @admin.display(description='Количество подписчиков')
    def subscribers_count(self, obj):
        return obj.follows.count()


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('subscriber', 'subscribed_to')
