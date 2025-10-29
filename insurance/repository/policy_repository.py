from django.db import models

from .base_repository import BaseRepository
from insurance.model.insurance_policy import InsurancePolicy
from django.utils import timezone

class PolicyRepository(BaseRepository):
    def __init__(self):
        super().__init__(InsurancePolicy)

    def find_by_number(self, policy_number: str):
        return self.model.objects.filter(policy_number=policy_number).first()

    def get_active_policies(self):
        today = timezone.localdate()
        return self.model.objects.filter(models.Q(start_date__lte=today) &
                                         (models.Q(end_date__isnull=True) | models.Q(end_date__gte=today)))
