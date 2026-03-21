import requests
import logging
from django.conf import settings
from requests.exceptions import RequestException

logger = logging.getLogger(__name__)

def generate_access_token():
    # base = settings.PESAPAL_BASE_URL.rstrip('/')  # remove trailing slash if present
    # url = f"{base}/Auth/RequestToken"
    # Avoid double slash if base URL ends with /
    if settings.PESAPAL_BASE_URL.endswith('/'):
        url = f"{settings.PESAPAL_BASE_URL}Auth/RequestToken"
    else:
        url = f"{settings.PESAPAL_BASE_URL}/Auth/RequestToken"

    payload = {
        "consumer_key": settings.PESAPAL_CONSUMER_KEY,
        "consumer_secret": settings.PESAPAL_CONSUMER_SECRET
    }
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    try:
        print(f"Requesting token from URL: {url}")  # debug
        print(f"Payload: {payload}")                 # debug
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        print(f"Response status: {response.status_code}")  # debug
        print(f"Response content: {response.text}")        # debug
        response.raise_for_status()
        data = response.json()
        token = data.get("token")
        if not token:
            print("Token missing in response:", data)
        return token
    except requests.exceptions.RequestException as e:
        print(f"Exception: {e}")
        logger.exception("Failed to generate Pesapal access token")
        return None

def submit_order_request(access_token, order_payload):
    """Submit order to Pesapal and return response with redirect_url."""
    url = f"{settings.PESAPAL_BASE_URL}/Transactions/SubmitOrderRequest"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(url, json=order_payload, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except RequestException as e:
        logger.exception("Pesapal order submission failed")
        return None

def get_transaction_status(access_token, order_tracking_id, merchant_reference=None):
    # Use the correct base for transaction endpoints
    url = f"{settings.PESAPAL_BASE_URL}/Transactions/GetTransactionStatus"  # <-- separate setting
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json"
    }
    params = {
        "orderTrackingId": order_tracking_id,
    }
    if merchant_reference:
        params["orderMerchantReference"] = merchant_reference   # camelCase

    logger.info(f"Calling status URL: {url} with params {params}")  # <-- log the full URL

    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except RequestException as e:
        logger.exception("Failed to get transaction status")
        return None