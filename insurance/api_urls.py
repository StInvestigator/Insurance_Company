from rest_framework.routers import DefaultRouter
from .view.ClaimView import ClaimView
from .view.CustomerView import CustomerView
from .view.InsurancePolicyView import InsurancePolicyView
from .view.PaymentView import PaymentView

router = DefaultRouter()
router.register('customers', CustomerView, basename="customer")
router.register('policies', InsurancePolicyView,  basename="policy")
router.register('claims', ClaimView,  basename="claim")
router.register('payments', PaymentView,  basename="payment")

urlpatterns = router.urls
