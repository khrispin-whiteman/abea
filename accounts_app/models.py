# accounts/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

class CustomUser(AbstractUser):
    SOCIAL_FIELDS = ('facebook_url', 'linkedin_url', 'x_url')

    # Override email field to make it unique and required
    email = models.EmailField(
        _('email address'),
        unique=True,
        blank=False,
        null=False,
        error_messages={
            'unique': _("A user with that email already exists."),
        }
    )

    # Override username field to make it not required (since we'll use email)
    username = models.CharField(
        _('username'),
        max_length=150,
        blank=True,  # Make it optional since we use email
        null=True,
        unique=False,
        help_text=_('Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.'),
    )

    # Personal Information
    title = models.CharField(_('Title'), max_length=10, blank=True,
                             choices=[('Dr.', 'Dr.'), ('Prof.', 'Prof.'), ('Eng.', 'Eng.'), ('Mr.', 'Mr.'), ('Ms.', 'Ms.')])
    phone = models.CharField(_('Phone Number'), max_length=20, blank=True)

    # Professional Information
    professional_id = models.CharField(_('Professional ID'), max_length=50, blank=True)
    specialization = models.CharField(_('Specialization'), max_length=100, blank=True)
    institution = models.CharField(_('Institution/Organization'), max_length=200, blank=True)
    position = models.CharField(_('Position'), max_length=100, blank=True)

    # Address Information
    country = models.CharField(_('Country'), max_length=100, blank=True)
    city = models.CharField(_('City'), max_length=100, blank=True)
    address = models.TextField(_('Address'), blank=True)

    # Profile
    profile_picture = models.ImageField(_('Profile Picture'), upload_to='profile_pics/', blank=True)
    bio = models.TextField(_('Biography'), blank=True)
    facebook_url = models.URLField(_('Facebook URL'), blank=True, null=True)
    linkedin_url = models.URLField(_('LinkedIn URL'), blank=True, null=True)
    x_url = models.URLField(_('X URL'), blank=True, null=True)

    # Membership Information
    membership_type = models.CharField(_('Membership Type'), max_length=50, blank=True,
                                       choices=[('FULL', 'Full Member'), ('AFFILIATE', 'Affiliate Member'),
                                                ('ASSOCIATE', 'Associate Member'), ('HONORARY', 'Honorary Member')])
    membership_status = models.CharField(_('Membership Status'), max_length=20, default='PENDING', blank=True,
                                         choices=[('ACTIVE', 'Active'), ('PENDING', 'Pending'),
                                                  ('EXPIRED', 'Expired'), ('SUSPENDED', 'Suspended')])
    membership_date = models.DateField(_('Membership Date'), null=True, blank=True)
    membership_expiry = models.DateField(_('Membership Expiry'), null=True, blank=True)

    # Payment Information
    payment_method = models.CharField(_('Preferred Payment Method'), max_length=50, blank=True)

    # Preferences
    language = models.CharField(_('Preferred Language'), max_length=10, default='en', blank=True, choices=[('en', 'English'), ('fr', 'French')])

    # Verification
    is_verified = models.BooleanField(_('Verified'), default=False)
    verification_date = models.DateTimeField(_('Verification Date'), null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Use email as the username field for accounts
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []  # No required fields for createsuperuser command

    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')

    def save(self, *args, **kwargs):
        for field_name in self.SOCIAL_FIELDS:
            if not getattr(self, field_name):
                setattr(self, field_name, None)

        # Automatically set username to email if not provided
        if not self.username and self.email:
            self.username = self.email
        elif self.email and self.username != self.email:
            # Update username to match email if email changes
            self.username = self.email
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_full_name()} - {self.email}"
