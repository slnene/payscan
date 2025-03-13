from django.db import models
from users.models import PayscanUser


class Agent(models.Model):
    agentuser = models.OneToOneField(PayscanUser, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    Id_number = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    priority = models.DecimalField(max_digits=10, decimal_places=0 ,default=0)
    default_pin = models.DecimalField(max_digits=5,decimal_places=0, null=True)

    def __str__(self):
        return f'{self.agentuser}'
