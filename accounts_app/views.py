# accounts/views.py
import csv
from django.core.mail import send_mail
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from ABEA_Project import settings
from abea_app.forms import UserForm
from abea_app.models import Event, News
from .models import CustomUser
from .forms import CustomUserCreationForm, ProfileUpdateForm, PasswordChangeForm
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
import secrets
import string
from django.utils import timezone
from datetime import date

User = get_user_model()

def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, _('Registration successful!'))
            return redirect('dashboard')
    else:
        form = CustomUserCreationForm()
    return render(request, 'accounts_app/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, _('Login successful!'))
            return redirect('dashboard')
        else:
            messages.error(request, _('Invalid email or password.'))
    return render(request, 'accounts_app/login.html')


@login_required
def logout_view(request):
    logout(request)
    messages.success(request, _('Logged out successfully.'))
    return redirect('home')


@login_required
def dashboard_view(request):
    context = {
        'user': request.user,
        'active_subscription': request.user.subscriptions.filter(is_active=True).first() if hasattr(request.user,
                                                                                                    'subscriptions') else None,
        'upcoming_events': Event.objects.filter(is_published=True, start_date__gte=timezone.now()).order_by(
            'start_date')[:5],
        'recent_news': News.objects.filter(is_published=True).order_by('-publish_date')[:5],
    }
    return render(request, 'accounts_app/dashboard.html', context)


@login_required
def profile_view(request):
    """View for user's own profile (read-only)"""
    user = request.user

    # Get user's data
    subscriptions = user.subscriptions.all().order_by('-created_at')
    event_registrations = user.event_registrations.all().order_by('-registration_date')
    news_articles = user.news_articles.all().order_by('-publish_date')

    context = {
        'user_profile': user,
        'subscriptions': subscriptions,
        'event_registrations': event_registrations,
        'news_articles': news_articles,
        'is_own_profile': True,
    }
    return render(request, 'accounts_app/user_profile.html', context)

@login_required
def edit_own_profile_view(request):
    """View for user to edit their own profile"""
    user_obj = request.user  # Get the current user

    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=user_obj)
        if form.is_valid():
            form.save()
            messages.success(request, _('Profile updated successfully!'))
            return redirect('profile')
    else:
        form = ProfileUpdateForm(instance=user_obj)

    return render(request, 'accounts_app/edit_user.html', {
        'form': form,
        'user_obj': user_obj,
        'is_own_profile': True
    })

@login_required
def change_password_view(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, _('Password changed successfully!'))
            return redirect('profile')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'accounts_app/change_password.html', {'form': form})


def subscription_history_view(request):
    subscriptions = request.user.subscriptions.all().order_by('-created_at')
    return render(request, 'accounts_app/subscription_history.html', {
        'subscriptions': subscriptions,
        'today': date.today()
    })


