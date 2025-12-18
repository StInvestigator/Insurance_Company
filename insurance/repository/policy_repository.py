from django.db import models

from .base_repository import BaseRepository
from insurance.model.insurance_policy import InsurancePolicy
from django.utils import timezone
from django.db.models import Sum, F, Min, Value, DecimalField
from django.db.models.functions import Coalesce

class PolicyRepository(BaseRepository):
    def __init__(self):
        super().__init__(InsurancePolicy)

    def find_by_number(self, policy_number: str):
        return self.model.objects.filter(policy_number=policy_number).first()

    def get_active_policies(self):
        today = timezone.localdate()
        return self.model.objects.filter(models.Q(start_date__lte=today) &
                                         (models.Q(end_date__isnull=True) | models.Q(end_date__gte=today)))

    def policy_profit_by_type(self, date_from=None, date_to=None):
        qs = self.model.objects.all()
        if date_from:
            qs = qs.filter(start_date__gte=date_from)
        if date_to:
            qs = qs.filter(start_date__lte=date_to)
        qs = (
            qs.values('policy_type')
            .annotate(
                total_premium=Coalesce(
                    Sum('premium'),
                    Value(0, output_field=DecimalField())
                )
            )
            .annotate(
                total_payouts=Coalesce(
                    Sum('claims__payments__amount'),
                    Value(0, output_field=DecimalField())
                )
            )
            .annotate(
                profit=F('total_premium') - F('total_payouts')
            )
            .order_by('-profit')
        )

        return qs

    def time_to_first_claim_per_policy(self):
        from django.db.models import ExpressionWrapper, DurationField
        qs = (
            self.model.objects
            .annotate(first_claim_date=Min('claims__claim_date'))
            .exclude(first_claim_date__isnull=True)
            .annotate(delta=ExpressionWrapper(F('first_claim_date') - F('start_date'), output_field=DurationField()))
            .values('id', 'policy_type', 'delta')
        )
        return qs
