from django.db import models
from django.contrib.auth.models import User

class VoiceUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    is_banned = models.BooleanField(default=False)
    last_connection = models.DateTimeField(auto_now=True)
    ip_address = models.CharField(max_length=50)
    
    def __str__(self):
        return f"{self.user.username} ({'Active' if self.is_active else 'Inactive'})"