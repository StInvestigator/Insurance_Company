from django.db import models
from django.core.validators import MinValueValidator
from insurance.model.claim import Claim

class Payment(models.Model):
    id = models.BigAutoField(primary_key=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    date = models.DateField()
    claim = models.ForeignKey(
        Claim,
        on_delete=models.CASCADE,
        related_name='payments'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "payment"

    def __str__(self):
        return f"Payment {self.id} — {self.amount}"
