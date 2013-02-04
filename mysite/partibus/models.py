from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Server(models.Model):
    description = models.CharField(max_length=30)
    hostname = models.CharField(max_length=60)
    port = models.IntegerField()
    user = models.ForeignKey(User)
