from django.db import models

# Create your models here.

from django.contrib.auth.models import User

class resource(models.Model):
    user = models.ForeignKey(User)
    ipList = models.CharField(max_length=5000)
    confirm = models.SmallIntegerField(default=0)
    applyTime = models.SmallIntegerField(null=True)
    datetime = models.DateTimeField(auto_now_add=True)