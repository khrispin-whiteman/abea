# services/payment_gateways.py
import stripe
import paypalrestsdk
import logging
from django.conf import settings
from django.urls import reverse
from django.utils import timezone

logger = logging.getLogger(__name__)


class StripeGateway:
    """Stripe payment gateway integration"""

    def __init__(self):
        stripe.api_key = settings.STRIPE_SECRET_KEY

    def create_checkout_session(self, subscription, request):
        """Create a Stripe Checkout session for a subscription"""
        try:
            # Get the plan details
            plan = subscription.membership_plan
            success_url = request.build_absolute_uri(
                reverse(
                    'payment_callback') + f"?subscription_id={subscription.id}&status=success&session_id={{CHECKOUT_SESSION_ID}}"
            )
            cancel_url = request.build_absolute_uri(
                reverse('payment_callback') + f"?subscription_id={subscription.id}&status=failure"
            )

            # Create the checkout session
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': plan.currency.lower(),
                        'unit_amount': int(float(plan.price) * 100),  # Stripe uses cents
                        'product_data': {
                            'name': plan.name,
                            'description': plan.description[:255],
                        },
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url=success_url,
                cancel_url=cancel_url,
                client_reference_id=subscription.id,
                metadata={
                    'subscription_id': subscription.id,
                    'user_id': request.user.id,
                    'plan_id': plan.id
                }
            )

            logger.info(f"Stripe session created: {checkout_session.id} for subscription {subscription.id}")
            return {
                'success': True,
                'session_id': checkout_session.id,
                'checkout_url': checkout_session.url
            }

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
        except Exception as e:
            logger.exception(f"Unexpected error creating Stripe session: {str(e)}")
            return {
                'success': False,
                'error': 'An unexpected error occurred'
            }

    @staticmethod
    def verify_webhook(payload, sig_header):
        """Verify Stripe webhook signature"""
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
            return event
        except ValueError:
            # Invalid payload
            return None
        except stripe.error.SignatureVerificationError:
            # Invalid signature
            return None


class PayPalGateway:
    """PayPal payment gateway integration using REST SDK"""

    def __init__(self):
        paypalrestsdk.configure({
            "mode": settings.PAYPAL_MODE,
            "client_id": settings.PAYPAL_CLIENT_ID,
            "client_secret": settings.PAYPAL_CLIENT_SECRET
        })

    def create_payment(self, subscription, request):
        """Create a PayPal payment for a subscription"""
        try:
            plan = subscription.membership_plan
            return_url = request.build_absolute_uri(
                reverse('payment_callback')
            )
            cancel_url = request.build_absolute_uri(
                reverse('payment_callback') + f"?subscription_id={subscription.id}&status=cancelled"
            )

            payment = paypalrestsdk.Payment({
                "intent": "sale",
                "payer": {
                    "payment_method": "paypal"
                },
                "redirect_urls": {
                    "return_url": return_url,
                    "cancel_url": cancel_url
                },
                "transactions": [{
                    "amount": {
                        "total": str(plan.price),
                        "currency": plan.currency
                    },
                    "description": f"ABEA Membership: {plan.name}",
                    "custom": str(subscription.id),
                    "invoice_number": f"SUB-{subscription.id}-{int(timezone.now().timestamp())}"
                }]
            })

            if payment.create():
                # Extract approval URL
                approval_url = next(link.href for link in payment.links if link.rel == "approval_url")

                logger.info(f"PayPal payment created: {payment.id} for subscription {subscription.id}")

                return {
                    'success': True,
                    'payment_id': payment.id,
                    'approval_url': approval_url
                }
            else:
                logger.error(f"PayPal error: {payment.error}")
                return {
                    'success': False,
                    'error': payment.error.get('message', 'Payment creation failed')
                }

        except Exception as e:
            logger.exception(f"Unexpected error creating PayPal payment: {str(e)}")
            return {
                'success': False,
                'error': 'An unexpected error occurred'
            }

    def execute_payment(self, payment_id, payer_id):
        """Execute an approved PayPal payment"""
        try:
            payment = paypalrestsdk.Payment.find(payment_id)

            if payment.execute({"payer_id": payer_id}):
                logger.info(f"PayPal payment executed: {payment_id}")
                return {
                    'success': True,
                    'payment': payment
                }
            else:
                logger.error(f"PayPal execution error: {payment.error}")
                return {
                    'success': False,
                    'error': payment.error.get('message', 'Payment execution failed')
                }
        except Exception as e:
            logger.exception(f"Error executing PayPal payment: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }