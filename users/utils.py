import requests
import json
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def initiate_momo_payment(amount, payer_number, external_id):
    url = "https://sandbox.momodeveloper.mtn.com/collection/v1_0/requesttopay"
    payload = json.dumps({
        "amount": str(amount),
        "currency": "EUR",  # Change to the appropriate currency if needed
        "externalId": external_id,
        "payer": {
            "partyIdType": "MSISDN",
            "partyId": payer_number
        },
        "payerMessage": "Payment for services",
        "payeeNote": "Thank you for your business"
    })
    headers = {
        'X-Reference-Id': external_id,
        'X-Target-Environment': 'sandbox',
        'Ocp-Apim-Subscription-Key': settings.MTN_MOMO_SUBSCRIPTION_KEY,
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {settings.MTN_MOMO_ACCESS_TOKEN}'
    }
    
    response = requests.post(url, headers=headers, data=payload)
    
    # Log the response status and content
    logger.debug(f"Response Status Code: {response.status_code}")
    logger.debug(f"Response Content: {response.text}")
    
    if response.status_code == 200:
        try:
            response_data = response.json()
        except json.JSONDecodeError:
            response_data = {"status": "error", "message": "Invalid JSON response"}
    else:
        response_data = {"status": "error", "message": f"HTTP {response.status_code}: {response.text}"}
    
    print(response.text)

    return response_data


def transfer_to_business(amount, business):
    url = "https://sandbox.momodeveloper.mtn.com/disbursement/v1_0/transfer"
    headers = {
        "Authorization": f"Bearer {settings.MTN_MOMO_API_KEY}",
        "Content-Type": "application/json",
        "X-Reference-Id": f"transfer_{business.id}",
        "X-Target-Environment": "sandbox"
    }
    data = {
        "amount": str(amount),
        "currency": "SZL",
        "externalId": f"business_{business.id}",
        "payee": {
            "partyIdType": "MSISDN",
            "partyId": business.owner.user.username  # Assuming the business owner's phone number is stored in the username field
        },
        "payerMessage": "Payment from Payscan",
        "payeeNote": "Payment received"
    }
    response = requests.post(url, json=data, headers=headers)
    return response.json()
