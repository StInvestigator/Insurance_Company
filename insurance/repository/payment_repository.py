from .base_repository import BaseRepository
from insurance.models import Payment

class PaymentRepository(BaseRepository):
    def __init__(self):
        super().__init__(Payment)

    def find_by_claim(self, claim_id: int):
        return self.model.objects.filter(claim_id=claim_id)
