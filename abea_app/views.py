# abea_app/views.py
import requests
from django.contrib.auth import get_user_model
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.http import require_POST
from django_pesapalv3.views import TransactionCompletedView, PaymentRequestMixin
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from ABEA_Project import settings
from abea_app.mobile_money_api import MoneyUnifyAPI
from .models import Event, News, ContactMessage, EventRegistration
from .forms import ContactForm, EventRegistrationForm, NewsForm, EventForm, MembershipPlanForm
from django.utils.translation import gettext_lazy as _
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Gallery, ExecutiveMember, Partner
from .forms import GalleryForm, ExecutiveMemberForm, PartnerForm
from django.db.models import Count
from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.translation import gettext as _
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
import uuid
from datetime import date, timedelta
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from .models import Subscription, MembershipPlan
from abea_app.services.pesapal_service import generate_access_token, submit_order_request, get_transaction_status
import logging

logger = logging.getLogger(__name__)

User = get_user_model()

def is_superuser(user):
    return user.is_superuser

def home_view(request):
    # Hero slider data (can be dynamic from database)
    hero_slides = [
        {
            'title': _('Advancing Biomedical Engineering in Africa'),
            'description': _('Uniting professionals across the continent for better healthcare'),
            'image': 'images/hero1.jpg',
            'cta_text': _('Join Us Now'),
            'cta_link': '/membership/'
        },
        # Add more slides as needed
    ]

    # Get featured events
    featured_events = Event.objects.filter(
        is_published=True,
        is_featured=True,
        start_date__gte=timezone.now()
    ).order_by('start_date')[:5]

    # Get latest news
    latest_news = News.objects.filter(
        is_published=True
    ).order_by('-publish_date')[:6]

    # Get executive members for homepage
    executive_members = ExecutiveMember.objects.select_related('user').filter(
        is_current=True,
        show_on_homepage=True
    ).order_by('display_order')[:4]

    # Get partners for homepage
    partners = Partner.objects.filter(
        partnership_active=True,
        show_on_homepage=True
    ).order_by('display_order')

    # Get upcoming events
    upcoming_events = Event.objects.filter(
        is_published=True,
        start_date__gte=timezone.now()
    ).order_by('start_date')[:3]

    context = {
        'hero_slides': hero_slides,
        'featured_events': featured_events,
        'latest_news': latest_news,
        'executive_members': executive_members,
        'partners': partners,
        'upcoming_events': upcoming_events,
        'page_title': _('Home - Africa Biomedical Engineering Alliance'),
    }

    return render(request, 'abea_app/home.html', context)


def about_view(request):
    sections = [
        {
            'title': _('Our Vision'),
            'content': _(
                'To be the leading collaborative platform for advancing the biomedical engineering profession and healthcare technologies across Africa.'),
            'icon': 'fas fa-eye'
        },
        {
            'title': _('Our Mission'),
            'content': _(
                'To unite and empower biomedical engineering professionals and their associations across Africa by fostering innovation, capacity building, mentorship, educational initiatives and policy advocacy.'),
            'icon': 'fas fa-bullseye'
        },
        {
            'title': _('Our Objectives'),
            'content': _('''
                • Promote collaboration, research, and knowledge exchange
                • Advocate for policies supporting biomedical engineering
                • Facilitate capacity building and professional development
                • Enhance healthcare technologies accessibility and sustainability
                • Establish partnerships with regional and international organizations
                • Champion Gender and Diversity Inclusion
            '''),
            'icon': 'fas fa-list-check'
        }
    ]

    # Get all executive members for about page
    executive_members = ExecutiveMember.objects.select_related('user').filter(
        is_current=True
    ).order_by('position')

    context = {
        'sections': sections,
        'executive_members': executive_members,
        'page_title': _('About Us - ABEA'),
    }

    return render(request, 'abea_app/about.html', context)


def news_list_view(request):
    category = request.GET.get('category', '')

    if category:
        news_list = News.objects.filter(
            is_published=True,
            category=category
        ).order_by('-publish_date')
    else:
        news_list = News.objects.filter(
            is_published=True
        ).order_by('-publish_date')

    # Pagination
    paginator = Paginator(news_list, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Get categories for filter
    categories = News.NEWS_CATEGORY_CHOICES

    context = {
        'news_list': page_obj,
        'categories': categories,
        'selected_category': category,
        'page_title': _('News & Events - ABEA'),
    }

    return render(request, 'abea_app/news_list.html', context)


def news_detail_view(request, slug):
    news = get_object_or_404(News, slug=slug, is_published=True)

    # Increment view count
    news.views += 1
    news.save(update_fields=['views'])

    # Get related news
    related_news = News.objects.filter(
        is_published=True,
        category=news.category
    ).exclude(id=news.id).order_by('-publish_date')[:3]

    # Get recent news for sidebar
    recent_news = News.objects.filter(
        is_published=True
    ).exclude(id=news.id).order_by('-publish_date')[:5]

    # Get tags list
    tags_list = [tag.strip() for tag in news.tags.split(',')] if news.tags else []

    # Get category counts
    category_counts = News.objects.filter(
        is_published=True
    ).values('category').annotate(count=Count('category'))

    category_counts_dict = {item['category']: item['count'] for item in category_counts}

    context = {
        'news': news,
        'related_news': related_news,
        'recent_news': recent_news,
        'tags_list': tags_list,
        'news_categories': News.NEWS_CATEGORY_CHOICES,
        'category_counts': category_counts_dict,
        'page_title': news.title,
    }

    return render(request, 'abea_app/news_detail.html', context)

@require_POST
@login_required
def register_event_view(request, event_slug):
    event = get_object_or_404(Event, slug=event_slug)

    # Check if event is still open for registration
    if event.registration_deadline and timezone.now() > event.registration_deadline:
        messages.error(request, _('Registration deadline has passed.'))
        return redirect('event_detail', slug=event_slug)

    # Check capacity
    if event.capacity and event.registered_count >= event.capacity:
        messages.error(request, _('Event has reached maximum capacity.'))
        return redirect('event_detail', slug=event_slug)

    # Check if already registered
    if event.registrations.filter(user=request.user).exists():
        messages.warning(request, _('You are already registered for this event.'))
        return redirect('event_detail', slug=event_slug)

    # Create registration
    registration = EventRegistration.objects.create(
        event=event,
        user=request.user,
        registration_date=timezone.now()
    )

    # Update registered count
    event.registered_count += 1
    event.save(update_fields=['registered_count'])

    messages.success(request, _('Successfully registered for the event!'))
    return redirect('event_detail', slug=event_slug)


def gallery_view(request):
    category = request.GET.get('category', '')

    if category:
        images = Gallery.objects.filter(category=category).order_by('-uploaded_at')
    else:
        images = Gallery.objects.all().order_by('-uploaded_at')

    # Pagination
    paginator = Paginator(images, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Get categories for filter
    categories = Gallery.GALLERY_CATEGORY_CHOICES

    # Calculate statistics
    total_images = Gallery.objects.count()
    featured_count = Gallery.objects.filter(is_featured=True).count()
    event_images = Gallery.objects.filter(event__isnull=False).count()

    context = {
        'images': page_obj,
        'categories': categories,
        'selected_category': category,
        'page_title': _('Gallery - ABEA'),
        'total_images': total_images,
        'featured_count': featured_count,
        'event_images': event_images,
    }

    return render(request, 'abea_app/gallery.html', context)


def partners_view(request):
    partners = Partner.objects.filter(
        partnership_active=True
    ).order_by('display_order', 'name')

    # Group by partner type
    partners_by_type = {}
    for partner in partners:
        partner_type = partner.get_partner_type_display()
        if partner_type not in partners_by_type:
            partners_by_type[partner_type] = []
        partners_by_type[partner_type].append(partner)

    context = {
        'partners_by_type': partners_by_type,
        'page_title': _('Our Partners - ABEA'),
    }

    return render(request, 'abea_app/partners.html', context)


def partner_detail_view(request, slug):
    partner = get_object_or_404(Partner, slug=slug)

    context = {
        'partner': partner,
        'page_title': f"{partner.name} - Partner",
    }

    return render(request, 'abea_app/partner_detail.html', context)


def membership_plans_view(request):
    plans = MembershipPlan.objects.filter(is_active=True).order_by('display_order', 'price')

    # Check user's current subscription if logged in
    current_subscription = None
    if request.user.is_authenticated:
        current_subscription = request.user.subscriptions.filter(
            is_active=True,
            end_date__gte=timezone.now().date()
        ).first()

    context = {
        'plans': plans,
        'current_subscription': current_subscription,
        'page_title': _('Membership Plans - ABEA'),
    }

    return render(request, 'abea_app/membership.html', context)


# @login_required
# def initiate_payment_view(request, plan_id):
#     if request.method == 'POST':
#         plan = get_object_or_404(MembershipPlan, id=plan_id, is_active=True)
#
#         # Get payment method from form
#         payment_method = request.POST.get('payment_method')
#         mobile_network = request.POST.get('mobile_network')
#         mobile_number = request.POST.get('mobile_number')
#
#         # Create pending subscription
#         subscription = Subscription.objects.create(
#             user=request.user,
#             membership_plan=plan,
#             start_date=timezone.now().date(),
#             end_date=timezone.now().date() + timezone.timedelta(days=plan.duration_months * 30),
#             amount_paid=plan.price,
#             payment_method=payment_method,
#             payment_status='PENDING',
#             mobile_network=mobile_network if payment_method == 'MOBILE_MONEY' else '',
#             mobile_number=mobile_number if payment_method == 'MOBILE_MONEY' else '',
#         )
#
#         # Here you would integrate with actual payment gateway
#         # For now, we'll simulate payment success
#
#         return JsonResponse({
#             'success': True,
#             'message': _('Payment initiated successfully.'),
#             'subscription_id': subscription.id,
#             'payment_url': '/payment/process/',  # This would be your payment gateway URL
#         })
#
#     return JsonResponse({'error': _('Invalid request')}, status=400)


def contact_view(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            contact_message = form.save(commit=False)

            # Add IP and user agent
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                contact_message.ip_address = x_forwarded_for.split(',')[0]
            else:
                contact_message.ip_address = request.META.get('REMOTE_ADDR')

            contact_message.user_agent = request.META.get('HTTP_USER_AGENT', '')

            contact_message.save()

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': _('Thank you for your message. We will get back to you soon.')
                })

            messages.success(request, _('Thank you for your message. We will get back to you soon.'))
            return redirect('contact')
    else:
        form = ContactForm()

    context = {
        'form': form,
        'page_title': _('Contact Us - ABEA'),
        'contact_email': 'africabmealliance24@gmail.com',
        'contact_phone': '+254723320894',
    }

    return render(request, 'abea_app/contact.html', context)


# Admin views for ABEA app
@login_required
def admin_dashboard_view(request):
    if not request.user.is_superuser and not request.user.is_staff:
        messages.error(request, _('You do not have permission to access this page.'))
        return redirect('dashboard')

    # Statistics for dashboard
    stats = {
        'total_users': User.objects.count(),
        'active_subscriptions': Subscription.objects.filter(is_active=True).count(),
        'total_events': Event.objects.count(),
        'upcoming_events': Event.objects.filter(start_date__gte=timezone.now()).count(),
        'total_news': News.objects.count(),
        'unread_messages': ContactMessage.objects.filter(is_read=False).count(),
        'total_partners': Partner.objects.filter(partnership_active=True).count(),
    }

    # Recent activities
    recent_users = User.objects.all().order_by('-date_joined')[:5]
    recent_subscriptions = Subscription.objects.all().order_by('-created_at')[:5]
    recent_messages = ContactMessage.objects.all().order_by('-created_at')[:5]

    context = {
        'stats': stats,
        'recent_users': recent_users,
        'recent_subscriptions': recent_subscriptions,
        'recent_messages': recent_messages,
    }

    return render(request, 'abea_app/admin/dashboard.html', context)


# Event CRUD Views (missing from your setup)
@login_required
def manage_events_view(request):
    if not request.user.is_superuser and not request.user.is_staff:
        messages.error(request, _('Permission denied.'))
        return redirect('dashboard')

    # Get filter parameters
    event_type = request.GET.get('event_type', '')
    status = request.GET.get('status', '')
    search = request.GET.get('search', '')

    events = Event.objects.all()

    # Apply filters
    if event_type:
        events = events.filter(event_type=event_type)
    if status == 'published':
        events = events.filter(is_published=True)
    elif status == 'draft':
        events = events.filter(is_published=False)
    if search:
        events = events.filter(title__icontains=search)

    events = events.order_by('-created_at')

    context = {
        'events': events,
        'event_type_choices': Event.EVENT_TYPE_CHOICES,
        'selected_type': event_type,
        'selected_status': status,
        'search_query': search,
    }

    return render(request, 'abea_app/admin/manage_events.html', context)


@login_required
def add_event_view(request):
    if not request.user.is_superuser and not request.user.is_staff:
        messages.error(request, _('Permission denied.'))
        return redirect('dashboard')

    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            event = form.save(commit=False)
            event.created_by = request.user
            event.save()
            messages.success(request, _('Event created successfully.'))
            return redirect('manage_events')
    else:
        form = EventForm()

    return render(request, 'abea_app/admin/add_event.html', {'form': form})

@login_required
def edit_event_view(request, pk):
    if not request.user.is_superuser and not request.user.is_staff:
        messages.error(request, _('Permission denied.'))
        return redirect('dashboard')

    event = get_object_or_404(Event, pk=pk)

    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES, instance=event)
        if form.is_valid():
            form.save()
            messages.success(request, _('Event updated successfully.'))
            return redirect('manage_events')
    else:
        form = EventForm(instance=event)

    return render(request, 'abea_app/admin/edit_event.html', {'form': form, 'event': event})

@login_required
def delete_event_view(request, pk):
    if not request.user.is_superuser and not request.user.is_staff:
        messages.error(request, _('Permission denied.'))
        return redirect('dashboard')

    member = get_object_or_404(Event, pk=pk)

    if request.method == 'POST':
        member.delete()
        messages.success(request, _('Event deleted successfully.'))
        return redirect('manage_events')

    return render(request, 'abea_app/admin/delete_event.html', {'member': member})

