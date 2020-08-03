from django import forms
from django.conf import settings
import django.contrib.auth.forms as auth_forms

from .models import User
from .utils import send_template_email


class PasswordResetForm(auth_forms.PasswordResetForm):
    def send_mail(self, subject_template_name, email_template_name,
                  context, from_email, to_email, html_email_template_name=None):
        """
        Patch Django's method to use a RequestContext rather than a plain Context
        when rendering email text, so that the context variables we expect to be present are there.

        from https://github.com/django/django/blob/9ef4a18dbe71f538a9ef8c39111ae2f0b62eb90b/django/contrib/auth/forms.py#L258.
        """
        subject = auth_forms.loader.render_to_string(subject_template_name, context, context['request'])
        # Email subject *must not* contain newlines
        subject = ''.join(subject.splitlines())
        body = auth_forms.loader.render_to_string(email_template_name, context, context['request'])

        email_message = auth_forms.EmailMultiAlternatives(subject, body, from_email, [to_email])
        if html_email_template_name is not None:
            html_email = loader.render_to_string(html_email_template_name, context, context['request'])
            email_message.attach_alternative(html_email, 'text/html')

        email_message.send()


class SetPasswordForm(auth_forms.SetPasswordForm):
    def save(self, commit=True):
        """
        When allowing user to set their password via an email link, we may be in a new-user flow with
        email_confirmed=False, or a forgot-password flow with email_confirmed=True.
        """
        if not self.user.email_confirmed:
            self.user.email_confirmed = True
            send_template_email(
                "Welcome!",
                'email/welcome.txt',
                {},
                settings.DEFAULT_FROM_EMAIL,
                [self.user.email],
            )
        return super().save(commit)


class UserForm(forms.ModelForm):

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']


class SignupForm(UserForm):

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        # save user, and set a password so that the password_reset flow can be
        # used for email confirmation
        self.instance.set_password(User.objects.make_random_password(length=20))
        user = forms.ModelForm.save(self, True)
        user.send_confirmation_email(self.request)
        return user
