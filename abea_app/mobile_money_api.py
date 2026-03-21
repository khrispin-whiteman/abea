# import requests
# from django.conf import settings
#
#
# class MobileMoneyAPI:
#     """Mobile Money API integration for MoneyUnify"""
#
#     BASE_URL = "https://api.moneyunify.one"
#
#     # API Endpoints
#     PAYMENT_REQUEST_URL = f"{BASE_URL}/payments/request"
#     PAYMENT_VERIFY_URL = f"{BASE_URL}/payments/verify"
#     ACCOUNT_LOOKUP_URL = f"{BASE_URL}/account/lookup"
#
#     # Auth ID from settings
#     AUTH_ID = getattr(
#         settings,
#         'MOBILE_MONEY_AUTH_ID',
#         '01KH0SWDQ5HTEBQWNNVTY34BZ0'
#     )
#
#     @classmethod
#     def lookup_account(cls, phone_number):
#         """Check if a mobile money account exists for the given phone number"""
#         try:
#             payload = {
#                 "auth_id": cls.AUTH_ID,
#                 "phone_number": phone_number
#             }
#
#             headers = {
#                 "Content-Type": "application/x-www-form-urlencoded",
#                 "Accept": "application/json"
#             }
#
#             response = requests.post(
#                 cls.ACCOUNT_LOOKUP_URL,
#                 data=payload,
#                 headers=headers,
#                 timeout=30
#             )
#
#             if response.status_code != 200:
#                 return {
#                     'success': False,
#                     'message': f'API request failed with status {response.status_code}'
#                 }
#
#             data = response.json()
#
#             if data.get('isError', True):
#                 return {
#                     'success': False,
#                     'message': data.get('message', 'Account lookup failed')
#                 }
#
#             return {
#                 'success': True,
#                 'account_name': data['data']['accountName'],
#                 'operator': data['data']['operator'].upper(),  # MTN / AIRTEL / ZAMTEL
#                 'phone': data['data']['phone'],
#                 'country': data['data']['country']
#             }
#
#         except Exception as e:
#             return {
#                 'success': False,
#                 'message': str(e)
#             }
#
#     @classmethod
#     def initiate_payment(cls, phone_number, amount):
#         """Initiate a mobile money payment request"""
#         try:
#             payload = {
#                 "auth_id": cls.AUTH_ID,
#                 "from_payer": phone_number,
#                 "amount": str(amount)
#             }
#
#             headers = {
#                 "Accept": "application/json",
#                 "Content-Type": "application/x-www-form-urlencoded"
#             }
#
#             response = requests.post(
#                 cls.PAYMENT_REQUEST_URL,
#                 headers=headers,
#                 data=payload,
#                 timeout=30
#             )
#
#             if response.status_code != 200:
#                 return {
#                     'success': False,
#                     'message': f'API request failed with status {response.status_code}'
#                 }
#
#             data = response.json()
#
#             if data.get('isError', True):
#                 return {
#                     'success': False,
#                     'message': data.get('message', 'Payment initiation failed')
#                 }
#
#             return {
#                 'success': True,
#                 'transaction_id': data['data']['transaction_id'],
#                 'amount': data['data']['amount'],
#                 'charges': data['data']['charges'],
#                 'phone': data['data']['from_payer'],
#                 'status': data['data']['status']
#             }
#
#         except Exception as e:
#             return {
#                 'success': False,
#                 'message': str(e)
#             }
#
#     @classmethod
#     def verify_payment(cls, transaction_id):
#         """Verify if a payment was successful"""
#         try:
#             payload = {
#                 "auth_id": cls.AUTH_ID,
#                 "transaction_id": transaction_id
#             }
#
#             headers = {
#                 "Accept": "application/json",
#                 "Content-Type": "application/x-www-form-urlencoded"
#             }
#
#             response = requests.post(
#                 cls.PAYMENT_VERIFY_URL,
#                 headers=headers,
#                 data=payload,
#                 timeout=30
#             )
#
#             if response.status_code != 200:
#                 return {
#                     'success': False,
#                     'message': f'API request failed with status {response.status_code}'
#                 }
#
#             data = response.json()
#
#             if data.get('isError', True):
#                 return {
#                     'success': False,
#                     'message': data.get('message', 'Payment verification failed')
#                 }
#
#             return {
#                 'success': True,
#                 'status': data['data']['status'],
#                 'amount': data['data']['amount'],
#                 'transaction_id': data['data']['transaction_id'],
#                 'charges': data['data']['charges'],
#                 'phone': data['data']['from_payer']
#             }
#
#         except Exception as e:
#             return {
#                 'success': False,
#                 'message': str(e)
#             }