@login_required
def event_registrations_view(request, slug):
    if not request.user.is_superuser and not request.user.is_staff:
        messages.error(request, _('Permission denied.'))
        return redirect('dashboard')

    event = get_object_or_404(Event, slug=slug)
    registrations = event.registrations.all().order_by('-registration_date')

    return render(request, 'abea_app/admin/event_registrations.html', {
        'event': event,
        'registrations': registrations
    })


def events_list_view(request):
    event_type = request.GET.get('type', '')

    now = timezone.now()

    if event_type:
        events = Event.objects.filter(
            is_published=True,
            event_type=event_type,
            end_date__gte=now
        ).order_by('start_date')
    else:
        events = Event.objects.filter(
            is_published=True,
            end_date__gte=now
        ).order_by('start_date')

    # Get past events for archive
    past_events = Event.objects.filter(
        is_published=True,
        end_date__lt=now
    ).order_by('-start_date')[:6]

    # Get event types for filter
    event_types = Event.EVENT_TYPE_CHOICES

    context = {
        'events': events,
        'past_events': past_events,
        'event_types': event_types,
        'selected_type': event_type,
        'page_title': _('Events - ABEA'),
    }

    return render(request, 'abea_app/events_list.html', context)


# def event_detail_view(request, slug):
#     event = get_object_or_404(Event, slug=slug, is_published=True)
#
#     # Check if user is registered (if logged in)
#     is_registered = False
#     if request.user.is_authenticated:
#         is_registered = event.registrations.filter(user=request.user).exists()
#
#     # Registration form
#     form = EventRegistrationForm()
#
#     context = {
#         'event': event,
#         'is_registered': is_registered,
#         'form': form,
#         'page_title': event.title,
#     }
#
#     return render(request, 'abea_app/event_detail.html', context)

def event_detail_view(request, slug):
    event = get_object_or_404(Event, slug=slug, is_published=True)

    # Ensure registered_count is up to date
    event.update_registered_count()

    # Check if user is registered (if logged in)
    is_registered = False
    if request.user.is_authenticated:
        is_registered = event.registrations.filter(user=request.user).exists()

    # Registration form
    form = EventRegistrationForm()

    context = {
        'event': event,
        'is_registered': is_registered,
        'form': form,
        'page_title': event.title,
        'now': timezone.now(),
    }

    return render(request, 'abea_app/event_detail.html', context)


# Manage News Views
@login_required
def manage_news_view(request):
    if not request.user.is_superuser and not request.user.is_staff:
        messages.error(request, _('Permission denied.'))
        return redirect('dashboard')

    # Get filter parameters
    category = request.GET.get('category', '')
    status = request.GET.get('status', '')
    search = request.GET.get('search', '')

    news_list = News.objects.all()

    # Apply filters
    if category:
        news_list = news_list.filter(category=category)
    if status == 'published':
        news_list = news_list.filter(is_published=True)
    elif status == 'draft':
        news_list = news_list.filter(is_published=False)
    if search:
        news_list = news_list.filter(title__icontains=search)

    news_list = news_list.order_by('-publish_date')

    context = {
        'news_list': news_list,
        'categories': News.NEWS_CATEGORY_CHOICES,
        'selected_category': category,
        'selected_status': status,
        'search_query': search,
    }
    return render(request, 'abea_app/admin/manage_news.html', context)


# News CRUD Views
@login_required
def add_news_view(request):
    if not request.user.is_superuser and not request.user.is_staff:
        messages.error(request, _('Permission denied.'))
        return redirect('dashboard')

    if request.method == 'POST':
        form = NewsForm(request.POST, request.FILES)
        if form.is_valid():
            news = form.save(commit=False)
            news.author = request.user
            news.save()
            messages.success(request, _('News article added successfully.'))
            return redirect('manage_news')
    else:
        form = NewsForm()

    return render(request, 'abea_app/admin/add_news.html', {'form': form})

@login_required
def edit_news_view(request, pk):
    if not request.user.is_superuser and not request.user.is_staff:
        messages.error(request, _('Permission denied.'))
        return redirect('dashboard')

    news = get_object_or_404(News, pk=pk)

    if request.method == 'POST':
        form = NewsForm(request.POST, request.FILES, instance=news)
        if form.is_valid():
            form.save()
            messages.success(request, _('News article updated successfully.'))
            return redirect('manage_news')
    else:
        form = NewsForm(instance=news)

    return render(request, 'abea_app/admin/edit_news.html', {'form': form, 'news': news})

@login_required
def delete_news_view(request, pk):
    if not request.user.is_superuser and not request.user.is_staff:
        messages.error(request, _('Permission denied.'))
        return redirect('dashboard')

    news = get_object_or_404(News, pk=pk)

    if request.method == 'POST':
        news.delete()
        messages.success(request, _('News article deleted successfully.'))
        return redirect('manage_news')

    return render(request, 'abea_app/admin/delete_news.html', {'news': news})

@login_required
@require_POST
def toggle_news_publish_view(request):
    if not request.user.is_superuser and not request.user.is_staff:
        return JsonResponse({'error': _('Permission denied.')}, status=403)

    try:
        data = json.loads(request.body)
        news_id = data.get('news_id')
        action = data.get('action')

        news = News.objects.get(id=news_id)

        if action == 'toggle_publish':
            news.is_published = not news.is_published
            news.save()
            return JsonResponse({
                'success': True,
                'is_published': news.is_published,
                'message': _('News article updated successfully.')
            })
        elif action == 'toggle_featured':
            news.is_featured = not news.is_featured
            news.save()
            return JsonResponse({
                'success': True,
                'is_featured': news.is_featured,
                'message': _('News article updated successfully.')
            })

    except News.DoesNotExist:
        return JsonResponse({'error': _('News article not found.')}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
def manage_gallery_view(request):
    if not request.user.is_superuser and not request.user.is_staff:
        messages.error(request, _('Permission denied.'))
        return redirect('dashboard')

    category = request.GET.get('category', '')
    search = request.GET.get('search', '')

    gallery_items = Gallery.objects.all()

    if category:
        gallery_items = gallery_items.filter(category=category)

    if search:
        gallery_items = gallery_items.filter(
            Q(title__icontains=search) |
            Q(description__icontains=search)
        )

    gallery_items = gallery_items.order_by('-uploaded_at')

    # Pagination
    paginator = Paginator(gallery_items, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    categories = Gallery.GALLERY_CATEGORY_CHOICES
    events = Event.objects.filter(is_published=True)

    context = {
        'gallery_items': page_obj,
        'categories': categories,
        'events': events,
        'selected_category': category,
        'search_query': search,
    }
    return render(request, 'abea_app/admin/manage_gallery.html', context)


@login_required
def add_gallery_view(request):
    if not request.user.is_superuser and not request.user.is_staff:
        messages.error(request, _('Permission denied.'))
        return redirect('dashboard')

    if request.method == 'POST':
        form = GalleryForm(request.POST, request.FILES)
        if form.is_valid():
            gallery_item = form.save(commit=False)
            gallery_item.uploaded_by = request.user
            gallery_item.save()
            messages.success(request, _('Gallery image added successfully.'))
            return redirect('manage_gallery')
    else:
        form = GalleryForm()

    return render(request, 'abea_app/admin/add_gallery.html', {'form': form})


@login_required
def edit_gallery_view(request, pk):
    if not request.user.is_superuser and not request.user.is_staff:
        messages.error(request, _('Permission denied.'))
        return redirect('dashboard')

    gallery_item = get_object_or_404(Gallery, pk=pk)

    if request.method == 'POST':
        form = GalleryForm(request.POST, request.FILES, instance=gallery_item)
        if form.is_valid():
            form.save()
            messages.success(request, _('Gallery image updated successfully.'))
            return redirect('manage_gallery')
    else:
        form = GalleryForm(instance=gallery_item)

    return render(request, 'abea_app/admin/edit_gallery.html', {'form': form, 'gallery_item': gallery_item})


@login_required
def delete_gallery_view(request, pk):
    if not request.user.is_superuser and not request.user.is_staff:
        messages.error(request, _('Permission denied.'))
        return redirect('dashboard')

    gallery_item = get_object_or_404(Gallery, pk=pk)

    if request.method == 'POST':
        gallery_item.delete()
        messages.success(request, _('Gallery image deleted successfully.'))
        return redirect('manage_gallery')

    return render(request, 'abea_app/admin/delete_gallery.html', {'gallery_item': gallery_item})


# Executive Members Management
@login_required
def manage_executive_members_view(request):
    if not request.user.is_superuser and not request.user.is_staff:
        messages.error(request, _('Permission denied.'))
        return redirect('dashboard')

    region = request.GET.get('region', '')
    position = request.GET.get('position', '')
    current = request.GET.get('current', '')

    members = ExecutiveMember.objects.all()

    if region:
        members = members.filter(region=region)
    if position:
        members = members.filter(position=position)
    if current == 'true':
        members = members.filter(is_current=True)
    elif current == 'false':
        members = members.filter(is_current=False)

    members = members.order_by('display_order', 'position')

    context = {
        'members': members,
        'regions': ExecutiveMember.REGION_CHOICES,
        'positions': ExecutiveMember.POSITION_CHOICES,
        'selected_region': region,
        'selected_position': position,
        'selected_current': current,
    }
    return render(request, 'abea_app/admin/manage_executive_members.html', context)


@login_required
def add_executive_member_view(request):
    if not request.user.is_superuser and not request.user.is_staff:
        messages.error(request, _('Permission denied.'))
        return redirect('dashboard')

    if request.method == 'POST':
        form = ExecutiveMemberForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _('Executive member added successfully.'))
            return redirect('manage_executive_members')
    else:
        form = ExecutiveMemberForm()

    return render(request, 'abea_app/admin/add_executive_member.html', {'form': form})


@login_required
def edit_executive_member_view(request, pk):
    if not request.user.is_superuser and not request.user.is_staff:
        messages.error(request, _('Permission denied.'))
        return redirect('dashboard')

    member = get_object_or_404(ExecutiveMember, pk=pk)

    if request.method == 'POST':
        form = ExecutiveMemberForm(request.POST, instance=member)
        if form.is_valid():
            form.save()
            messages.success(request, _('Executive member updated successfully.'))
            return redirect('manage_executive_members')
    else:
        form = ExecutiveMemberForm(instance=member)

    return render(request, 'abea_app/admin/edit_executive_member.html', {'form': form, 'member': member})


@login_required
def delete_executive_member_view(request, pk):
    if not request.user.is_superuser and not request.user.is_staff:
        messages.error(request, _('Permission denied.'))
        return redirect('dashboard')

    member = get_object_or_404(ExecutiveMember, pk=pk)

    if request.method == 'POST':
        member.delete()
        messages.success(request, _('Executive member deleted successfully.'))
        return redirect('manage_executive_members')

    return render(request, 'abea_app/admin/delete_executive_member.html', {'member': member})


# Partners Management
@login_required
def manage_partners_view(request):
    if not request.user.is_superuser and not request.user.is_staff:
        messages.error(request, _('Permission denied.'))
        return redirect('dashboard')

    partner_type = request.GET.get('type', '')
    active = request.GET.get('active', '')
    search = request.GET.get('search', '')

    partners = Partner.objects.all()

    if partner_type:
        partners = partners.filter(partner_type=partner_type)
    if active == 'true':
        partners = partners.filter(partnership_active=True)
    elif active == 'false':
        partners = partners.filter(partnership_active=False)
    if search:
        partners = partners.filter(
            Q(name__icontains=search) |
            Q(description__icontains=search) |
            Q(country__icontains=search)
        )

    partners = partners.order_by('display_order', 'name')

    context = {
        'partners': partners,
        'partner_types': Partner.PARTNER_TYPE_CHOICES,
        'selected_type': partner_type,
        'selected_active': active,
        'search_query': search,
    }
    return render(request, 'abea_app/admin/manage_partners.html', context)


@login_required
def add_partner_view(request):
    if not request.user.is_superuser and not request.user.is_staff:
        messages.error(request, _('Permission denied.'))
        return redirect('dashboard')

    if request.method == 'POST':
        form = PartnerForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, _('Partner added successfully.'))
            return redirect('manage_partners')
    else:
        form = PartnerForm()

    return render(request, 'abea_app/admin/add_partner.html', {'form': form})


@login_required
def edit_partner_view(request, pk):
    if not request.user.is_superuser and not request.user.is_staff:
        messages.error(request, _('Permission denied.'))
        return redirect('dashboard')

    partner = get_object_or_404(Partner, pk=pk)

    if request.method == 'POST':
        form = PartnerForm(request.POST, request.FILES, instance=partner)
        if form.is_valid():
            form.save()
            messages.success(request, _('Partner updated successfully.'))
            return redirect('manage_partners')
    else:
        form = PartnerForm(instance=partner)

    return render(request, 'abea_app/admin/edit_partner.html', {'form': form, 'partner': partner})


@login_required
def delete_partner_view(request, pk):
    if not request.user.is_superuser and not request.user.is_staff:
        messages.error(request, _('Permission denied.'))
        return redirect('dashboard')

    partner = get_object_or_404(Partner, pk=pk)

    if request.method == 'POST':
        partner.delete()
        messages.success(request, _('Partner deleted successfully.'))
        return redirect('manage_partners')

    return render(request, 'abea_app/admin/delete_partner.html', {'partner': partner})


# AJAX Actions
@login_required
def toggle_featured_gallery(request):
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        image_id = request.POST.get('image_id')
        try:
            image = Gallery.objects.get(id=image_id)
            image.is_featured = not image.is_featured
            image.save()
            return JsonResponse({
                'success': True,
                'is_featured': image.is_featured
            })
        except Gallery.DoesNotExist:
            return JsonResponse({'error': _('Image not found.')}, status=404)
    return JsonResponse({'error': _('Invalid request.')}, status=400)


@login_required
@require_POST
def toggle_current_executive(request):
    """AJAX view to toggle is_current status of executive member"""
    if not request.user.is_superuser and not request.user.is_staff:
        return JsonResponse({'error': _('Permission denied.')}, status=403)

    member_id = request.POST.get('member_id')
    try:
        member = ExecutiveMember.objects.get(id=member_id)
        member.is_current = not member.is_current
        member.save()
        return JsonResponse({
            'success': True,
            'is_current': member.is_current,
            'message': _('Member status updated successfully.')
        })
    except ExecutiveMember.DoesNotExist:
        return JsonResponse({'error': _('Executive member not found.')}, status=404)


