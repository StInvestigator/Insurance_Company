from .base_repository import BaseRepository
from insurance.model.claim import Claim

class ClaimRepository(BaseRepository):
    def __init__(self):
        super().__init__(Claim)

    def find_by_policy(self, policy_id: int):
        return self.model.objects.filter(policy_id=policy_id)

    def find_by_customer(self, customer_id: int):
        return (
            self.model.objects
            .filter(policy__customer_id=customer_id)
            .select_related('policy', 'policy__customer')
            .order_by('-claim_date')
        )