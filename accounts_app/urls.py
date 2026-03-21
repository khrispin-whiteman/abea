# accounts/urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .views import CustomPasswordResetView

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Dashboard and Profile
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.edit_own_profile_view, name='edit_own_profile'),
    path('profile/change-password/', views.change_password_view, name='change_password'),
    path('subscriptions/', views.subscription_history_view, name='subscription_history'),

    # Admin Management
    # path('manage-users/', views.manage_users_view, name='manage_users'),
    path('toggle-user-status/<int:user_id>/', views.toggle_user_status, name='toggle_user_status'),

    # User Management URLs
    path('manage-users/', views.manage_users_view, name='manage_users'),
    path('users/add/', views.add_user_view, name='add_user'),
    path('users/<int:pk>/edit/', views.edit_user_view, name='edit_user'),
    path('users/<int:pk>/profile/', views.user_profile_view, name='user_profile'),
    path('users/<int:pk>/toggle-active/', views.toggle_user_active_view, name='toggle_user_active'),
    path('users/<int:pk>/delete/', views.delete_user_view, name='delete_user'),
    path('export-users/', views.export_users_view, name='export_users'),

    path('members/all/', views.all_members_view, name='all_members'),

    # Authentication URLs
    path('account/password-reset/',
         CustomPasswordResetView.as_view(
             template_name='accounts/password_reset.html',
             email_template_name='accounts/password_reset_email.html',
             subject_template_name='accounts/password_reset_subject.txt',
             html_email_template_name='accounts/password_reset_email.html'  # Explicitly specify HTML template
         ),
         name='password_reset'),

    path('account/password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='accounts/password_reset_done.html'
         ),
         name='password_reset_done'),

    path('account/password-reset-confirm/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='accounts/password_reset_confirm.html'
         ),
         name='password_reset_confirm'),

    path('account/password-reset-complete/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='accounts/password_reset_complete.html'
         ),
         name='password_reset_complete'),
]