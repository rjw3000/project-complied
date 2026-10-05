# Monthly source-package review

5 October 2026. This workflow reviews source evidence, not tax returns.

Import the two normalized synthetic store reports, open Sales preparation and select **Review source package**. The page shows selected source snapshots, combined totals, known alternative versions, current review status, tax-return blockers and review history.

Record source totals reviewed, needs information or rejected, with notes. A review binds the package hash, authenticated actor, optimistic review revision and complete known source-version set for the month. A concurrent review or newly imported source makes an older form fail. Later source versions mark an earlier review stale; other months do not.

Reviews and source packages are append-only. A reviewer may explicitly revalidate a retained older package after considering alternative versions and documenting why. This does not silently select the latest report or overwrite a prior decision.

Download JSON from **Download source review packet**. Download requires a valid session and contains exact source totals/hashes, review history and unresolved blockers. export_type is source_review_packet_not_a_tax_return; return_ready remains false. Source review cannot authorize filing or payment or clear unverified tax rules.

Schema v7 preserves existing records. Tests cover review/export authentication, stale sources/forms, immutable history, rejection, revocation, source completeness, HTML escaping and HTTP downloads. Actual PostalMate mapping, tax classifications, return-line calculations, government form and submission route remain pending.
