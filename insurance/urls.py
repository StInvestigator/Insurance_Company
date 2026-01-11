from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from insurance.api_view.register_view import RegisterView
from insurance.template_view import (
    InsurancePolicyListView,
    InsurancePolicyDetailView,
    InsurancePolicyCreateView,
    InsurancePolicyUpdateView,
    InsurancePolicyDeleteView,
    ClaimsByCustomerListView,
    CustomerListView,
    CustomerDetailView,
    CustomerCreateView,
    CustomerUpdateView,
    CustomerDeleteView,
    PaymentListView,
    PaymentDetailView,
    PaymentCreateView,
    PaymentUpdateView,
    PaymentDeleteView,
    ClaimListView,
    ClaimDetailView,
    ClaimCreateView,
    ClaimUpdateView,
    ClaimDeleteView,
    HomeView,
)
from insurance.template_view.auth_view import RegisterPageView, SiteLoginView, SiteLogoutView
from insurance.template_view.analytics_view import AnalyticsDashboardV1View, AnalyticsDashboardV2View
from insurance.template_view.db_optimization_view import DatabaseOptimizationDashboardView

app_name = 'insurance'
urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('admin/', admin.site.urls),
    # Auth: override default login/logout to inject JWT handling
    path('accounts/login/', SiteLoginView.as_view(), name='login'),
    path('accounts/logout/', SiteLogoutView.as_view(), name='logout'),
    # Registration page (calls API under the hood)
    path('register/', RegisterPageView.as_view(), name='register_page'),
    # Keep other auth URLs (password reset etc.)
    path('accounts/', include('django.contrib.auth.urls')),
    path('api/', include('insurance.api_urls')),
    path('api/register/', RegisterView.as_view(), name='register'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    path('analytics/dashboard/v1', AnalyticsDashboardV1View.as_view(), name='analytics_dashboard_v1'),
    path('analytics/dashboard/v2', AnalyticsDashboardV2View.as_view(), name='analytics_dashboard_v2'),
    path('analytics/db-optimization/', DatabaseOptimizationDashboardView.as_view(), name='db_optimization_dashboard'),
    # path('analytics/db-optimization/run/', run_optimization_experiment, name='run_db_optimization'),
    path('claims/byCustomer/<int:pk>/', ClaimsByCustomerListView.as_view(), name='claims_by_customer_list'),

    # Customers
    path('customers/', CustomerListView.as_view(), name='customer_list'),
    path('customers/create/', CustomerCreateView.as_view(), name='customer_create'),
    path('customers/<int:pk>/', CustomerDetailView.as_view(), name='customer_detail'),
    path('customers/<int:pk>/edit/', CustomerUpdateView.as_view(), name='customer_edit'),
    path('customers/<int:pk>/delete/', CustomerDeleteView.as_view(), name='customer_delete'),

    # Payments
    path('payments/', PaymentListView.as_view(), name='payment_list'),
    path('payments/create/', PaymentCreateView.as_view(), name='payment_create'),
    path('payments/<int:pk>/', PaymentDetailView.as_view(), name='payment_detail'),
    path('payments/<int:pk>/edit/', PaymentUpdateView.as_view(), name='payment_edit'),
    path('payments/<int:pk>/delete/', PaymentDeleteView.as_view(), name='payment_delete'),

    # Claims
    path('claims/', ClaimListView.as_view(), name='claim_list'),
    path('claims/create/', ClaimCreateView.as_view(), name='claim_create'),
    path('claims/<int:pk>/', ClaimDetailView.as_view(), name='claim_detail'),
    path('claims/<int:pk>/edit/', ClaimUpdateView.as_view(), name='claim_edit'),
    path('claims/<int:pk>/delete/', ClaimDeleteView.as_view(), name='claim_delete'),

    path('policies/', InsurancePolicyListView.as_view(), name='policy_list'),
    path('policies/create/', InsurancePolicyCreateView.as_view(), name='policy_create'),
    path('policies/<int:pk>/', InsurancePolicyDetailView.as_view(), name='policy_detail'),
    path('policies/<int:pk>/edit/', InsurancePolicyUpdateView.as_view(), name='policy_edit'),
    path('policies/<int:pk>/delete/', InsurancePolicyDeleteView.as_view(), name='policy_delete'),
]

handler401 = 'insurance.template_view.error_view.custom_401'
handler404 = 'insurance.template_view.error_view.custom_404'
handler500 = 'insurance.template_view.error_view.custom_500'
handler403 = 'insurance.template_view.error_view.custom_403'
