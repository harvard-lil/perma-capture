from django.conf import settings
from django.contrib.auth import views as auth_views
from django.urls import path, include
from django.views.generic import TemplateView

from .test.test_permissions_helpers import no_perms_test
from . import views, forms


urlpatterns = [
    path('', views.index, name='index'),

    path(f'{settings.API_PREFIX}/captures', views.CaptureListView.as_view(), name='captures'),
    path(f'{settings.API_PREFIX}/capture/<slug:jobid>', views.CaptureDetailView.as_view(), name='delete_capture'),
    path('webhooks/', views.WebhookSubscriptionListView.as_view(), name='webhooks'),
    path('webhooks/<int:pk>', views.WebhookSubscriptionDetailView.as_view(), name='webhook'),
    path('callbacks/archived/', views.archived_callback, name='archived_callback'),
    path('replay/sw.js', views.render_sw, name='sw'),
    path('replay/', views.replay_error, name='replay_error'),

    path('sign-up/', views.sign_up, name='sign_up'),

    path('docs/', no_perms_test(TemplateView.as_view(template_name='main/docs.html')), name='docs'),

    ### user account pages ###
    path('user/account/', views.account, name='account'),
    path('user/token_reset/', views.reset_token, name='token_reset'),
    # built-in Django auth views, with overrides to replace the form or tweak behavior in some views
    path('user/password_reset/', no_perms_test(views.reset_password), name='password_reset'),
    path('user/reset/<uidb64>/<token>/', no_perms_test(auth_views.PasswordResetConfirmView.as_view(form_class=forms.SetPasswordForm)), name='password_reset_confirm'),
    path('user/', include('django.contrib.auth.urls')),

    ### internal pages ###
    path('manage/celery/', views.celery_queue_status, name='celery_queue_status'),
]

if settings.EXPOSE_WEBHOOK_TEST_ROUTE:
    urlpatterns += [
        path('manage/webhook-test/<int:user_id>/<event>/', views.webhooks_test, name='webhooks_test'),
    ]

# debugging routes to see error pages
# for example, http://localhost:8000/404 triggers an actual 404
# and http://localhost:8000/404.html shows the 404 template
if settings.DEBUG or settings.TESTING:
    from .test import views as test_views
    urlpatterns += [
        path(error_page, TemplateView.as_view(template_name=error_page), name=error_page)
        for error_page in ('400.html', '403.html', '403_csrf.html', '404.html', '500.html')
    ]
    urlpatterns += [
        path(error_page, no_perms_test(getattr(test_views, f"raise_{error_page}")), name=error_page)
        for error_page in ('400', '403', '403_csrf', '404', '500')
    ]
