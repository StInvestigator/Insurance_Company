from rest_framework.routers import DefaultRouter
from .api_view.claim_view import ClaimView
from .api_view.customer_view import CustomerView
from .api_view.insurance_policy_view import InsurancePolicyView
from .api_view.payment_view import PaymentView
from .api_view.analytics_view import AnalyticsView

router = DefaultRouter()
router.register(r'customers', CustomerView, basename="customer")
router.register(r'policies', InsurancePolicyView,  basename="policy")
router.register(r'claims', ClaimView,  basename="claim")
router.register(r'payments', PaymentView,  basename="payment")
router.register(r'analytics', AnalyticsView, basename="analytics")

urlpatterns = router.urls
