from django.conf import settings
from django.contrib.auth import views as auth_views
from django.urls import path, include
from django.views.generic import TemplateView

from .test.test_permissions_helpers import no_perms_test
from . import views, forms


urlpatterns = [
    path('', views.index, name='index'),

    path('sign-up/', views.sign_up, name='sign_up'),

    ### user account pages ###
    path('user/account', views.account, name='account'),
    path('user/token_reset', views.reset_token, name='token_reset'),
    # built-in Django auth views, with overrides to replace the form or tweak behavior in some views
    path('user/password_reset/', no_perms_test(views.reset_password), name='password_reset'),
    path('user/reset/<uidb64>/<token>/', no_perms_test(auth_views.PasswordResetConfirmView.as_view(form_class=forms.SetPasswordForm)), name='password_reset_confirm'),
    path('user/', include('django.contrib.auth.urls')),
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
