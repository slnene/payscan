import requests
from django.http import JsonResponse
import json
from payscan.models import Transaction
import uuid 
from django.conf import settings
import requests
import base64
from django.conf import settings
import base64
import requests
import uuid
from django.conf import settings

# Generate a unique reference 
x_reference_id = str(uuid.uuid4())
print(x_reference_id)

class Collections:
    def __init__(self, subscription_key, user_id, api_key, environment):
        self.subscription_key = subscription_key
        self.user_id = user_id
        self.api_key = api_key
        self.environment = environment
        self.base_url = 'https://sandbox.momodeveloper.mtn.com/collection' if environment == 'sandbox' else 'https://momodeveloper.mtn.com/collection'

    def get_access_token(self):
        url = f"{self.base_url}/token/"
        # Base64 encode the credentials in the form of user_id:api_key
        credentials = f"{self.user_id}:{self.api_key}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        headers = {
            'Authorization': f'Basic {encoded_credentials}',
            'Ocp-Apim-Subscription-Key': self.subscription_key,
        }
        print(f"Request URL: {url}")  # Debugging: Print request URL
        print(f"Request Headers: {headers}")  # Debugging: Print headers to ensure they're correct
        response = requests.post(url, headers=headers)
        print(f"Response status code: {response.status_code}")  # Debugging: Print status code
        print(f"Response text: {response.text}")  # Debugging: Print response text
        if response.status_code == 200:
            return response.json().get('access_token')
        else:
            raise Exception(f"Failed to get access token: {response.status_code} {response.text}")

    def request_to_pay(self, amount, currency, external_id, payer, payer_message, payee_note):
        access_token = self.get_access_token()
        url = f"{self.base_url}/v1_0/requesttopay"
        headers = {
            'Authorization': f'Bearer {access_token}',
            'X-Reference-Id': str(uuid.uuid4()),  # Generate a unique reference ID for each request
            'X-Target-Environment': self.environment,
            'Content-Type': 'application/json',
            'Ocp-Apim-Subscription-Key': self.subscription_key,
        }
        data = {
            'amount': str(amount),
            'currency': currency,
            'externalId': external_id,
            'payer': payer,
            'payerMessage': payer_message,
            'payeeNote': payee_note,
        }
        response = requests.post(url, headers=headers, json=data)
        return response

# Example usage
collections = Collections(
    subscription_key=settings.MOMOAPI['collections']['sandbox']['subscription_key'],
    user_id=settings.MOMOAPI['collections']['sandbox']['user_id'],
    api_key=settings.MOMOAPI['collections']['sandbox']['api_key'],
    environment=settings.MOMOAPI['collections']['sandbox']['environment']
)

external_id = "unique_external_id_123"
payer_message = 'Test Payment'
payee_note = 'Test Payment Note'

try:
    access_token = collections.get_access_token()
    print(f"Access Token: {access_token}")
    response = collections.request_to_pay(
        amount=5.0,  # Amount in your chosen currency
        currency='EUR',
        external_id=external_id,
        payer={'party_id_type': 'MSISDN', 'party_id': '26812345678'},  # Example MSISDN number for Eswatini
        payer_message=payer_message,
        payee_note=payee_note
    )
    print(response.status_code, response.json())
except Exception as e:
    print(f"Error: {e}")



def momo_callback(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            external_id = data.get('externalId')
            status = data.get('status')
            transaction = Transaction.objects.get(external_id=external_id)

            if status == 'SUCCESSFUL':
                transaction.status = 'success'
            else:
                transaction.status = 'failed'

            transaction.save()
            return JsonResponse({'status': 'received'}, status=200)
        except (json.JSONDecodeError, Transaction.DoesNotExist) as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid request'}, status=400)

import requests
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import PayscanUser, Transaction

# Replace with your own MTN Mobile Money API credentials
client_id = '98da44ce-dff8-4eb1-9fad-1fd68c9d4450'
client_secret = '0365be4731f24275994ddc69866d0342'
subscription_key = 'b9642e7f19d84220b5d0774daf08840b'
base_url = 'https://sandbox.momodeveloper.mtn.com/collection/v1_0/'

# Function to get an access token
def get_access_token():
    url = base_url + 'gettoken'
    headers = {
        'Ocp-Apim-Subscription-Key': subscription_key
    }
    response = requests.post(url, auth=(client_id, client_secret), headers=headers)
    response.raise_for_status()
    return response.json().get('access_token')

# Function to get the balance
def get_balance():
    try:
        token = get_access_token()
        url = base_url + 'account/balance'
        headers = {
            'Authorization': f'Bearer {token}',
            'Ocp-Apim-Subscription-Key': subscription_key,
            'X-Target-Environment': 'sandbox'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching balance: {e}")
        return {'availableBalance': 'N/A', 'currency': ''}