# User Management Views
@login_required
def manage_users_view(request):
    if not request.user.is_superuser:
        messages.error(request, _('You do not have permission to access this page.'))
        return redirect('dashboard')

    # Get filter parameters
    membership_status = request.GET.get('membership_status', '')
    membership_type = request.GET.get('membership_type', '')
    search = request.GET.get('search', '')
    is_active = request.GET.get('is_active', '')

    users = User.objects.all()

    # Apply filters
    if membership_status:
        users = users.filter(membership_status=membership_status)
    if membership_type:
        users = users.filter(membership_type=membership_type)
    if search:
        users = users.filter(
            Q(username__icontains=search) |
            Q(email__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(institution__icontains=search)
        )
    if is_active == 'true':
        users = users.filter(is_active=True)
    elif is_active == 'false':
        users = users.filter(is_active=False)

    users = users.order_by('-date_joined')

    context = {
        'users': users,
        'membership_statuses': User._meta.get_field('membership_status').choices,
        'membership_types': User._meta.get_field('membership_type').choices,
        'selected_membership_status': membership_status,
        'selected_membership_type': membership_type,
        'search_query': search,
        'selected_is_active': is_active,
    }
    return render(request, 'accounts_app/manage_users.html', context)


def send_account_creation_email(user, password, request):
    """Send accounts creation email with credentials"""
    subject = _('Your Account Has Been Created')

    # Get the site URL
    site_url = request.build_absolute_uri('/')
    login_url = request.build_absolute_uri('/accounts/login/')

    # Email content
    message = f"""
Dear {user.get_full_name() or 'User'},

Your accounts has been successfully created by an administrator.

Here are your login credentials:
- Username/Email: {user.email}
- Password: {password}
- Login URL: {login_url}

Please log in and change your password immediately for security reasons.

If you have any questions or need assistance, please contact our support team.

Best regards,
{settings.SITE_NAME} Team
"""

    # HTML version for better formatting
    html_message = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background-color: #4a6fa5; color: white; padding: 20px; text-align: center; }}
        .content {{ padding: 30px; background-color: #f9f9f9; }}
        .credentials {{ background-color: #fff; border: 1px solid #ddd; padding: 20px; margin: 20px 0; }}
        .credential-item {{ margin: 10px 0; }}
        .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 12px; }}
        .button {{ display: inline-block; padding: 12px 24px; background-color: #4a6fa5; color: white; text-decoration: none; border-radius: 4px; margin: 20px 0; }}
        .warning {{ color: #d9534f; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Account Created</h1>
        </div>
        <div class="content">
            <p>Dear <strong>{user.get_full_name() or 'User'}</strong>,</p>

            <p>Your accounts has been successfully created by an administrator.</p>

            <div class="credentials">
                <h3>Your Login Credentials:</h3>
                <div class="credential-item">
                    <strong>Username/Email:</strong> {user.email}
                </div>
                <div class="credential-item">
                    <strong>Password:</strong> {password}
                </div>
            </div>

            <p class="warning">⚠️ For security reasons, please change your password immediately after logging in.</p>

            <div style="text-align: center;">
                <a href="{login_url}" class="button">Login to Your Account</a>
            </div>

            <p>If the button doesn't work, copy and paste this URL into your browser:<br>
            <code>{login_url}</code></p>

            <p>If you have any questions or need assistance, please contact our support team.</p>

            <p>Best regards,<br>
            <strong>{settings.SITE_NAME} Team</strong></p>
        </div>
        <div class="footer">
            <p>This is an automated message, please do not reply to this email.</p>
            <p>&copy; {timezone.now().year} {settings.SITE_NAME}. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
"""

    # Send email
    send_mail(
        subject=subject,
        message=message.strip(),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False,
    )


@login_required
def add_user_view(request):
    if not request.user.is_superuser:
        messages.error(request, _('You do not have permission to access this page.'))
        return redirect('dashboard')

    if request.method == 'POST':
        form = UserForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                # Generate a random password
                alphabet = string.ascii_letters + string.digits + string.punctuation
                password = ''.join(secrets.choice(alphabet) for _ in range(12))

                # Validate the generated password
                validate_password(password)

                # Create user with the generated password
                user = form.save(commit=False)
                user.set_password(password)

                # If membership is set, update membership date
                if user.membership_type:
                    user.membership_date = timezone.now().date()

                user.save()

                # Send email with credentials
                send_account_creation_email(user, password, request)

                messages.success(request, 'User added successfully. Credentials, EMAIL: ' + user.email + ' & PASSWORD: ' + password + ' have been emailed.')
                return redirect('manage_users')

            except ValidationError as e:
                # Handle password validation errors
                messages.error(request, 'Password generation failed: %(error)s' % {'error': ', '.join(e.messages)})
                return render(request, 'accounts_app/add_user.html', {'form': form})

            except Exception as e:
                # Handle email sending errors
                messages.warning(request, 'User created but email sending failed: %(error)s' % {'error': str(e)})
                return redirect('manage_users')
    else:
        form = UserForm()

    return render(request, 'accounts_app/add_user.html', {'form': form})


def all_members_view(request):
    members = User.objects.all()
    return render(request, 'accounts_app/all_members.html',
                  {
                      'members': members,
                  })

# @login_required
# def edit_user_view(request, pk):
#     if not request.user.is_superuser:
#         messages.error(request, _('You do not have permission to access this page.'))
#         return redirect('dashboard')
#
#     user = get_object_or_404(User, pk=pk)
#
#     if request.method == 'POST':
#         form = UserForm(request.POST, request.FILES, instance=user)
#         if form.is_valid():
#             form.save()
#             messages.success(request, _('User updated successfully.'))
#             return redirect('manage_users')
#     else:
#         form = UserForm(instance=user)
#
#     return render(request, 'accounts_app/edit_user.html', {'form': form, 'user_obj': user})

@login_required
def edit_user_view(request, pk):
    if not request.user.is_superuser:
        messages.error(request, _('You do not have permission to access this page.'))
        return redirect('dashboard')

    user_obj = get_object_or_404(User, pk=pk)

    if request.method == 'POST':
        form = UserForm(request.POST, request.FILES, instance=user_obj)
        if form.is_valid():
            form.save()
            messages.success(request, _('User updated successfully.'))
            return redirect('manage_users')
    else:
        form = UserForm(instance=user_obj)

    return render(request, 'accounts_app/edit_user.html', {
        'form': form,
        'user_obj': user_obj,
        'is_own_profile': (request.user == user_obj)
    })


@login_required
def user_profile_view(request, pk):
    if not request.user.is_superuser:
        messages.error(request, _('You do not have permission to access this page.'))
        return redirect('dashboard')

    user = get_object_or_404(User, pk=pk)

    # Get user's data
    subscriptions = user.subscriptions.all().order_by('-created_at')
    event_registrations = user.event_registrations.all().order_by('-registration_date')
    news_articles = user.news_articles.all().order_by('-publish_date')

    context = {
        'user_profile': user,
        'subscriptions': subscriptions,
        'event_registrations': event_registrations,
        'news_articles': news_articles,
        'is_own_profile': False,
    }
    return render(request, 'accounts_app/user_profile.html', context)

@login_required
@require_POST
def toggle_user_active_view(request, pk):
    if not request.user.is_superuser:
        return JsonResponse({'error': _('Permission denied.')}, status=403)

    user = get_object_or_404(User, pk=pk)

    # Prevent deactivating yourself
    if user == request.user:
        return JsonResponse({'error': _('You cannot deactivate your own accounts.')}, status=400)

    user.is_active = not user.is_active
    user.save()

    action = _('activated') if user.is_active else _('deactivated')
    return JsonResponse({
        'success': True,
        'is_active': user.is_active,
        'message': _('User {} successfully.').format(action)
    })


@login_required
def delete_user_view(request, pk):
    if not request.user.is_superuser:
        messages.error(request, _('You do not have permission to access this page.'))
        return redirect('dashboard')

    user = get_object_or_404(User, pk=pk)

    # Prevent deleting yourself
    if user == request.user:
        messages.error(request, _('You cannot delete your own accounts.'))
        return redirect('manage_users')

    if request.method == 'POST':
        user.delete()
        messages.success(request, _('User deleted successfully.'))
        return redirect('manage_users')

    return render(request, 'accounts_app/delete_user.html', {'user': user})


@login_required
def export_users_view(request):
    if not request.user.is_superuser:
        messages.error(request, _('You do not have permission to access this page.'))
        return redirect('dashboard')

    # Get filter parameters from request
    membership_status = request.GET.get('membership_status', '')
    membership_type = request.GET.get('membership_type', '')
    format_type = request.GET.get('format', 'csv')

    users = User.objects.all()

    if membership_status:
        users = users.filter(membership_status=membership_status)
    if membership_type:
        users = users.filter(membership_type=membership_type)

    users = users.order_by('-date_joined')

    if format_type == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="abea_users_{}.csv"'.format(
            timezone.now().strftime('%Y%m%d_%H%M%S')
        )

        writer = csv.writer(response)
        writer.writerow([
            'Username', 'Email', 'First Name', 'Last Name', 'Title',
            'Phone', 'Professional ID', 'Specialization',
            'Institution', 'Position', 'Country', 'City', 'Address',
            'Membership Type', 'Membership Status', 'Membership Date',
            'Membership Expiry', 'Is Active', 'Is Staff', 'Is Superuser',
            'Date Joined', 'Last Login'
        ])

        for user in users:
            writer.writerow([
                user.username,
                user.email,
                user.first_name,
                user.last_name,
                user.title,
                user.phone,
                user.professional_id,
                user.specialization,
                user.institution,
                user.position,
                user.country,
                user.city,
                user.address,
                user.get_membership_type_display(),
                user.get_membership_status_display(),
                user.membership_date,
                user.membership_expiry,
                'Yes' if user.is_active else 'No',
                'Yes' if user.is_staff else 'No',
                'Yes' if user.is_superuser else 'No',
                user.date_joined.strftime('%Y-%m-%d %H:%M:%S') if user.date_joined else '',
                user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else '',
            ])

        return response
    else:
        # For future expansion (Excel, PDF, etc.)
        messages.error(request, _('Export format not supported.'))
        return redirect('manage_users')


@require_POST
@login_required
def toggle_user_status(request, user_id):
    if not request.user.is_superuser:
        return JsonResponse({'error': _('Permission denied')}, status=403)

    user = get_object_or_404(CustomUser, id=user_id)
    user.is_active = not user.is_active
    user.save()

    return JsonResponse({
        'success': True,
        'is_active': user.is_active,
        'message': _('User status updated successfully.')
    })


from django.contrib.auth.views import PasswordResetView
from django.core.mail import EmailMultiAlternatives
from django.template import loader


# accounts_app/views.py
class CustomPasswordResetView(PasswordResetView):
    """Custom password reset view to ensure HTML emails are sent correctly"""

    def send_mail(self, subject_template_name, email_template_name,
                  context, from_email, to_email, html_email_template_name=None):
        """
        Send a django.core.mail.EmailMultiAlternatives to `to_email`.
        """
        subject = loader.render_to_string(subject_template_name, context)
        subject = ''.join(subject.splitlines())

        # Get plain text version
        body = loader.render_to_string('accounts/password_reset_email.txt', context)

        # Get HTML version
        html_email = loader.render_to_string('accounts/password_reset_email.html', context)

        # Create email with both plain text and HTML versions
        email_message = EmailMultiAlternatives(
            subject,
            body,  # Plain text version
            from_email,
            [to_email]
        )

        # Attach HTML version
        email_message.attach_alternative(html_email, 'text/html')

        email_message.send()