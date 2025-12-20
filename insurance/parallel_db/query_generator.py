from typing import List, Callable
from insurance.repository.unit_of_work import UnitOfWork
from insurance.model.customer import Customer
from insurance.model.insurance_policy import InsurancePolicy
from insurance.model.claim import Claim
from insurance.model.payment import Payment


def generate_test_queries(num_queries: int = 100) -> List[Callable]:
    queries = []
    
    query_types = [
        _query_get_all_customers,
        _query_get_all_policies,
        _query_get_all_claims,
        _query_get_all_payments,
        _query_count_customers,
        _query_count_policies,
        _query_count_claims,
        _query_count_payments,
        _query_get_customer_by_id,
        _query_get_policy_by_id,
        _query_get_claims_by_policy,
        _query_get_payments_by_claim,
    ]
    
    for i in range(num_queries):
        query_type = query_types[i % len(query_types)]
        queries.append(query_type)
    
    return queries


def _query_get_all_customers():
    with UnitOfWork() as repo:
        return list(repo.customers.get_all().values('id', 'full_name', 'email')[:100])


def _query_get_all_policies():
    with UnitOfWork() as repo:
        return list(repo.policies.get_all().values('id', 'policy_number', 'policy_type')[:100])


def _query_get_all_claims():
    with UnitOfWork() as repo:
        return list(repo.claims.get_all().values('id', 'claim_date', 'amount')[:100])


def _query_get_all_payments():
    with UnitOfWork() as repo:
        return list(repo.payments.get_all().values('id', 'date', 'amount')[:100])


def _query_count_customers():
    with UnitOfWork() as repo:
        return repo.customers.count()


def _query_count_policies():
    with UnitOfWork() as repo:
        return repo.policies.count()


def _query_count_claims():
    with UnitOfWork() as repo:
        return repo.claims.count()


def _query_count_payments():
    with UnitOfWork() as repo:
        return repo.payments.count()


def _query_get_customer_by_id():
    with UnitOfWork() as repo:
        customers = list(repo.customers.get_all().values_list('id', flat=True))
        if customers:
            customer_id = customers[0]
            return repo.customers.get_by_id(customer_id)
    return None


def _query_get_policy_by_id():
    with UnitOfWork() as repo:
        policies = list(repo.policies.get_all().values_list('id', flat=True))
        if policies:
            policy_id = policies[0]
            return repo.policies.get_by_id(policy_id)
    return None


def _query_get_claims_by_policy():
    with UnitOfWork() as repo:
        policies = list(repo.policies.get_all().values_list('id', flat=True))
        if policies:
            policy_id = policies[0]
            policy = repo.policies.get_by_id(policy_id)
            if policy:
                return list(policy.claims.all().values('id', 'claim_date', 'amount')[:10])
    return []


def _query_get_payments_by_claim():
    with UnitOfWork() as repo:
        claims = list(repo.claims.get_all().values_list('id', flat=True))
        if claims:
            claim_id = claims[0]
            claim = repo.claims.get_by_id(claim_id)
            if claim:
                return list(claim.payments.all().values('id', 'date', 'amount')[:10])
    return []

