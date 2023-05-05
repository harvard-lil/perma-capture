from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Group
from django.urls import reverse
from django.utils.html import format_html

from .models import User, WebhookSubscription, CaptureJob, Archive

#
# Filters
#

class InputFilter(admin.SimpleListFilter):
    """
    Text input filter, from:
    https://hakibenita.com/how-to-add-a-text-filter-to-django-admin
    """
    template = 'admin/input_filter.html'

    def lookups(self, request, model_admin):
        # Dummy, required to show the filter.
        return ((),)

    def choices(self, changelist):
        # Grab only the "all" option.
        all_choice = next(super().choices(changelist))
        all_choice['query_parts'] = (
            (k, v)
            for k, v in changelist.get_filters_params().items()
            if k != self.parameter_name
        )
        yield all_choice


class UserEmailFilter(InputFilter):
    parameter_name = 'user_email'
    title = 'user (email)'

    def queryset(self, request, queryset):
        value = self.value()
        if value is not None:
            return queryset.filter(user__email__icontains=value)


class UserIDFilter(InputFilter):
    parameter_name = 'user_id'
    title = 'user (ID)'

    def queryset(self, request, queryset):
        value = self.value()
        if value is not None:
            return queryset.filter(user_id=value)


class RequestedURLFilter(InputFilter):
    parameter_name = 'requested_url'
    title = 'Requested URL'

    def queryset(self, request, queryset):
        value = self.value()
        if value is not None:
            return queryset.filter(requested_url__icontains=value)


class MessageFilter(InputFilter):
    parameter_name = 'message'
    title = 'message'

    def queryset(self, request, queryset):
        value = self.value()
        if value is not None:
            return queryset.filter(message__icontains=value)


class CaptureJobUserEmailFilter(InputFilter):
    parameter_name = 'user_email'
    title = 'user (email)'

    def queryset(self, request, queryset):
        value = self.value()
        if value is not None:
            return queryset.filter(capture_job__user__email__icontains=value)


class CaptureJobUserIDFilter(InputFilter):
    parameter_name = 'user_id'
    title = 'user (ID)'

    def queryset(self, request, queryset):
        value = self.value()
        if value is not None:
            return queryset.filter(capture_job__user_id=value)


class ArchiveDownloadableFilter(admin.SimpleListFilter):
    parameter_name = 'downloadable'
    title = 'downloadable'

    def lookups(self, request, model_admin):
        return (
            (None, 'All'),
            ('1', 'Yes'),
            ('0', 'No')
        )

    def choices(self, changelist):
        for lookup, title in self.lookup_choices:
            yield {
                'selected': self.value() == (str(lookup) if lookup else lookup),
                'query_string': changelist.get_query_string({self.parameter_name: lookup}, []),
                'display': title,
            }

    def queryset(self, request, queryset):
        value = self.value()
        if value is None:
            return queryset
        elif int(value):
            return queryset.filter(download_url__isnull=False)
        return queryset.filter(download_url__isnull=True)


#
# Forms
#

class UserAddForm(UserCreationForm):
    username = None

    class Meta:
        model = User
        fields = ('email',)

    def clean_username(self):
        return self.cleaned_data['username']


#
# Inlines
#

class ArchiveInline(admin.StackedInline):
    model = Archive
    fields = readonly_fields = ('hash', 'hash_algorithm', 'warc_size', 'download_expiration_timestamp', 'download_url', 'created_at', 'updated_at')
    can_delete = False


#
# Admins
#

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


@admin.register(CaptureJob)
class CaptureJobAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user_link',
        'requested_url',
        'headless',
        'label',
        'status',
        'message',
        'human',
        'created_at',
        'updated_at',
        'queue_time',
        'capture_time'
    )
    list_filter = [UserEmailFilter, UserIDFilter, RequestedURLFilter, 'status', 'headless', 'human']
    fieldsets = (
        (None, {'fields': ('user_link', 'requested_url', 'headless', 'human', 'label')}),
        ('Progress', {'fields': ( 'status', 'message', 'order', 'step_count', 'step_description', 'created_at', 'updated_at', 'capture_start_time', 'capture_end_time')})
    )
    readonly_fields = ('user_link', 'requested_url', 'headless', 'human', 'label', 'status', 'message', 'order', 'step_count', 'step_description', 'created_at', 'updated_at', 'capture_start_time', 'capture_end_time')
    inlines = [ArchiveInline]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')

    def user_link(self, obj):
        url = reverse('admin:main_user_change', args=(obj.user.pk,))
        return format_html('<a href="{}">{}</a>', url, obj.user.email)
    user_link.short_description = 'user'


@admin.register(Archive)
class ArchiveAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user_link',
        'hash_algorithm',
        'warc_size',
        'download_expiration_timestamp',
        'download_url',
        'created_at',
        'updated_at'
    )
    list_filter = [ArchiveDownloadableFilter, CaptureJobUserEmailFilter, CaptureJobUserIDFilter]
    fields = readonly_fields = ('capture_job_link', 'user_link', 'hash', 'hash_algorithm', 'warc_size', 'download_url', 'download_expiration_timestamp', 'created_at', 'updated_at')

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('capture_job__user')

    def user_link(self, obj):
        url = reverse('admin:main_user_change', args=(obj.capture_job.user.pk,))
        return format_html('<a href="{}">{}</a>', url, obj.capture_job.user.email)
    user_link.short_description = 'user'

    def capture_job_link(self, obj):
        url = reverse('admin:main_capturejob_change', args=(obj.capture_job_id,))
        return format_html('<a href="{}">{}</a>', url, obj.capture_job_id)
    capture_job_link.short_description = 'capture job'


admin.site.unregister(Group)
admin.site.site_header = "Perma Capture"
