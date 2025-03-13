from django.db import models
from django.contrib.auth.models import User

class PayscanUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    default_pin = models.DecimalField(max_digits=5,decimal_places=0, null=True)
    priority = models.DecimalField(max_digits=10, decimal_places=0 ,default=0)



