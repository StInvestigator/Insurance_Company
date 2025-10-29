from rest_framework.routers import DefaultRouter
from .views.ClaimViewSet import ClaimViewSet
from .views.CustomerViewSet import CustomerViewSet
from .views.InsurancePolicyViewSet import InsurancePolicyViewSet
from .views.PaymentViewSet import PaymentViewSet

router = DefaultRouter()
router.register(r'customers', CustomerViewSet, basename="customer")
router.register(r'policies', InsurancePolicyViewSet,  basename="policies")
router.register(r'claims', ClaimViewSet,  basename="claims")
router.register(r'payments', PaymentViewSet,  basename="payments")

urlpatterns = router.urls
