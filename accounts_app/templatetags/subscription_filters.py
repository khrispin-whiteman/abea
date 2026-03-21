# accounts_app/templatetags/subscription_filters.py
from django import template
from django.utils import timezone

register = template.Library()

@register.filter
def filter_active(subscriptions):
    """Filter active subscriptions"""
    return [sub for sub in subscriptions if sub.is_active and sub.end_date >= timezone.now().date()]

@register.filter
def filter_expired(subscriptions):
    """Filter expired subscriptions"""
    return [sub for sub in subscriptions if not sub.is_active or sub.end_date < timezone.now().date()]

@register.filter
def filter_pending(subscriptions):
    """Filter pending payment subscriptions"""
    return [sub for sub in subscriptions if sub.payment_status == 'PENDING']