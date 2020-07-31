from rest_framework.authtoken.models import Token

from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from .utils import send_template_email

from pytest import raises as assert_raises


#
# HELPERS
#

class EditTrackedModel(models.Model):
    """
    Provide subclasses with a has_changed() function that checks whether a field name listed in tracked_fields
    has been changed since the last time the model instance was loaded or saved.

    This is the same functionality provided by django-model-utils and django-dirtyfields, but
    those packages can be error-prone in hard-to-diagnose ways, or impose a significant performance cost:

        https://www.alextomkins.com/2016/12/the-cost-of-dirtyfields/
        https://github.com/jazzband/django-model-utils/issues/331
        https://github.com/jazzband/django-model-utils/pull/313

    This class attempts to do the same thing in a minimally magical way, by requiring child classes to list the
    fields they want to track explicitly. It depends on no Django internals, except for these assumptions:

        (a) deferred fields are populated via refresh_from_db(), and
        (b) populated field values will be added to instance.__dict__

    Originally from https://github.com/harvard-lil/h2o/commit/38f54e5dd7fd5e10d815c8ecfc27692c512729ee#diff-41fd7c2ab0e36742b4af449b181e66f7R43
    """

    class Meta:
        abstract = True

    tracked_fields = []
    original_state = {}

    # built-in methods that need to call reset_original_state() after running:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.reset_original_state()

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.reset_original_state()

    def refresh_from_db(self, *args, **kwargs):
        super().refresh_from_db(*args, **kwargs)
        self.reset_original_state()

    def reset_original_state(self):
        """
        Update original_state with the current value of each field name in tracked_fields.
        Checking k in self.__dict__ means that deferred fields will be omitted entirely,
        rather than fetched.
        """
        self.original_state = {k: getattr(self, k) for k in self.tracked_fields if k in self.__dict__}

    def has_changed(self, field_name):
        """
        Return True if the field with the given name has changed locally. Will return True for all fields of a new
        unsaved instance, and True for deferred fields whether or not they happen to match the database value.

        >>> db, assert_num_queries = [getfixture(f) for f in ['db', 'assert_num_queries']]
        >>> u = User(is_active=True)
        >>> assert u.has_changed('is_active')             # new model: has_changed == True
        >>> u.save()
        >>> assert not u.has_changed('is_active')         # saved: has_changed == False
        >>> u.is_active = False
        >>> assert u.has_changed('is_active')             # changing the saved value: has_changed == True
        >>> u.refresh_from_db()
        >>> assert not u.has_changed('is_active')         # refresh from db: has_changed == False
        >>> u2 = User.objects.get(pk=u.pk)
        >>> assert not u2.has_changed('is_active')        # load new copy from db: has_changed == False
        >>> u2 = User.objects.defer('is_active').get(pk=u.pk)
        >>> with assert_num_queries():
        ...     assert not u2.has_changed('is_active')    # load new copy with deferred field: has_changed == False
        >>> u2.is_active = False
        >>> assert u2.has_changed('is_active')            # assign to deferred field: has_changed == True (may not be correct!)
        """
        if field_name not in self.tracked_fields:  # pragma: no cover
            raise ValueError("%s is not in tracked_fields" % field_name)
        if not self.pk:
            # if model hasn't been saved yet, report all fields as changed
            return True
        if field_name not in self.__dict__:
            # if the field was deferred and hasn't been assigned to locally, report as not changed
            return False
        if field_name not in self.original_state:
            # if the field was deferred and has been assigned to locally, report as changed
            # (which won't be correct if it happens to be assigned the same value as in the db)
            return True
        return self.original_state[field_name] != getattr(self, field_name)


class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


#
# MODELS
#

