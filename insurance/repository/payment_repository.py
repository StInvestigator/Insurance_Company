from .base_repository import BaseRepository
from insurance.model.payment import Payment
from django.db.models import Sum, F
from django.db.models.functions import TruncMonth

class PaymentRepository(BaseRepository):
    def __init__(self):
        super().__init__(Payment)

    def find_by_claim(self, claim_id: int):
        return self.model.objects.filter(claim_id=claim_id)

    def payments_by_month(self, date_from=None, date_to=None, policy_type: str | None = None):
        qs = (
            self.model.objects.select_related('claim__policy')
        )
        if date_from:
            qs = qs.filter(date__gte=date_from)
        if date_to:
            qs = qs.filter(date__lte=date_to)
        if policy_type:
            qs = qs.filter(claim__policy__policy_type=policy_type)
        qs = (
            qs.annotate(month=TruncMonth('date'), ptype=F('claim__policy__policy_type'))
              .values('month', 'ptype')
              .annotate(total_amount=Sum('amount'))
              .order_by('month', 'ptype')
        )
        return qs

    def top_customers_by_payouts(self, limit: int = 10, threshold=None, date_from=None, date_to=None):
        qs = (
            self.model.objects
            .select_related('claim__policy__customer')
        )
        if date_from:
            qs = qs.filter(date__gte=date_from)
        if date_to:
            qs = qs.filter(date__lte=date_to)
        qs = (
            qs.values('claim__policy__customer_id', 'claim__policy__customer__full_name')
              .annotate(total_payout=Sum('amount'))
        )
        if threshold is not None:
            qs = qs.filter(total_payout__gt=threshold)
        qs = qs.order_by('-total_payout')
        if limit:
            return qs[:limit]
        return qs
