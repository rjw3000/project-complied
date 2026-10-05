# Monthly source import contract

5 October 2026. normalized-monthly-v1 is an internal synthetic exchange format, not a claim about PostalMate report columns.

One UTF-8 CSV per store and month, exactly one data row. Header order:

```text
store_id,period,net_taxable_sales,net_nontaxable_sales,net_sales_control,tax_collected
```

Store IDs are ivy and pantops. Period is YYYY-MM. Amounts are signed decimal strings with exactly two places, at most 12 whole digits. Values are net of any included refunds/adjustments and exclude tax from sales totals. The adapter to actual PostalMate reports must verify those semantics and separate refund/adjustment evidence before real use.

Net taxable plus net nontaxable sales must exactly match the supplied net sales control. Tax collected is reported independently; no tax rate, exemption, return line, liability or payment amount is calculated.

## Import and review

Seed demo data and create a local account as in README. Import the included synthetic fixture pair:

```sh
PYTHONPATH=src python3 -m complied.imports --user owner-demo fixtures/synthetic/ivy-2026-10.csv fixtures/synthetic/pantops-2026-10.csv
```

Password is prompted privately. Snapshots retain raw bytes, normalized values, format version and SHA-256 hash in the private local database. Maximum file size 64 KiB. Exact repeats reuse a snapshot. Corrections create a new snapshot; prior snapshots/packages cannot be overwritten or deleted through ordinary SQL operations.

A preparation package requires both distinct stores from the same period. It binds sorted source hashes and exact decimal totals in an immutable manifest; reversed input order produces the same package. Every action is tied to the authenticated actor.

Open **Sales preparation** to review store totals, combined totals and source hashes. Status is source_reconciled_not_return_ready. Actual PostalMate mapping, reviewed tax treatment, return-line preparation, accounting reconciliation and filing/payment approval remain pending.

Only synthetic fixtures belong in public Git. Real exports and financial records must never be committed or sent to CI. Local storage is not a production encrypted evidence service.
