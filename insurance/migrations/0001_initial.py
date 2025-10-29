from django.db import migrations


class Migration(migrations.Migration):
    dependencies = []

    operations = [
        migrations.RunSQL("""
                          CREATE TABLE customer
                          (
                              id            BIGSERIAL PRIMARY KEY,
                              full_name     VARCHAR(512) NOT NULL,
                              tax_number    VARCHAR(128) NOT NULL UNIQUE,
                              date_of_birth DATE         NOT NULL,
                              email         VARCHAR(512) NOT NULL UNIQUE,
                              phone         VARCHAR(16)  NOT NULL,
                              address       VARCHAR(256) NOT NULL,
                              created_at    TIMESTAMP WITH TIME ZONE DEFAULT now()
                          );

                          CREATE TABLE insurance_policy
                          (
                              id              BIGSERIAL PRIMARY KEY,
                              policy_number   VARCHAR(64)    NOT NULL UNIQUE,
                              policy_type     VARCHAR(64)    NOT NULL,
                              start_date      DATE           NOT NULL,
                              end_date        DATE,
                              premium         NUMERIC(10, 2) NOT NULL  DEFAULT 75,
                              coverage_amount NUMERIC(12, 2) NOT NULL,
                              customer_id     BIGINT         NOT NULL REFERENCES customer (id) ON DELETE cascade,
                              created_at      TIMESTAMP WITH TIME ZONE DEFAULT now(),
                              CHECK (end_date IS NULL OR end_date >= start_date)
                          );

                          CREATE TABLE claim
                          (
                              id          BIGSERIAL PRIMARY KEY,
                              policy_id   BIGINT         NOT NULL REFERENCES insurance_policy (id) ON DELETE CASCADE,
                              claim_date  DATE           NOT NULL,
                              amount      NUMERIC(12, 2) NOT NULL,
                              description Text           NOT NULL,
                              created_at  TIMESTAMP WITH TIME ZONE DEFAULT now()
                          );

                          CREATE TABLE payment
                          (
                              id         BIGSERIAL PRIMARY KEY,
                              amount     NUMERIC(12, 2) NOT NULL,
                              date       DATE           NOT NULL,
                              claim_id   BIGINT         NOT NULL REFERENCES claim (id) ON DELETE CASCADE,
                              created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
                          );
                          """,
                          reverse_sql="""
                                      DROP TABLE IF EXISTS payment CASCADE;
                                      DROP TABLE IF EXISTS claim CASCADE;
                                      DROP TABLE IF EXISTS insurance_policy CASCADE;
                                      DROP TABLE IF EXISTS customer CASCADE;
                                      """)
    ]
