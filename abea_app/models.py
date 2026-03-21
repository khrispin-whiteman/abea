# abea/models.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from decimal import Decimal

User = get_user_model()

class Event(models.Model):
    EVENT_TYPE_CHOICES = [
        ('CONFERENCE', _('Conference')),
        ('WORKSHOP', _('Workshop')),
        ('SEMINAR', _('Seminar')),
        ('WEBINAR', _('Webinar')),
        ('TRAINING', _('Training')),
        ('OTHER', _('Other')),
    ]

    title = models.CharField(_('Title'), max_length=200)
    description = models.TextField(_('Description'))
    short_description = models.CharField(_('Short Description'), max_length=300, blank=True)
    event_type = models.CharField(_('Event Type'), max_length=50, choices=EVENT_TYPE_CHOICES)

    # Date & Time
    start_date = models.DateTimeField(_('Start Date'))
    end_date = models.DateTimeField(_('End Date'))
    registration_deadline = models.DateTimeField(_('Registration Deadline'), null=True, blank=True)

    # Location
    location = models.CharField(_('Location'), max_length=200, blank=True)
    venue = models.TextField(_('Venue Details'), blank=True)
    is_online = models.BooleanField(_('Online Event'), default=False)
    online_link = models.URLField(_('Online Link'), blank=True)

    # Media
    image = models.ImageField(_('Event Image'), upload_to='events/', blank=True)
    banner = models.ImageField(_('Event Banner'), upload_to='events/banners/', blank=True)

    # Registration
    is_free = models.BooleanField(_('Free Event'), default=True)
    fee = models.DecimalField(_('Registration Fee'), max_digits=10, decimal_places=2, default=0.00,
                              validators=[MinValueValidator(Decimal('0.00'))])
    capacity = models.PositiveIntegerField(_('Capacity'), null=True, blank=True)
    registered_count = models.PositiveIntegerField(_('Registered Count'), default=0)

    # Status
    is_published = models.BooleanField(_('Published'), default=False)
    is_featured = models.BooleanField(_('Featured'), default=False)

    # SEO
    slug = models.SlugField(_('Slug'), unique=True, max_length=250)
    meta_description = models.CharField(_('Meta Description'), max_length=300, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, null=True, related_name='created_events')

    class Meta:
        verbose_name = _('Event')
        verbose_name_plural = _('Events')
        ordering = ['-start_date']

    def __str__(self):
        return self.title

    @property
    def seats_available(self):
        if self.capacity:
            return max(0, self.capacity - self.registered_count)
        return None

    def update_registered_count(self):
        """Update the registered count based on actual registrations"""
        self.registered_count = self.registrations.count()
        self.save(update_fields=['registered_count'])


class EventRegistration(models.Model):
    """Model to track event registrations"""
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='registrations')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='event_registrations')

    # Registration details
    registration_date = models.DateTimeField(_('Registration Date'), auto_now_add=True)
    attended = models.BooleanField(_('Attended'), default=False)
    attendance_date = models.DateTimeField(_('Attendance Date'), null=True, blank=True)

    # Payment (if event is paid)
    payment_status = models.CharField(_('Payment Status'), max_length=20, default='NOT_REQUIRED',
                                      choices=[('PENDING', 'Pending'), ('PAID', 'Paid'),
                                               ('REFUNDED', 'Refunded'), ('NOT_REQUIRED', 'Not Required')])
    transaction_id = models.CharField(_('Transaction ID'), max_length=100, blank=True)

    # Additional information
    additional_notes = models.TextField(_('Additional Notes'), blank=True)

    # Confirmation
    is_confirmed = models.BooleanField(_('Confirmed'), default=True)
    confirmation_date = models.DateTimeField(_('Confirmation Date'), auto_now_add=True)
    confirmation_code = models.CharField(_('Confirmation Code'), max_length=20, blank=True)

    class Meta:
        verbose_name = _('Event Registration')
        verbose_name_plural = _('Event Registrations')
        unique_together = ['event', 'user']  # Prevent duplicate registrations
        ordering = ['-registration_date']

    def __str__(self):
        return f"{self.user.email} - {self.event.title}"


