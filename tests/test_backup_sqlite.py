import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from backup_sqlite import backup
import backup_sqlite

class BackupTests(unittest.TestCase):
    def test_consistent_copy_and_separate_destination(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            source=root/"live.sqlite3"
            target=root/"offhost"
            target.mkdir()
            db=sqlite3.connect(source)
            db.execute("CREATE TABLE sample(value TEXT)")
            db.execute("INSERT INTO sample VALUES('synthetic')")
            db.commit()
            actual_connect=sqlite3.connect
            modes=[]
            def inspect(path,*args,**kwargs):
                if str(path).startswith(str(target)):
                    modes.append(Path(path).stat().st_mode & 0o777)
                return actual_connect(path,*args,**kwargs)
            with patch.object(backup_sqlite.sqlite3,"connect",side_effect=inspect):
                copy=backup(source,target)
            self.assertEqual(modes,[0o600])
            self.assertEqual(sqlite3.connect(copy).execute("SELECT value FROM sample").fetchone()[0],"synthetic")
            self.assertEqual(copy.stat().st_mode & 0o777,0o600)
            with self.assertRaises(ValueError):
                backup(source,root)
            db.close()
