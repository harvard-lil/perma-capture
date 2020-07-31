from django.contrib.auth import views as auth_views
from django.urls import path, include

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