@login_required
@require_POST
def toggle_partner_active(request):
    """AJAX view to toggle partnership_active status"""
    if not request.user.is_superuser and not request.user.is_staff:
        return JsonResponse({'error': _('Permission denied.')}, status=403)

    partner_id = request.POST.get('partner_id')
    try:
        partner = Partner.objects.get(id=partner_id)
        partner.partnership_active = not partner.partnership_active
        partner.save()
        return JsonResponse({
            'success': True,
            'is_active': partner.partnership_active,
            'message': _('Partner status updated successfully.')
        })
    except Partner.DoesNotExist:
        return JsonResponse({'error': _('Partner not found.')}, status=404)


# abea_app/views.py (add these API views)
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_http_methods
import json
import csv
from django.http import HttpResponse


@login_required
@require_POST
def toggle_attendance_view(request, pk):
    if not request.user.is_superuser and not request.user.is_staff:
        return JsonResponse({'error': _('Permission denied.')}, status=403)

    try:
        registration = EventRegistration.objects.get(pk=pk)
        registration.attended = not registration.attended
        if registration.attended and not registration.attendance_date:
            registration.attendance_date = timezone.now()
        elif not registration.attended:
            registration.attendance_date = None
        registration.save()

        return JsonResponse({
            'success': True,
            'attended': registration.attended,
            'attendance_date': registration.attendance_date.strftime(
                '%Y-%m-%d %H:%M:%S') if registration.attendance_date else None
        })
    except EventRegistration.DoesNotExist:
        return JsonResponse({'error': _('Registration not found.')}, status=404)


@login_required
@require_http_methods(["DELETE"])
def delete_registration_view(request, pk):
    if not request.user.is_superuser and not request.user.is_staff:
        return JsonResponse({'error': _('Permission denied.')}, status=403)

    try:
        registration = EventRegistration.objects.get(pk=pk)
        event = registration.event
        registration.delete()

        # Update event registration count
        event.registered_count = event.registrations.count()
        event.save()

        return JsonResponse({
            'success': True,
            'message': _('Registration deleted successfully.')
        })
    except EventRegistration.DoesNotExist:
        return JsonResponse({'error': _('Registration not found.')}, status=404)


@login_required
@require_POST
def toggle_event_publish_view(request, pk):
    if not request.user.is_superuser and not request.user.is_staff:
        return JsonResponse({'error': _('Permission denied.')}, status=403)

    try:
        event = Event.objects.get(pk=pk)
        event.is_published = not event.is_published
        event.save()

        return JsonResponse({
            'success': True,
            'is_published': event.is_published,
            'message': _('Event updated successfully.')
        })
    except Event.DoesNotExist:
        return JsonResponse({'error': _('Event not found.')}, status=404)


@login_required
def export_event_registrations_view(request, slug):
    if not request.user.is_superuser and not request.user.is_staff:
        messages.error(request, _('Permission denied.'))
        return redirect('dashboard')

    event = get_object_or_404(Event, slug=slug)
    registrations = event.registrations.all().order_by('-registration_date')
    format_type = request.GET.get('format', 'csv')

    if format_type == 'csv':
        response = HttpResponse(content_type='text/csv')
        response[
            'Content-Disposition'] = f'attachment; filename="{event.slug}_registrations_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'

        writer = csv.writer(response)
        writer.writerow([
            'Name', 'Email', 'Phone', 'Institution', 'Position',
            'Registration Date', 'Attendance', 'Attendance Date',
            'Payment Status', 'Transaction ID', 'Additional Notes'
        ])

        for reg in registrations:
            writer.writerow([
                reg.user.get_full_name() or reg.user.username,
                reg.user.email,
                reg.user.phone or '',
                reg.user.institution or '',
                reg.user.position or '',
                reg.registration_date.strftime('%Y-%m-%d %H:%M:%S'),
                'Yes' if reg.attended else 'No',
                reg.attendance_date.strftime('%Y-%m-%d %H:%M:%S') if reg.attendance_date else '',
                reg.get_payment_status_display(),
                reg.transaction_id or '',
                reg.additional_notes or ''
            ])

        return response
    else:
        messages.error(request, _('Export format not supported.'))
        return redirect('event_registrations', slug=slug)

#Membership Plans views
@login_required
def manage_membership_plans_view(request):
    """View for managing all membership plans"""
    if not request.user.is_superuser and not request.user.is_staff:
        messages.error(request, _('Permission denied.'))
        return redirect('dashboard')

    # Get filter parameters
    plan_type = request.GET.get('plan_type', '')
    status = request.GET.get('status', '')
    search = request.GET.get('search', '')

    plans = MembershipPlan.objects.all()

    # Apply filters
    if plan_type:
        plans = plans.filter(plan_type=plan_type)
    if status == 'active':
        plans = plans.filter(is_active=True)
    elif status == 'inactive':
        plans = plans.filter(is_active=False)
    if search:
        plans = plans.filter(name__icontains=search)

    plans = plans.order_by('display_order', 'price')

    context = {
        'plans': plans,
        'plan_type_choices': MembershipPlan.PLAN_TYPE_CHOICES,
        'selected_type': plan_type,
        'selected_status': status,
        'search_query': search,
    }

    return render(request, 'abea_app/admin/manage_membership_plans.html', context)


@login_required
def add_membership_plan_view(request):
    """View for adding a new membership plan"""
    if not request.user.is_superuser and not request.user.is_staff:
        messages.error(request, _('Permission denied.'))
        return redirect('dashboard')

    if request.method == 'POST':
        form = MembershipPlanForm(request.POST)
        if form.is_valid():
            plan = form.save()
            messages.success(request, _('Membership plan created successfully!'))
            return redirect('manage_membership_plans')
    else:
        form = MembershipPlanForm()

    return render(request, 'abea_app/admin/add_membership_plan.html', {'form': form})


@login_required
def edit_membership_plan_view(request, pk):
    """View for editing an existing membership plan"""
    if not request.user.is_superuser and not request.user.is_staff:
        messages.error(request, _('Permission denied.'))
        return redirect('dashboard')

    plan = get_object_or_404(MembershipPlan, pk=pk)

    if request.method == 'POST':
        form = MembershipPlanForm(request.POST, instance=plan)
        if form.is_valid():
            form.save()
            messages.success(request, _('Membership plan updated successfully!'))
            return redirect('manage_membership_plans')
    else:
        form = MembershipPlanForm(instance=plan)

    return render(request, 'abea_app/admin/edit_membership_plan.html', {'form': form, 'plan': plan})


@login_required
def delete_membership_plan_view(request, pk):
    """View for deleting a membership plan"""
    if not request.user.is_superuser and not request.user.is_staff:
        messages.error(request, _('Permission denied.'))
        return redirect('dashboard')

    plan = get_object_or_404(MembershipPlan, pk=pk)

    if request.method == 'POST':
        # Check if there are active subscriptions for this plan
        active_subscriptions = plan.subscription_set.filter(is_active=True).exists()
        if active_subscriptions:
            messages.error(request, _('Cannot delete plan with active subscriptions.'))
            return redirect('manage_membership_plans')

        plan_name = plan.name
        plan.delete()
        messages.success(request, _(f'Membership plan "{plan_name}" deleted successfully.'))
        return redirect('manage_membership_plans')

    return render(request, 'abea_app/admin/delete_membership_plan.html', {'plan': plan})


@login_required
def toggle_plan_active_view(request, pk):
    """API view to toggle plan active status"""
    if not request.user.is_superuser and not request.user.is_staff:
        return JsonResponse({'error': 'Permission denied'}, status=403)

    if request.method == 'POST':
        plan = get_object_or_404(MembershipPlan, pk=pk)
        plan.is_active = not plan.is_active
        plan.save()

        return JsonResponse({
            'success': True,
            'is_active': plan.is_active,
            'message': _('Plan activated successfully.') if plan.is_active else _('Plan deactivated successfully.')
        })

    return JsonResponse({'error': 'Invalid request'}, status=400)


@login_required
def toggle_plan_popular_view(request, pk):
    """API view to toggle plan popular status"""
    if not request.user.is_superuser and not request.user.is_staff:
        return JsonResponse({'error': 'Permission denied'}, status=403)

    if request.method == 'POST':
        plan = get_object_or_404(MembershipPlan, pk=pk)
        plan.is_popular = not plan.is_popular
        plan.save()

        return JsonResponse({
            'success': True,
            'is_popular': plan.is_popular,
            'message': _('Plan marked as popular.') if plan.is_popular else _('Plan removed from popular.')
        })

    return JsonResponse({'error': 'Invalid request'}, status=400)

def executive_members(request):
    exec_members = ExecutiveMember.objects.select_related('user').all()
    return render(request, 'abea_app/executive_members.html',
                  {
                      'exec_members': exec_members,
                  })


#MOBILE PAYMENTS INTEGRATION
# @login_required
# def initiate_payment_view(request, plan_id):
#     """Initiate payment for a membership plan"""
#
#     logger.info("LOGGED IN USER PHONE: %s", request.user.phone)
#
#     plan = get_object_or_404(MembershipPlan, id=plan_id, is_active=True)
#
#     # Check if user already has an active subscription
#     active_subscription = request.user.subscriptions.filter(
#         is_active=True,
#         end_date__gte=timezone.now().date(),
#         payment_status='COMPLETED'
#     ).first()
#
#     if active_subscription and active_subscription.membership_plan_id == plan_id:
#         messages.error(request, _('You already have an active subscription to this plan.'))
#         return redirect('membership')
#
#     # -------------------------
#     # GET REQUEST
#     # -------------------------
#     # if request.method == 'GET':
#     #     user_phone = request.user.phone
#     #     default_network = ''
#     #     account_name = ''
#     #
#     #     if user_phone:
#     #         # Clean the phone number
#     #         digits = ''.join(filter(str.isdigit, user_phone))
#     #
#     #         # Normalize Zambian numbers
#     #         if digits.startswith('+26'):
#     #             digits = digits[3:]
#     #         elif digits.startswith('26'):
#     #             digits = digits[2:]
#     #
#     #         # Use the API to detect the network for the user's phone
#     #         lookup_result = MoneyUnifyAPI.lookup_account(digits)
#     #
#     #         if lookup_result['success']:
#     #             default_network = lookup_result['operator']  # Will be MTN, AIRTEL, or ZAMTEL
#     #             account_name = lookup_result['account_name']
#     #             logger.info(f"Default network detected via API: {default_network} for phone {digits}")
#     #         else:
#     #             logger.warning(f"Could not detect network for default phone {digits}: {lookup_result.get('message')}")
#     #             # Fallback to hardcoded detection if API fails
#     #             if digits.startswith(('096', '097', '076', '077')):
#     #                 default_network = 'MTN'
#     #             elif digits.startswith(('095', '075')):
#     #                 default_network = 'AIRTEL'
#     #             elif digits.startswith(('094','055')):
#     #                 default_network = 'ZAMTEL'
#     if request.method == 'GET':
#         user_phone = request.user.phone
#         default_network = ''
#         account_name = ''
#
#         if user_phone:
#             # 1. Extract only digits for the API
#             digits_only = ''.join(filter(str.isdigit, user_phone))
#
#             # 2. (Optional) Keep a version with typical formatting characters
#             #    Adjust the allowed characters as needed.
#             allowed_chars = set('0123456789+-() ')
#             formatted_phone = ''.join(c for c in user_phone if c in allowed_chars)
#
#             # Normalize Zambian numbers (using digits_only)
#             if digits_only.startswith('+26'):
#                 digits_only = digits_only[3:]
#             elif digits_only.startswith('26'):
#                 digits_only = digits_only[2:]
#
#             # Use the API to detect the network for the user's phone
#             lookup_result = MoneyUnifyAPI.lookup_account(digits_only)
#
#             if lookup_result['success']:
#                 default_network = lookup_result['operator']  # MTN, AIRTEL, ZAMTEL
#                 account_name = lookup_result['account_name']
#                 logger.info(
#                     f"Default network detected via API: {default_network} for phone {digits_only} (original: {user_phone})")
#             else:
#                 logger.warning(
#                     f"Could not detect network for default phone {digits_only}: {lookup_result.get('message')} (original: {user_phone})")
#                 # Fallback to hardcoded detection if API fails
#                 if digits_only.startswith(('096', '097', '076', '077')):
#                     default_network = 'MTN'
#                 elif digits_only.startswith(('095', '075')):
#                     default_network = 'AIRTEL'
#                 elif digits_only.startswith(('094', '055')):
#                     default_network = 'ZAMTEL'
#
#         return render(request, 'abea_app/payment_method.html', {
#             'plan': plan,
#             'page_title': _('Select Payment Method'),
#             'active_subscription': active_subscription,
#             'user_phone': user_phone,
#             'default_network': default_network,
#             'account_name': account_name  # Pass account name to template
#         })
#
#     # -------------------------
#     # POST REQUEST
#     # -------------------------
#     if request.method == 'POST':
#         try:
#             payment_method = request.POST.get('payment_method', '').strip()
#
#             if not payment_method:
#                 messages.error(request, _('Please select a payment method.'))
#                 return redirect('initiate_payment', plan_id=plan_id)
#
#             # -------- Mobile Money Validation --------
#             if payment_method == 'MOBILE_MONEY':
#                 mobile_number = request.POST.get('mobile_number', '').strip()
#                 mobile_network = request.POST.get('mobile_network', '').strip()
#
#                 if not mobile_number:
#                     messages.error(request, _('Please enter your mobile number.'))
#                     return redirect('initiate_payment', plan_id=plan_id)
#
#                 digits = ''.join(filter(str.isdigit, mobile_number))
#
#                 if digits.startswith('260'):
#                     digits = digits[3:]
#
#                 if not (len(digits) == 10 and digits.startswith('0')):
#                     messages.error(
#                         request,
#                         _('Please enter a valid 10-digit Zambian mobile number starting with 0 (e.g. 0971234567).')
#                     )
#                     return redirect('initiate_payment', plan_id=plan_id)
#
#                 if not mobile_network:
#                     messages.error(request, _('Please select your mobile network.'))
#                     return redirect('initiate_payment', plan_id=plan_id)
#
#                 # overwrite cleaned number for downstream handlers
#                 request.POST = request.POST.copy()
#                 request.POST['mobile_number'] = digits
#
#             # -------- Payment Routing --------
#             if payment_method == 'MOBILE_MONEY':
#                 return handle_mobile_money_payment(request, plan)
#
#             elif payment_method == 'BANK_TRANSFER':
#                 return handle_bank_transfer_payment(request, plan)
#
#             elif payment_method in ('CREDIT_CARD', 'PAYPAL'):
#                 return handle_online_payment(request, plan, payment_method)
#
#             else:
#                 messages.error(request, _('Invalid payment method selected.'))
#                 return redirect('initiate_payment', plan_id=plan_id)
#
#         except Exception as e:
#             logger.exception("Payment initiation error")
#             messages.error(request, _('An unexpected error occurred. Please try again.'))
#             return redirect('initiate_payment', plan_id=plan_id)