class UserManager(BaseUserManager):
    """
    Custom manager where email is the unique identifier for authentication instead of username.
    """

    def create_user(self, email, password, **kwargs):
        """
        Given:
        >>> db = getfixture('db')
        >>> email = 'regular_user@EXAMPLE.com'
        >>> password = 'foo'
        >>> user = User.objects.create_user(email=email, password=password)

        Users don't have a 'username' field.
        >>> with assert_raises(AttributeError, match="'User' object has no attribute 'username'"):
        ...    user.username

        Rather, email and password are both required:
        >>> with assert_raises(TypeError, match="missing 2 required positional arguments: 'email' and 'password'"):
        ...    User.objects.create_user()
        >>> with assert_raises(TypeError, match="missing 1 required positional argument: 'password'"):
        ...    User.objects.create_user(email='')
        >>> with assert_raises(ValueError, match='Email address is required'):
        ...    User.objects.create_user(email='', password=password)

        Users' emails are normalized on saving.
        >>> assert user.email != email and user.email == email.lower()

        Standard users are active, need to confirm their email address, and have no special privileges.
        >>> assert user.is_active
        >>> assert not user.email_confirmed
        >>> assert not user.is_staff
        >>> assert not user.is_superuser
        """

        if not email:
            raise ValueError('Email address is required')

        user = self.model(email=self.normalize_email(email), **kwargs)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **kwargs):
        """
        Given:
        >>> db = getfixture('db')
        >>> email = 'super_user@example.com'
        >>> password = 'foo'
        >>> super_user = User.objects.create_superuser(email=email, password=password)

        Superusers are active and confirmed, and are awarded staff and superuser privileges.
        >>> assert super_user.is_active
        >>> assert super_user.email_confirmed
        >>> assert super_user.is_staff
        >>> assert super_user.is_superuser

        You can't manually set is_staff or is_superuser False:
        >>> with assert_raises(ValueError, match='Superuser must have is_superuser=True.'):
        ...     User.objects.create_superuser(email=email, password=password, is_superuser=False)
        >>> with assert_raises(ValueError, match='Superuser must have is_staff=True.'):
        ...     User.objects.create_superuser(email=email, password=password, is_staff=False)
        """
        kwargs.setdefault('is_staff', True)
        kwargs.setdefault('is_superuser', True)
        kwargs.setdefault('email_confirmed', True)

        if kwargs.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if kwargs.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        user = self.create_user(email=email, password=password, **kwargs)
        return user

    def get_by_natural_key(self, username):
        """
        Make user logins case-insensitive, which works because you can't sign up
        with the same email with different capitalization anyway.
        """
        return self.get(email__iexact=username)


class User(EditTrackedModel, TimestampedModel, PermissionsMixin, AbstractBaseUser):
    email = models.EmailField(
        max_length=254,
        unique=True,
        db_index=True,
        error_messages={'unique': "A user with that email address already exists."}
    )

    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)

    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    deactivated_date = models.DateTimeField(blank=True, null=True)
    email_confirmed = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = UserManager()

    class Meta:
        verbose_name = 'User'

    tracked_fields = ['is_active', 'email_confirmed']

    def __str__(self):
        return f"User {self.pk}: {self.email}"

    def save(self, *args, **kwargs):
        """
        You get an API key when you confirm your email address.

        >>> unconfirmed_user = getfixture('unconfirmed_user')
        >>> assert not unconfirmed_user.email_confirmed
        >>> with assert_raises(ObjectDoesNotExist):
        ...     unconfirmed_user.auth_token.key
        >>> unconfirmed_user.email_confirmed = True
        >>> unconfirmed_user.save(update_fields=['email_confirmed'])
        >>> assert unconfirmed_user.auth_token.key

        If you programmatically create a user with `email_confirmed=True`,
        for instance...

          -  in the Django admin
          -  manually via `User.object.create_[super]user`
          -  User().save()
          -  via test fixture factories

        ...an API key will automatically be created.
        >>> fixture_user = getfixture('user')
        >>> manager_user = User.objects.create_user(email='test@api_key.com', password='pass', email_confirmed=True)
        >>> manual_user = User(email_confirmed=True); manual_user.save()
        >>> for user in [fixture_user, manager_user, manual_user]:
        ...     assert user.auth_token.key
        """
        create_token = (not self.pk or self.has_changed('email_confirmed')) and self.email_confirmed
        if self.has_changed('is_active') and not self.is_active:
            self.deactivated_date = timezone.now()
        super().save(*args, **kwargs)
        if create_token:
            self.get_new_token()

    def get_new_token(self):
        try:
            self.auth_token.delete()
        except ObjectDoesNotExist:
            pass
        return Token.objects.create(user=self)

    def get_short_name(self):
        return self.email.split('@')[0]

    def get_full_name(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}".strip()
        return self.get_short_name()

    def send_confirmation_email(self, request):
        # Send verify-email-address email.
        # This uses the forgot-password flow; logic is borrowed from auth_forms.PasswordResetForm.save()
        confirmation_link = request.build_absolute_uri(reverse('password_reset_confirm', args=[
            urlsafe_base64_encode(force_bytes(self.pk)),
            default_token_generator.make_token(self),
        ]))
        send_template_email(
            "Confirm your email",
            'email/confirm_email.txt',
            {'confirmation_link': confirmation_link},
            settings.DEFAULT_FROM_EMAIL,
            [self.email],
        )
