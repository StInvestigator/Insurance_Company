from datetime import date, timedelta
from typing import Any, Dict, List
import logging
import math
import requests
from urllib.parse import urljoin
from collections import Counter, defaultdict

from django.views.generic import TemplateView

# Plotly imports (for V1)
import plotly.graph_objects as go
import plotly.io as pio

# Bokeh imports (for V2)
from bokeh.embed import components
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource

logger = logging.getLogger(__name__)

API_BASE = "/api/analytics"

def _parse_params(request) -> Dict[str, Any]:
    df = request.GET.get('date_from') or ''
    dt = request.GET.get('date_to') or ''
    pt = request.GET.get('policy_type') or ''
    try:
        limit = int(request.GET.get('limit') or '10')
    except Exception:
        limit = 10
    try:
        threshold = float(request.GET.get('threshold') or '0')
    except Exception:
        threshold = 0.0
    def _parse_date(s: str):
        if not s:
            return None
        try:
            y, m, d = map(int, s.split('-'))
            return date(y, m, d)
        except Exception:
            return None
    return {
        'date_from': _parse_date(df),
        'date_to': _parse_date(dt),
        'policy_type': pt.strip() or None,
        'limit': max(1, limit),
        'threshold': threshold,
    }

def _to_list_from_api(obj) -> List[Dict]:
    if obj is None:
        return []
    if isinstance(obj, list):
        return obj
    try:
        return list(obj)
    except Exception:
        return []

def _days_from_timedelta_str(s: str | None) -> float | None:
    if not s:
        return None
    try:
        if isinstance(s, str) and 'day' in s:
            return float(s.split('day')[0].strip().replace(',', ''))
    except Exception:
        pass
    return None

def _timedelta_to_days(val) -> float | None:
    if val is None:
        return None
    try:
        if hasattr(val, "days") and hasattr(val, "seconds"):
            return float(val.days + val.seconds / 86400.0)
        if isinstance(val, timedelta):
            return float(val.days + val.seconds / 86400.0)
        if isinstance(val, str) and 'day' in val:
            return float(val.split('day')[0].strip().replace(',', ''))
        try:
            return float(val)
        except Exception:
            return None
    except Exception:
        pass
    return None

def api_get(request, path: str, params: Dict[str, Any] = None, timeout=6):
    """
    Perform GET to analytics API and return parsed JSON.
    - path: relative path after API_BASE, e.g. 'payments-by-month'
    - params: dict of query params (values must be serializable)
    """
    base = API_BASE
    if not base.endswith('/'):
        base = base + '/'
    url = urljoin(request.build_absolute_uri('/'), '')
    api_root = urljoin(url, base.lstrip('/'))
    full = urljoin(api_root, path.lstrip('/'))
    try:
        # Convert date objects to ISO strings if present
        qs = {}
        if params:
            for k, v in params.items():
                if v is None:
                    continue
                if isinstance(v, date):
                    qs[k] = v.isoformat()
                else:
                    qs[k] = str(v)
        resp = requests.get(full, params=qs, timeout=timeout)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        logger.exception("analytics API request failed: %s %s", full, e)
        return None
    except ValueError as e:
        logger.exception("analytics API returned non-json for %s: %s", full, e)
        return None

