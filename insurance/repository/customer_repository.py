from .base_repository import BaseRepository
from insurance.model.customer import Customer

class CustomerRepository(BaseRepository):
    def __init__(self):
        super().__init__(Customer)

    def find_by_email(self, email: str):
        return self.model.objects.filter(email=email).first()

    def find_by_tax_number(self, tax_number: str):
        return self.model.objects.filter(tax_number=tax_number).first()