@login_required
def initiate_payment_view(request, plan_id):
    """Initiate payment for a membership plan"""
    logger.info("LOGGED IN USER PHONE: %s", request.user.phone)

    plan = get_object_or_404(MembershipPlan, id=plan_id, is_active=True)

    # Check if user already has an active subscription
    active_subscription = request.user.subscriptions.filter(
        is_active=True,
        end_date__gte=timezone.now().date(),
        payment_status='COMPLETED'
    ).first()

    if active_subscription and active_subscription.membership_plan_id == plan_id:
        messages.error(request, _('You already have an active subscription to this plan.'))
        return redirect('membership')

    # -------------------------
    # GET REQUEST
    # -------------------------
    if request.method == 'GET':
        user_phone = request.user.phone
        default_network = ''
        account_name = ''

        if user_phone:
            # 1. Extract only digits for the API
            digits_only = ''.join(filter(str.isdigit, user_phone))

            # 2. (Optional) Keep a version with typical formatting characters
            allowed_chars = set('0123456789+-() ')
            formatted_phone = ''.join(c for c in user_phone if c in allowed_chars)

            # Normalize Zambian numbers (using digits_only)
            if digits_only.startswith('+26'):
                digits_only = digits_only[3:]
            elif digits_only.startswith('26'):
                digits_only = digits_only[2:]
            # Now digits_only is 10 digits starting with 0
            normalized_phone = digits_only

            # Use the API to detect the network for the user's phone
            lookup_result = MoneyUnifyAPI.lookup_account(digits_only)

            if lookup_result['success']:
                default_network = lookup_result['operator']  # MTN, AIRTEL, ZAMTEL
                account_name = lookup_result['account_name']
                logger.info(f"Default network detected via API: {default_network} for phone {digits_only} (original: {user_phone})")
            else:
                logger.warning(f"Could not detect network for default phone {digits_only}: {lookup_result.get('message')} (original: {user_phone})")
                # Fallback to hardcoded detection if API fails
                if digits_only.startswith(('096', '097', '076', '077')):
                    default_network = 'MTN'
                elif digits_only.startswith(('095', '075')):
                    default_network = 'AIRTEL'
                elif digits_only.startswith(('094','055')):
                    default_network = 'ZAMTEL'

        return render(request, 'abea_app/payment_method.html', {
            'plan': plan,
            'page_title': _('Select Payment Method'),
            'active_subscription': active_subscription,
            'user_phone': user_phone,
            'default_network': default_network,
            'account_name': account_name,
            'normalized_phone': normalized_phone
        })

    # -------------------------
    # POST REQUEST
    # -------------------------
    if request.method == 'POST':
        try:
            payment_method = request.POST.get('payment_method', '').strip()

            if not payment_method:
                messages.error(request, _('Please select a payment method.'))
                return redirect('initiate_payment', plan_id=plan_id)

            # -------- Mobile Money Validation --------
            if payment_method == 'MOBILE_MONEY':
                mobile_number = request.POST.get('mobile_number', '').strip()
                mobile_network = request.POST.get('mobile_network', '').strip()

                if not mobile_number:
                    messages.error(request, _('Please enter your mobile number.'))
                    return redirect('initiate_payment', plan_id=plan_id)

                # Extract only digits
                digits = ''.join(filter(str.isdigit, mobile_number))

                # --- FIXED NORMALIZATION ---
                # If number starts with 260 (country code without +) convert to local format
                if digits.startswith('260'):
                    digits = '0' + digits[3:]          # 260769566586 → 0769566586
                # If number already starts with 0 and has 10 digits, keep it
                elif digits.startswith('0') and len(digits) == 10:
                    pass
                # If number has 9 digits (e.g., after stripping +260 incorrectly), add leading zero
                elif len(digits) == 9 and digits.isdigit():
                    digits = '0' + digits
                # If number has 12 digits and starts with 260 (including leading zero?), handle
                elif len(digits) == 12 and digits.startswith('260'):
                    digits = '0' + digits[3:]
                # Otherwise, accept only if 10 digits starting with 0
                # (The validation below will catch invalid cases)

                # Final validation: must be 10 digits starting with 0
                if not (len(digits) == 10 and digits.startswith('0')):
                    messages.error(
                        request,
                        _('Please enter a valid 10-digit Zambian mobile number starting with 0 (e.g. 0971234567).')
                    )
                    return redirect('initiate_payment', plan_id=plan_id)

                if not mobile_network:
                    messages.error(request, _('Please select your mobile network.'))
                    return redirect('initiate_payment', plan_id=plan_id)

                # Overwrite cleaned number for downstream handlers
                request.POST = request.POST.copy()
                request.POST['mobile_number'] = digits

            # -------- Payment Routing --------
            if payment_method == 'MOBILE_MONEY':
                return handle_mobile_money_payment(request, plan)
            elif payment_method == 'BANK_TRANSFER':
                return handle_bank_transfer_payment(request, plan)
            elif payment_method in ('CREDIT_CARD', 'PAYPAL'):
                return handle_online_payment(request, plan, payment_method)
            else:
                messages.error(request, _('Invalid payment method selected.'))
                return redirect('initiate_payment', plan_id=plan_id)

        except Exception as e:
            logger.exception("Payment initiation error")
            messages.error(request, _('An unexpected error occurred. Please try again.'))
            return redirect('initiate_payment', plan_id=plan_id)


def handle_mobile_money_payment(request, plan):
    user = request.user
    phone = request.POST.get('mobile_number')
    selected_network = request.POST.get('mobile_network')

    # Clean the phone number for API
    clean_phone = phone
    if phone.startswith('0'):
        # API example shows "0769566586" without leading 0? Let's check
        # Based on the example, it seems they want "0769566586" with leading 0
        clean_phone = phone  # Keep the leading 0

    # 🔍 Lookup account via MoneyUnify
    lookup = MoneyUnifyAPI.lookup_account(clean_phone)

    if not lookup['success']:
        messages.error(
            request,
            _("We could not verify this mobile money number. Please check the number and try again.")
        )
        return redirect('initiate_payment', plan.id)

    detected_network = lookup['operator']  # MTN / AIRTEL / ZAMTEL (from API response)

    # ❌ Network mismatch
    if detected_network != selected_network:
        messages.error(
            request,
            _(
                f"The phone number you entered belongs to {detected_network}, "
                f"but you selected {selected_network}. Please correct this."
            )
        )
        return redirect('initiate_payment', plan.id)

    # 💰 Initiate payment
    payment = MoneyUnifyAPI.initiate_payment(clean_phone, plan.price)

    if not payment['success']:
        logger.error(
            f"Mobile money payment failed: User={user.id}, "
            f"Phone={phone}, Error={payment['message']}"
        )

        messages.error(
            request,
            _("Payment request failed. Please try again or use a different payment method.")
        )
        return redirect('initiate_payment', plan.id)

    # Store transaction in session for verification
    request.session['pending_transaction'] = {
        'transaction_id': payment['transaction_id'],
        'plan_id': plan.id,
        'amount': str(payment['amount']),
        'phone': phone,
        'network': detected_network
    }

    # Redirect to verification page instead of directly to membership
    messages.success(
        request,
        _("Payment request sent successfully. Please approve the payment on your phone, then click verify below.")
    )

    return redirect('verify_payment', transaction_id=payment['transaction_id'])


@login_required
def verify_payment_view(request, transaction_id):
    """Verify payment status and update subscription"""

    logger.info(f"Verifying payment for transaction: {transaction_id}")

    # Get pending transaction from session
    pending = request.session.get('pending_transaction', {})

    if pending.get('transaction_id') != transaction_id:
        logger.warning(f"Transaction ID mismatch: Session={pending.get('transaction_id')}, URL={transaction_id}")
        messages.error(request, _("Invalid transaction session. Please try again."))
        return redirect('membership')

    # First, check if subscription already exists for this transaction
    existing_subscriptions = Subscription.objects.filter(transaction_id=transaction_id)

    if existing_subscriptions.exists():
        logger.info(f"Found {existing_subscriptions.count()} existing subscription(s) for transaction {transaction_id}")

        if existing_subscriptions.count() > 1:
            # Multiple subscriptions found - this shouldn't happen, log and use the most recent
            logger.error(f"Multiple subscriptions found for transaction {transaction_id}. Using the most recent.")
            subscription = existing_subscriptions.order_by('-created_at').first()

            # Delete duplicates to clean up
            duplicates = existing_subscriptions.exclude(id=subscription.id)
            for dup in duplicates:
                logger.info(f"Deleting duplicate subscription ID: {dup.id}")
                dup.delete()
        else:
            subscription = existing_subscriptions.first()

        # Check if this subscription belongs to the current user
        if subscription.user != request.user:
            logger.error(
                f"Subscription {subscription.id} belongs to user {subscription.user.id}, not current user {request.user.id}")
            messages.error(request, _("This transaction belongs to another user."))
            return redirect('membership')

        # Redirect to success page if already completed
        if subscription.payment_status == 'COMPLETED':
            logger.info(f"Subscription {subscription.id} already completed for transaction {transaction_id}")
            messages.success(request, _("Payment already verified and membership activated."))
            return redirect('payment_success', transaction_id=transaction_id)

    # Verify payment with API
    verification = MoneyUnifyAPI.verify_payment(transaction_id)

    logger.info(f"Verification response: {verification}")

    if verification['success']:
        status = verification.get('status', '').lower()

        if status == 'successful':
            # Use atomic transaction to prevent race conditions
            try:
                with transaction.atomic():
                    # Check again if subscription exists within the transaction (with row lock)
                    subscription = Subscription.objects.select_for_update().filter(
                        transaction_id=transaction_id
                    ).first()

                    if subscription:
                        logger.info(f"Found existing subscription {subscription.id} within atomic transaction")

                        # Update existing subscription
                        if subscription.payment_status != 'COMPLETED':
                            subscription.payment_status = 'COMPLETED'
                            subscription.payment_date = timezone.now()
                            subscription.verified_at = timezone.now()
                            subscription.charges = verification.get('charges', subscription.charges)
                            subscription.save()

                            logger.info(f"Updated subscription {subscription.id} to COMPLETED")

                            # Update user membership status
                            request.user.membership_status = 'ACTIVE'
                            request.user.membership_type = subscription.membership_plan.plan_type
                            request.user.membership_date = subscription.start_date
                            request.user.membership_expiry = subscription.end_date
                            request.user.save()

                            logger.info(f"Updated user {request.user.id} membership status to ACTIVE")
                    else:
                        # Create new subscription
                        try:
                            plan = MembershipPlan.objects.get(id=pending['plan_id'])
                        except MembershipPlan.DoesNotExist:
                            logger.error(f"Membership plan not found: {pending.get('plan_id')}")
                            messages.error(request, _("Membership plan not found."))
                            return redirect('membership')

                        # Calculate end date based on plan duration
                        end_date = timezone.now().date() + timedelta(days=plan.duration_months * 30)

                        subscription = Subscription.objects.create(
                            user=request.user,
                            membership_plan=plan,
                            start_date=timezone.now().date(),
                            end_date=end_date,
                            amount_paid=verification['amount'],
                            payment_method='MOBILE_MONEY',
                            payment_status='COMPLETED',
                            transaction_id=transaction_id,
                            payment_date=timezone.now(),
                            mobile_number=pending['phone'],
                            mobile_network=pending['network'],
                            charges=verification.get('charges', 0),
                            reference_number=transaction_id,
                            verified_at=timezone.now()
                        )

                        logger.info(f"Created new subscription {subscription.id} for transaction {transaction_id}")

                        # Update user membership status
                        request.user.membership_status = 'ACTIVE'
                        request.user.membership_type = plan.plan_type
                        request.user.membership_date = timezone.now().date()
                        request.user.membership_expiry = end_date
                        request.user.save()

                        logger.info(f"Updated user {request.user.id} membership status to ACTIVE")

                    # Clear session after successful transaction
                    if 'pending_transaction' in request.session:
                        del request.session['pending_transaction']
                        logger.info("Cleared pending_transaction from session")

                    messages.success(request, _("Payment successful! Your membership has been activated."))
                    return redirect('payment_success', transaction_id=transaction_id)

            except Exception as e:
                logger.exception(f"Error in atomic transaction for transaction {transaction_id}: {str(e)}")
                messages.error(request, _("An error occurred while processing your payment. Please contact support."))
                return redirect('membership')

        elif status == 'initiated' or 'initiated' in verification.get('message', '').lower():
            # Payment still pending - wait for user to approve
            logger.info(f"Payment still pending for transaction: {transaction_id}")

            # Update session with latest status
            request.session['pending_transaction'] = pending

            return render(request, 'abea_app/payment_pending.html', {
                'transaction_id': transaction_id,
                'pending_transaction': pending,
                'message': _("Please check your phone and approve the payment, then click verify again.")
            })

        else:
            # Payment failed for other reasons
            logger.warning(f"Payment failed with status: {status}, message: {verification.get('message')}")

            # Update subscription status if it exists
            subscription = Subscription.objects.filter(transaction_id=transaction_id).first()
            if subscription:
                subscription.payment_status = 'FAILED'
                subscription.save()
                logger.info(f"Updated subscription {subscription.id} status to FAILED")

            messages.error(request, _(f"Payment failed: {verification.get('message', 'Unknown error')}"))
            return redirect('payment_failed', transaction_id=transaction_id)

    else:
        # API call failed
        logger.error(f"Payment verification API failed: {verification.get('message')}")
        messages.error(request, _(f"Payment verification failed: {verification.get('message', 'Unknown error')}"))
        return redirect('payment_failed', transaction_id=transaction_id)

