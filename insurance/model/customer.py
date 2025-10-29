from django.db import models

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