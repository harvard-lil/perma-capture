from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Group

from .models import User, WebhookSubscription, Archive


class UserAddForm(UserCreationForm):
    username = None

    class Meta:
        model = User
        fields = ('email',)

    def clean_username(self):
        return self.cleaned_data['username']


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    add_form = UserAddForm
    model = User

    ordering = ('-created_at',)
    search_fields = ('email', 'last_name', 'first_name')
    readonly_fields = (
        'created_at',
        'updated_at',
        'last_login'
    )
    list_display = (
        'id',
        'email',
        'first_name',
        'last_name',
        'is_active',
        'is_staff',
        'created_at',
        'updated_at',
        'last_login'
    )
    list_filter = ('email', 'is_staff', 'is_active',)
    fieldsets = (
        (None, {'fields': ('email', 'password', 'created_at', 'updated_at')}),
        ('Account Type', {'fields': ('is_staff', 'is_superuser')}),
        ('Account Status', {'fields': (
            'is_active',
            'email_confirmed'
        )}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('first_name', 'last_name', 'email', 'password1', 'password2')}
        ),
    )


@admin.register(WebhookSubscription)
class WebhookSubscriptionAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'event_type',
        'callback_url',
        'signing_key_algorithm',
        'created_at',
        'updated_at'
    )

    readonly_fields = (
        'created_at',
        'updated_at',
        'signing_key',
        'signing_key_algorithm',
    )


@admin.register(Archive)
class ArchiveAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'user_id',
        'hash_algorithm',
        'created_at',
        'updated_at'
    )

    readonly_fields = (
        'created_at',
        'updated_at',
        'jobid',
        'hash',
        'hash_algorithm',
    )

admin.site.unregister(Group)