# -------------------------
# Analytics Dashboard V1 (Plotly) using REST API
# -------------------------
class AnalyticsDashboardV1View(TemplateView):
    template_name = 'analytics/dashboard_v1.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        p = _parse_params(self.request)

        # call API endpoints
        r1 = api_get(self.request, 'payments-by-month', params={
            'date_from': p['date_from'],
            'date_to': p['date_to'],
            'policy_type': p['policy_type']
        }) or {}
        r2 = api_get(self.request, 'avg-claim-by-age-group', params={
            'date_from': p['date_from'],
            'date_to': p['date_to'],
        }) or {}
        r3 = api_get(self.request, 'claims-per-customer', params={
            'only_with_claims': 'false',
        }) or {}
        r4 = api_get(self.request, 'policy-profit-by-type', params={
            'date_from': p['date_from'],
            'date_to': p['date_to'],
        }) or {}
        r5 = api_get(self.request, 'time-to-claim') or {}
        r6 = api_get(self.request, 'top-customers-by-payouts', params={
            'limit': p['limit'],
            'threshold': p['threshold'],
            'date_from': p['date_from'],
            'date_to': p['date_to']
        }) or {}

        data1 = _to_list_from_api(r1.get('data') if isinstance(r1, dict) else r1)
        data2 = _to_list_from_api(r2.get('data') if isinstance(r2, dict) else r2)
        data3 = _to_list_from_api(r3.get('data') if isinstance(r3, dict) else r3)
        data4 = _to_list_from_api(r4.get('data') if isinstance(r4, dict) else r4)
        data5 = _to_list_from_api(r5.get('data') if isinstance(r5, dict) else r5)
        data6 = _to_list_from_api(r6.get('data') if isinstance(r6, dict) else r6)

        for item in data5:
            if 'delta' in item:
                item['days'] = _timedelta_to_days(item['delta'])

        def _to_plotly_html(fig):
            return pio.to_html(fig, include_plotlyjs=False, full_html=False)

        # 1) Payments by month and policy type (bar)
        if data1:
            x = []
            y = []
            for item in data1:
                month = str(item.get('month', item.get('ptype', '')))
                ptype = str(item.get('ptype', item.get('policy_type', '')))
                x.append(f"{month} / {ptype}")
                y.append(float(item.get('total_amount', 0)))
        else:
            x, y = [], []
        fig1 = go.Figure(data=[go.Bar(x=x, y=y)]) if x else go.Figure()
        fig1.update_layout(title='Payments by month and policy type', margin=dict(t=40))
        c1_html = _to_plotly_html(fig1)

        # 2) Avg claim by age group
        if data2:
            x2 = [str(item.get('age_group', '')) for item in data2]
            y2 = [float(item.get('avg_amount', 0)) for item in data2]
            fig2 = go.Figure(data=[go.Bar(x=x2, y=y2)])
        else:
            fig2 = go.Figure()
            fig2.update_layout(title='Average claim amount by age group (no data)')
        fig2.update_layout(title='Average claim amount by age group', margin=dict(t=40))
        c2_html = _to_plotly_html(fig2)

        # 3) Claims per customer distribution -> use Bar if discrete 0/1 or few unique values
        if data3:
            vals = []
            for item in data3:
                try:
                    val = int(item.get('claims_count', 0) or 0)
                    vals.append(val)
                except (ValueError, TypeError):
                    vals.append(0)
            uniq = sorted(set(vals))
            if len(uniq) <= 6:
                counts = Counter(vals)
                x3 = sorted(counts.keys())
                y3 = [counts[k] for k in x3]
                fig3 = go.Figure(data=[go.Bar(x=x3, y=y3)])
                fig3.update_layout(title='Claims per customer (counts)', xaxis_title='Number of claims', yaxis_title='Customers')
            else:
                nbins = min(50, max(1, int(math.sqrt(len(vals)))))
                fig3 = go.Figure(data=[go.Histogram(x=vals, nbinsx=nbins)])
                fig3.update_layout(title='Claims per customer distribution', xaxis_title='Number of claims', yaxis_title='Frequency')
        else:
            fig3 = go.Figure()
            fig3.update_layout(title='Claims per customer distribution (no data)')
        c3_html = _to_plotly_html(fig3)

        # 4) Policy profit by type (pie fallback to bar)
        if data4:
            profit_by_type = defaultdict(float)
            for item in data4:
                ptype = item.get('policy_type', '')
                try:
                    profit = float(item.get('profit', 0) or 0)
                    profit_by_type[ptype] += profit
                except (ValueError, TypeError):
                    pass
            pos = {k: v for k, v in profit_by_type.items() if v > 0}
            if pos:
                labels4 = list(pos.keys())
                values4 = list(pos.values())
                fig4 = go.Figure(data=[go.Pie(labels=labels4, values=values4)])
                fig4.update_layout(title='Policy profit by type')
            else:
                labels4 = list(profit_by_type.keys())
                values4 = list(profit_by_type.values())
                fig4 = go.Figure(data=[go.Bar(x=labels4, y=values4)])
        else:
            fig4 = go.Figure()
            fig4.update_layout(title='Policy profit by type (no data)')
        c4_html = _to_plotly_html(fig4)

        # 5) Time to first claim per policy type
        traces5 = []
        if data5:
            by_type = defaultdict(list)
            for item in data5:
                ptype = item.get('policy_type')
                days = item.get('days')
                if ptype is not None and days is not None:
                    try:
                        by_type[ptype].append(float(days))
                    except (ValueError, TypeError):
                        pass
            for ptype, ys in by_type.items():
                if ys:
                    traces5.append(go.Box(name=str(ptype), y=ys))
        if traces5:
            fig5 = go.Figure(data=traces5)
            fig5.update_layout(title='Time to first claim (days) per policy type')
        else:
            fig5 = go.Figure()
            fig5.update_layout(title='Time to first claim (days) per policy type (no data)')
        c5_html = _to_plotly_html(fig5)

        # 6) Top customers by payouts
        if data6:
            x6 = []
            y6 = []
            for item in data6:
                name = (item.get('claim__policy__customer__full_name') or 
                       item.get('full_name') or 
                       item.get('customer__full_name') or 
                       '')
                x6.append(str(name))
                try:
                    y6.append(float(item.get('total_payout', 0) or 0))
                except (ValueError, TypeError):
                    y6.append(0.0)
            fig6 = go.Figure(data=[go.Bar(x=x6, y=y6)])
            fig6.update_layout(title='Top customers by payouts')
        else:
            fig6 = go.Figure()
            fig6.update_layout(title='Top customers by payouts (no data)')
        c6_html = _to_plotly_html(fig6)

        ctx.update({
            'params': p,
            'c1_html': c1_html,
            'c2_html': c2_html,
            'c3_html': c3_html,
            'c4_html': c4_html,
            'c5_html': c5_html,
            'c6_html': c6_html,
        })
        return ctx

