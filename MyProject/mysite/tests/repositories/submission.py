# models.py
from django.conf import settings
from django.db import models

class Submission(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="submissions",
        null=True,
        blank=True,
    )
    test = models.ForeignKey("Test", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    total_score = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.test.title} - {self.created_at:%Y-%m-%d %H:%M}"