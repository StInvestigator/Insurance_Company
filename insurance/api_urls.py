from rest_framework.routers import DefaultRouter
from .api_view.claim_view import ClaimView
from .api_view.customer_view import CustomerView
from .api_view.insurance_policy_view import InsurancePolicyView
from .api_view.payment_view import PaymentView

router = DefaultRouter()
router.register(r'customers', CustomerView, basename="customer")
router.register(r'policies', InsurancePolicyView,  basename="policy")
router.register(r'claims', ClaimView,  basename="claim")
router.register(r'payments', PaymentView,  basename="payment")

urlpatterns = router.urls
