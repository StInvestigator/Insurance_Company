from rest_framework.routers import DefaultRouter
from .views import CustomerViewSet, InsurancePolicyViewSet, ClaimViewSet, PaymentViewSet

router = DefaultRouter()
router.register(r'customers', CustomerViewSet)
router.register(r'policies', InsurancePolicyViewSet)
router.register(r'claims', ClaimViewSet)
router.register(r'payments', PaymentViewSet)

urlpatterns = router.urls