class News(models.Model):
    NEWS_CATEGORY_CHOICES = [
        ('GENERAL', _('General')),
        ('RESEARCH', _('Research')),
        ('POLICY', _('Policy & Advocacy')),
        ('EDUCATION', _('Education')),
        ('TECHNOLOGY', _('Technology')),
        ('AWARD', _('Awards & Recognition')),
        ('PARTNERSHIP', _('Partnership')),
    ]

    title = models.CharField(_('Title'), max_length=200)
    content = models.TextField(_('Content'))
    excerpt = models.TextField(_('Excerpt'), max_length=500, blank=True)
    category = models.CharField(_('Category'), max_length=50, choices=NEWS_CATEGORY_CHOICES)

    # Media
    image = models.ImageField(_('News Image'), upload_to='news/', blank=True)
    thumbnail = models.ImageField(_('Thumbnail'), upload_to='news/thumbnails/', blank=True)

    # Publishing
    is_published = models.BooleanField(_('Published'), default=False)
    is_featured = models.BooleanField(_('Featured'), default=False)
    publish_date = models.DateTimeField(_('Publish Date'), auto_now_add=True)

    # SEO
    slug = models.SlugField(_('Slug'), unique=True, max_length=250)
    meta_description = models.CharField(_('Meta Description'), max_length=300, blank=True)
    tags = models.CharField(_('Tags'), max_length=500, blank=True, help_text=_('Comma-separated tags'))

    # Statistics
    views = models.PositiveIntegerField(_('Views'), default=0)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='news_articles')

    class Meta:
        verbose_name = _('News')
        verbose_name_plural = _('News')
        ordering = ['-publish_date']

    def __str__(self):
        return self.title


class ExecutiveMember(models.Model):
    POSITION_CHOICES = [
        ('PRESIDENT', _('President')),
        ('VICE_PRESIDENT', _('Vice President')),
        ('SECRETARY', _('Secretary')),
        ('TREASURER', _('Treasurer')),
        ('EXECUTIVE_MEMBER', _('Executive Member')),
        ('REGIONAL_REP', _('Regional Representative')),
    ]

    REGION_CHOICES = [
        ('NORTH', _('North Africa')),
        ('EAST', _('East Africa')),
        ('WEST', _('West Africa')),
        ('CENTRAL', _('Central Africa')),
        ('SOUTHERN', _('Southern Africa')),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='executive_role')
    position = models.CharField(_('Position'), max_length=50, choices=POSITION_CHOICES)
    region = models.CharField(_('Region'), max_length=50, choices=REGION_CHOICES, blank=True)

    # Term Information
    term_start = models.DateField(_('Term Start'))
    term_end = models.DateField(_('Term End'))
    is_current = models.BooleanField(_('Current Member'), default=True)

    # Display Order
    display_order = models.PositiveIntegerField(_('Display Order'), default=0)
    show_on_homepage = models.BooleanField(_('Show on Homepage'), default=False)

    # Additional Info
    biography = models.TextField(_('Biography'), blank=True)
    achievements = models.TextField(_('Key Achievements'), blank=True)
    linkedin = models.URLField(_('LinkedIn Profile'), blank=True)
    twitter = models.URLField(_('Twitter Profile'), blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Executive Member')
        verbose_name_plural = _('Executive Members')
        ordering = ['display_order', 'position']

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_position_display()}"


