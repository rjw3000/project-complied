"""Source review cannot authorize a filing or payment."""
import hashlib
import json
import time
from complied.access import authorize,audit
from complied.imports import assemble

BLOCKERS=["Actual PostalMate mapping is unverified",
          "Tax classifications and return-line rules are unverified",
          "Government form, filing route and registration reporting need verification"]

def migrate(db):
    db.executescript("""
      CREATE TABLE IF NOT EXISTS package_reviews(
        id INTEGER PRIMARY KEY,package_id TEXT NOT NULL REFERENCES preparation_packages(id),
        revision INTEGER NOT NULL,actor TEXT NOT NULL REFERENCES users(id),
        decision TEXT NOT NULL CHECK(decision IN ('sources_reviewed','needs_information','rejected')),
        notes TEXT NOT NULL,context_hash TEXT NOT NULL,created INTEGER NOT NULL,UNIQUE(package_id,revision));
      CREATE TRIGGER IF NOT EXISTS reviews_no_update BEFORE UPDATE ON package_reviews
        BEGIN SELECT RAISE(ABORT,'Reviews are append only'); END;
      CREATE TRIGGER IF NOT EXISTS reviews_no_delete BEFORE DELETE ON package_reviews
        BEGIN SELECT RAISE(ABORT,'Reviews are append only'); END;
    """)
    with db: db.execute("INSERT OR IGNORE INTO schema_versions VALUES(7)")

def validated(db,package_id):
    record=db.execute("SELECT * FROM preparation_packages WHERE id=?",(package_id,)).fetchone()
    if record is None: raise ValueError("Package not found")
    if hashlib.sha256(record["manifest"].encode()).hexdigest()!=package_id:
        raise ValueError("Package integrity failed")
    manifest=json.loads(record["manifest"])
    expected=assemble(db,[source["snapshot_id"] for source in manifest["sources"]])
    if expected!=manifest or record["period"]!=manifest["period"]:
        raise ValueError("Package does not match source evidence")
    return manifest

def context(db,manifest):
    versions=[r["id"] for r in db.execute("SELECT id FROM sales_snapshots WHERE period=? ORDER BY id",(manifest["period"],))]
    return hashlib.sha256(json.dumps(versions).encode()).hexdigest(),versions

def summary(db,package_id):
    manifest=validated(db,package_id)
    context_hash,versions=context(db,manifest)
    reviews=[dict(r) for r in db.execute("SELECT * FROM package_reviews WHERE package_id=? ORDER BY revision",(package_id,))]
    latest=reviews[-1] if reviews else None
    stale=bool(latest and latest["context_hash"]!=context_hash)
    state="needs_review" if not latest or stale else latest["decision"]
    blockers=list(BLOCKERS)
    if state!="sources_reviewed": blockers.insert(0,"Source review is missing, rejected, incomplete or stale")
    return dict(package_id=package_id,manifest=manifest,review_revision=latest["revision"] if latest else 0,
                review_state=state,review_stale=stale,source_versions=versions,
                reviews=reviews,blockers=blockers,return_ready=False)

def record_review(db,token,package_id,expected_revision,decision,notes,expected_context):
    user=authorize(db,token,"review")
    if type(expected_revision) is not int or decision not in ("sources_reviewed","needs_information","rejected"):
        raise ValueError("Invalid review decision")
    if not notes.strip() or len(notes)>4000: raise ValueError("Review notes required")
    db.execute("BEGIN IMMEDIATE")
    try:
        user=authorize(db,token,"review")
        current=summary(db,package_id)
        current_context,_=context(db,current["manifest"])
        if current["review_revision"]!=expected_revision or current_context!=expected_context:
            raise ValueError("Review or source versions changed; reload")
        revision=expected_revision+1
        db.execute("INSERT INTO package_reviews(package_id,revision,actor,decision,notes,context_hash,created) VALUES(?,?,?,?,?,?,?)",
                   (package_id,revision,user["id"],decision,notes,current_context,int(time.time())))
        audit(db,user,"review-sales-package",package_id,{"revision":revision,"decision":decision,"notes":notes,"context_hash":current_context})
        db.commit()
        return revision
    except Exception:
        db.rollback()
        raise

def export_package(db,token,package_id):
    authorize(db,token,"review")
    result=summary(db,package_id)
    return json.dumps(dict(export_type="source_review_packet_not_a_tax_return",**result),sort_keys=True,indent=2)
