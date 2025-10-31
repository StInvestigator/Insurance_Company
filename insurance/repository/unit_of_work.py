# repository/unit_of_work.py
from django.db import transaction
from .claim_repository import ClaimRepository
from .customer_repository import CustomerRepository
from .payment_repository import PaymentRepository
from .policy_repository import PolicyRepository

class UnitOfWork:
    def __init__(self):
        self.claims = ClaimRepository()
        self.customers = CustomerRepository()
        self.payments = PaymentRepository()
        self.policies = PolicyRepository()

    def __enter__(self):
        self._ctx = transaction.atomic()
        self._ctx.__enter__()
        return self

    def commit(self):
        pass

    def __exit__(self, exc_type, exc, tb):
        self._ctx.__exit__(exc_type, exc, tb)
