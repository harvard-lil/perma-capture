from django.contrib.auth.backends import ModelBackend

from rest_framework.test import APIClient, APIRequestFactory
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed

from pytest import raises as assert_raises


class ConfirmedUserSessionBackend(ModelBackend):

    def user_can_authenticate(self, user):
        """
        Don't let users log in if they haven't confirmed their email,
        even if they somehow end up with a password due to an irregularity.

        This user can log in:
        >>> user = getfixture('user')
        >>> client = APIClient()
        >>> assert client.login(username=user.email, password='pass')
        >>> client.logout()

        We'll artificially toggle `email_confirmed` to False.
        >>> user.email_confirmed = False
        >>> user.save()

        Now... they can't.
        >>> assert not client.login(username=user.email, password='pass')
        """
        return super().user_can_authenticate(user) and user.email_confirmed


class ConfirmedUserTokenBackend(TokenAuthentication):

    def authenticate(self, request):
        """
        Don't accept the API keys of users who haven't confirmed their email,
        even if they somehow end up with one due to an irregularity.

        Given:
        >>> from rest_framework.views import APIView
        >>> authenticator = APIView().get_authenticators()[0]
        >>> assert isinstance(authenticator, ConfirmedUserTokenBackend)
        >>> user = getfixture('user')

        This user can use their API key:
        >>> request = APIRequestFactory().get('/some-route/', HTTP_AUTHORIZATION=f'Token {user.auth_token.key}')
        >>> assert authenticator.authenticate(request)

        We'll artificially toggle `email_confirmed` to False.
        >>> user.email_confirmed = False
        >>> user.save()

        Now... they can't.
        >>> with assert_raises(AuthenticationFailed,  match='User inactive or deleted.'):
        ...     authenticator.authenticate(request)
        """
        user_auth_tuple = super().authenticate(request)
        if user_auth_tuple:
            (user, token) = user_auth_tuple
            if not user.email_confirmed:
                raise AuthenticationFailed('User inactive or deleted.')
            return user_auth_tuple

