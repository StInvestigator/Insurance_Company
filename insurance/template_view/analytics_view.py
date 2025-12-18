from datetime import date
from typing import Any, Dict, List
import math

import pandas as pd
import numpy as np
from django.views.generic import TemplateView

# Plotly
import plotly.graph_objects as go
import plotly.io as pio

from insurance.repository.unit_of_work import UnitOfWork


def _days_from_timedelta_str(s: str | None) -> float | None:
    if not s:
        return None
    try:
        # Pandas/QuerySet delta may be in format 'X days, 00:00:00'
        if isinstance(s, str) and 'day' in s:
            return float(s.split('day')[0].strip().replace(',', ''))
    except Exception:
        pass
    return None

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


def _to_df(rows: List[Dict[str, Any]]) -> pd.DataFrame:
    if isinstance(rows, list):
        try:
            return pd.DataFrame(rows)
        except Exception:
            return pd.DataFrame([])
    try:
        return pd.DataFrame(list(rows))
    except Exception:
        return pd.DataFrame([])


def _timedelta_to_days(val) -> float | None:
    """Convert timedelta-like values (timedelta or string like 'X days, HH:MM:SS') to float days."""
    if val is None:
        return None
    # If it's a pandas Timedelta or python timedelta
    try:
        if pd.notnull(val):
            if hasattr(val, "days") and hasattr(val, "seconds"):
                # pandas.Timedelta or datetime.timedelta
                return float(val.days + val.seconds / 86400.0)
            # if numpy timedelta
            if isinstance(val, np.timedelta64):
                return float(pd.to_timedelta(val).days)
            # if it's a string like '5 days, 00:00:00'
            if isinstance(val, str):
                if 'day' in val:
                    # "5 days, 00:00:00" -> 5
                    return float(val.split('day')[0].strip().replace(',', ''))
                # try to parse simple numeric string
                try:
                    return float(val)
                except Exception:
                    return None
    except Exception:
        pass
    return None


