from django.views.generic import TemplateView


class AnalyticsDashboardV1View(TemplateView):
    template_name = 'analytics/dashboard_v1.html'


class AnalyticsDashboardV2View(TemplateView):
    template_name = 'analytics/dashboard_v2.html'
