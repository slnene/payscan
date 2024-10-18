from django.db import models
from users.models import PayscanUser


class Agent(models.Model):
    agentuser = models.OneToOneField(PayscanUser, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    def __str__(self):
        return f'{self.agentuser}'
