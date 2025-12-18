from datetime import date
from typing import Any, Dict
import logging
import math
import requests
from urllib.parse import urljoin

import pandas as pd
import numpy as np
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

def _to_df_from_api(obj) -> pd.DataFrame:
    """Converts API response 'data' (list/dict/iterable) to DataFrame safely."""
    if obj is None:
        return pd.DataFrame([])
    if isinstance(obj, pd.DataFrame):
        return obj
    if isinstance(obj, list):
        try:
            return pd.DataFrame(obj)
        except Exception:
            return pd.DataFrame([])
    try:
        return pd.DataFrame(list(obj))
    except Exception:
        return pd.DataFrame([])

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
        if pd.notnull(val):
            if hasattr(val, "days") and hasattr(val, "seconds"):
                return float(val.days + val.seconds / 86400.0)
            if isinstance(val, (pd.Timedelta,)):
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

        df1 = _to_df_from_api(r1.get('data') if isinstance(r1, dict) else r1)
        df2 = _to_df_from_api(r2.get('data') if isinstance(r2, dict) else r2)
        df3 = _to_df_from_api(r3.get('data') if isinstance(r3, dict) else r3)
        df4 = _to_df_from_api(r4.get('data') if isinstance(r4, dict) else r4)
        df5 = _to_df_from_api(r5.get('data') if isinstance(r5, dict) else r5)
        df6 = _to_df_from_api(r6.get('data') if isinstance(r6, dict) else r6)

        if not df5.empty and 'delta' in df5.columns:
            df5['days'] = df5['delta'].apply(lambda d: _timedelta_to_days(d))

        def _to_plotly_html(fig):
            return pio.to_html(fig, include_plotlyjs=False, full_html=False)

        # 1) Payments by month and policy type (bar)
        if not df1.empty:
            month_col = 'month' if 'month' in df1.columns else (df1.columns[0] if len(df1.columns) else '')
            ptype_col = 'ptype' if 'ptype' in df1.columns else ('policy_type' if 'policy_type' in df1.columns else None)
            month_series = df1.get(month_col, pd.Series([], dtype=object)).astype(str)
            ptype_series = df1[ptype_col].astype(str) if ptype_col and ptype_col in df1.columns else pd.Series([''] * len(month_series))
            x = (month_series + ' / ' + ptype_series).tolist()
            y = df1.get('total_amount', pd.Series([0] * len(x))).astype(float).tolist() if len(x) else []
        else:
            x, y = [], []
        fig1 = go.Figure(data=[go.Bar(x=x, y=y)]) if x else go.Figure()
        fig1.update_layout(title='Payments by month and policy type', margin=dict(t=40))
        c1_html = _to_plotly_html(fig1)

        # 2) Avg claim by age group
        if not df2.empty and 'age_group' in df2.columns and 'avg_amount' in df2.columns:
            fig2 = go.Figure(data=[go.Bar(x=df2['age_group'].astype(str).tolist(), y=df2['avg_amount'].astype(float).tolist())])
        else:
            fig2 = go.Figure()
            fig2.update_layout(title='Average claim amount by age group (no data)')
        fig2.update_layout(title='Average claim amount by age group', margin=dict(t=40))
        c2_html = _to_plotly_html(fig2)

        # 3) Claims per customer distribution -> use Bar if discrete 0/1 or few unique values
        if not df3.empty and 'claims_count' in df3.columns:
            df3['claims_count'] = pd.to_numeric(df3['claims_count'], errors='coerce').fillna(0).astype(int)
            vals = df3['claims_count'].tolist()
            uniq = sorted(set(vals))
            if len(uniq) <= 6:
                counts = df3['claims_count'].value_counts().sort_index()
                fig3 = go.Figure(data=[go.Bar(x=list(counts.index.astype(int)), y=counts.to_list())])
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
        if not df4.empty and 'policy_type' in df4.columns and 'profit' in df4.columns:
            df4_local = df4.copy()
            df4_local['profit'] = pd.to_numeric(df4_local['profit'], errors='coerce').fillna(0.0).astype(float)
            agg = df4_local.groupby('policy_type', as_index=False)['profit'].sum()
            pos = agg[agg['profit'] > 0]
            if not pos.empty:
                labels4 = pos['policy_type'].astype(str).tolist()
                values4 = pos['profit'].astype(float).tolist()
                fig4 = go.Figure(data=[go.Pie(labels=labels4, values=values4)])
                fig4.update_layout(title='Policy profit by type')
            else:
                fig4 = go.Figure(data=[go.Bar(x=agg['policy_type'].astype(str).tolist(), y=agg['profit'].astype(float).tolist())])
        else:
            fig4 = go.Figure()
            fig4.update_layout(title='Policy profit by type (no data)')
        c4_html = _to_plotly_html(fig4)

        # 5) Time to first claim per policy type
        traces5 = []
        if not df5.empty and 'policy_type' in df5.columns and 'days' in df5.columns:
            for ptype, grp in df5.groupby('policy_type'):
                ys = grp['days'].dropna().astype(float).tolist()
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
        if not df6.empty:
            name_col = None
            for candidate in ['claim__policy__customer__full_name', 'full_name', 'customer__full_name']:
                if candidate in df6.columns:
                    name_col = candidate
                    break
            if name_col:
                x6 = df6[name_col].astype(str).tolist()
            else:
                x6 = df6.index.astype(str).tolist()
            y6 = pd.to_numeric(df6.get('total_payout', pd.Series([0]*len(x6))), errors='coerce').fillna(0.0).astype(float).tolist()
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

        df1 = _to_df_from_api(r1.get('data') if isinstance(r1, dict) else r1)
        df2 = _to_df_from_api(r2.get('data') if isinstance(r2, dict) else r2)
        df3 = _to_df_from_api(r3.get('data') if isinstance(r3, dict) else r3)
        df4 = _to_df_from_api(r4.get('data') if isinstance(r4, dict) else r4)
        df5 = _to_df_from_api(r5.get('data') if isinstance(r5, dict) else r5)
        df6 = _to_df_from_api(r6.get('data') if isinstance(r6, dict) else r6)

        # parse df5 delta -> days
        if not df5.empty and 'delta' in df5.columns:
            df5['days'] = df5['delta'].apply(lambda d: _timedelta_to_days(d))

        # 1) Payments by month and policy type
        if not df1.empty:
            x1 = (df1.get('month', df1.index.astype(str)).astype(str) + ' / ' + df1.get('ptype', df1.get('policy_type', '')).astype(str)).tolist()
            y1 = pd.to_numeric(df1.get('total_amount', pd.Series([])), errors='coerce').fillna(0).astype(float).tolist()
        else:
            x1, y1 = [], []
        src1 = ColumnDataSource(dict(x=x1, y=y1))
        if x1:
            f1 = figure(x_range=x1, height=350, title='Payments by month and policy type')
        else:
            f1 = figure(height=350, title='Payments by month and policy type')
        f1.vbar(x='x', top='y', source=src1, width=0.8)
        c1_script, c1_div = components(f1)

        # 2) Avg claim by age group
        x2 = df2.get('age_group', pd.Series([], dtype=object)).tolist() if not df2.empty else []
        y2 = pd.to_numeric(df2.get('avg_amount', pd.Series([])), errors='coerce').fillna(0).astype(float).tolist() if not df2.empty else []
        src2 = ColumnDataSource(dict(x=x2, y=y2))
        if x2:
            f2 = figure(x_range=x2, height=350, title='Average claim amount by age group')
        else:
            f2 = figure(height=350, title='Average claim amount by age group')
        f2.vbar(x='x', top='y', source=src2, width=0.8)
        c2_script, c2_div = components(f2)

        # 3) Claims per customer (bar for discrete)
        x3 = df3['claims_count'].fillna(0).astype(int).tolist() if not df3.empty else []
        hist, edges = np.histogram(x3, bins=min(10, max(1, len(set(x3)) or 1))) if x3 else ([], [0, 1])
        src3 = ColumnDataSource(dict(top=hist.tolist() if len(hist) else [], left=edges[:-1].tolist() if len(edges)>1 else [0], right=edges[1:].tolist() if len(edges)>1 else [1]))
        f3 = figure(height=350, title='Claims per customer distribution')
        f3.quad(top='top', bottom=0, left='left', right='right', source=src3)
        c3_script, c3_div = components(f3)

        # 4) Policy profit by type -> pie (wedge) or placeholder
        x4 = df4['policy_type'].tolist() if not df4.empty else []
        y4 = df4['profit'].astype(float).tolist() if not df4.empty else []
        src4 = ColumnDataSource(dict(x=x4, y=y4))
        f4 = figure(x_range=x4, height=350, title='Policy profit by type')
        f4.vbar(x='x', top='y', source=src4, width=0.8)
        c4_script, c4_div = components(f4)

        # 5) Time to first claim (scatter per type)
        if not df5.empty and 'policy_type' in df5.columns and 'days' in df5.columns:
            policy_types = sorted(df5['policy_type'].dropna().unique().tolist())
            f5 = figure(height=350, title='Time to first claim (days) per policy type', x_range=policy_types, y_axis_label='Days')
            for ptype, grp in df5.groupby('policy_type'):
                ys = grp['days'].dropna().astype(float).tolist()
                if ys:
                    xs = [ptype] * len(ys)
                    src = ColumnDataSource(dict(x=xs, y=ys))
                    f5.scatter(x='x', y='y', size=6, alpha=0.6, source=src, legend_label=str(ptype))
            f5.legend.visible = False
            f5.xaxis.axis_label = 'Policy Type'
        else:
            f5 = figure(height=350, title='Time to first claim (days) per policy type')
        c5_script, c5_div = components(f5)

        # 6) Top customers by payouts
        if not df6.empty:
            # normalize name field
            name_col = None
            for candidate in ['claim__policy__customer__full_name', 'full_name', 'customer__full_name']:
                if candidate in df6.columns:
                    name_col = candidate
                    break
            if name_col:
                x6 = df6[name_col].astype(str).tolist()
            else:
                x6 = df6.index.astype(str).tolist()
            y6 = pd.to_numeric(df6.get('total_payout', pd.Series([0]*len(x6))), errors='coerce').fillna(0.0).astype(float).tolist()
            src6 = ColumnDataSource(dict(x=x6, y=y6))
            f6 = figure(x_range=x6 if x6 else None, height=350, title='Top customers by payouts')
            if x6:
                f6.vbar(x='x', top='y', source=src6, width=0.8)
            else:
                pass
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
