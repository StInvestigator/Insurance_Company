from .base_repository import BaseRepository
from insurance.model.claim import Claim
from django.db import models
from django.db.models import Avg, Count, Sum, F, Case, When, Value
from django.db.models.functions import ExtractYear, Now

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

    def avg_claim_by_age_group(self, date_from=None, date_to=None):
        qs = self.model.objects.all()
        if date_from:
            qs = qs.filter(claim_date__gte=date_from)
        if date_to:
            qs = qs.filter(claim_date__lte=date_to)
        qs = qs.annotate(
            age_years=ExtractYear(Now()) - ExtractYear(F('policy__customer__date_of_birth'))
        ).annotate(
            age_group=Case(
                When(age_years__lt=25, then=Value('0-24')),
                When(age_years__gte=25, age_years__lt=35, then=Value('25-34')),
                When(age_years__gte=35, age_years__lt=45, then=Value('35-44')),
                When(age_years__gte=45, age_years__lt=55, then=Value('45-54')),
                When(age_years__gte=55, age_years__lt=65, then=Value('55-64')),
                default=Value('65+'),
                output_field=models.CharField(max_length=10)
            )
        )
        qs = (
            qs
              .values('age_group')
              .annotate(avg_amount=Avg('amount'), count=Count('id'), total_amount=Sum('amount'))
              .order_by('age_group')
        )
        return qs

    def claims_per_customer(self, only_with_claims=False):
        from insurance.model.customer import Customer
        customers = Customer.objects.all().values('id', 'full_name')
        qs = (
            self.model.objects
            .values('policy__customer_id')
            .annotate(claims_count=Count('id'))
        )
        from django.db.models import OuterRef, Subquery
        sub = Subquery(qs.filter(policy__customer_id=OuterRef('id')).values('claims_count')[:1])
        annotated = customers.annotate(claims_count=sub)
        if only_with_claims:
            annotated = annotated.filter(claims_count__gt=0)
        return annotated.order_by('-claims_count', 'full_name')