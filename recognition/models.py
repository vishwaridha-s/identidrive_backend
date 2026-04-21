from django.db import models
from django.contrib.auth.models import User

class PlatePrediction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    video_name = models.CharField(max_length=255)
    frame_path = models.CharField(max_length=500)
    top1 = models.CharField(max_length=100)
    confidence = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username if self.user else 'Anonymous'} - {self.top1}"