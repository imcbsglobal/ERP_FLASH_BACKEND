from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    """Custom manager for User with username as the unique identifier."""

    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError('Username is required.')
        extra_fields.setdefault('is_active', True)
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'Admin')   # ← FIXED: was 'admin' (lowercase), must match Role.ADMIN = 'Admin'
        extra_fields.setdefault('status', 'Active')
        extra_fields.setdefault('is_active', True)
        return self.create_user(username, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Custom user model — username-based authentication."""

    class Role(models.TextChoices):
        ADMIN    = 'Admin',    'Admin'
        MANAGER  = 'Manager',  'Manager'
        OPERATOR = 'Operator', 'Operator'
        VIEWER   = 'Viewer',   'Viewer'
        SUPPORT  = 'Support',  'Support'
        AUDITOR  = 'Auditor',  'Auditor'

    class Status(models.TextChoices):
        ACTIVE   = 'Active',   'Active'
        INACTIVE = 'Inactive', 'Inactive'

    # Core fields
    username   = models.CharField(max_length=60, unique=True)
    email      = models.EmailField(blank=True)
    first_name = models.CharField(max_length=60, blank=True)
    last_name  = models.CharField(max_length=60, blank=True)
    role       = models.CharField(max_length=20, choices=Role.choices, default=Role.OPERATOR)

    address    = models.CharField(max_length=255, blank=True)
    phone      = models.CharField(max_length=20, blank=True)
    branch_id  = models.IntegerField(null=True, blank=True)   # stores users.Branch PK
    photo      = models.ImageField(upload_to='user_photos/', null=True, blank=True, help_text='Optional profile photo (JPEG/PNG)')
    status     = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)

    # Django auth flags
    is_active  = models.BooleanField(default=True)
    is_staff   = models.BooleanField(default=False)

    # Timestamps
    date_joined = models.DateTimeField(default=timezone.now)
    last_login  = models.DateTimeField(null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD  = 'username'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name        = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-date_joined']

    def __str__(self):
        return self.username

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'.strip() or self.username