# services/moneyunify.py
import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


class MoneyUnifyAPI:
    BASE_URL = "https://api.moneyunify.one"

    # @classmethod
    # def lookup_account(cls, phone_number):
    #     """Look up account details to detect network"""
    #     url = f"{cls.BASE_URL}/account/lookup"
    #
    #     payload = {
    #         "auth_id": settings.MOBILE_MONEY_AUTH_ID,
    #         "phone_number": phone_number
    #     }
    #
    #     try:
    #         response = requests.post(
    #             url,
    #             data=payload,
    #             headers={
    #                 "Content-Type": "application/x-www-form-urlencoded",
    #                 "Accept": "application/json"
    #             },
    #             timeout=30
    #         )
    #
    #         data = response.json()
    #
    #         if data.get("isError") is False:
    #             return {
    #                 "success": True,
    #                 "operator": data["data"]["operator"].upper(),  # "airtel" -> "AIRTEL"
    #                 "account_name": data["data"]["accountName"],
    #                 "phone": data["data"]["phone"],
    #                 "type": data["data"]["type"],
    #                 "country": data["data"]["country"]
    #             }
    #         else:
    #             return {
    #                 "success": False,
    #                 "message": data.get("message", "Account lookup failed")
    #             }
    #
    #     except requests.exceptions.RequestException as e:
    #         logger.exception(f"MoneyUnify lookup error: {str(e)}")
    #         return {
    #             "success": False,
    #             "message": "Network error. Please try again."
    #         }
    #     except (ValueError, KeyError) as e:
    #         logger.exception(f"MoneyUnify parse error: {str(e)}")
    #         return {
    #             "success": False,
    #             "message": "Invalid response from payment provider"
    #         }

    @classmethod
    def lookup_account(cls, phone_number):
        """Look up account details to detect network"""
        url = f"{cls.BASE_URL}/account/lookup"

        # Clean the phone number - API expects local format without country code
        cleaned_phone = phone_number
        if phone_number.startswith('260'):
            cleaned_phone = phone_number[3:]  # Remove country code
        elif phone_number.startswith('0'):
            cleaned_phone = phone_number  # Keep leading 0

        logger.info(f"Looking up account for phone: {cleaned_phone}")

        payload = {
            "auth_id": settings.MOBILE_MONEY_AUTH_ID,
            "phone_number": cleaned_phone
        }

        try:
            response = requests.post(
                url,
                data=payload,
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Accept": "application/json"
                },
                timeout=30
            )

            logger.info(f"Lookup response status: {response.status_code}")
            data = response.json()
            logger.info(f"Lookup response data: {data}")

            if not data.get("isError", True):  # Check if isError is False
                # Convert operator to uppercase for consistent comparison
                operator = data["data"]["operator"].upper()  # "airtel" -> "AIRTEL"

                logger.info(f"Successfully detected network: {operator} for phone {cleaned_phone}")

                return {
                    "success": True,
                    "operator": operator,
                    "account_name": data["data"]["accountName"],
                    "phone": data["data"]["phone"],
                    "type": data["data"]["type"],
                    "country": data["data"]["country"]
                }
            else:
                error_msg = data.get("message", "Account lookup failed")
                logger.error(f"Account lookup failed: {error_msg}")
                return {
                    "success": False,
                    "message": error_msg
                }

        except requests.exceptions.RequestException as e:
            logger.exception(f"MoneyUnify lookup error: {str(e)}")
            return {
                "success": False,
                "message": "Network error. Please try again."
            }
        except (ValueError, KeyError) as e:
            logger.exception(f"MoneyUnify parse error: {str(e)}")
            return {
                "success": False,
                "message": "Invalid response from payment provider"
            }

    @classmethod
    def initiate_payment(cls, phone_number, amount, auth_id=None):
        """Initiate a payment request"""
        url = f"{cls.BASE_URL}/payments/request"

        # Use the auth_id from settings if not provided
        auth_id = auth_id or settings.MOBILE_MONEY_AUTH_ID

        # Clean phone number - ensure it's in the format the API expects
        # The API example shows "0769566586" - likely expects local format without country code
        cleaned_phone = phone_number
        if phone_number.startswith('260'):
            cleaned_phone = phone_number[3:]  # Remove country code
        elif phone_number.startswith('0'):
            cleaned_phone = phone_number  # Keep as is

        payload = {
            "from_payer": cleaned_phone,
            "amount": str(amount),  # Convert to string
            "auth_id": auth_id
        }

        try:
            response = requests.post(
                url,
                data=payload,
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Accept": "application/json"
                },
                timeout=30
            )

            data = response.json()

            if data.get("isError") is False:
                return {
                    "success": True,
                    "transaction_id": data["data"]["transaction_id"],
                    "status": data["data"]["status"],
                    "amount": data["data"]["amount"],
                    "charges": data["data"]["charges"],
                    "message": data["message"]
                }
            else:
                return {
                    "success": False,
                    "message": data.get("message", "Payment initiation failed")
                }

        except requests.exceptions.RequestException as e:
            logger.exception(f"MoneyUnify payment initiation error: {str(e)}")
            return {
                "success": False,
                "message": "Network error. Please try again."
            }
        except (ValueError, KeyError) as e:
            logger.exception(f"MoneyUnify payment parse error: {str(e)}")
            return {
                "success": False,
                "message": "Invalid response from payment provider"
            }

    @classmethod
    def verify_payment(cls, transaction_id, auth_id=None):
        """Verify payment status"""
        url = f"{cls.BASE_URL}/payments/verify"

        auth_id = auth_id or settings.MOBILE_MONEY_AUTH_ID

        payload = {
            "auth_id": auth_id,
            "transaction_id": transaction_id
        }

        logger.info(f"Verifying payment: transaction_id={transaction_id}")

        try:
            response = requests.post(
                url,
                data=payload,
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Accept": "application/json"
                },
                timeout=30
            )

            logger.info(f"Verify response status: {response.status_code}")
            data = response.json()
            logger.info(f"Verify response data: {data}")

            # Check if the transaction was successful
            if data.get("isError") is False:
                # Extract status from message or data
                message = data.get("message", "").lower()
                status = data.get("data", {}).get("status", "").lower()

                # If no status in data, infer from message
                if not status:
                    if "successful" in message:
                        status = "successful"
                    elif "initiated" in message:
                        status = "initiated"
                    elif "pending" in message:
                        status = "pending"
                    elif "failed" in message:
                        status = "failed"

                return {
                    "success": True,
                    "status": status,
                    "amount": data.get("data", {}).get("amount"),
                    "transaction_id": data.get("data", {}).get("transaction_id", transaction_id),
                    "charges": data.get("data", {}).get("charges", 0),
                    "from_payer": data.get("data", {}).get("from_payer"),
                    "message": data.get("message", "")
                }
            else:
                # API returned an error
                return {
                    "success": False,
                    "message": data.get("message", "Verification failed")
                }

        except requests.exceptions.RequestException as e:
            logger.exception(f"MoneyUnify verification error: {str(e)}")
            return {
                "success": False,
                "message": "Network error. Please try again."
            }
        except (ValueError, KeyError) as e:
            logger.exception(f"MoneyUnify verification parse error: {str(e)}")
            return {
                "success": False,
                "message": "Invalid response from payment provider"
            }


    # @classmethod
    # def verify_payment(cls, transaction_id, auth_id=None):
    #     """Verify payment status"""
    #     url = f"{cls.BASE_URL}/payments/verify"
    #
    #     auth_id = auth_id or settings.MOBILE_MONEY_AUTH_ID
    #
    #     payload = {
    #         "auth_id": auth_id,
    #         "transaction_id": transaction_id
    #     }
    #
    #     try:
    #         response = requests.post(
    #             url,
    #             data=payload,
    #             headers={
    #                 "Content-Type": "application/x-www-form-urlencoded",
    #                 "Accept": "application/json"
    #             },
    #             timeout=30
    #         )
    #
    #         data = response.json()
    #
    #         if data.get("isError") is False:
    #             return {
    #                 "success": True,
    #                 "status": data["data"]["status"],
    #                 "amount": data["data"]["amount"],
    #                 "transaction_id": data["data"]["transaction_id"],
    #                 "charges": data["data"]["charges"],
    #                 "from_payer": data["data"]["from_payer"],
    #                 "message": data["message"]
    #             }
    #         else:
    #             return {
    #                 "success": False,
    #                 "message": data.get("message", "Verification failed")
    #             }
    #
    #     except requests.exceptions.RequestException as e:
    #         logger.exception(f"MoneyUnify verification error: {str(e)}")
    #         return {
    #             "success": False,
    #             "message": "Network error. Please try again."
    #         }
    #     except (ValueError, KeyError) as e:
    #         logger.exception(f"MoneyUnify verification parse error: {str(e)}")
    #         return {
    #             "success": False,
    #             "message": "Invalid response from payment provider"
    #         }