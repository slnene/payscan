from django.contrib.auth.models import User
from django.db import models
from django.db import models
from users.models import PayscanUser
from businesses.models import Business
from agents.models import Agent


class Transaction(models.Model):
    payer = models.ForeignKey(PayscanUser, on_delete=models.CASCADE, related_name='payer')
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='transactions',null=True, blank=True)
    payee = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='payee', null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)
    transaction_type = models.CharField(max_length=20)
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, null=True, blank=True)
    commission = models.DecimalField(max_digits=10, decimal_places=2,null=True, blank=True)

    def __str__(self):
        return f'{self.payer} - {self.payee} - {self.amount} - {self.timestamp} - {self.transaction_type}'
