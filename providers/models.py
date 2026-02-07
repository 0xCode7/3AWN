from django.db import models


class Pharmacy(models.Model):

    name = models.CharField(
        max_length=255,
        db_index=True
    )

    address = models.TextField()

    latitude = models.FloatField()
    longitude = models.FloatField()

    website = models.URLField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["latitude", "longitude"]),
        ]

    def __str__(self):
        return self.name
