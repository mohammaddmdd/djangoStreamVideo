from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    stream_key = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.user.first_name
