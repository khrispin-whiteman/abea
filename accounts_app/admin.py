# accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser
from django.utils.translation import gettext_lazy as _


class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'country', 'membership_type',
                    'membership_status', 'is_active', 'is_staff', 'date_joined')
    list_filter = ('membership_type', 'membership_status', 'country', 'is_active',
                   'is_staff', 'is_superuser', 'date_joined')
    search_fields = ('email', 'first_name', 'last_name', 'phone', 'professional_id', 'institution')
    ordering = ('-date_joined',)

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal Info'), {'fields': ('title', 'first_name', 'last_name', 'profile_picture', 'bio')}),
        (_('Contact Info'), {'fields': ('phone', 'country', 'city', 'address')}),
        (_('Professional Info'), {'fields': ('professional_id', 'specialization', 'institution', 'position')}),
        (_('Membership'), {'fields': ('membership_type', 'membership_status',
                                      'membership_date', 'membership_expiry')}),
        (_('Preferences'), {'fields': ('language', 'payment_method')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'is_verified',
                       'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined', 'verification_date')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password1', 'password2'),
        }),
    )

    readonly_fields = ('date_joined', 'last_login', 'verification_date')


admin.site.register(CustomUser, CustomUserAdmin)

# abea/admin.py
# from django.contrib import admin
# from django.utils.translation import gettext_lazy as _
# from abea_app.models import (
#     Event, News, ExecutiveMember, Partner,
#     MembershipPlan, Subscription, Gallery, ContactMessage
# )
#
#
# @admin.register(Event)
# class EventAdmin(admin.ModelAdmin):
#     list_display = ('title', 'event_type', 'start_date', 'end_date', 'location',
#                     'is_published', 'is_featured', 'registered_count', 'created_at')
#     list_filter = ('event_type', 'is_published', 'is_featured', 'is_free', 'start_date')
#     search_fields = ('title', 'description', 'location', 'venue')
#     prepopulated_fields = {'slug': ('title',)}
#     readonly_fields = ('registered_count', 'created_at', 'updated_at')
#     date_hierarchy = 'start_date'
#
#     fieldsets = (
#         (_('Basic Information'), {
#             'fields': ('title', 'slug', 'description', 'short_description', 'event_type')
#         }),
#         (_('Date & Time'), {
#             'fields': ('start_date', 'end_date', 'registration_deadline')
#         }),
#         (_('Location'), {
#             'fields': ('location', 'venue', 'is_online', 'online_link')
#         }),
#         (_('Media'), {
#             'fields': ('image', 'banner')
#         }),
#         (_('Registration'), {
#             'fields': ('is_free', 'fee', 'capacity', 'registered_count')
#         }),
#         (_('Status & SEO'), {
#             'fields': ('is_published', 'is_featured', 'meta_description')
#         }),
#         (_('Metadata'), {
#             'fields': ('created_by', 'created_at', 'updated_at')
#         }),
#     )
#
#
# @admin.register(News)
# class NewsAdmin(admin.ModelAdmin):
#     list_display = ('title', 'category', 'author', 'publish_date', 'is_published',
#                     'is_featured', 'views', 'created_at')
#     list_filter = ('category', 'is_published', 'is_featured', 'publish_date')
#     search_fields = ('title', 'content', 'excerpt')
#     prepopulated_fields = {'slug': ('title',)}
#     readonly_fields = ('views', 'created_at', 'updated_at')
#     date_hierarchy = 'publish_date'
#
#     fieldsets = (
#         (_('Content'), {
#             'fields': ('title', 'slug', 'content', 'excerpt', 'category', 'tags')
#         }),
#         (_('Media'), {
#             'fields': ('image', 'thumbnail')
#         }),
#         (_('Publishing'), {
#             'fields': ('is_published', 'is_featured', 'meta_description')
#         }),
#         (_('Statistics'), {
#             'fields': ('views',)
#         }),
#         (_('Metadata'), {
#             'fields': ('author', 'created_at', 'updated_at')
#         }),
#     )
#
#     def save_model(self, request, obj, form, change):
#         if not obj.author:
#             obj.author = request.user
#         super().save_model(request, obj, form, change)
#
#
# @admin.register(ExecutiveMember)
# class ExecutiveMemberAdmin(admin.ModelAdmin):
#     list_display = ('user', 'position', 'region', 'term_start', 'term_end',
#                     'is_current', 'show_on_homepage', 'display_order')
#     list_filter = ('position', 'region', 'is_current', 'show_on_homepage')
#     search_fields = ('user__email', 'user__first_name', 'user__last_name', 'biography')
#     raw_id_fields = ('user',)
#
#
# @admin.register(Partner)
# class PartnerAdmin(admin.ModelAdmin):
#     list_display = ('name', 'partner_type', 'country', 'partnership_date',
#                     'partnership_active', 'show_on_homepage', 'display_order')
#     list_filter = ('partner_type', 'country', 'partnership_active', 'show_on_homepage')
#     search_fields = ('name', 'description', 'website', 'email')
#     prepopulated_fields = {'slug': ('name',)}
#
#
# @admin.register(MembershipPlan)
# class MembershipPlanAdmin(admin.ModelAdmin):
#     list_display = ('name', 'plan_type', 'price', 'currency', 'duration_months',
#                     'is_active', 'is_popular', 'display_order')
#     list_filter = ('plan_type', 'is_active', 'is_popular')
#     search_fields = ('name', 'description', 'benefits')
#
#
# @admin.register(Subscription)
# class SubscriptionAdmin(admin.ModelAdmin):
#     list_display = ('user', 'membership_plan', 'start_date', 'end_date',
#                     'is_active', 'amount_paid', 'payment_status', 'payment_method',
#                     'created_at')
#     list_filter = ('payment_status', 'payment_method', 'is_active', 'start_date',
#                    'end_date')
#     search_fields = ('user__email', 'transaction_id', 'receipt_number',
#                      'mobile_number')
#     raw_id_fields = ('user', 'membership_plan')
#     readonly_fields = ('created_at', 'updated_at')
#     date_hierarchy = 'created_at'
#
#
# @admin.register(Gallery)
# class GalleryAdmin(admin.ModelAdmin):
#     list_display = ('title', 'category', 'event', 'is_featured', 'display_order',
#                     'uploaded_at')
#     list_filter = ('category', 'is_featured', 'uploaded_at')
#     search_fields = ('title', 'description')
#     raw_id_fields = ('event', 'uploaded_by')
#
#
# @admin.register(ContactMessage)
# class ContactMessageAdmin(admin.ModelAdmin):
#     list_display = ('name', 'email', 'message_type', 'subject', 'is_read',
#                     'is_responded', 'priority', 'created_at')
#     list_filter = ('message_type', 'is_read', 'is_responded', 'priority', 'created_at')
#     search_fields = ('name', 'email', 'subject', 'message')
#     readonly_fields = ('created_at', 'ip_address', 'user_agent')
#     date_hierarchy = 'created_at'
#
#     fieldsets = (
#         (_('Message Details'), {
#             'fields': ('name', 'email', 'phone', 'organization',
#                        'message_type', 'subject', 'message')
#         }),
#         (_('Response'), {
#             'fields': ('is_read', 'is_responded', 'response',
#                        'responded_by', 'responded_at', 'priority')
#         }),
#         (_('Metadata'), {
#             'fields': ('ip_address', 'user_agent', 'created_at')
#         }),
#     )