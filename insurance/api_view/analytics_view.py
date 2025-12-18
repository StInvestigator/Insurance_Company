from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import pandas as pd

from ..repository.unit_of_work import UnitOfWork


class AnalyticsView(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]

    @action(detail=False, methods=['get'], url_path='payments-by-month')
    def payments_by_month(self, request):
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        policy_type = request.query_params.get('policy_type')
        with UnitOfWork() as repo:
            qs = repo.payments.payments_by_month(date_from=date_from, date_to=date_to, policy_type=policy_type)
            data = list(qs)
        df = pd.DataFrame(data)
        if not df.empty:
            df['month'] = df['month'].astype(str)
            stats = {
                'total_amount': {
                    'mean': float(df['total_amount'].astype(float).mean()),
                    'median': float(df['total_amount'].astype(float).median()),
                    'min': float(df['total_amount'].astype(float).min()),
                    'max': float(df['total_amount'].astype(float).max()),
                }
            }
        else:
            stats = {'total_amount': {'mean': 0, 'median': 0, 'min': 0, 'max': 0}}
        return Response({'data': df.to_dict(orient='records'), 'stats': stats, 'meta': {'rows': len(data)}})


    @action(detail=False, methods=['get'], url_path='avg-claim-by-age-group')
    def avg_claim_by_age_group(self, request):
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        with UnitOfWork() as repo:
            qs = repo.claims.avg_claim_by_age_group(date_from=date_from, date_to=date_to)
            data = list(qs)
        df = pd.DataFrame(data)
        if not df.empty:
            stats = {
                'avg_amount': {
                    'mean': float(df['avg_amount'].astype(float).mean()),
                    'median': float(df['avg_amount'].astype(float).median()),
                    'min': float(df['avg_amount'].astype(float).min()),
                    'max': float(df['avg_amount'].astype(float).max()),
                },
                'count': {
                    'mean': float(df['count'].astype(float).mean()),
                    'median': float(df['count'].astype(float).median()),
                    'min': int(df['count'].min()),
                    'max': int(df['count'].max()),
                }
            }
        else:
            stats = {'avg_amount': {'mean': 0, 'median': 0, 'min': 0, 'max': 0},
                     'count': {'mean': 0, 'median': 0, 'min': 0, 'max': 0}}
        return Response({'data': df.to_dict(orient='records'), 'stats': stats, 'meta': {'rows': len(data)}})


    @action(detail=False, methods=['get'], url_path='claims-per-customer')
    def claims_per_customer(self, request):
        only_with_claims = request.query_params.get('only_with_claims', 'false').lower() in ('1', 'true', 'yes')
        with UnitOfWork() as repo:
            qs = repo.claims.claims_per_customer(only_with_claims=only_with_claims)
            data = list(qs)
        df = pd.DataFrame(data)
        if not df.empty:
            df['claims_count'] = df['claims_count'].fillna(0)
            stats = {
                'claims_count': {
                    'mean': float(df['claims_count'].astype(float).mean()),
                    'median': float(df['claims_count'].astype(float).median()),
                    'min': float(df['claims_count'].min() if not df['claims_count'].isnull().all() else 0),
                    'max': float(df['claims_count'].max() if not df['claims_count'].isnull().all() else 0),
                }
            }
        else:
            stats = {'claims_count': {'mean': 0, 'median': 0, 'min': 0, 'max': 0}}
        return Response({'data': df.to_dict(orient='records'), 'stats': stats, 'meta': {'rows': len(data)}})


    @action(detail=False, methods=['get'], url_path='policy-profit-by-type')
    def policy_profit_by_type(self, request):
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        try:
            with UnitOfWork() as repo:
                qs = repo.policies.policy_profit_by_type(date_from=date_from, date_to=date_to)
                data = list(qs)
        except Exception as e:
            print(e)
        df = pd.DataFrame(data)
        if not df.empty:
            for col in ('total_premium', 'total_payouts', 'profit'):
                df[col] = df[col].astype(float)
            stats = {
                'profit': {
                    'mean': float(df['profit'].mean()),
                    'median': float(df['profit'].median()),
                    'min': float(df['profit'].min()),
                    'max': float(df['profit'].max()),
                }
            }
        else:
            stats = {'profit': {'mean': 0, 'median': 0, 'min': 0, 'max': 0}}
        return Response({'data': df.to_dict(orient='records'), 'stats': stats, 'meta': {'rows': len(data)}})


    @action(detail=False, methods=['get'], url_path='time-to-claim')
    def time_to_claim(self, request):
        with UnitOfWork() as repo:
            qs = repo.policies.time_to_first_claim_per_policy()
            data = list(qs)

        try:
            df = pd.DataFrame(data)
            if not df.empty:
                df['days'] = df['delta'].apply(lambda d: d.days if pd.notnull(d) else None)
                stats = {
                    'days': {
                        'mean': float(df['days'].mean() if not df['days'].empty else 0),
                        'median': float(df['days'].median() if not df['days'].empty else 0),
                        'min': float(df['days'].min() if not df['days'].empty else 0),
                        'max': float(df['days'].max() if not df['days'].empty else 0),
                    }
                }
                df = df.drop(columns=['delta'])
            else:
                stats = {'days': {'mean': 0, 'median': 0, 'min': 0, 'max': 0}}
        except Exception as e:
            print(e)

        return Response({'data': df.to_dict(orient='records'), 'stats': stats, 'meta': {'rows': len(data)}})



    @action(detail=False, methods=['get'], url_path='top-customers-by-payouts')
    def top_customers_by_payouts(self, request):
        try:
            limit = int(request.query_params.get('limit', 10))
        except Exception:
            limit = 10
        threshold_param = request.query_params.get('threshold')
        threshold = float(threshold_param) if threshold_param is not None else None
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        with UnitOfWork() as repo:
            qs = repo.payments.top_customers_by_payouts(limit=limit, threshold=threshold, date_from=date_from,
                                                        date_to=date_to)
            data = list(qs)
        # normalize keys
        for it in data:
            it['customer_id'] = it.pop('claim__policy__customer_id')
            it['full_name'] = it.pop('claim__policy__customer__full_name')
        df = pd.DataFrame(data)
        if not df.empty:
            df['total_payout'] = df['total_payout'].astype(float)
            stats = {
                'total_payout': {
                    'mean': float(df['total_payout'].mean()),
                    'median': float(df['total_payout'].median()),
                    'min': float(df['total_payout'].min()),
                    'max': float(df['total_payout'].max()),
                }
            }
        else:
            stats = {'total_payout': {'mean': 0, 'median': 0, 'min': 0, 'max': 0}}
        return Response({'data': df.to_dict(orient='records'), 'stats': stats, 'meta': {'rows': len(data)}})
