from django.db import models
from django.core.validators import MinValueValidator

from insurance.model.InsurancePolicy import InsurancePolicy


class Claim(models.Model):
    id = models.BigAutoField(primary_key=True)
    policy = models.ForeignKey(
        InsurancePolicy,
        on_delete=models.CASCADE,
        related_name='claims'
    )
    claim_date = models.DateField()
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "claim"

    def __str__(self):
        return f"Claim {self.id} — {self.policy.policy_number}"