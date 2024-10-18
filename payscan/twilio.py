import random
import string
from twilio.rest import Client

def send_otp(phone_number, otp):
    account_sid = 'your_account_sid'
    auth_token = 'your_auth_token'
    client = Client(account_sid, auth_token)

    message = client.messages.create(
        body=f'Your OTP code is {otp}',
        from_='+1234567890',
        to=phone_number
    )

def generate_otp():
    return ''.join(random.choices(string.digits, k=6))
