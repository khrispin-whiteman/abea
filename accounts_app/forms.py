# accounts/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, PasswordChangeForm
from django.utils.translation import gettext_lazy as _
from .models import CustomUser

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(
        label=_("Email"),
        max_length=254,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': _('Enter your email address')
        })
    )

    password1 = forms.CharField(
        label=_("Password"),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': _('Create a password')
        })
    )

    password2 = forms.CharField(
        label=_("Confirm Password"),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': _('Confirm your password')
        })
    )

    # New fields for phone with country code
    phone_country_code = forms.ChoiceField(
        label=_("Country Code"),
        choices=[
            ('+213', '+213'),  # Algeria
            ('+244', '+244'),  # Angola
            ('+229', '+229'),  # Benin
            ('+267', '+267'),  # Botswana
            ('+226', '+226'),  # Burkina Faso
            ('+257', '+257'),  # Burundi
            ('+238', '+238'),  # Cabo Verde
            ('+237', '+237'),  # Cameroon
            ('+236', '+236'),  # Central African Republic
            ('+235', '+235'),  # Chad
            ('+269', '+269'),  # Comoros
            ('+242', '+242'),  # Congo
            ('+243', '+243'),  # DRC
            ('+225', '+225'),  # Côte d'Ivoire
            ('+253', '+253'),  # Djibouti
            ('+20', '+20'),  # Egypt
            ('+240', '+240'),  # Equatorial Guinea
            ('+291', '+291'),  # Eritrea
            ('+268', '+268'),  # Eswatini
            ('+251', '+251'),  # Ethiopia
            ('+241', '+241'),  # Gabon
            ('+220', '+220'),  # Gambia
            ('+233', '+233'),  # Ghana
            ('+224', '+224'),  # Guinea
            ('+245', '+245'),  # Guinea-Bissau
            ('+254', '+254'),  # Kenya
            ('+266', '+266'),  # Lesotho
            ('+231', '+231'),  # Liberia
            ('+218', '+218'),  # Libya
            ('+261', '+261'),  # Madagascar
            ('+265', '+265'),  # Malawi
            ('+223', '+223'),  # Mali
            ('+222', '+222'),  # Mauritania
            ('+230', '+230'),  # Mauritius
            ('+212', '+212'),  # Morocco
            ('+258', '+258'),  # Mozambique
            ('+264', '+264'),  # Namibia
            ('+227', '+227'),  # Niger
            ('+234', '+234'),  # Nigeria
            ('+250', '+250'),  # Rwanda
            ('+290', '+290'),  # Saint Helena
            ('+239', '+239'),  # São Tomé and Príncipe
            ('+221', '+221'),  # Senegal
            ('+248', '+248'),  # Seychelles
            ('+232', '+232'),  # Sierra Leone
            ('+252', '+252'),  # Somalia
            ('+27', '+27'),  # South Africa
            ('+211', '+211'),  # South Sudan
            ('+249', '+249'),  # Sudan
            ('+255', '+255'),  # Tanzania
            ('+228', '+228'),  # Togo
            ('+216', '+216'),  # Tunisia
            ('+256', '+256'),  # Uganda
            ('+260', '+260'),  # Zambia
            ('+263', '+263'),  # Zimbabwe
        ],
        initial='+260',  # Default to Zambia (can be changed)
        widget=forms.Select(attrs={
            'class': 'form-select',
            'style': 'border: 2px solid #e9ecef; border-radius: 8px; padding: 0.75rem 1rem;'
        })
    )

    phone_number = forms.CharField(
        label=_("Phone Number"),
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Phone Number'),
            'style': 'border: 2px solid #e9ecef; border-radius: 8px; padding: 0.75rem 1rem;'
        })
    )

    class Meta:
        model = CustomUser
        fields = ('email', 'first_name', 'last_name', 'country', 'institution')  # phone removed
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('First Name')}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Last Name')}),
            'country': forms.Select(attrs={'class': 'form-select', 'placeholder': _('Country')}),
            'institution': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': _('Institution/Organization')}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].required = True
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True

    def clean(self):
        cleaned_data = super().clean()
        country_code = cleaned_data.get('phone_country_code')
        phone_number = cleaned_data.get('phone_number')

        if phone_number and country_code:
            # Remove any non-digit characters from phone_number? Keep as entered, but ensure no extra spaces
            full_phone = f"{country_code}{phone_number}"
            cleaned_data['phone'] = full_phone
        else:
            if self.fields['phone_number'].required and not phone_number:
                self.add_error('phone_number', _('This field is required.'))
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.phone = self.cleaned_data.get('phone')
        if commit:
            instance.save()
        return instance


class ProfileUpdateForm(UserChangeForm):
    password = None  # Remove password field
    class Meta:
        model = CustomUser
        fields = ('title', 'first_name', 'last_name', 'email', 'phone',
                  'country', 'city', 'address', 'institution', 'position',
                  'specialization', 'professional_id', 'profile_picture',
                  'facebook_url', 'linkedin_url', 'x_url',
                  'bio', 'language', 'payment_method')
        widgets = {
            'title': forms.Select(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'mobile': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'institution': forms.TextInput(attrs={'class': 'form-control'}),
            'position': forms.TextInput(attrs={'class': 'form-control'}),
            'specialization': forms.TextInput(attrs={'class': 'form-control'}),
            'professional_id': forms.TextInput(attrs={'class': 'form-control'}),
            'facebook_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://facebook.com/username'}),
            'linkedin_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://linkedin.com/in/username'}),
            'x_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://x.com/username'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'language': forms.Select(attrs={'class': 'form-control'}),
            'payment_method': forms.Select(attrs={'class': 'form-control'}),
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        for field_name in CustomUser.SOCIAL_FIELDS:
            setattr(instance, field_name, self.cleaned_data.get(field_name) or None)
        if commit:
            instance.save()
        return instance
