# abea/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Public Pages
    path('', views.home_view, name='home'),
    path('about/', views.about_view, name='about'),
    path('news/', views.news_list_view, name='news_list'),
    path('news/<slug:slug>/', views.news_detail_view, name='news_detail'),
    path('events/', views.events_list_view, name='events_list'),
    path('events/<slug:slug>/', views.event_detail_view, name='event_detail'),
    path('gallery/', views.gallery_view, name='gallery'),
    path('partners/', views.partners_view, name='partners'),
    path('partners/<slug:slug>/', views.partner_detail_view, name='partner_detail'),
    path('membership/', views.membership_plans_view, name='membership'),
    path('contact/', views.contact_view, name='contact'),
    path('members/executive/', views.executive_members, name='executive_members'),

    # Event Registration
    path('events/register/<slug:event_slug>/', views.register_event_view, name='register_event'),

    # Admin Pages
    path('admin-dashboard/', views.admin_dashboard_view, name='admin_dashboard'),

    # Event Management URLs
    path('manage-events/', views.manage_events_view, name='manage_events'),
    path('events-admin/add/', views.add_event_view, name='add_event'),
    path('events-admin/<int:pk>/edit/', views.edit_event_view, name='edit_event'),
    path('events-admin/<int:pk>/delete/', views.delete_event_view, name='delete_event'),
    path('events-admin/<slug:slug>/registrations/', views.event_registrations_view, name='event_registrations'),

    # News Management URLs (if not already added)
    path('manage-news/', views.manage_news_view, name='manage_news'),
    path('news-admin/add/', views.add_news_view, name='add_news'),
    path('news-admin/<int:pk>/edit/', views.edit_news_view, name='edit_news'),
    path('news-admin/<int:pk>/delete/', views.delete_news_view, name='delete_news'),
    path('news-admin/toggle-publish/', views.toggle_news_publish_view, name='toggle_news_publish'),

    # Gallery CRUD URLs
    path('manage-gallery/', views.manage_gallery_view, name='manage_gallery'),
    path('gallery-admin/add/', views.add_gallery_view, name='add_gallery'),
    path('gallery-admin/<int:pk>/edit/', views.edit_gallery_view, name='edit_gallery'),
    path('gallery-admin/<int:pk>/delete/', views.delete_gallery_view, name='delete_gallery'),
    path('gallery-admin/toggle-featured/', views.toggle_featured_gallery, name='toggle_featured_gallery'),

    # Executive Members CRUD URLs
    path('manage-executive-members/', views.manage_executive_members_view, name='manage_executive_members'),
    path('executive-members-admin/add/', views.add_executive_member_view, name='add_executive_member'),
    path('executive-members-admin/<int:pk>/edit/', views.edit_executive_member_view, name='edit_executive_member'),
    path('executive-members-admin/<int:pk>/delete/', views.delete_executive_member_view, name='delete_executive_member'),
    path('executive-members-admin/toggle-current/', views.toggle_current_executive, name='toggle_current_executive'),

    # Partners CRUD URLs
    path('manage-partners/', views.manage_partners_view, name='manage_partners'),
    path('partners-admin/add/', views.add_partner_view, name='add_partner'),
    path('partners-admin/<int:pk>/edit/', views.edit_partner_view, name='edit_partner'),
    path('partners-admin/<int:pk>/delete/', views.delete_partner_view, name='delete_partner'),
    path('partners-admin/toggle-active/', views.toggle_partner_active, name='toggle_partner_active'),

    # Membership Plans Management
    path('membership-plans/', views.manage_membership_plans_view, name='manage_membership_plans'),
    path('membership-plans-admin/add/', views.add_membership_plan_view, name='add_membership_plan'),
    path('membership-plans-admin/<int:pk>/edit/', views.edit_membership_plan_view, name='edit_membership_plan'),
    path('membership-plans-admin/<int:pk>/delete/', views.delete_membership_plan_view, name='delete_membership_plan'),
    path('membership-plans-admin/<int:pk>/toggle-active/', views.toggle_plan_active_view, name='toggle_plan_active'),
    path('membership-plans-admin/<int:pk>/toggle-popular/', views.toggle_plan_popular_view, name='toggle_plan_popular'),
    # Membership Payment
    path('membership-plans/initiate-payment/<int:plan_id>/', views.initiate_payment_view, name='initiate_payment'),
    # path('payment/success/<int:subscription_id>/', views.payment_success_view, name='payment_success'),
    # path('payment/failed/<int:subscription_id>/', views.payment_failed_view, name='payment_failed'),
    # path("payments/lookup-network/", views.lookup_mobile_network, name="lookup_mobile_network"),

    # MANAGE PAYMENTS
    # Mobile money payments
    path('payment/verify/<str:transaction_id>/', views.verify_payment_view, name='verify_payment'),
    path('payment/success/<str:transaction_id>/', views.payment_success_view, name='payment_success'),
    path('payment/failed/<str:transaction_id>/', views.payment_failed_view, name='payment_failed'),
    path('payment/lookup-network/', views.lookup_mobile_network, name='lookup_network'),

    # Online payments
    # path('payment/process/<int:subscription_id>/', views.process_online_payment, name='process_online_payment'),
    # path('payment/simulate/credit-card/<int:subscription_id>/', views.simulate_credit_card_payment, name='simulate_credit_card_payment'),
    # path('payment/simulate/paypal/<int:subscription_id>/', views.simulate_paypal_payment, name='simulate_paypal_payment'),
    # path('payment/callback/', views.payment_callback, name='payment_callback'),
    #
    # path('payment/callback/', views.payment_callback, name='payment_callback'),
    # path('payment/stripe-webhook/', views.stripe_webhook, name='stripe_webhook'),

    # Pesapal online payment endpoints
    path('register/ipn/', views.register_ipn, name='register_ipn'),
    # path('pesapal/ipn/', views.pesapal_ipn, name='pesapal_ipn'),
    # path('pesapal/callback/', views.pesapal_callback, name='pesapal_callback'),
    path('payment-outcome/<str:merchant_reference>/', views.payment_outcome, name='payment_outcome'),

    # path('make-payment/', views.PaymentView.as_view(), name='make_payment'),  # optional, for React
    path('v3/paymentstransaction/completed/', views.CustomTransactionCompletedView.as_view(), name='transaction_completed'),
    path('v3/pesapal-callback/', views.PesapalCallbackView.as_view(), name='pesapal_callback'),
    path('v3/ipn/', views.PesapalIPNView.as_view(), name='pesapal_ipn'),  # new IPN endpoint


    path('admin/update-subscription/<int:subscription_id>/',
         views.admin_update_subscription_view, name='admin_update_subscription'),

    # API endpoints
    # path('api/check-phone/', views.check_phone_number_view, name='check_phone'),
    # path('api/verify-payment/<int:subscription_id>/', views.verify_payment_view, name='verify_payment'),
    # path('api/check-payment-status/<int:subscription_id>/', views.check_payment_status, name='check_payment_status'),

    # Proof upload for bank transfers
    path('subscriptions/<int:subscription_id>/upload-proof/',
         views.upload_payment_proof, name='upload_payment_proof'),

    # Webhooks
    # path('webhooks/stripe/', views.payment_webhook, {'gateway': 'stripe'},
    #      name='stripe_webhook'),
    # path('webhooks/paypal/', views.payment_webhook, {'gateway': 'paypal'},
    #      name='paypal_webhook'),
    path('webhooks/mobile-money/', views.payment_webhook, {'gateway': 'mobile_money'},
         name='mobile_money_webhook'),
]