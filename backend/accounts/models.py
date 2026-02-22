"""
User and dynamic Role models.
Admin can add, remove, or modify roles without code changes.
"""
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager


class Role(models.Model):
    """
    Dynamic role; admin can add/remove/modify via admin or API.
    Names align with spec: System Administrator, Police Chief, Captain, etc.
    """
    name = models.CharField(max_length=64, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class UserManager(BaseUserManager):
    """Custom manager: require email and support unique national_id, phone."""

    def create_user(self, username, email=None, password=None, **kwargs):
        if not username:
            raise ValueError('Users must have a username')
        email = self.normalize_email(email) if email else ''
        user = self.model(username=username, email=email or '', **kwargs)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email=None, password=None, **kwargs):
        kwargs.setdefault('is_staff', True)
        kwargs.setdefault('is_superuser', True)
        kwargs.setdefault('is_active', True)
        return self.create_user(username, email=email, password=password, **kwargs)


class User(AbstractUser):
    """
    Custom user: username, password, email, phone, full_name, national_id.
    All of username, email, phone, national_id must be unique.
    """
    email = models.EmailField(blank=True, unique=True, null=True)
    phone = models.CharField(max_length=20, blank=True, unique=True, null=True)
    full_name = models.CharField(max_length=255, blank=True)
    national_id = models.CharField(max_length=32, blank=True, unique=True, null=True)
    roles = models.ManyToManyField(Role, related_name='users', blank=True)

    objects = UserManager()

    # Allow login with username, national_id, phone, or email
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']  # for createsuperuser

    class Meta:
        indexes = [
            models.Index(fields=['national_id']),
            models.Index(fields=['phone']),
            models.Index(fields=['email']),
        ]

    def __str__(self):
        return self.username or self.email or str(self.pk)

    def has_role(self, role_name):
        """Check if user has a role by name."""
        return self.roles.filter(name__iexact=role_name).exists()

    def role_names(self):
        return list(self.roles.values_list('name', flat=True))
