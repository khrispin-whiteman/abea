# abea/forms.py
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from .models import ContactMessage, EventRegistration, MembershipPlan
from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Gallery, ExecutiveMember, Partner, Event, News

User = get_user_model()

class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ('name', 'email', 'phone', 'organization', 'message_type', 'subject', 'message')
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Your Name')
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': _('Your Email')
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Phone Number')
            }),
            'organization': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Organization (Optional)')
            }),
            'message_type': forms.Select(attrs={'class': 'form-control'}),
            'subject': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Subject')
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': _('Your Message')
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].required = True
        self.fields['email'].required = True
        self.fields['subject'].required = True
        self.fields['message'].required = True


class EventRegistrationForm(forms.ModelForm):
    class Meta:
        model = EventRegistration
        fields = ('additional_notes',)
        widgets = {
            'additional_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('Any additional notes or requirements')
            }),
        }


class GalleryForm(forms.ModelForm):
    class Meta:
        model = Gallery
        fields = ['title', 'description', 'category', 'image', 'thumbnail', 'event', 'is_featured', 'display_order']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'event': forms.Select(attrs={'class': 'form-select'}),
        }

class ExecutiveMemberForm(forms.ModelForm):
    class Meta:
        model = ExecutiveMember
        fields = ['user', 'position', 'region', 'term_start', 'term_end', 'is_current',
                 'display_order', 'show_on_homepage', 'biography', 'achievements',
                 'linkedin', 'twitter']
        widgets = {
            'biography': forms.Textarea(attrs={'rows': 4}),
            'achievements': forms.Textarea(attrs={'rows': 3}),
            'term_start': forms.DateInput(attrs={'type': 'date'}),
            'term_end': forms.DateInput(attrs={'type': 'date'}),
        }

class PartnerForm(forms.ModelForm):
    class Meta:
        model = Partner
        fields = ['name', 'description', 'partner_type', 'website', 'email', 'phone',
                 'address', 'country', 'logo', 'banner', 'partnership_date',
                 'partnership_active', 'display_order', 'show_on_homepage', 'slug']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'address': forms.Textarea(attrs={'rows': 3}),
            'partnership_date': forms.DateInput(attrs={'type': 'date'}),
        }

class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['title', 'description', 'short_description', 'event_type',
                 'start_date', 'end_date', 'registration_deadline', 'location',
                 'venue', 'is_online', 'online_link', 'image', 'banner',
                 'is_free', 'fee', 'capacity', 'is_published', 'is_featured',
                 'slug', 'meta_description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
            'venue': forms.Textarea(attrs={'rows': 3}),
            'start_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'registration_deadline': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

class NewsForm(forms.ModelForm):
    class Meta:
        model = News
        fields = ['title', 'content', 'excerpt', 'category', 'image', 'thumbnail',
                 'is_published', 'is_featured', 'slug', 'meta_description', 'tags']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 10}),
            'excerpt': forms.Textarea(attrs={'rows': 3}),
            'tags': forms.TextInput(attrs={'placeholder': 'comma,separated,tags'}),
        }


class UserForm(forms.ModelForm):
    # Add custom styling for boolean fields with default values
    is_active = forms.BooleanField(
        required=False,
        initial=True,  # Checked by default
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    is_staff = forms.BooleanField(
        required=False,
        initial=True,  # Checked by default
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    is_superuser = forms.BooleanField(
        required=False,
        initial=False,  # Unchecked by default
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    is_verified = forms.BooleanField(
        required=False,
        initial=False,  # Unchecked by default
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    class Meta:
        model = User
        fields = [
            'email', 'first_name', 'last_name', 'title', 'phone',
            'professional_id', 'specialization', 'institution', 'position',
            'country', 'city', 'address', 'profile_picture', 'bio',
            'membership_type', 'membership_status', 'membership_date',
            'membership_expiry', 'payment_method', 'language', 'is_verified',
            'is_active', 'is_staff', 'is_superuser'
        ]
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'address': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'membership_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'membership_expiry': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'title': forms.Select(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'professional_id': forms.TextInput(attrs={'class': 'form-control'}),
            'specialization': forms.TextInput(attrs={'class': 'form-control'}),
            'institution': forms.TextInput(attrs={'class': 'form-control'}),
            'position': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
            'membership_type': forms.Select(attrs={'class': 'form-control'}),
            'membership_status': forms.Select(attrs={'class': 'form-control'}),
            'payment_method': forms.TextInput(attrs={'class': 'form-control'}),
            'language': forms.Select(attrs={'class': 'form-control'}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email:
            raise ValidationError("Email is required.")

        # Check if email already exists
        qs = User.objects.filter(email__iexact=email)

        # If we're editing an existing user, exclude them from the check
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise ValidationError("This email address is already in use. Please use a different email.")

        return email

    def save(self, commit=True):
        # Get the user instance
        user = super().save(commit=False)

        # Set username to email
        if user.email:
            user.username = user.email

        if commit:
            user.save()

        return user


class MembershipPlanForm(forms.ModelForm):
    # Custom field for features (JSON array as textarea)
    features_text = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 5, 'placeholder': 'Enter one feature per line'}),
        required=False,
        help_text="Enter one feature per line. Each line will become a list item."
    )

    class Meta:
        model = MembershipPlan
        fields = ['name', 'plan_type', 'description', 'price', 'currency',
                  'duration_months', 'features_text', 'benefits', 'is_active',
                  'is_popular', 'display_order']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'benefits': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # If editing an existing plan, load features into textarea
        if self.instance and self.instance.pk and self.instance.features:
            self.fields['features_text'].initial = '\n'.join(self.instance.features)

        # Set currency choices
        self.fields['currency'].initial = 'USD'

        # Add form-control class to all fields
        for field_name, field in self.fields.items():
            if field_name != 'is_active' and field_name != 'is_popular':
                field.widget.attrs['class'] = 'form-control'

    def clean_features_text(self):
        features_text = self.cleaned_data.get('features_text', '')
        if features_text:
            # Convert textarea lines to JSON array
            features = [feature.strip() for feature in features_text.split('\n') if feature.strip()]
            return features
        return []

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Set features from cleaned data
        instance.features = self.cleaned_data.get('features_text', [])
        if commit:
            instance.save()
        return instance