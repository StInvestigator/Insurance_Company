from django.db import migrations
from datetime import date, timedelta
from decimal import Decimal
import random


SEED_PREFIX = "SEED-"
SEED = 1337
COUNT_PER_TABLE = 200


def _mk_decimal(val, places=2):
    q = Decimal('1').scaleb(-places)
    return (Decimal(val).quantize(q))


def forward(apps, schema_editor):
    Customer = apps.get_model('insurance', 'Customer')
    Policy = apps.get_model('insurance', 'InsurancePolicy')
    Claim = apps.get_model('insurance', 'Claim')
    Payment = apps.get_model('insurance', 'Payment')

    rnd = random.Random(SEED)

    streets = [
        'Oak Street', 'Maple Avenue', 'Pine Road', 'Cedar Lane', 'Birch Boulevard',
        'Willow Way', 'Elm Street', 'Ash Drive', 'Spruce Court', 'Cherry Street'
    ]
    cities = [
        'Springfield', 'Fairview', 'Riverton', 'Lakeside', 'Greenville',
        'Hillcrest', 'Madison', 'Georgetown', 'Franklin', 'Clinton'
    ]
    policy_types = ['Auto', 'Home', 'Health', 'Life', 'Travel']

    # 1) Create customers (same as before)
    customers = []
    base_dob_year = 1965
    for i in range(COUNT_PER_TABLE):
        full_name = f"Seed User {i:03d}"
        tax_number = f"{SEED_PREFIX}TAX-{i:06d}"
        email = f"seed+u{i:03d}@example.com"
        phone = f"+1-555-{i:04d}"
        house = 10 + (i % 90)
        address = f"{house} {streets[i % len(streets)]}, {cities[i % len(cities)]}"
        year = base_dob_year + (i % 41)  # 1965..2005
        month = 1 + (i % 12)
        day = 1 + (i % 28)
        dob = date(year, month, day)
        customers.append(Customer(
            full_name=full_name,
            tax_number=tax_number,
            date_of_birth=dob,
            email=email,
            phone=phone,
            address=address,
        ))
    Customer.objects.bulk_create(customers, batch_size=COUNT_PER_TABLE, ignore_conflicts=True)

    # Refresh customer ids list
    customer_ids = list(Customer.objects.values_list('id', flat=True).order_by('id'))
    if not customer_ids:
        return

    # 2) Create policies — повысим премию, чтобы она значительно перекрывала ожидаемые выплаты
    policies = []
    base_start = date(2018, 1, 1)
    for i in range(COUNT_PER_TABLE):
        policy_number = f"{SEED_PREFIX}POL-{i:06d}"
        ptype = policy_types[i % len(policy_types)]
        start_date = base_start + timedelta(days=i * 7)
        # 25% policies are open-ended
        if (i % 4) == 0:
            end_date = None
        else:
            end_date = start_date + timedelta(days=365 + (i % 60))

        # Premium: make it substantially larger than typical payouts (e.g. 800..1700)
        premium = _mk_decimal(800 + (i * 13) % 900 + rnd.randint(0, 199))
        # Coverage: relatively large, irrelevant for profit calc but realistic
        coverage = _mk_decimal(10000 + ((i * 137) % 90000))
        cust_id = customer_ids[i % len(customer_ids)]
        policies.append(Policy(
            policy_number=policy_number,
            policy_type=ptype,
            start_date=start_date,
            end_date=end_date,
            premium=premium,
            coverage_amount=coverage,
            customer_id=cust_id,
        ))
    Policy.objects.bulk_create(policies, batch_size=COUNT_PER_TABLE, ignore_conflicts=True)

    # 3) Build map customer_id -> list of their policies (to attach claims to customer's policies)
    policy_rows = list(Policy.objects.filter(policy_number__startswith=f"{SEED_PREFIX}POL-")
                       .values('id', 'customer_id', 'start_date', 'end_date')
                       .order_by('id'))
    if not policy_rows:
        return

    policies_by_customer = {}
    for prow in policy_rows:
        policies_by_customer.setdefault(prow['customer_id'], []).append(prow)

    # 4) Create claims: 0..4 per customer, uneven distribution
    # probabilities: 0:60%, 1:20%, 2:12%, 3:6%, 4:2% (weights)
    claim_counts_choices = [0, 1, 2, 3, 4]
    claim_counts_weights = [60, 20, 12, 6, 2]
    claims = []
    now = date.today()

    for cust_id in customer_ids:
        # choose number of claims for this customer (deterministic via rnd)
        n_claims = rnd.choices(claim_counts_choices, weights=claim_counts_weights, k=1)[0]
        cust_policies = policies_by_customer.get(cust_id, [])
        if not cust_policies:
            continue
        for j in range(n_claims):
            # choose one of customer's policies
            prow = rnd.choice(cust_policies)
            start = prow['start_date']
            end = prow['end_date'] or (start + timedelta(days=365))
            span = max(1, (end - start).days)
            # pick random offset within span
            offset = rnd.randrange(span)
            cdate = start + timedelta(days=offset)
            if cdate > now:
                cdate = now
            # claim amount smaller than in original seed (to keep payouts < premiums)
            amount = _mk_decimal(100 + rnd.randint(0, 400))  # 100..500
            desc = f"{SEED_PREFIX}CLAIM #{cust_id}-{j:03d} — simulated incident"
            claims.append(Claim(
                policy_id=prow['id'],
                claim_date=cdate,
                amount=amount,
                description=desc,
            ))

    # bulk create claims (may create zero claims for many customers)
    Claim.objects.bulk_create(claims, batch_size=100)

    # 5) payments for created claims (one payment per claim, 10-30% fraction)
    claim_rows = list(Claim.objects.filter(description__startswith=f"{SEED_PREFIX}CLAIM")
                      .values('id', 'claim_date', 'amount')
                      .order_by('id'))
    payments = []
    for i, crow in enumerate(claim_rows):
        cdate = crow['claim_date']
        # pay within 0..14 days after claim
        pdate = cdate + timedelta(days=rnd.randint(0, 14))
        if pdate < cdate:
            pdate = cdate
        claim_amount = Decimal(str(crow['amount']))
        # fraction 10%..30%
        fraction = Decimal(10 + rnd.randint(0, 20)) / Decimal(100)
        amt = (claim_amount * fraction).quantize(Decimal('0.01'))
        if amt > claim_amount:
            amt = claim_amount
        payments.append(Payment(
            amount=amt,
            date=pdate,
            claim_id=crow['id'],
        ))
    if payments:
        Payment.objects.bulk_create(payments, batch_size=100)


def reverse(apps, schema_editor):
    Customer = apps.get_model('insurance', 'Customer')
    Policy = apps.get_model('insurance', 'InsurancePolicy')
    Claim = apps.get_model('insurance', 'Claim')
    Payment = apps.get_model('insurance', 'Payment')

    seed_claims = Claim.objects.filter(description__startswith=f"{SEED_PREFIX}CLAIM")
    Payment.objects.filter(claim__in=seed_claims).delete()
    seed_claims.delete()

    Policy.objects.filter(policy_number__startswith=f"{SEED_PREFIX}POL-").delete()
    Customer.objects.filter(email__startswith='seed+').delete()
    Customer.objects.filter(tax_number__startswith=f"{SEED_PREFIX}TAX-").delete()


class Migration(migrations.Migration):
    dependencies = [
        ('insurance', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(forward, reverse),
    ]