@login_required
@require_POST
def lookup_mobile_network(request):
    phone = request.POST.get("phone")

    if not phone:
        return JsonResponse({"success": False, "error": "Phone number required"})

    # Clean phone number
    digits = ''.join(filter(str.isdigit, phone))
    if digits.startswith('260'):
        digits = digits[3:]

    # Use the API service
    result = MoneyUnifyAPI.lookup_account(digits)

    if result['success']:
        return JsonResponse({
            "success": True,
            "network": result['operator'],  # MTN / AIRTEL / ZAMTEL
            "account_name": result['account_name']
        })
    else:
        return JsonResponse({
            "success": False,
            "error": result.get('message', 'Lookup failed')
        })


def handle_bank_transfer_payment(request, plan):
    """Handle bank transfer payment"""
    # Create pending subscription for bank transfer
    with transaction.atomic():
        subscription = Subscription.objects.create(
            user=request.user,
            membership_plan=plan,
            start_date=timezone.now().date(),
            end_date=timezone.now().date() + timedelta(days=plan.duration_months * 30),
            amount_paid=plan.price,
            payment_method='BANK_TRANSFER',
            payment_status='PENDING',
        )

        # Generate unique reference number
        reference_number = f"ABEA{subscription.id:06d}{request.user.id:06d}"
        subscription.reference_number = reference_number
        subscription.save()

        # Log bank transfer initiation
        logger.info(f"Bank transfer payment initiated: User={request.user.id}, "
                    f"Subscription={subscription.id}, Reference={reference_number}")

        return JsonResponse({
            'success': True,
            'message': _('Please complete the bank transfer using the details provided.'),
            'subscription_id': subscription.id,
            'reference_number': reference_number,
            'bank_details': {
                'bank_name': 'Standard Chartered Bank',
                'account_name': 'Africa Biomedical Engineering Alliance',
                'account_number': '010 1234 5678 90',
                'swift_code': 'SCBLKENA',
                'branch': 'Nairobi West',
                'reference': reference_number,
                'amount': str(plan.price),
                'currency': plan.currency
            },
            'requires_proof_upload': True,
            'upload_url': f'/subscriptions/{subscription.id}/upload-proof/'
        })



# PESAPAL PAYMENTS
# def handle_online_payment(request, plan, payment_method):
#     """
#     Handle Pesapal (CREDIT_CARD or PAYPAL) payments.
#     Creates a pending subscription and redirects to Pesapal checkout.
#     """
#     user = request.user
#
#     # 1. Obtain access token
#     token = generate_access_token()
#     if not token:
#         logger.error("Pesapal auth failed for user %s", user.id)
#         messages.error(request, "Online payment service is temporarily unavailable. Please try again later.")
#         return redirect('initiate_payment', plan_id=plan.id)
#
#     # 2. Prepare unique merchant reference (UUID)
#     merchant_reference = str(uuid.uuid4())
#
#     # Build callback URL (where user returns after payment)
#     callback_url = request.build_absolute_uri(
#         reverse('pesapal_callback')  # name of the callback view
#     )
#
#     # Build order payload for Pesapal
#     order_payload = {
#         "id": merchant_reference,
#         "currency": plan.currency or "KES",
#         "amount": float(plan.price),
#         "description": f"Membership: {plan.name}",
#         "callback_url": callback_url,
#         "notification_id": settings.PESAPAL_IPN_ID,
#         "billing_address": {
#             "email_address": user.email,
#             "phone_number": getattr(user, 'phone', '') or '',  # adjust if your User has phone field
#             "country_code": "ZM",  # or get from user profile if available
#             "first_name": user.first_name or '',
#             "last_name": user.last_name or '',
#         }
#     }
#
#     # 3. Submit order to Pesapal
#     response_data = submit_order_request(token, order_payload)
#     if not response_data or 'redirect_url' not in response_data:
#         logger.error("Pesapal order submission failed: %s", response_data)
#         messages.error(request, "Failed to initiate online payment. Please try again.")
#         return redirect('initiate_payment', plan_id=plan.id)
#
#     redirect_url = response_data['redirect_url']
#     order_tracking_id = response_data.get('order_tracking_id')
#
#     # 4. Create a pending subscription record
#     today = date.today()
#     end_date_calc = today + timedelta(days=plan.duration_months * 30)  # approximate; adjust if you have exact logic
#
#     subscription = Subscription.objects.create(
#         user=user,
#         membership_plan=plan,
#         start_date=today,               # provisional; will be updated on confirmation if needed
#         end_date=end_date_calc,          # provisional
#         is_active=False,                 # not active until payment completed
#         auto_renew=True,                   # default, can be changed later
#         amount_paid=plan.price,
#         payment_method=payment_method,    # 'CREDIT_CARD' or 'PAYPAL'
#         payment_status='PENDING',
#         transaction_id=order_tracking_id, # Pesapal tracking ID
#         reference_number=merchant_reference,  # our internal reference
#         payment_date=None,
#         # mobile fields left blank for online payments
#         mobile_network='',
#         mobile_number='',
#         receipt_number='',
#         charges=0,
#         payment_notes='',
#         webhook_received=False,
#         webhook_payload={},
#         verified_at=None,
#     )
#
#     # 5. Redirect user to Pesapal checkout
#     return redirect(redirect_url)

def handle_online_payment(request, plan, payment_method):
    user = request.user
    mixin = PaymentRequestMixin()

    # 1. Generate unique merchant reference (our reference_number)
    merchant_reference = str(uuid.uuid4())

    # 2. Build order payload for Pesapal – use the same reference as the order id
    callback_url = request.build_absolute_uri(reverse('transaction_completed'))
    logger.info(f"handle_online_payment: merchant_ref={merchant_reference}, callback_url={callback_url}")

    order_info = {
        "id": merchant_reference,
        "currency": plan.currency or "KES",
        "amount": float(plan.price),
        "description": f"Membership: {plan.name}",
        "callback_url": callback_url,
        "notification_id": settings.PESAPAL_IPN_ID,
        "billing_address": {
            "email_address": user.email,
            "phone_number": getattr(user, 'phone', '') or '',
            "country_code": "ZM",
            "first_name": user.first_name or '',
            "last_name": user.last_name or '',
        }
    }
    logger.debug(f"Order info: {order_info}")

    try:
        response_data = mixin.submit_order_request(**order_info)
        logger.info(f"submit_order_request response: {response_data}")
    except Exception as e:
        logger.exception("Pesapal order submission failed")
        messages.error(request, "Failed to initiate online payment. Please try again.")
        return redirect('initiate_payment', plan_id=plan.id)

    if not response_data or 'redirect_url' not in response_data:
        logger.error("Pesapal order submission returned no redirect_url: %s", response_data)
        messages.error(request, "Failed to initiate online payment. Please try again.")
        return redirect('initiate_payment', plan_id=plan.id)

    redirect_url = response_data['redirect_url']
    order_tracking_id = response_data.get('order_tracking_id')
    logger.info(f"Pesapal redirect_url: {redirect_url}, tracking_id: {order_tracking_id}")

    # Create pending subscription
    today = date.today()
    end_date_calc = today + timedelta(days=plan.duration_months * 30)

    # Create subscription with reference_number = merchant_reference
    Subscription.objects.create(
        user=user,
        membership_plan=plan,
        start_date=today,
        end_date=end_date_calc,
        is_active=False,
        auto_renew=True,
        amount_paid=plan.price,
        payment_method=payment_method,
        payment_status='PENDING',
        transaction_id=order_tracking_id,
        reference_number=merchant_reference,
        payment_date=None,
        # ... other fields omitted for brevity ...
    )
    return redirect(redirect_url)


class CustomTransactionCompletedView(TransactionCompletedView):
    def get(self, request, *args, **kwargs):
        tracking_id = request.GET.get('OrderTrackingId')
        merchant_ref = request.GET.get('OrderMerchantReference')
        logger.info(f"CustomTransactionCompletedView.get: tracking_id={tracking_id}, merchant_ref={merchant_ref}")

        if tracking_id and merchant_ref:
            self.update_subscription_status(tracking_id, merchant_ref)

        response = super().get(request, *args, **kwargs)
        logger.info(f"super().get returned, status: {response.status_code}")
        return response

    def update_subscription_status(self, tracking_id, merchant_ref):
        logger.info(f"update_subscription_status: tracking_id={tracking_id}, merchant_ref={merchant_ref}")
        try:
            mixin = PaymentRequestMixin()
            token_data = mixin._get_token()
            logger.info(f"Token data: {token_data}")
            if not token_data or 'token' not in token_data:
                logger.error("Failed to obtain access token")
                return
            access_token = token_data["token"]

            headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}
            # Use the correct base URL setting
            # base_url = getattr(settings, 'PESAPAL_BASE_URL', 'https://cybqa.pesapal.com/pesapalv3')
            url = f"{settings.PESAPAL_BASE_URL}/Transactions/GetTransactionStatus?orderTrackingId={tracking_id}"
            logger.info(f"Calling Pesapal status URL: {url}")

            response = requests.get(url, headers=headers, timeout=10)
            logger.info(f"Status response status: {response.status_code}")
            logger.debug(f"Status response body: {response.text[:500]}")

            if response.status_code == 200:
                status_data = response.json()
                pesapal_status = status_data.get("payment_status_description", "").upper()
                logger.info(f"Pesapal status: {pesapal_status}")

                try:
                    subscription = Subscription.objects.get(reference_number=merchant_ref)
                    if pesapal_status == "COMPLETED":
                        subscription.payment_status = "COMPLETED"
                        subscription.is_active = True
                        subscription.payment_date = timezone.now()
                    elif pesapal_status in ["FAILED", "REVERSED"]:
                        subscription.payment_status = "FAILED"
                    subscription.webhook_received = True
                    subscription.webhook_payload = status_data
                    subscription.verified_at = timezone.now()
                    subscription.save()
                    logger.info(f"Subscription {subscription.id} updated to {subscription.payment_status}")
                except Subscription.DoesNotExist:
                    logger.warning(f"Subscription not found for ref {merchant_ref}")
            else:
                logger.error(f"Failed to get transaction status: {response.status_code}")
        except Exception as e:
            logger.exception("Error in update_subscription_status")

    def get_order_completion_url(self):
        merchant_ref = self.request.GET.get('OrderMerchantReference')
        logger.info(f"get_order_completion_url called with merchant_ref={merchant_ref}")

        if merchant_ref:
            try:
                url = reverse('payment_outcome', args=[merchant_ref])
                logger.info(f"Returning payment_outcome URL: {url}")
                return url
            except Exception as e:
                logger.exception("Failed to reverse payment_outcome")

        fallback = reverse(settings.PESAPAL_TRANSACTION_DEFAULT_REDIRECT_URL)
        logger.info(f"Using fallback URL: {fallback}")
        return fallback

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        merchant_ref = self.request.GET.get('OrderMerchantReference')
        if merchant_ref:
            try:
                subscription = Subscription.objects.get(reference_number=merchant_ref)
                context['amount'] = subscription.amount_paid
            except Subscription.DoesNotExist:
                pass
        return context


class PesapalCallbackView(APIView):
    def get(self, request):
        tracking_id = request.query_params.get('OrderTrackingId')
        merchant_ref = request.query_params.get('OrderMerchantReference')
        logger.info(f"PesapalCallbackView.get: tracking_id={tracking_id}, merchant_ref={merchant_ref}")

        if not tracking_id or not merchant_ref:
            return Response({"detail": "Missing parameters"}, status=400)

        status_response = self.check_payment_status(merchant_ref, tracking_id)
        logger.info(f"check_payment_status returned: {status_response}")

        try:
            subscription = Subscription.objects.get(reference_number=merchant_ref)
            pesapal_status = status_response.get("payment_status_description", "").upper()
            if pesapal_status == "COMPLETED":
                subscription.payment_status = "COMPLETED"
                subscription.is_active = True
                subscription.payment_date = timezone.now()
            elif pesapal_status in ["FAILED", "REVERSED"]:
                subscription.payment_status = "FAILED"
            subscription.webhook_payload = status_response
            subscription.webhook_received = True
            subscription.verified_at = timezone.now()
            subscription.save()
            logger.info(f"Subscription updated: {subscription.payment_status}")
        except Subscription.DoesNotExist:
            return Response({"detail": "Subscription not found"}, status=404)

        return Response({
            "status": status_response.get("payment_status_description"),
            "method": status_response.get("payment_method"),
            "message": status_response.get("message"),
            "merchant_reference": status_response.get("merchant_reference")
        })

    def check_payment_status(self, merchant_ref, tracking_id):
        mixin = PaymentRequestMixin()
        token_data = mixin._get_token()
        logger.info(f"check_payment_status token_data: {token_data}")
        if not token_data or 'token' not in token_data:
            logger.error("Failed to get token")
            return {
                "payment_status_description": "UNKNOWN",
                "payment_method": None,
                "message": "Token error",
                "merchant_reference": merchant_ref,
            }
        access_token = token_data["token"]
        headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}
        # base_url = getattr(settings, 'PESAPAL_BASE_URL', 'https://cybqa.pesapal.com/pesapalv3')
        url = f"{settings.PESAPAL_BASE_URL}/Transactions/GetTransactionStatus?orderTrackingId={tracking_id}"
        logger.info(f"check_payment_status URL: {url}")
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"check_payment_status failed: {response.status_code} - {response.text}")
                return {
                    "payment_status_description": "UNKNOWN",
                    "payment_method": None,
                    "message": f"HTTP {response.status_code}",
                    "merchant_reference": merchant_ref,
                }
        except Exception as e:
            logger.exception("Exception in check_payment_status")
            return {
                "payment_status_description": "UNKNOWN",
                "payment_method": None,
                "message": str(e),
                "merchant_reference": merchant_ref,
            }


