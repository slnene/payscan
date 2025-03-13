from django.db import models
from users.models import PayscanUser
from agents.models import Agent
from django.db import models
from users.models import PayscanUser
from agents.models import Agent


class Business(models.Model):
    owner = models.ForeignKey(PayscanUser, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    agent = models.ForeignKey(Agent, on_delete=models.SET_NULL, null=True, blank=True)
    qr_code = models.ImageField(upload_to='static/img/qrcodes/', blank=True, null=True)
    Dynamic_qr_code = models.ImageField(upload_to='static/img/qrcodes_PAYMENTS/', blank=True, null=True)
    public_transport=models.BooleanField(default=0)
    corridor = models.CharField(max_length=100, blank=True, null=True, default='N/A')
    number_plate = models.CharField(max_length=100, blank=True, null=True, default='N/A')
    fcm_token = models.CharField(max_length=255, blank=True, default='n/a', null=True)
    default_pin = models.DecimalField(max_digits=5,decimal_places=0, null=True)
    priority = models.DecimalField(max_digits=10, decimal_places=0 ,default=0)

    def __str__(self):
        return f'{self.name} {self.owner} {self.balance}'
    
    def transaction_count(self):
        return self.transactions.count()
    
   