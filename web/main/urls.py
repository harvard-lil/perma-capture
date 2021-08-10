from django.conf import settings
from django.contrib.auth import views as auth_views
from django.urls import path, re_path
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.generic import TemplateView

from .test.test_permissions_helpers import no_perms_test
from . import views, forms
from .utils import auth_view_json_response


urlpatterns = [
    path('', views.index, name='index'),

    path('captures/', views.CaptureListView.as_view(), name='captures'),
    path('captures/<int:pk>', views.CaptureDetailView.as_view(), name='capture'),
    path('webhooks/', views.WebhookSubscriptionListView.as_view(), name='webhooks'),
    path('webhooks/<int:pk>', views.WebhookSubscriptionDetailView.as_view(), name='webhook'),
    path('replay/sw.js', views.render_sw, name='sw'),
    path('replay/', views.replay_error, name='replay_error'),

    path('sign-up/', views.sign_up, name='sign_up'),

    path('docs/', views.docs, name='docs'),

    ### user account pages ###
    path('user/account/', views.account, name='account'),
    path('user/token_reset/', views.reset_token, name='token_reset'),
    # built-in Django auth views, wrapped to return JSON, with overrides to replace the form or tweak behavior in some views
    *[path(f'user/{view[0]}/', no_perms_test(auth_view_json_response(view[1])), name=f'{view[2]}')
        for view in [
            ('login',ensure_csrf_cookie(auth_views.LoginView.as_view()), 'login'),
            ('logout', auth_views.LogoutView.as_view(), 'logout'),
            ('password_change', auth_views.PasswordChangeView.as_view(), 'password_change'),
            ('password_change/done', auth_views.PasswordChangeDoneView.as_view(), 'password_change_done'),
            ('password_reset', views.reset_password, 'password_reset'),
            ('password_reset/done', auth_views.PasswordResetDoneView.as_view(), 'password_reset_done'),
            ('reset/<uidb64>/<token>', auth_views.PasswordResetConfirmView.as_view(form_class=forms.SetPasswordForm), 'password_reset_confirm'),
            ('reset/done', auth_views.PasswordResetCompleteView.as_view(), 'password_reset_complete')
        ]
    ],

    ### internal pages ###
    path('manage/celery/', views.celery_queue_status, name='celery_queue_status'),
]

if settings.EXPOSE_WEBHOOK_TEST_ROUTE:
    urlpatterns += [
        path('manage/webhook-test/', views.webhook_test, name='webhook_test'),
    ]

# debugging routes to see error pages
# for example, http://localhost:8000/404 triggers an actual 404
# and http://localhost:8000/404.html shows the 404 template
if settings.DEBUG or settings.TESTING:
    from .vite_proxy import ViteProxy
    urlpatterns += [
        re_path(r'^(?P<url>vite/.*)$', ViteProxy.as_view(), name='vite_proxy')
    ]

    from .test import views as test_views
    urlpatterns += [
        path(error_page, TemplateView.as_view(template_name=error_page), name=error_page)
        for error_page in ('400.html', '403.html', '403_csrf.html', '404.html', '500.html')
    ]
    urlpatterns += [
        path(error_page, no_perms_test(getattr(test_views, f"raise_{error_page}")), name=error_page)
        for error_page in ('400', '403', '403_csrf', '404', '500')
    ]