class AnalyticsDashboardV1View(TemplateView):
    template_name = 'analytics/dashboard_v1.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        params = _parse_params(self.request)

        # Fetch all results from repository
        with UnitOfWork() as uow:
            r1 = uow.payments.payments_by_month(params['date_from'], params['date_to'], params['policy_type'])
            r2 = uow.claims.avg_claim_by_age_group(params['date_from'], params['date_to'])
            r3 = uow.claims.claims_per_customer(only_with_claims=False)
            r4 = uow.policies.policy_profit_by_type(params['date_from'], params['date_to'])
            r5 = uow.policies.time_to_first_claim_per_policy()
            r6 = uow.payments.top_customers_by_payouts(limit=params['limit'],
                                                       threshold=params['threshold'],
                                                       date_from=params['date_from'],
                                                       date_to=params['date_to'])

        df1 = _to_df(list(r1))
        df2 = _to_df(list(r2))
        df3 = _to_df(list(r3))
        df4 = _to_df(list(r4))
        df5raw = list(r5)
        df5 = _to_df(df5raw)
        df6 = _to_df(list(r6))

        # Convert df5.delta -> days if present
        if not df5.empty and 'delta' in df5.columns:
            df5['days'] = df5['delta'].apply(lambda d: _timedelta_to_days(d))

        # Helper to safely produce Plotly HTML
        def _to_plotly_html(fig):
            # We assume user template already includes plotly.js
            return pio.to_html(fig, include_plotlyjs=False, full_html=False)

        # 1) Payments by month and policy type (bar)
        try:
            if not df1.empty:
                # try common column names safely
                month_col = 'month' if 'month' in df1.columns else df1.columns[0]
                ptype_col = 'ptype' if 'ptype' in df1.columns else ('policy_type' if 'policy_type' in df1.columns else None)
                month_series = df1.get(month_col, df1.index.astype(str)).astype(str)
                ptype_series = df1[ptype_col].astype(str) if ptype_col and ptype_col in df1.columns else pd.Series([''] * len(month_series))
                x = (month_series + ' / ' + ptype_series).tolist()
                y = df1.get('total_amount', pd.Series([0] * len(x))).astype(float).tolist()
            else:
                x, y = [], []
            fig1 = go.Figure(data=[go.Bar(x=x, y=y)]) if x else go.Figure()
            fig1.update_layout(title='Payments by month and policy type', margin=dict(t=40))
            c1_html = _to_plotly_html(fig1)
        except Exception as e:
            # fallback empty figure
            fig1 = go.Figure()
            fig1.update_layout(title='Payments by month and policy type (error)', margin=dict(t=40))
            c1_html = _to_plotly_html(fig1)

        # 2) Avg claim by age group (bar)
        try:
            if not df2.empty and 'age_group' in df2.columns and 'avg_amount' in df2.columns:
                x2 = df2['age_group'].astype(str).tolist()
                y2 = df2['avg_amount'].astype(float).tolist()
                fig2 = go.Figure(data=[go.Bar(x=x2, y=y2)])
            else:
                fig2 = go.Figure()
                fig2.update_layout(title='Average claim amount by age group (no data)')
            fig2.update_layout(title='Average claim amount by age group', margin=dict(t=40))
            c2_html = _to_plotly_html(fig2)
        except Exception:
            fig2 = go.Figure()
            fig2.update_layout(title='Average claim amount by age group (error)', margin=dict(t=40))
            c2_html = _to_plotly_html(fig2)

        try:
            # debug info (server log) — можно убрать позже
            print("DEBUG df3.columns:", getattr(df3, 'columns', None))
            print("DEBUG df3.head:", None if df3.empty else df3.head().to_dict())

            if not df3.empty and 'claims_count' in df3.columns:
                # принудительно в числовой тип, неудачные -> NaN -> 0
                y3_series = pd.to_numeric(df3['claims_count'], errors='coerce').fillna(0)
                # убрать отрицательные значения, если они бессмысленны
                y3_series = y3_series.clip(lower=0)
                y3 = y3_series.astype(float).tolist()
            else:
                y3 = []

            if y3 and any(v > 0 for v in y3):
                nbins = min(50, max(1, int(math.sqrt(len(y3)))))
                fig3 = go.Figure(data=[go.Histogram(x=y3, nbinsx=nbins)])
                fig3.update_layout(title='Claims per customer distribution', margin=dict(t=40),
                                   xaxis_title='Number of claims', yaxis_title='Frequency')
            elif y3:
                # Все значения нулевые — показать простой столбик "0: count"
                fig3 = go.Figure(data=[go.Bar(x=[0], y=[len(y3)])])
                fig3.update_layout(title='Claims per customer distribution (all zeros)', margin=dict(t=40),
                                   xaxis_title='Number of claims', yaxis_title='Count')
            else:
                fig3 = go.Figure()
                fig3.update_layout(title='Claims per customer distribution (no data)', margin=dict(t=40))

            c3_html = _to_plotly_html(fig3)
        except Exception as e:
            print("ERROR building fig3:", e)
            fig3 = go.Figure()
            fig3.update_layout(title='Claims per customer distribution (error)', margin=dict(t=40))
            c3_html = _to_plotly_html(fig3)

        # 4) Policy profit by type (pie) — robust and fallback to bar
        try:
            # debug info
            print("DEBUG df4.columns:", getattr(df4, 'columns', None))
            print("DEBUG df4.head:", None if df4.empty else df4.head().to_dict())

            if not df4.empty:
                df4_local = df4.copy()

                # нормализуем колонки
                if 'profit' in df4_local.columns:
                    df4_local['profit'] = pd.to_numeric(df4_local['profit'], errors='coerce').fillna(0)
                else:
                    # если profit отсутствует — создаём нулевой столбец
                    df4_local['profit'] = 0.0

                if 'policy_type' not in df4_local.columns:
                    if 'ptype' in df4_local.columns:
                        df4_local['policy_type'] = df4_local['ptype'].astype(str)
                    else:
                        # как fallback — взять индекс
                        df4_local['policy_type'] = df4_local.index.astype(str)

                # агрегируем на случай дублированных типов
                agg = df4_local.groupby('policy_type', as_index=False)['profit'].sum()
                # отфильтруем NaN
                agg = agg[~agg['profit'].isnull()]

                # оставим только положительные прибыли для pie
                agg_pos = agg[agg['profit'] > 0]

                if not agg_pos.empty:
                    labels4 = agg_pos['policy_type'].astype(str).tolist()
                    values4 = agg_pos['profit'].astype(float).tolist()
                    fig4 = go.Figure(data=[go.Pie(labels=labels4, values=values4, sort=False)])
                    fig4.update_layout(title='Policy profit by type', margin=dict(t=40))
                elif not agg.empty:
                    # нет положительных, но есть данные — показать bar с явным указанием (fallback)
                    fig4 = go.Figure(data=[go.Bar(x=agg['policy_type'].astype(str).tolist(),
                                                  y=agg['profit'].astype(float).tolist())])
                    fig4.update_layout(title='Policy profit by type (no positive profits)', margin=dict(t=40),
                                       xaxis_tickangle=-45, xaxis_title='Policy type', yaxis_title='Profit')
                else:
                    fig4 = go.Figure()
                    fig4.update_layout(title='Policy profit by type (no data)', margin=dict(t=40))
            else:
                fig4 = go.Figure()
                fig4.update_layout(title='Policy profit by type (no data)', margin=dict(t=40))

            c4_html = _to_plotly_html(fig4)
        except Exception as e:
            print("ERROR building fig4:", e)
            fig4 = go.Figure()
            fig4.update_layout(title='Policy profit by type (error)', margin=dict(t=40))
            c4_html = _to_plotly_html(fig4)

        # 5) Time to first claim (box by policy type)
        try:
            traces = []
            if not df5.empty and 'policy_type' in df5.columns and 'days' in df5.columns:
                for ptype, grp in df5.groupby('policy_type'):
                    ys = grp['days'].dropna().astype(float).tolist()
                    if ys:
                        traces.append(go.Box(name=str(ptype), y=ys))
            if traces:
                fig5 = go.Figure(data=traces)
            else:
                fig5 = go.Figure()
                fig5.update_layout(title='Time to first claim (days) per policy type (no data)')
            fig5.update_layout(title='Time to first claim (days) per policy type', margin=dict(t=40))
            c5_html = _to_plotly_html(fig5)
        except Exception:
            fig5 = go.Figure()
            fig5.update_layout(title='Time to first claim (days) per policy type (error)', margin=dict(t=40))
            c5_html = _to_plotly_html(fig5)

        # 6) Top customers by payouts
        try:
            # normalize column name if necessary
            cust_col = 'claim__policy__customer__full_name'
            if not df6.empty and cust_col not in df6.columns and 'full_name' in df6.columns:
                df6[cust_col] = df6['full_name']
            if not df6.empty and cust_col in df6.columns and 'total_payout' in df6.columns:
                x6 = df6[cust_col].astype(str).tolist()
                y6 = df6['total_payout'].astype(float).tolist()
                fig6 = go.Figure(data=[go.Bar(x=x6, y=y6)])
            else:
                fig6 = go.Figure()
                fig6.update_layout(title='Top customers by payouts (no data)')
            fig6.update_layout(title='Top customers by payouts', margin=dict(t=40))
            c6_html = _to_plotly_html(fig6)
        except Exception:
            fig6 = go.Figure()
            fig6.update_layout(title='Top customers by payouts (error)', margin=dict(t=40))
            c6_html = _to_plotly_html(fig6)

        # put everything into context
        ctx.update({
            'params': params,
            'c1_html': c1_html,
            'c2_html': c2_html,
            'c3_html': c3_html,
            'c4_html': c4_html,
            'c5_html': c5_html,
            'c6_html': c6_html,
        })
        return ctx


