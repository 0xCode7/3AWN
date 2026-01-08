from django.db import models
from authentication.models import User

class ActiveIngredient(models.Model):
    name = models.CharField(max_length=255, unique=True)
    smiles = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name

class Drug(models.Model):
    name = models.CharField(max_length=255, unique=True)
    active_ingredients = models.ManyToManyField(
        ActiveIngredient,
        related_name="drugs",
        blank=True
    )

    def __str__(self):
        return f"{self.name}"

class DrugAlternative(models.Model):
    drug = models.ForeignKey(Drug, on_delete=models.CASCADE, related_name="alternatives")
    substitute = models.CharField(max_length=255)
    match_score = models.FloatField(null=True, blank=True)
    drug_class = models.CharField(max_length=255, null=True, blank=True)
    atc_code = models.CharField(max_length=20, null=True, blank=True)
    herbal_alternatives = models.TextField(null=True, blank=True)

    class Meta:
        unique_together = ("drug", "substitute")  # 🧠 ensures skip-on-duplicate

    def __str__(self):
        return f"{self.substitute} (Alternative for {self.drug.name})"

class Medication(models.Model):
    name = models.CharField(max_length=255, null=False, blank=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    dosage = models.CharField(max_length=100)
    time = models.TimeField()
    type = models.CharField(max_length=60, default='Tablet')
    times_per_day = models.IntegerField(default=1)
    duration_in_days = models.IntegerField(default=7)
    start_date = models.DateField(auto_now_add=True)
    dose_taken = models.JSONField(default=dict, blank=True)
    is_finished = models.BooleanField(default=False, blank=True)

    def __str__(self):
        return f"{self.name} ({self.user.email})"

    def save(self, *args, **kwargs):
        if self.time:
            self.time = self.time.replace(second=0, microsecond=0)
        super().save(*args, **kwargs)