# -------------------------
# Analytics Dashboard V2 (Bokeh) using REST API
# -------------------------
class AnalyticsDashboardV2View(TemplateView):
    template_name = 'analytics/dashboard_v2.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        p = _parse_params(self.request)

        # call API endpoints
        r1 = api_get(self.request, 'payments-by-month', params={
            'date_from': p['date_from'],
            'date_to': p['date_to'],
            'policy_type': p['policy_type']
        }) or {}
        r2 = api_get(self.request, 'avg-claim-by-age-group', params={
            'date_from': p['date_from'],
            'date_to': p['date_to'],
        }) or {}
        r3 = api_get(self.request, 'claims-per-customer', params={
            'only_with_claims': 'false',
        }) or {}
        r4 = api_get(self.request, 'policy-profit-by-type', params={
            'date_from': p['date_from'],
            'date_to': p['date_to'],
        }) or {}
        r5 = api_get(self.request, 'time-to-claim') or {}
        r6 = api_get(self.request, 'top-customers-by-payouts', params={
            'limit': p['limit'],
            'threshold': p['threshold'],
            'date_from': p['date_from'],
            'date_to': p['date_to']
        }) or {}

        data1 = _to_list_from_api(r1.get('data') if isinstance(r1, dict) else r1)
        data2 = _to_list_from_api(r2.get('data') if isinstance(r2, dict) else r2)
        data3 = _to_list_from_api(r3.get('data') if isinstance(r3, dict) else r3)
        data4 = _to_list_from_api(r4.get('data') if isinstance(r4, dict) else r4)
        data5 = _to_list_from_api(r5.get('data') if isinstance(r5, dict) else r5)
        data6 = _to_list_from_api(r6.get('data') if isinstance(r6, dict) else r6)

        for item in data5:
            if 'delta' in item:
                item['days'] = _timedelta_to_days(item['delta'])

        # 1) Payments by month and policy type
        if data1:
            x1 = []
            y1 = []
            for item in data1[:32]:
                month = str(item.get('month', ''))
                ptype = str(item.get('ptype', item.get('policy_type', '')))
                x1.append(f"{month} / {ptype}")
                try:
                    y1.append(float(item.get('total_amount', 0) or 0))
                except (ValueError, TypeError):
                    y1.append(0.0)
        else:
            x1, y1 = [], []
        src1 = ColumnDataSource(dict(x=x1, y=y1))
        if x1:
            f1 = figure(x_range=x1, height=350, title='Payments by month and policy type')
        else:
            f1 = figure(height=350, title='Payments by month and policy type')
            
        f1.xaxis.major_label_orientation = "vertical"
        f1.vbar(x='x', top='y', source=src1, width=0.8)
        c1_script, c1_div = components(f1)

        # 2) Avg claim by age group
        x2 = [str(item.get('age_group', '')) for item in data2] if data2 else []
        y2 = []
        if data2:
            for item in data2:
                try:
                    y2.append(float(item.get('avg_amount', 0) or 0))
                except (ValueError, TypeError):
                    y2.append(0.0)
        src2 = ColumnDataSource(dict(x=x2, y=y2))
        if x2:
            f2 = figure(x_range=x2, height=350, title='Average claim amount by age group')
        else:
            f2 = figure(height=350, title='Average claim amount by age group')
        f2.vbar(x='x', top='y', source=src2, width=0.8)
        c2_script, c2_div = components(f2)

        # 3) Claims per customer (bar for discrete)
        x3 = []
        if data3:
            for item in data3:
                try:
                    x3.append(int(item.get('claims_count', 0) or 0))
                except (ValueError, TypeError):
                    x3.append(0)
        
        if x3:
            bins = min(10, max(1, len(set(x3)) or 1))
            min_val, max_val = min(x3), max(x3)
            if min_val == max_val:
                hist, edges = [len(x3)], [min_val, max_val + 1]
            else:
                bin_width = (max_val - min_val) / bins
                edges = [min_val + i * bin_width for i in range(bins + 1)]
                hist = [0] * bins
                for val in x3:
                    idx = min(int((val - min_val) / bin_width), bins - 1)
                    hist[idx] += 1
        else:
            hist, edges = [], [0, 1]
        src3 = ColumnDataSource(dict(top=hist if len(hist) else [], left=edges[:-1] if len(edges)>1 else [0], right=edges[1:] if len(edges)>1 else [1]))
        f3 = figure(height=350, title='Claims per customer distribution')
        f3.quad(top='top', bottom=0, left='left', right='right', source=src3)
        c3_script, c3_div = components(f3)

        # 4) Policy profit by type -> pie (wedge) or placeholder
        x4 = [str(item.get('policy_type', '')) for item in data4] if data4 else []
        y4 = []
        if data4:
            for item in data4:
                try:
                    y4.append(float(item.get('profit', 0) or 0))
                except (ValueError, TypeError):
                    y4.append(0.0)
        src4 = ColumnDataSource(dict(x=x4, y=y4))
        f4 = figure(x_range=x4, height=350, title='Policy profit by type')
        f4.vbar(x='x', top='y', source=src4, width=0.8)
        c4_script, c4_div = components(f4)

        # 5) Time to first claim (scatter per type)
        if data5:
            by_type = defaultdict(list)
            for item in data5:
                ptype = item.get('policy_type')
                days = item.get('days')
                if ptype is not None and days is not None:
                    try:
                        by_type[ptype].append(float(days))
                    except (ValueError, TypeError):
                        pass
            policy_types = sorted(by_type.keys())
            if policy_types:
                f5 = figure(height=350, title='Time to first claim (days) per policy type', x_range=policy_types, y_axis_label='Days')
                for ptype in policy_types:
                    ys = by_type[ptype]
                    if ys:
                        xs = [ptype] * len(ys)
                        src = ColumnDataSource(dict(x=xs, y=ys))
                        f5.scatter(x='x', y='y', size=6, alpha=0.6, source=src, legend_label=str(ptype))
                f5.legend.visible = False
                f5.xaxis.axis_label = 'Policy Type'
            else:
                f5 = figure(height=350, title='Time to first claim (days) per policy type')
        else:
            f5 = figure(height=350, title='Time to first claim (days) per policy type')
        c5_script, c5_div = components(f5)

        # 6) Top customers by payouts
        if data6:
            x6 = []
            y6 = []
            for item in data6:
                name = (item.get('claim__policy__customer__full_name') or 
                       item.get('full_name') or 
                       item.get('customer__full_name') or 
                       '')
                x6.append(str(name))
                try:
                    y6.append(float(item.get('total_payout', 0) or 0))
                except (ValueError, TypeError):
                    y6.append(0.0)
            src6 = ColumnDataSource(dict(x=x6, y=y6))
            f6 = figure(x_range=x6 if x6 else None, height=350, title='Top customers by payouts')
            if x6:
                f6.vbar(x='x', top='y', source=src6, width=0.8)
                f6.xaxis.major_label_orientation = "vertical"
        else:
            f6 = figure(height=350, title='Top customers by payouts')
        c6_script, c6_div = components(f6)

        ctx.update({
            'params': p,
            'c1_script': c1_script, 'c1_div': c1_div,
            'c2_script': c2_script, 'c2_div': c2_div,
            'c3_script': c3_script, 'c3_div': c3_div,
            'c4_script': c4_script, 'c4_div': c4_div,
            'c5_script': c5_script, 'c5_div': c5_div,
            'c6_script': c6_script, 'c6_div': c6_div,
        })
        return ctx