@method_decorator(csrf_exempt, name='dispatch')
class PesapalIPNView(View):
    def post(self, request):
        try:
            payload = json.loads(request.body)
        except json.JSONDecodeError:
            logger.error("IPN: Invalid JSON")
            return HttpResponse("Invalid JSON", status=400)

        tracking_id = payload.get('order_tracking_id')
        merchant_ref = payload.get('merchant_reference')
        logger.info(f"IPN received: tracking_id={tracking_id}, merchant_ref={merchant_ref}, payload={payload}")

        if not tracking_id or not merchant_ref:
            return HttpResponse("Missing parameters", status=400)

        mixin = PaymentRequestMixin()
        token_data = mixin._get_token()
        logger.info(f"IPN token_data: {token_data}")
        if not token_data or 'token' not in token_data:
            return HttpResponse("Auth failed", status=500)
        access_token = token_data["token"]
        headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}
        # base_url = getattr(settings, 'PESAPAL_BASE_URL', 'https://cybqa.pesapal.com/pesapalv3')
        url = f"{settings.PESAPAL_BASE_URL}/Transactions/GetTransactionStatus?orderTrackingId={tracking_id}"
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            logger.error(f"IPN status check failed: {response.status_code}")
            return HttpResponse("Failed to verify status", status=500)

        status_data = response.json()
        pesapal_status = status_data.get("payment_status_description", "").upper()
        logger.info(f"IPN status_data: {status_data}")

        try:
            subscription = Subscription.objects.get(reference_number=merchant_ref)
            if pesapal_status == "COMPLETED" and subscription.payment_status != "COMPLETED":
                subscription.payment_status = "COMPLETED"
                subscription.is_active = True
                subscription.payment_date = timezone.now()
            elif pesapal_status in ["FAILED", "REVERSED"] and subscription.payment_status == "PENDING":
                subscription.payment_status = "FAILED"
            subscription.webhook_received = True
            subscription.webhook_payload = status_data
            subscription.verified_at = timezone.now()
            subscription.save()
            logger.info(f"IPN updated subscription {subscription.id} to {subscription.payment_status}")
        except Subscription.DoesNotExist:
            logger.warning(f"IPN: Subscription not found for ref {merchant_ref}")
            return HttpResponse("Subscription not found", status=404)

        return HttpResponse("OK", status=200)

# @csrf_exempt
# def pesapal_ipn(request):
#     """
#     Endpoint for Pesapal to send asynchronous payment notifications.
#     Expects GET parameters: tracking_id, merchant_reference
#     """
#     if request.method == 'GET':
#         tracking_id = request.GET.get('tracking_id')
#         merchant_reference = request.GET.get('merchant_reference')
#
#         if not tracking_id or not merchant_reference:
#             return HttpResponse("Missing parameters", status=400)
#
#         # Get current status from Pesapal
#         token = generate_access_token()
#         if not token:
#             logger.error("IPN: Failed to get access token")
#             return HttpResponse("Auth failed", status=500)
#
#         status_data = get_transaction_status(token, tracking_id, merchant_reference)
#         if not status_data:
#             logger.error("IPN: Failed to get transaction status for ref %s", merchant_reference)
#             return HttpResponse("Status check failed", status=500)
#
#         # Map Pesapal status to your internal status
#         pesapal_status = status_data.get('payment_status')  # e.g., 'COMPLETED', 'FAILED'
#         internal_status = 'PENDING'
#         if pesapal_status == 'COMPLETED':
#             internal_status = 'COMPLETED'
#         elif pesapal_status in ['FAILED', 'REVERSED']:
#             internal_status = 'FAILED'
#
#         # Update subscription
#         subscription = Subscription.objects.filter(reference_number=merchant_reference).first()
#         if subscription:
#             subscription.payment_status = internal_status
#             subscription.webhook_received = True
#             subscription.webhook_payload = status_data
#             if internal_status == 'COMPLETED':
#                 subscription.is_active = True
#                 subscription.payment_date = timezone.now()
#                 # Optionally set actual start/end based on payment date
#                 # subscription.start_date = date.today()
#                 # subscription.end_date = ... calculate from plan
#             subscription.save()
#             logger.info("IPN updated subscription %s to status %s", subscription.id, internal_status)
#         else:
#             logger.warning("IPN received for unknown merchant ref %s", merchant_reference)
#
#         return HttpResponse("OK", status=200)
#
#     return HttpResponse("Method not allowed", status=405)

# @csrf_exempt
# def pesapal_ipn(request):
#     logger.info(f"IPN received. Method: {request.method}")
#     logger.info(f"GET params: {request.GET}")
#     logger.info(f"POST params: {request.POST}")
#
#     # Try to extract parameters – use common possible names
#     tracking_id = (
#         request.GET.get('OrderTrackingId') or
#         request.GET.get('orderTrackingId') or
#         request.GET.get('pesapal_transaction_tracking_id') or
#         request.GET.get('tracking_id')
#     )
#     merchant_reference = (
#         request.GET.get('OrderMerchantReference') or
#         request.GET.get('orderMerchantReference') or
#         request.GET.get('pesapal_merchant_reference') or
#         request.GET.get('merchant_reference')
#     )
#
#     logger.info(f"Extracted: tracking_id={tracking_id}, merchant_ref={merchant_reference}")
#
#     if not tracking_id or not merchant_reference:
#         logger.error("Missing required parameters")
#         return HttpResponse("Missing parameters", status=400)
#
#     token = generate_access_token()
#     if not token:
#         logger.error("IPN: Failed to get access token")
#         return HttpResponse("Auth failed", status=500)
#
#     status_data = get_transaction_status(token, tracking_id, merchant_reference)
#     logger.info(f"Transaction status data: {status_data}")
#
#     if not status_data:
#         logger.error("IPN: Failed to get transaction status")
#         return HttpResponse("Status check failed", status=500)
#
#     # Determine internal status based on actual PesaPal response key
#     pesapal_status = status_data.get('payment_status')  # adjust key as needed
#     internal_status = 'PENDING'
#     if pesapal_status == 'COMPLETED':
#         internal_status = 'COMPLETED'
#     elif pesapal_status in ['FAILED', 'REVERSED']:
#         internal_status = 'FAILED'
#
#     subscription = Subscription.objects.filter(reference_number=merchant_reference).first()
#     if subscription:
#         subscription.payment_status = internal_status
#         subscription.webhook_received = True
#         subscription.webhook_payload = status_data
#         if internal_status == 'COMPLETED':
#             subscription.is_active = True
#             subscription.payment_date = timezone.now()
#         subscription.save()
#         logger.info(f"Subscription {subscription.id} updated to {internal_status}")
#     else:
#         logger.warning(f"No subscription found for ref {merchant_reference}")
#
#     return HttpResponse("OK", status=200)
#
# def pesapal_callback(request):
#     tracking_id = request.GET.get('OrderTrackingId')
#     merchant_reference = request.GET.get('OrderMerchantReference')
#     logger.info(f"Callback received: tracking_id={tracking_id}, merchant_ref={merchant_reference}")
#
#     if not tracking_id or not merchant_reference:
#         messages.error(request, "Invalid payment callback.")
#         return redirect('membership')
#
#     token = generate_access_token()
#     if not token:
#         logger.error("Failed to obtain access token in callback")
#         # Still redirect to outcome page without updating
#         return redirect('payment_outcome', merchant_reference=merchant_reference)
#
#     status_data = get_transaction_status(token, tracking_id, merchant_reference)
#     logger.info(f"Transaction status data: {status_data}")
#
#     if status_data:
#         pesapal_status = status_data.get('payment_status')  # adjust key if needed
#         logger.info(f"Pesapal status: {pesapal_status}")
#
#         subscription = Subscription.objects.filter(reference_number=merchant_reference).first()
#         if subscription:
#             # Only update if we have a definitive status
#             if pesapal_status == 'COMPLETED':
#                 if subscription.payment_status != 'COMPLETED':
#                     subscription.payment_status = 'COMPLETED'
#                     subscription.is_active = True
#                     subscription.payment_date = timezone.now()
#                     subscription.save()
#                     logger.info(f"Subscription {subscription.id} marked COMPLETED")
#             elif pesapal_status in ['FAILED', 'REVERSED']:
#                 if subscription.payment_status == 'PENDING':
#                     subscription.payment_status = 'FAILED'
#                     subscription.save()
#                     logger.info(f"Subscription {subscription.id} marked FAILED")
#             else:
#                 # For any other status (PENDING, etc.), do nothing – leave as PENDING
#                 logger.info(f"Status {pesapal_status} – leaving subscription as PENDING, will rely on IPN")
#         else:
#             logger.warning(f"No subscription found for ref {merchant_reference}")
#     else:
#         logger.error("get_transaction_status returned None – cannot determine status")
#
#     return redirect('payment_outcome', merchant_reference=merchant_reference)
#
#
def payment_outcome(request, merchant_reference):
    subscription = get_object_or_404(Subscription, reference_number=merchant_reference, user=request.user)
    return render(request, 'abea_app/payment_outcome.html', {
        'subscription': subscription
    })


