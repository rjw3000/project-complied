"""Create a consistent SQLite backup in a separately protected destination."""
import argparse
import os
import sqlite3
from datetime import datetime,timezone
from pathlib import Path

def backup(source,target_dir):
    source=Path(source).resolve(strict=True)
    target_dir=Path(target_dir).resolve(strict=True)
    if not source.is_file() or not target_dir.is_dir() or source.parent==target_dir:
        raise ValueError("Use an existing database and separate backup directory")
    name="complied-"+datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f")+".sqlite3"
    target=target_dir/name
    fd=os.open(target,os.O_CREAT|os.O_EXCL|os.O_RDWR,0o600)
    os.close(fd)
    try:
        destination=sqlite3.connect(target)
    except Exception:
        target.unlink(missing_ok=True)
        raise
    try:
        with sqlite3.connect(source.as_uri()+"?mode=ro",uri=True) as origin:
            origin.backup(destination)
        result=destination.execute("PRAGMA integrity_check").fetchone()[0]
        if result!="ok":
            raise ValueError("Backup integrity check failed")
    except Exception:
        destination.close()
        target.unlink(missing_ok=True)
        raise
    destination.close()
    return target

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db",required=True)
    parser.add_argument("--output-dir",required=True)
    args=parser.parse_args()
    print(backup(args.db,args.output_dir))

if __name__=="__main__":
    main()