class AnalyticsDashboardV2View(TemplateView):
    template_name = 'analytics/dashboard_v2.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        p = _parse_params(self.request)
        with UnitOfWork() as uow:
            r1 = uow.payments.payments_by_month(p['date_from'], p['date_to'], p['policy_type'])
            r2 = uow.claims.avg_claim_by_age_group(p['date_from'], p['date_to'])
            r3 = uow.claims.claims_per_customer(only_with_claims=False)
            r4 = uow.policies.policy_profit_by_type(p['date_from'], p['date_to'])
            r5 = uow.policies.time_to_first_claim_per_policy()
            r6 = uow.payments.top_customers_by_payouts(limit=p['limit'], threshold=p['threshold'], date_from=p['date_from'], date_to=p['date_to'])

        df1 = _to_df(list(r1))
        df2 = _to_df(list(r2))
        df3 = _to_df(list(r3))
        df4 = _to_df(list(r4))
        df5raw = list(r5)
        df5 = _to_df(df5raw)
        if not df5.empty:
            if 'delta' in df5.columns:
                df5['days'] = df5['delta'].astype(str).apply(_days_from_timedelta_str)
        df6 = _to_df(list(r6))

        from bokeh.embed import components
        from bokeh.plotting import figure
        from bokeh.models import ColumnDataSource

        # 1) Payments by month and policy type (bar)
        x1 = (df1['month'].astype(str) + ' / ' + df1['ptype'].astype(str)).tolist() if not df1.empty else []
        y1 = df1['total_amount'].astype(float).tolist() if not df1.empty else []
        src1 = ColumnDataSource(dict(x=x1, y=y1))
        f1 = figure(x_range=x1, height=350, title='Payments by month and policy type')
        f1.vbar(x='x', top='y', source=src1, width=0.8)
        c1_script, c1_div = components(f1)

        # 2) Avg claim by age group (bar)
        x2 = df2['age_group'].tolist() if not df2.empty else []
        y2 = df2['avg_amount'].astype(float).tolist() if not df2.empty else []
        src2 = ColumnDataSource(dict(x=x2, y=y2))
        f2 = figure(x_range=x2, height=350, title='Average claim amount by age group')
        f2.vbar(x='x', top='y', source=src2, width=0.8)
        c2_script, c2_div = components(f2)

        # 3) Claims per customer (hist)
        x3 = df3['claims_count'].fillna(0).astype(int).tolist() if not df3.empty else []
        # Approximate histogram by binning on server
        import numpy as np
        hist, edges = np.histogram(x3, bins=min(10, max(1, len(set(x3)) or 1))) if x3 else ([], [0, 1])
        src3 = ColumnDataSource(dict(top=hist.tolist() if len(hist) else [], left=edges[:-1].tolist() if len(edges)>1 else [0], right=edges[1:].tolist() if len(edges)>1 else [1]))
        f3 = figure(height=350, title='Claims per customer distribution')
        f3.quad(top='top', bottom=0, left='left', right='right', source=src3)
        c3_script, c3_div = components(f3)

        # 4) Policy profit by type (bar as pie is heavier in bokeh without extra)
        x4 = df4['policy_type'].tolist() if not df4.empty else []
        y4 = df4['profit'].astype(float).tolist() if not df4.empty else []
        src4 = ColumnDataSource(dict(x=x4, y=y4))
        f4 = figure(x_range=x4, height=350, title='Policy profit by type')
        f4.vbar(x='x', top='y', source=src4, width=0.8)
        c4_script, c4_div = components(f4)

        # 5) Time to first claim (box-like via jitter bars simplified)
        # For simplicity, draw scatter per type (boxplot in bokeh requires more setup)
        f5 = figure(height=350, title='Time to first claim (days) per policy type')
        if not df5.empty and 'policy_type' in df5.columns and 'days' in df5.columns:
            for ptype, grp in df5.groupby('policy_type'):
                xs = [str(ptype)] * len(grp)
                ys = grp['days'].dropna().astype(float).tolist()
                src = ColumnDataSource(dict(x=xs, y=ys))
                f5.scatter(x='x', y='y', size=6, alpha=0.6, source=src, legend_label=str(ptype))
        c5_script, c5_div = components(f5)

        # 6) Top customers by payouts (bar)
        x6 = df6['claim__policy__customer__full_name'].tolist() if not df6.empty else []
        y6 = df6['total_payout'].astype(float).tolist() if not df6.empty else []
        src6 = ColumnDataSource(dict(x=x6, y=y6))
        f6 = figure(x_range=x6, height=350, title='Top customers by payouts')
        f6.vbar(x='x', top='y', source=src6, width=0.8)
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