#RUN ONCE
def register_ipn(request):
    """
    One-time endpoint to register your IPN URL with Pesapal.
    After successful registration, save the returned ipn_id in your .env file.
    """
    if request.method != 'GET':
        return HttpResponse("Method not allowed", status=405)

    token = generate_access_token()
    if not token:
        logger.error("Failed to generate access token for IPN registration")
        return HttpResponse("Failed to authenticate with Pesapal", status=500)

    url = f"{settings.PESAPAL_BASE_URL}/URLSetup/RegisterIPN"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {
        "url": "https://www.abea1.org/pesapal/ipn/",  # your public IPN endpoint
        "ipn_notification_type": "GET"
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        ipn_id = data.get('ipn_id')
        if ipn_id:
            logger.info(f"IPN registered successfully with ID: {ipn_id}")
            return HttpResponse(f"IPN registered. Your IPN ID is: {ipn_id}. Save this in your .env as PESAPAL_IPN_ID")
        else:
            logger.error(f"IPN registration response missing ipn_id: {data}")
            return HttpResponse(f"IPN registration failed: {data}", status=500)
    except requests.exceptions.RequestException as e:
        logger.exception("IPN registration request failed")
        return HttpResponse(f"IPN registration error: {str(e)}", status=500)



# django-pesapal
# reverse custom redirecturl
# class CustomTransactionCompletedView(TransactionCompletedView):
#     def get_order_completion_url(self):
#         return settings.PESAPAL_TRANSACTION_DEFAULT_REDIRECT_URL
#
#
# # Use this view in react to activate the payment and get pesapal redirect url
# class PaymentView(PaymentRequestMixin, APIView):
#
#     def get(self, request, *args, **kwargs):
#         # Extract from query parameters
#         amount = request.query_params.get('amount')
#         email = request.query_params.get('email')
#         phone_number = request.query_params.get('phone_number')
#         first_name = request.query_params.get('first_name')
#
#         # Validate required fields
#         if not all([amount, email, phone_number, first_name]):
#             return Response({"status": "error", "message": "Missing payment details."},
#                             status=status.HTTP_400_BAD_REQUEST)
#
#         iframe_url = self.get_pesapal_payment_iframe(
#             amount=amount,
#             email=email,
#             phone_number=phone_number,
#             first_name=first_name
#         )
#         return Response({"iframe_url": iframe_url}, status=status.HTTP_200_OK)
#
#     def get_pesapal_payment_iframe(self, amount, email, phone_number, first_name):
#         ipn = self.get_default_ipn()
#
#         merchant_ref = str(uuid.uuid4())  # your own ref to track this transaction
#
#         order_info = {
#             "id": str(uuid.uuid4()),
#             "currency": "UGX",
#             "amount": amount,
#             "description": "Restaurant Order Payment",
#             "callback_url": settings.PESAPAL_TRANSACTION_DEFAULT_REDIRECT_URL,
#             "notification_id": ipn,
#             "billing_address": {
#                 "first_name": first_name,
#                 "last_name": "",
#                 "email": email,
#                 "phone_number": phone_number
#             },
#         }
#         req = self.submit_order_request(**order_info)
#
#         # Save payment info
#         Payment.objects.create(
#             method="pending",
#             amount=int(float(amount)),
#             merchant="Development Work UG",
#             Merchant_Ref=merchant_ref,
#             Tracking_Id=req['order_tracking_id'],
#             Transaction_Date=now(),
#             status="processing"
#         )
#         iframe_src_url = req["redirect_url"]
#         return iframe_src_url
#
#
# # call back view
# class PesapalCallbackView(APIView):
#     def get(self, request):
#         tracking_id = request.query_params.get('OrderTrackingId')
#         merchant_ref = request.query_params.get('OrderMerchantReference')
#
#         if not tracking_id or not merchant_ref:
#             return Response({"detail": "Missing parameters"}, status=400)
#
#         # Check payment status via Pesapal API
#         status_response = self.check_payment_status(merchant_ref, tracking_id)
#
#         try:
#             payment = Payment.objects.get(Tracking_Id=tracking_id)
#             payment.status = status_response["payment_status_description"]
#             payment.method = status_response["payment_method"] or "unknown_method"
#             payment.Transaction_Date = status_response["created_date"] or now()
#             payment.save()
#         except Payment.DoesNotExist:
#             return Response({"detail": "Payment not found"}, status=404)
#
#         return Response({
#             "status": status_response["payment_status_description"],
#             "method": status_response["payment_method"],
#             "message": status_response["message"],
#             "merchant_reference": status_response["merchant_reference"]
#         })
#
#     # check status function
#     def check_payment_status(self, merchant_ref, tracking_id):
#         mixin = PaymentRequestMixin()
#         token_data = mixin._get_token()
#
#         # Extract just the token string
#         access_token = token_data["token"]
#
#         headers = {
#             "Authorization": f"Bearer {access_token}",
#             "Accept": "application/json",
#         }
#         url = f" https://cybqa.pesapal.com/pesapalv3/api/Transactions/GetTransactionStatus?orderTrackingId={tracking_id}"  # used for development
#
#         response = requests.get(url, headers=headers)
#         if response.status_code == 200:
#             return response.json()
#         else:
#             return {
#                 "status": "UNKNOWN",
#                 "payment_method": None,
#                 "payment_date": None,
#             }
# def handle_online_payment(request, plan, payment_method):
#     """
#     Handle credit card and PayPal payments.
#     Creates a pending subscription and redirects to the payment gateway.
#     """
#     user = request.user
#
#     # Create subscription with PENDING status
#     with transaction.atomic():
#         subscription = Subscription.objects.create(
#             user=user,
#             membership_plan=plan,
#             start_date=timezone.now().date(),
#             end_date=timezone.now().date() + timedelta(days=plan.duration_months * 30),
#             amount_paid=plan.price,
#             payment_method=payment_method,
#             payment_status='PENDING',
#             reference_number=f"SUB-{plan.id}-{user.id}-{int(timezone.now().timestamp())}"
#         )
#
#     logger.info(f"Online payment initiated: User={user.id}, Subscription={subscription.id}, Method={payment_method}")
#
#     # Store subscription ID in session for later retrieval
#     request.session['pending_subscription'] = {
#         'subscription_id': subscription.id,
#         'plan_id': plan.id,
#         'method': payment_method
#     }
#
#     # Redirect to the payment gateway processing view
#     return redirect('process_online_payment', subscription_id=subscription.id)

# def handle_online_payment(request, plan, payment_method):
#     """
#     Handle credit card and PayPal payments.
#     Creates a pending subscription and redirects to the actual payment gateway.
#     """
#     user = request.user
#
#     # Create subscription with PENDING status
#     with transaction.atomic():
#         subscription = Subscription.objects.create(
#             user=user,
#             membership_plan=plan,
#             start_date=timezone.now().date(),
#             end_date=timezone.now().date() + timedelta(days=plan.duration_months * 30),
#             amount_paid=plan.price,
#             payment_method=payment_method,
#             payment_status='PENDING',
#             reference_number=f"SUB-{plan.id}-{user.id}-{int(timezone.now().timestamp())}"
#         )
#
#     logger.info(f"Online payment initiated: User={user.id}, Subscription={subscription.id}, Method={payment_method}")
#
#     # Store subscription ID in session for later retrieval
#     request.session['pending_subscription'] = {
#         'subscription_id': subscription.id,
#         'plan_id': plan.id,
#         'method': payment_method
#     }
#
#     # Route to appropriate gateway
#     if payment_method == 'CREDIT_CARD':
#         gateway = StripeGateway()
#         result = gateway.create_checkout_session(subscription, request)
#
#         if result['success']:
#             # For Stripe, we can either redirect directly or return JSON for frontend
#             if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
#                 return JsonResponse({
#                     'success': True,
#                     'session_id': result['session_id'],
#                     'checkout_url': result['checkout_url']
#                 })
#             else:
#                 # Redirect to Stripe Checkout
#                 return redirect(result['checkout_url'])
#         else:
#             # Handle failure
#             subscription.payment_status = 'FAILED'
#             subscription.save()
#             messages.error(request, _(f"Payment gateway error: {result.get('error', 'Unknown error')}"))
#             return redirect('initiate_payment', plan.id)
#
#     elif payment_method == 'PAYPAL':
#         gateway = PayPalGateway()
#         result = gateway.create_payment(subscription, request)
#
#         if result['success']:
#             # Store payment ID in session for execution after return
#             request.session['paypal_payment_id'] = result['payment_id']
#             return redirect(result['approval_url'])
#         else:
#             subscription.payment_status = 'FAILED'
#             subscription.save()
#             messages.error(request, _(f"PayPal error: {result.get('error', 'Unknown error')}"))
#             return redirect('initiate_payment', plan.id)


# @login_required
# def process_online_payment(request, subscription_id):
#     """
#     Redirect the user to the appropriate payment gateway.
#     In production, this would integrate with Stripe/PayPal SDKs.
#     """
#     subscription = get_object_or_404(Subscription, id=subscription_id, user=request.user)
#
#     # Ensure subscription is still pending
#     if subscription.payment_status != 'PENDING':
#         messages.error(request, _("This payment has already been processed."))
#         return redirect('membership')
#
#     payment_method = subscription.payment_method
#
#     if payment_method == 'CREDIT_CARD':
#         # Simulate Stripe integration
#         # In production, create a Stripe PaymentIntent and return the client secret
#         # For now, we'll redirect to a simulated payment page
#         gateway_url = reverse('simulate_credit_card_payment', args=[subscription.id])
#     elif payment_method == 'PAYPAL':
#         # Simulate PayPal integration
#         gateway_url = reverse('simulate_paypal_payment', args=[subscription.id])
#     else:
#         messages.error(request, _("Invalid payment method."))
#         return redirect('membership')
#
#     return redirect(gateway_url)
#
#
# @login_required
# def simulate_credit_card_payment(request, subscription_id):
#     """Simulate a credit card payment page (for testing only)"""
#     subscription = get_object_or_404(Subscription, id=subscription_id, user=request.user)
#     return render(request, 'abea_app/simulate_credit_card.html', {
#         'subscription': subscription,
#         'page_title': _('Simulate Credit Card Payment')
#     })
#
# @login_required
# def simulate_paypal_payment(request, subscription_id):
#     """Simulate a PayPal payment page (for testing only)"""
#     subscription = get_object_or_404(Subscription, id=subscription_id, user=request.user)
#     return render(request, 'abea_app/simulate_paypal.html', {
#         'subscription': subscription,
#         'page_title': _('Simulate PayPal Payment')
#     })


# @login_required
# def payment_callback(request):
#     """
#     Handle return from payment gateway.
#     For Stripe: redirected after checkout (with session_id)
#     For PayPal: redirected after approval (with paymentId and PayerID)
#     """
#     subscription_id = request.GET.get('subscription_id')
#     status = request.GET.get('status')
#
#     # Handle Stripe callback
#     session_id = request.GET.get('session_id')
#     if session_id:
#         try:
#             # Retrieve the session from Stripe to verify
#             stripe_session = stripe.checkout.Session.retrieve(session_id)
#             subscription_id = stripe_session.client_reference_id
#             status = 'success' if stripe_session.payment_status == 'paid' else 'failure'
#         except Exception as e:
#             logger.error(f"Error retrieving Stripe session: {str(e)}")
#
#     # Handle PayPal callback
#     payment_id = request.GET.get('paymentId')
#     payer_id = request.GET.get('PayerID')
#     if payment_id and payer_id:
#         gateway = PayPalGateway()
#         result = gateway.execute_payment(payment_id, payer_id)
#         if result['success']:
#             status = 'success'
#             # Get subscription_id from custom field
#             subscription_id = result['payment'].transactions[0].custom
#         else:
#             status = 'failure'
#
#     if not subscription_id or not status:
#         messages.error(request, _("Invalid payment callback."))
#         return redirect('membership')
#
#     try:
#         subscription = Subscription.objects.get(id=subscription_id, user=request.user)
#     except Subscription.DoesNotExist:
#         messages.error(request, _("Subscription not found."))
#         return redirect('membership')
#
#     if status == 'success':
#         subscription.payment_status = 'COMPLETED'
#         if session_id:
#             subscription.transaction_id = session_id
#         elif payment_id:
#             subscription.transaction_id = payment_id
#         else:
#             subscription.transaction_id = f"TXN-{int(timezone.now().timestamp())}"
#         subscription.payment_date = timezone.now()
#         subscription.verified_at = timezone.now()
#         subscription.save()
#
#         # Update user membership
#         user = request.user
#         user.membership_status = 'ACTIVE'
#         user.membership_type = subscription.membership_plan.plan_type
#         user.membership_date = subscription.start_date
#         user.membership_expiry = subscription.end_date
#         user.save()
#
#         messages.success(request, _("Payment successful! Your membership has been activated."))
#         return redirect('payment_success', transaction_id=subscription.transaction_id)
#     else:
#         subscription.payment_status = 'FAILED'
#         subscription.save()
#
#         txn_id = subscription.transaction_id or f"FAILED-{subscription.id}"
#         messages.error(request, _("Payment failed. Please try again."))
#         return redirect('payment_failed', transaction_id=txn_id)
#
#
# @csrf_exempt
# def stripe_webhook(request):
#     """Handle Stripe webhook events"""
#     payload = request.body
#     sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
#
#     event = StripeGateway.verify_webhook(payload, sig_header)
#
#     if not event:
#         return HttpResponse(status=400)
#
#     # Handle the event
#     if event['type'] == 'checkout.session.completed':
#         session = event['data']['object']
#         # Payment successful - you can update subscription here
#         subscription_id = session.get('client_reference_id')
#         try:
#             subscription = Subscription.objects.get(id=subscription_id)
#             if subscription.payment_status == 'PENDING':
#                 subscription.payment_status = 'COMPLETED'
#                 subscription.transaction_id = session['id']
#                 subscription.payment_date = timezone.now()
#                 subscription.verified_at = timezone.now()
#                 subscription.save()
#
#                 # Update user
#                 user = subscription.user
#                 user.membership_status = 'ACTIVE'
#                 user.membership_type = subscription.membership_plan.plan_type
#                 user.membership_date = subscription.start_date
#                 user.membership_expiry = subscription.end_date
#                 user.save()
#         except Subscription.DoesNotExist:
#             pass
#
#     return HttpResponse(status=200)

# @login_required
# def payment_callback(request):
#     """
#     Handle return from payment gateway.
#     Expects GET parameters: subscription_id, status (success/failure), transaction_id
#     """
#     subscription_id = request.GET.get('subscription_id')
#     status = request.GET.get('status')
#     transaction_id = request.GET.get('transaction_id', '')
#
#     if not subscription_id or not status:
#         messages.error(request, _("Invalid payment callback."))
#         return redirect('membership')
#
#     try:
#         subscription = Subscription.objects.get(id=subscription_id, user=request.user)
#     except Subscription.DoesNotExist:
#         messages.error(request, _("Subscription not found."))
#         return redirect('membership')
#
#     if status == 'success':
#         subscription.payment_status = 'COMPLETED'
#         subscription.transaction_id = transaction_id or f"TXN-{int(timezone.now().timestamp())}"
#         subscription.payment_date = timezone.now()
#         subscription.verified_at = timezone.now()
#         subscription.save()
#
#         # Update user membership
#         user = request.user
#         user.membership_status = 'ACTIVE'
#         user.membership_type = subscription.membership_plan.plan_type
#         user.membership_date = subscription.start_date
#         user.membership_expiry = subscription.end_date
#         user.save()
#
#         messages.success(request, _("Payment successful! Your membership has been activated."))
#         return redirect('payment_success', transaction_id=subscription.transaction_id)
#     else:
#         subscription.payment_status = 'FAILED'
#         subscription.save()
#
#         # Ensure we have a non-empty transaction ID for the failure page
#         txn_id = subscription.transaction_id or f"FAILED-{subscription.id}"
#
#         messages.error(request, _("Payment failed. Please try again."))
#         return redirect('payment_failed', transaction_id=txn_id)


# def format_phone_number(phone_number):
#     """Format phone number to include country code"""
#     # Remove all non-digit characters
#     digits = ''.join(filter(str.isdigit, phone_number))
#
#     # If starts with 0, replace with 260 (Zambia country code)
#     if digits.startswith('0'):
#         digits = '260' + digits[1:]
#
#     # If doesn't start with country code, add it
#     if not digits.startswith('260'):
#         digits = '260' + digits
#
#     return digits


# def is_valid_phone_number(phone_number):
#     """Validate Zambian phone number format"""
#     digits = ''.join(filter(str.isdigit, phone_number))
#
#     # Check if it's a valid Zambian mobile number
#     if len(digits) != 12 or not digits.startswith('260'):
#         return False
#
#     # Check if the next 2 digits are valid mobile prefixes
#     prefix = digits[3:5]
#     valid_prefixes = ['75', '76', '77', '95', '96', '97']
#
#     return prefix in valid_prefixes


# @login_required
# def check_payment_status(request, subscription_id):
#     """Check and update payment status with retry logic"""
#     subscription = get_object_or_404(Subscription, id=subscription_id, user=request.user)
#
#     # If already completed, return success
#     if subscription.payment_status == 'COMPLETED':
#         return JsonResponse({
#             'success': True,
#             'status': 'completed',
#             'message': _('Payment already completed.'),
#             'subscription': {
#                 'id': subscription.id,
#                 'plan_name': subscription.membership_plan.name,
#                 'end_date': subscription.end_date.strftime('%Y-%m-%d'),
#                 'receipt_number': subscription.receipt_number
#             }
#         })
#
#     # Handle different payment methods
#     if subscription.payment_method == 'MOBILE_MONEY' and subscription.transaction_id:
#         return check_mobile_money_payment(subscription)
#     elif subscription.payment_method == 'BANK_TRANSFER':
#         return check_bank_transfer_status(subscription)
#     elif subscription.payment_method in ['CREDIT_CARD', 'PAYPAL']:
#         return check_online_payment_status(subscription)
#
#     return JsonResponse({
#         'success': False,
#         'message': _('Unable to check payment status for this payment method.')
#     })


# def check_mobile_money_payment(subscription):
#     """Check mobile money payment status with retry"""
#     max_retries = 5
#     retry_delay = 3  # seconds
#
#     for attempt in range(max_retries):
#         verification_result = MobileMoneyAPI.verify_payment(subscription.transaction_id)
#
#         if verification_result['success']:
#             if verification_result['status'] == 'successful':
#                 # Payment successful
#                 with transaction.atomic():
#                     subscription.payment_status = 'COMPLETED'
#                     subscription.payment_date = timezone.now()
#                     subscription.is_active = True
#                     subscription.charges = Decimal(verification_result.get('charges', 0))
#                     subscription.receipt_number = f'REC-{timezone.now().strftime("%Y%m%d")}-{subscription.id:06d}'
#                     subscription.save()
#
#                 logger.info(f"Mobile money payment completed: Subscription={subscription.id}, "
#                             f"Transaction={subscription.transaction_id}")
#
#                 return JsonResponse({
#                     'success': True,
#                     'status': 'completed',
#                     'message': _('Payment completed successfully! Your membership is now active.'),
#                     'subscription': {
#                         'id': subscription.id,
#                         'plan_name': subscription.membership_plan.name,
#                         'end_date': subscription.end_date.strftime('%Y-%m-%d'),
#                         'receipt_number': subscription.receipt_number
#                     }
#                 })
#             elif verification_result['status'] in ['pending', 'initiated']:
#                 # Still pending
#                 if attempt < max_retries - 1:
#                     time.sleep(retry_delay)
#                     continue
#                 else:
#                     return JsonResponse({
#                         'success': False,
#                         'status': 'pending',
#                         'message': _('Payment is still pending. Please check your phone and approve the payment.'),
#                         'retry_count': attempt + 1
#                     })
#             else:
#                 # Failed or cancelled
#                 subscription.payment_status = 'FAILED'
#                 subscription.save()
#
#                 return JsonResponse({
#                     'success': False,
#                     'status': 'failed',
#                     'message': _('Payment failed or was cancelled. Please try again.')
#                 })
#         else:
#             # API error
#             if attempt < max_retries - 1:
#                 time.sleep(retry_delay)
#                 continue
#             else:
#                 return JsonResponse({
#                     'success': False,
#                     'message': verification_result.get('message', _('Payment verification failed.')),
#                     'retry_count': attempt + 1
#                 })
#
#     return JsonResponse({
#         'success': False,
#         'status': 'timeout',
#         'message': _('Payment verification timed out. Please check your payment status manually.')
#     })


def check_bank_transfer_status(subscription):
    """Check bank transfer status (manual verification)"""
    # For bank transfers, admin needs to manually verify
    # This just returns the current status
    return JsonResponse({
        'success': True,
        'status': subscription.payment_status.lower(),
        'message': _('Bank transfer pending verification. Please upload proof of payment.'),
        'requires_proof': subscription.payment_status == 'PENDING',
        'upload_url': f'/subscriptions/{subscription.id}/upload-proof/'
    })


def check_online_payment_status(subscription):
    """Check online payment status"""
    # In production, integrate with payment gateway webhooks
    # For now, return current status
    return JsonResponse({
        'success': True,
        'status': subscription.payment_status.lower(),
        'message': _('Payment status: ') + subscription.get_payment_status_display(),
        'gateway_name': subscription.payment_method.replace('_', ' ').title()
    })


@login_required
def upload_payment_proof(request, subscription_id):
    """Handle payment proof upload for bank transfers"""
    subscription = get_object_or_404(Subscription, id=subscription_id, user=request.user)

    if subscription.payment_method != 'BANK_TRANSFER':
        return JsonResponse({
            'success': False,
            'message': _('Proof upload only available for bank transfers.')
        })

    if request.method == 'POST' and request.FILES.get('proof_file'):
        try:
            proof_file = request.FILES['proof_file']
            notes = request.POST.get('notes', '')

            # Validate file type and size
            allowed_types = ['image/jpeg', 'image/png', 'image/jpg', 'application/pdf']
            max_size = 5 * 1024 * 1024  # 5MB

            if proof_file.content_type not in allowed_types:
                return JsonResponse({
                    'success': False,
                    'message': _('Invalid file type. Please upload JPEG, PNG, or PDF files.')
                })

            if proof_file.size > max_size:
                return JsonResponse({
                    'success': False,
                    'message': _('File too large. Maximum size is 5MB.')
                })

            # Save the file (you need to implement file storage)
            # For now, just update the subscription
            subscription.payment_notes = f"Proof uploaded: {proof_file.name}\n{notes}"
            subscription.payment_status = 'PENDING_VERIFICATION'
            subscription.save()

            # Notify admin about new proof
            # send_admin_notification(subscription, 'proof_uploaded')

            logger.info(f"Payment proof uploaded: Subscription={subscription.id}, "
                        f"File={proof_file.name}")

            return JsonResponse({
                'success': True,
                'message': _('Proof uploaded successfully. Our team will verify your payment within 24-48 hours.'),
                'subscription_id': subscription.id
            })

        except Exception as e:
            logger.error(f"Proof upload error: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False,
                'message': _('Error uploading file. Please try again.')
            })

    return JsonResponse({
        'success': False,
        'message': _('Please select a file to upload.')
    })


