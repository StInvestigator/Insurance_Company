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

    customers = []
    base_dob_year = 1965
    for i in range(COUNT_PER_TABLE):
        full_name = f"Seed User {i:03d}"
        tax_number = f"{SEED_PREFIX}TAX-{i:06d}"
        email = f"seed+u{i:03d}@example.com"
        phone = f"+1-555-{i:04d}"
        house = 10 + (i % 90)
        address = f"{house} {streets[i % len(streets)]}, {cities[i % len(cities)]}"
        # distribute DOB across years and months deterministically
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
        premium = _mk_decimal(50 + (i * 7) % 200 + rnd.randint(0, 49))
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

    policy_rows = list(Policy.objects.filter(policy_number__startswith=f"{SEED_PREFIX}POL-")
                       .values('id', 'start_date', 'end_date')
                       .order_by('id'))
    if not policy_rows:
        # nothing to seed further
        return

    claims = []
    today = date.today()
    for i in range(COUNT_PER_TABLE):
        prow = policy_rows[i % len(policy_rows)]
        start = prow['start_date']
        end = prow['end_date'] or (start + timedelta(days=365))
        # choose claim_date inside [start, end]
        span = max(1, (end - start).days)
        offset = (i * 13) % span
        cdate = start + timedelta(days=offset)
        if cdate > today:
            cdate = today
        amount = _mk_decimal(100 + (i * 37) % 4900)
        desc = f"{SEED_PREFIX}CLAIM #{i:03d} — simulated incident"
        claims.append(Claim(
            policy_id=prow['id'],
            claim_date=cdate,
            amount=amount,
            description=desc,
        ))
    Claim.objects.bulk_create(claims, batch_size=COUNT_PER_TABLE)

    claim_rows = list(Claim.objects.filter(description__startswith=f"{SEED_PREFIX}CLAIM")
                      .values('id', 'claim_date', 'amount')
                      .order_by('id'))
    if not claim_rows:
        return

    payments = []
    for i in range(COUNT_PER_TABLE):
        crow = claim_rows[i % len(claim_rows)]
        cdate = crow['claim_date']
        pdate = cdate + timedelta(days=(i % 30))
        if pdate < cdate:
            pdate = cdate
        claim_amount = Decimal(str(crow['amount']))
        # pay between 20% and 60% deterministically
        fraction = Decimal(20 + (i * 7) % 41) / Decimal(100)
        amt = (claim_amount * fraction).quantize(Decimal('0.01'))
        if amt > claim_amount:
            amt = claim_amount
        payments.append(Payment(
            amount=amt,
            date=pdate,
            claim_id=crow['id'],
        ))
    Payment.objects.bulk_create(payments, batch_size=COUNT_PER_TABLE)


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
