from .base_repository import BaseRepository
from insurance.model.Claim import Claim

class ClaimRepository(BaseRepository):
    def __init__(self):
        super().__init__(Claim)

    def find_by_policy(self, policy_id: int):
        return self.model.objects.filter(policy_id=policy_id)