class Partner(models.Model):
    PARTNER_TYPE_CHOICES = [
        ('CORPORATE', _('Corporate Partner')),
        ('ACADEMIC', _('Academic Institution')),
        ('GOVERNMENT', _('Government Agency')),
        ('NGO', _('Non-Governmental Organization')),
        ('INTERNATIONAL', _('International Organization')),
        ('SPONSOR', _('Sponsor')),
    ]

    name = models.CharField(_('Organization Name'), max_length=200)
    description = models.TextField(_('Description'), blank=True)
    partner_type = models.CharField(_('Partner Type'), max_length=50, choices=PARTNER_TYPE_CHOICES)

    # Contact Information
    website = models.URLField(_('Website'))
    email = models.EmailField(_('Contact Email'), blank=True)
    phone = models.CharField(_('Phone'), max_length=20, blank=True)
    address = models.TextField(_('Address'), blank=True)
    country = models.CharField(_('Country'), max_length=100)

    # Logo and Media
    logo = models.ImageField(_('Logo'), upload_to='partners/logos/')
    banner = models.ImageField(_('Banner Image'), upload_to='partners/banners/', blank=True)

    # Partnership Details
    partnership_date = models.DateField(_('Partnership Start Date'))
    partnership_active = models.BooleanField(_('Active Partnership'), default=True)

    # Display
    display_order = models.PositiveIntegerField(_('Display Order'), default=0)
    show_on_homepage = models.BooleanField(_('Show on Homepage'), default=False)

    # SEO
    slug = models.SlugField(_('Slug'), unique=True, max_length=250)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Partner')
        verbose_name_plural = _('Partners')
        ordering = ['display_order', 'name']

    def __str__(self):
        return self.name


class MembershipPlan(models.Model):
    PLAN_TYPE_CHOICES = [
        ('FULL', _('Full Member (National Association)')),
        ('AFFILIATE', _('Affiliate Member (Regional Organization)')),
        ('ASSOCIATE', _('Associate Member (Organization/Individual)')),
        ('HONORARY', _('Honorary Member')),
        ('STUDENT', _('Student Member')),
    ]

    name = models.CharField(_('Plan Name'), max_length=100)
    plan_type = models.CharField(_('Plan Type'), max_length=50, choices=PLAN_TYPE_CHOICES)
    description = models.TextField(_('Description'))

    # Pricing
    price = models.DecimalField(_('Annual Fee'), max_digits=10, decimal_places=2)
    currency = models.CharField(_('Currency'), max_length=3, default='USD')
    duration_months = models.PositiveIntegerField(_('Duration (Months)'), default=12)

    # Features
    features = models.JSONField(_('Features'), default=list,
                                help_text=_('List of features as JSON array'))
    benefits = models.TextField(_('Benefits'), blank=True)

    # Status
    is_active = models.BooleanField(_('Active'), default=True)
    is_popular = models.BooleanField(_('Popular Plan'), default=False)

    # Display
    display_order = models.PositiveIntegerField(_('Display Order'), default=0)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Membership Plan')
        verbose_name_plural = _('Membership Plans')
        ordering = ['display_order', 'price']

    def __str__(self):
        return f"{self.name} - {self.get_plan_type_display()}"


