# abea_app/templatetags/custom_filters.py
from django import template
from django.db.models import Count
from ..models import News

register = template.Library()

@register.filter
def filter_attendance(queryset, value):
    """Filter registrations by attendance status"""
    return queryset.filter(attended=value)

@register.filter
def filter_payment_status(queryset, value):
    """Filter registrations by payment status"""
    return queryset.filter(payment_status=value)

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

@register.simple_tag
def get_news_categories():
    return News.NEWS_CATEGORY_CHOICES

@register.simple_tag
def get_news_category_counts():
    return News.objects.filter(is_published=True).values('category').annotate(count=Count('category'))