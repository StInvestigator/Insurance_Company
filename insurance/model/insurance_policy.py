from django.db import models
from django.core.validators import MinValueValidator

from insurance.model.customer import Customer


class InsurancePolicy(models.Model):
    id = models.BigAutoField(primary_key=True)
    policy_number = models.CharField(max_length=64, unique=True)
    policy_type = models.CharField(max_length=64)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    premium = models.DecimalField(max_digits=10, decimal_places=2, default=75, validators=[MinValueValidator(0)])
    coverage_amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='policies'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "insurance_policy"
        constraints = [
            models.CheckConstraint(
                check=(models.Q(end_date__isnull=True) | models.Q(end_date__gte=models.F('start_date'))),
                name='insurance_policy_end_after_start'
            )
        ]

    def __str__(self):
        return self.policy_number