class Subscription(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('PENDING', _('Pending')),
        ('COMPLETED', _('Completed')),
        ('FAILED', _('Failed')),
        ('REFUNDED', _('Refunded')),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('MOBILE_MONEY', _('Mobile Money')),
        ('BANK_TRANSFER', _('Bank Transfer')),
        ('CREDIT_CARD', _('Credit Card')),
        ('PAYPAL', _('PayPal')),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions')
    membership_plan = models.ForeignKey(MembershipPlan, on_delete=models.CASCADE)

    # Subscription Details
    start_date = models.DateField(_('Start Date'))
    end_date = models.DateField(_('End Date'))
    is_active = models.BooleanField(_('Active'), default=True)
    auto_renew = models.BooleanField(_('Auto Renew'), default=True)

    # Payment Information
    amount_paid = models.DecimalField(_('Amount Paid'), max_digits=10, decimal_places=2)
    payment_method = models.CharField(_('Payment Method'), max_length=50, choices=PAYMENT_METHOD_CHOICES)
    payment_status = models.CharField(_('Payment Status'), max_length=20, choices=PAYMENT_STATUS_CHOICES)
    transaction_id = models.CharField(_('Transaction ID'), max_length=100, unique=True)
    payment_date = models.DateTimeField(_('Payment Date'), null=True, blank=True)

    # Mobile Payment Details (Africa specific)
    mobile_network = models.CharField(_('Mobile Network'), max_length=50, blank=True, choices=[('MTN', 'MTN'), ('AIRTEL', 'Airtel'), ('VODAFONE', 'Vodafone'), ('ORANGE', 'Orange')])
    mobile_number = models.CharField(_('Mobile Number'), max_length=20, blank=True)

    # Receipt
    receipt_number = models.CharField(_('Receipt Number'), max_length=50, blank=True)

    reference_number = models.CharField(_('Reference Number'), max_length=100, blank=True)
    charges = models.DecimalField(_('Transaction Charges'), max_digits=10, decimal_places=2, default=0)
    payment_notes = models.TextField(_('Payment Notes'), blank=True)

    # Webhook/notification fields
    webhook_received = models.BooleanField(_('Webhook Received'), default=False)
    webhook_payload = models.JSONField(_('Webhook Payload'), default=dict, blank=True)

    # Timestamps
    verified_at = models.DateTimeField(_('Verified At'), null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Subscription')
        verbose_name_plural = _('Subscriptions')
        ordering = ['-created_at']

        indexes = [
            models.Index(fields=['transaction_id']),
            models.Index(fields=['reference_number']),
            models.Index(fields=['payment_status', 'is_active']),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.membership_plan.name}"


class Gallery(models.Model):
    GALLERY_CATEGORY_CHOICES = [
        ('EVENT', _('Events')),
        ('CONFERENCE', _('Conferences')),
        ('WORKSHOP', _('Workshops')),
        ('COMMITTEE', _('Committee Meetings')),
        ('GENERAL', _('General')),
    ]

    title = models.CharField(_('Title'), max_length=200)
    description = models.TextField(_('Description'), blank=True)
    category = models.CharField(_('Category'), max_length=50, choices=GALLERY_CATEGORY_CHOICES)

    # Image
    image = models.ImageField(_('Image'), upload_to='gallery/')
    thumbnail = models.ImageField(_('Thumbnail'), upload_to='gallery/thumbnails/', blank=True)

    # Event Association
    event = models.ForeignKey(Event, on_delete=models.SET_NULL, null=True, blank=True,
                              related_name='gallery_images')

    # Display
    is_featured = models.BooleanField(_('Featured Image'), default=False)
    display_order = models.PositiveIntegerField(_('Display Order'), default=0)

    # Metadata
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Gallery Image')
        verbose_name_plural = _('Gallery Images')
        ordering = ['-uploaded_at']

    def __str__(self):
        return self.title


class ContactMessage(models.Model):
    MESSAGE_TYPE_CHOICES = [
        ('GENERAL', _('General Inquiry')),
        ('MEMBERSHIP', _('Membership Inquiry')),
        ('EVENT', _('Event Inquiry')),
        ('TECH_SUPPORT', _('Technical Support')),
        ('PARTNERSHIP', _('Partnership Inquiry')),
        ('FEEDBACK', _('Feedback')),
    ]

    name = models.CharField(_('Name'), max_length=100)
    email = models.EmailField(_('Email'))
    phone = models.CharField(_('Phone'), max_length=20, blank=True)
    organization = models.CharField(_('Organization'), max_length=200, blank=True)

    message_type = models.CharField(_('Message Type'), max_length=50, choices=MESSAGE_TYPE_CHOICES)
    subject = models.CharField(_('Subject'), max_length=200)
    message = models.TextField(_('Message'))

    # Status
    is_read = models.BooleanField(_('Read'), default=False)
    is_responded = models.BooleanField(_('Responded'), default=False)
    priority = models.CharField(_('Priority'), max_length=20, default='NORMAL',
                                choices=[('LOW', 'Low'), ('NORMAL', 'Normal'), ('HIGH', 'High'), ('URGENT', 'Urgent')])

    # Response
    response = models.TextField(_('Response'), blank=True)
    responded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    responded_at = models.DateTimeField(_('Responded At'), null=True, blank=True)

    # Metadata
    ip_address = models.GenericIPAddressField(_('IP Address'), null=True, blank=True)
    user_agent = models.TextField(_('User Agent'), blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Contact Message')
        verbose_name_plural = _('Contact Messages')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.subject} - {self.name}"