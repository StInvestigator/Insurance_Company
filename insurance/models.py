from django.db import models
from django.core.validators import MinValueValidator

class Customer(models.Model):
    id = models.BigAutoField(primary_key=True)
    full_name = models.CharField(max_length=512)
    tax_number = models.CharField(max_length=128, unique=True)
    date_of_birth = models.DateField()
    email = models.EmailField(max_length=512, unique=True)
    phone = models.CharField(max_length=16)
    address = models.CharField(max_length=256)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "customer"

    def __str__(self):
        return self.full_name


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
        # повертає зрозумілий опис, не використовуй policy_id у форматуванні, використовуй FKоб'єкт
        return f"Claim {self.id} — {self.policy.policy_number}"


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