@csrf_exempt
def payment_webhook(request, gateway):
    """Handle payment gateway webhooks"""
    if request.method != 'POST':
        return HttpResponse(status=405)

    try:
        payload = json.loads(request.body)

        if gateway == 'stripe':
            return handle_stripe_webhook(payload)
        elif gateway == 'paypal':
            return handle_paypal_webhook(payload)
        elif gateway == 'mobile_money':
            return handle_mobile_money_webhook(payload)

        return HttpResponse(status=400)

    except json.JSONDecodeError:
        return HttpResponse(status=400)
    except Exception as e:
        logger.error(f"Webhook error: {str(e)}", exc_info=True)
        return HttpResponse(status=500)


def handle_stripe_webhook(payload):
    """Handle Stripe webhook events"""
    # Implement Stripe webhook handling
    # Check event type and update subscription accordingly
    return HttpResponse(status=200)


def handle_paypal_webhook(payload):
    """Handle PayPal webhook events"""
    # Implement PayPal webhook handling
    return HttpResponse(status=200)


def handle_mobile_money_webhook(payload):
    """Handle mobile money webhook events (if supported by MoneyUnify)"""
    # Check if MoneyUnify supports webhooks
    # If yes, implement webhook handling here
    return HttpResponse(status=200)

# @login_required
# def verify_payment_view(request, subscription_id):
#     """Verify if a payment was completed"""
#     subscription = get_object_or_404(Subscription, id=subscription_id, user=request.user)
#
#     if subscription.payment_method == 'MOBILE_MONEY' and subscription.transaction_id:
#         # Verify payment with API
#         verification_result = MobileMoneyAPI.verify_payment(subscription.transaction_id)
#
#         if verification_result['success']:
#             if verification_result['status'] == 'successful':
#                 # Payment successful
#                 subscription.payment_status = 'COMPLETED'
#                 subscription.payment_date = timezone.now()
#                 subscription.is_active = True
#
#                 # Generate receipt number
#                 subscription.receipt_number = f'REC-{timezone.now().strftime("%Y%m%d")}-{subscription.id:06d}'
#                 subscription.save()
#
#                 return JsonResponse({
#                     'success': True,
#                     'message': _('Payment verified successfully! Your membership is now active.'),
#                     'subscription': {
#                         'id': subscription.id,
#                         'plan': subscription.membership_plan.name,
#                         'end_date': subscription.end_date.strftime('%Y-%m-%d'),
#                         'receipt_number': subscription.receipt_number
#                     }
#                 })
#             else:
#                 # Payment not yet completed
#                 return JsonResponse({
#                     'success': False,
#                     'message': _('Payment is still pending. Please approve the payment on your phone.'),
#                     'status': 'pending'
#                 })
#         else:
#             return JsonResponse({
#                 'success': False,
#                 'message': verification_result.get('message', _('Payment verification failed.'))
#             })
#
#     return JsonResponse({
#         'success': False,
#         'message': _('No mobile money payment to verify.')
#     })


# @login_required
# def check_payment_status(request, subscription_id):
#     """Check payment status with retry logic"""
#     subscription = get_object_or_404(Subscription, id=subscription_id, user=request.user)
#
#     if subscription.payment_status == 'COMPLETED':
#         return JsonResponse({
#             'success': True,
#             'status': 'completed',
#             'message': _('Payment already completed.')
#         })
#
#     # Try verifying multiple times for mobile money
#     if subscription.payment_method == 'MOBILE_MONEY' and subscription.transaction_id:
#         max_retries = 3
#         for attempt in range(max_retries):
#             verification_result = MobileMoneyAPI.verify_payment(subscription.transaction_id)
#
#             if verification_result['success']:
#                 if verification_result['status'] == 'successful':
#                     # Update subscription
#                     subscription.payment_status = 'COMPLETED'
#                     subscription.payment_date = timezone.now()
#                     subscription.is_active = True
#                     subscription.receipt_number = f'REC-{timezone.now().strftime("%Y%m%d")}-{subscription.id:06d}'
#                     subscription.save()
#
#                     return JsonResponse({
#                         'success': True,
#                         'status': 'completed',
#                         'message': _('Payment completed successfully!')
#                     })
#                 elif attempt < max_retries - 1:
#                     # Wait before next retry
#                     time.sleep(2)
#                     continue
#                 else:
#                     return JsonResponse({
#                         'success': False,
#                         'status': 'pending',
#                         'message': _('Payment is still pending. Please check your phone.')
#                     })
#             else:
#                 return JsonResponse({
#                     'success': False,
#                     'message': verification_result.get('message', _('Verification failed.'))
#                 })
#
#     return JsonResponse({
#         'success': False,
#         'message': _('Unable to check payment status.')
#     })



# @login_required
# def payment_success_view(request, transaction_id):
#     """Show payment success page"""
#
#     # Try to find the subscription by transaction_id
#     try:
#         subscription = Subscription.objects.get(transaction_id=transaction_id, user=request.user)
#         return render(request, 'abea_app/payment_success.html', {
#             'subscription': subscription,
#             'page_title': _('Payment Successful')
#         })
#     except Subscription.DoesNotExist:
#         # Check if it's a pending transaction
#         pending = request.session.get('pending_transaction', {})
#         if pending.get('transaction_id') == transaction_id:
#             # Transaction is still pending - redirect to verification
#             messages.info(request, _('Please verify your payment status.'))
#             return redirect('verify_payment', transaction_id=transaction_id)
#
#         # No transaction found
#         messages.error(request, _('Transaction not found.'))
#         return redirect('membership')


@login_required
def payment_success_view(request, transaction_id):
    """Show payment success page"""

    logger.info(f"Payment success view called with transaction_id: {transaction_id}")

    # Try to find the subscription by transaction_id
    subscriptions = Subscription.objects.filter(transaction_id=transaction_id, user=request.user)

    if subscriptions.exists():
        if subscriptions.count() > 1:
            # Multiple subscriptions found - log and use the most recent
            logger.error(f"Multiple subscriptions found for transaction {transaction_id}. Using the most recent.")
            subscription = subscriptions.order_by('-created_at').first()

            # Delete duplicates to clean up
            duplicates = subscriptions.exclude(id=subscription.id)
            for dup in duplicates:
                logger.info(f"Deleting duplicate subscription ID: {dup.id}")
                dup.delete()
        else:
            subscription = subscriptions.first()

        return render(request, 'abea_app/payment_success.html', {
            'subscription': subscription,
            'page_title': _('Payment Successful')
        })

    # Check if it's a pending transaction
    pending = request.session.get('pending_transaction', {})
    if pending.get('transaction_id') == transaction_id:
        # Transaction is still pending - redirect to verification
        logger.info(f"Transaction still pending: {transaction_id}")
        messages.info(request, _('Please verify your payment status.'))
        return redirect('verify_payment', transaction_id=transaction_id)

    # No transaction found
    logger.error(f"No transaction found for transaction_id: {transaction_id}")
    messages.error(request, _('Transaction not found.'))
    return redirect('membership')


# @login_required
# def payment_failed_view(request, subscription_id):
#     """Show payment failure page"""
#     subscription = get_object_or_404(Subscription, id=subscription_id, user=request.user)
#
#     return render(request, 'abea_app/payment_failed.html', {
#         'subscription': subscription,
#         'page_title': _('Payment Failed')
#     })

@login_required
def payment_failed_view(request, transaction_id):
    """Show payment failure page"""

    # Try to find the subscription by transaction_id
    subscription = None
    pending = request.session.get('pending_transaction', {})

    # First check if we have a pending transaction with this ID
    if pending.get('transaction_id') == transaction_id:
        # We don't have a subscription yet, but we can show the plan details
        try:
            plan = MembershipPlan.objects.get(id=pending['plan_id'])
            return render(request, 'abea_app/payment_failed.html', {
                'transaction_id': transaction_id,
                'plan': plan,
                'phone': pending.get('phone'),
                'network': pending.get('network'),
                'amount': pending.get('amount'),
                'page_title': _('Payment Failed')
            })
        except MembershipPlan.DoesNotExist:
            pass

    # If not found in session, try to find by subscription transaction_id
    try:
        subscription = Subscription.objects.get(transaction_id=transaction_id, user=request.user)
        return render(request, 'abea_app/payment_failed.html', {
            'subscription': subscription,
            'page_title': _('Payment Failed')
        })
    except Subscription.DoesNotExist:
        # No subscription found with this transaction_id
        return render(request, 'abea_app/payment_failed.html', {
            'transaction_id': transaction_id,
            'page_title': _('Payment Failed'),
            'error_message': _('Transaction not found. Please contact support.')
        })


@user_passes_test(is_superuser)
def admin_update_subscription_view(request, subscription_id):
    """Admin view to manually update subscription status"""
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'message': _('Permission denied.')}, status=403)

    subscription = get_object_or_404(Subscription, id=subscription_id)

    if request.method == 'POST':
        try:
            action = request.POST.get('action')
            notes = request.POST.get('notes', '')

            with transaction.atomic():
                if action == 'approve':
                    subscription.payment_status = 'COMPLETED'
                    subscription.payment_date = timezone.now()
                    subscription.is_active = True
                    subscription.receipt_number = f'REC-ADMIN-{timezone.now().strftime("%Y%m%d")}-{subscription.id:06d}'

                    # Create admin note
                    subscription.notes = f"{subscription.notes or ''}\n[Admin {request.user.email}]: Approved manually. {notes}"

                    subscription.save()

                    messages.success(request, _('Subscription approved successfully.'))

                elif action == 'reject':
                    subscription.payment_status = 'FAILED'
                    subscription.is_active = False
                    subscription.notes = f"{subscription.notes or ''}\n[Admin {request.user.email}]: Rejected. {notes}"
                    subscription.save()

                    messages.warning(request, _('Subscription rejected.'))

                elif action == 'refund':
                    subscription.payment_status = 'REFUNDED'
                    subscription.is_active = False
                    subscription.notes = f"{subscription.notes or ''}\n[Admin {request.user.email}]: Refunded. {notes}"
                    subscription.save()

                    messages.info(request, _('Subscription refund processed.'))

            return redirect('admin:abea_app_subscription_changelist')

        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
            return redirect('admin:abea_app_subscription_change', object_id=subscription_id)

    return render(request, 'abea_app/admin/admin_update_subscription.html', {
        'subscription': subscription,
        'page_title': _('Update Subscription')
    })


# def check_phone_number_view(request):
#     """AJAX endpoint to check if a phone number has mobile money"""
#     if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
#         phone_number = request.POST.get('phone_number', '').strip()
#
#         if not phone_number:
#             return JsonResponse({
#                 'success': False,
#                 'message': _('Please enter a phone number.')
#             })
#
#         # Check account
#         result = MobileMoneyAPI.lookup_account(phone_number)
#
#         if result['success']:
#             return JsonResponse({
#                 'success': True,
#                 'account_name': result['account_name'],
#                 'operator': result['operator'],
#                 'phone': result['phone'],
#                 'country': result['country'],
#                 'message': _('Account found: {}').format(result['account_name'])
#             })
#         else:
#             # Try to detect network anyway
#             detected_network = MobileMoneyAPI.detect_network(phone_number)
#
#             return JsonResponse({
#                 'success': False,
#                 'detected_network': detected_network,
#                 'message': result.get('message',
#                                       _('Unable to verify account. Please ensure your mobile money account is active.'))
#             })
#
#     return JsonResponse({'success': False, 'message': _('Invalid request.')})
