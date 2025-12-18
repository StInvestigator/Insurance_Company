# Re-export views for convenient imports
from .policy_view import (
    InsurancePolicyListView,
    InsurancePolicyDetailView,
    InsurancePolicyCreateView,
    InsurancePolicyUpdateView,
    InsurancePolicyDeleteView,
)
from .claims_view import (
    ClaimsByCustomerListView,
    ClaimListView,
    ClaimDetailView,
    ClaimCreateView,
    ClaimUpdateView,
    ClaimDeleteView,
)
from .customer_view import (
    CustomerListView,
    CustomerDetailView,
    CustomerCreateView,
    CustomerUpdateView,
    CustomerDeleteView,
)
from .payment_view import (
    PaymentListView,
    PaymentDetailView,
    PaymentCreateView,
    PaymentUpdateView,
    PaymentDeleteView,
)
from .home_view import HomeView

__all__ = [
    'InsurancePolicyListView',
    'InsurancePolicyDetailView',
    'InsurancePolicyCreateView',
    'InsurancePolicyUpdateView',
    'InsurancePolicyDeleteView',
    'ClaimsByCustomerListView',
    'ClaimListView',
    'ClaimDetailView',
    'ClaimCreateView',
    'ClaimUpdateView',
    'ClaimDeleteView',
    'CustomerListView',
    'CustomerDetailView',
    'CustomerCreateView',
    'CustomerUpdateView',
    'CustomerDeleteView',
    'PaymentListView',
    'PaymentDetailView',
    'PaymentCreateView',
    'PaymentUpdateView',
    'PaymentDeleteView',
    'HomeView',
]
