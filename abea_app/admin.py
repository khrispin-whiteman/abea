from django.contrib import admin
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html
from .models import (
    Event,
    EventRegistration,
    News,
    ExecutiveMember,
    Partner,
    MembershipPlan,
    Subscription,
    Gallery,
    ContactMessage,
)


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user_email', 'plan_name', 'payment_status', 'is_active',
                    'payment_date', 'amount_paid', 'admin_actions')
    list_filter = ('payment_status', 'is_active', 'payment_method', 'created_at')
    search_fields = ('user__email', 'transaction_id', 'receipt_number', 'mobile_number')
    readonly_fields = ('created_at', 'updated_at')
    actions = ['approve_payments', 'mark_as_failed']

    def user_email(self, obj):
        return obj.user.email

    user_email.short_description = 'User'

    def plan_name(self, obj):
        return obj.membership_plan.name

    plan_name.short_description = 'Plan'

    def admin_actions(self, obj):
        return format_html(
            '<a href="{}" class="button">Manual Update</a>',
            reverse('admin_update_subscription', args=[obj.id])
        )

    admin_actions.short_description = 'Actions'

    def approve_payments(self, request, queryset):
        updated = queryset.update(
            payment_status='COMPLETED',
            is_active=True,
            payment_date=timezone.now()
        )
        self.message_user(request, f'{updated} subscription(s) approved.')

    approve_payments.short_description = "Approve selected payments"

    def mark_as_failed(self, request, queryset):
        updated = queryset.update(payment_status='FAILED', is_active=False)
        self.message_user(request, f'{updated} subscription(s) marked as failed.')

    mark_as_failed.short_description = "Mark selected as failed"



# =========================
# EVENT & REGISTRATION
# =========================

class EventRegistrationInline(admin.TabularInline):
    model = EventRegistration
    extra = 0
    readonly_fields = (
        'registration_date',
        'confirmation_date',
    )


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'event_type',
        'start_date',
        'end_date',
        'is_published',
        'is_featured',
        'is_free',
        'capacity',
        'registered_count',
    )
    list_filter = (
        'event_type',
        'is_published',
        'is_featured',
        'is_free',
        'is_online',
        'start_date',
    )
    search_fields = ('title', 'description', 'location')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('registered_count', 'created_at', 'updated_at')
    inlines = [EventRegistrationInline]
    ordering = ('-start_date',)


@admin.register(EventRegistration)
class EventRegistrationAdmin(admin.ModelAdmin):
    list_display = (
        'event',
        'user',
        'payment_status',
        'is_confirmed',
        'attended',
        'registration_date',
    )
    list_filter = (
        'payment_status',
        'is_confirmed',
        'attended',
    )
    search_fields = (
        'user__email',
        'event__title',
        'transaction_id',
        'confirmation_code',
    )
    readonly_fields = (
        'registration_date',
        'confirmation_date',
    )


# =========================
# NEWS
# =========================

@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'category',
        'is_published',
        'is_featured',
        'publish_date',
        'views',
    )
    list_filter = (
        'category',
        'is_published',
        'is_featured',
    )
    search_fields = ('title', 'content', 'tags')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('views', 'created_at', 'updated_at')
    ordering = ('-publish_date',)


# =========================
# EXECUTIVE MEMBERS
# =========================

@admin.register(ExecutiveMember)
class ExecutiveMemberAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'position',
        'region',
        'is_current',
        'display_order',
        'show_on_homepage',
    )
    list_filter = (
        'position',
        'region',
        'is_current',
        'show_on_homepage',
    )
    search_fields = (
        'user__first_name',
        'user__last_name',
        'user__email',
    )
    ordering = ('display_order', 'position')


# =========================
# PARTNERS
# =========================

@admin.register(Partner)
class PartnerAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'partner_type',
        'country',
        'partnership_active',
        'show_on_homepage',
        'display_order',
    )
    list_filter = (
        'partner_type',
        'country',
        'partnership_active',
        'show_on_homepage',
    )
    search_fields = ('name', 'country')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('display_order', 'name')


# =========================
# MEMBERSHIP PLANS
# =========================

@admin.register(MembershipPlan)
class MembershipPlanAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'plan_type',
        'price',
        'currency',
        'duration_months',
        'is_active',
        'is_popular',
        'display_order',
    )
    list_filter = (
        'plan_type',
        'is_active',
        'is_popular',
    )
    search_fields = ('name', 'description')
    ordering = ('display_order', 'price')


# =========================
# SUBSCRIPTIONS
# =========================

# @admin.register(Subscription)
# class SubscriptionAdmin(admin.ModelAdmin):
#     list_display = (
#         'user',
#         'membership_plan',
#         'amount_paid',
#         'payment_status',
#         'payment_method',
#         'is_active',
#         'start_date',
#         'end_date',
#     )
#     list_filter = (
#         'payment_status',
#         'payment_method',
#         'is_active',
#         'auto_renew',
#     )
#     search_fields = (
#         'user__email',
#         'membership_plan__name',
#         'transaction_id',
#         'receipt_number',
#     )
#     readonly_fields = ('created_at', 'updated_at')
#     ordering = ('-created_at',)


# =========================
# GALLERY
# =========================

@admin.register(Gallery)
class GalleryAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'category',
        'event',
        'is_featured',
        'display_order',
        'uploaded_at',
    )
    list_filter = (
        'category',
        'is_featured',
    )
    search_fields = ('title', 'description')
    ordering = ('-uploaded_at',)


# =========================
# CONTACT MESSAGES
# =========================

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = (
        'subject',
        'name',
        'email',
        'message_type',
        'priority',
        'is_read',
        'is_responded',
        'created_at',
    )
    list_filter = (
        'message_type',
        'priority',
        'is_read',
        'is_responded',
    )
    search_fields = ('name', 'email', 'subject', 'message')
    readonly_fields = ('created_at', 'ip_address', 'user_agent')
    ordering = ('-created_at',)
