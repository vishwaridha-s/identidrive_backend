from django.db import models

class PlatePrediction(models.Model):
    video_name = models.CharField(max_length=255)
    frame_path = models.CharField(max_length=500)
    top1 = models.CharField(max_length=100)
    confidence = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.top1