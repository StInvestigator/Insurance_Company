from rest_framework.routers import DefaultRouter
from .view.claim_view import ClaimView
from .view.customer_view import CustomerView
from .view.insurance_policy_view import InsurancePolicyView
from .view.payment_view import PaymentView

router = DefaultRouter()
router.register('customers', CustomerView, basename="customer")
router.register('policies', InsurancePolicyView,  basename="policy")
router.register('claims', ClaimView,  basename="claim")
router.register('payments', PaymentView,  basename="payment")

urlpatterns = router.urls
