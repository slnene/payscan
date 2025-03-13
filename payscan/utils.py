from http import client
import random
from uni.client import UniClient
from uni.exception import UniException

# Initialize UniClient with your credentials
client = UniClient("NHxLRh7E7psscG1GtFaN2j", "23F32EQ6EK6TgLSvMvtzuje3krA4D9a")

def generate_pin():
    return str(random.randint(10000, 99999))  # Generates a 5-digit PIN


def send_pin(phone_number, pin):
    try:
        res = client.messages.send({
            "to": f"{phone_number}", # in E.164 format
            "text": f"Welcome to PAYSCAN! Your default PIN is {pin}. Please use it for your first login. You'll be prompted to reset your PIN for added security."
        })
        print(res.data)
    except UniException as e:
        print(e)
        
        
def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))