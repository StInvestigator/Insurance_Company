from rest_framework.routers import DefaultRouter
from .view.claim_view import ClaimView
from .view.customer_view import CustomerView
from .view.insurance_policy_view import InsurancePolicyView
from .view.payment_view import PaymentView

router = DefaultRouter()
router.register(r'customers', CustomerView, basename="customer")
router.register(r'policies', InsurancePolicyView,  basename="policy")
router.register(r'claims', ClaimView,  basename="claim")
router.register(r'payments', PaymentView,  basename="payment")

urlpatterns = router.urls
