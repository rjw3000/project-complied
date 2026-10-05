import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
from cryptography.fernet import Fernet
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from complied.deadlines import connect
from complied.access import authenticate
from complied import microsoft_identity as identity

TENANT="11111111-1111-4111-8111-111111111111"
CLIENT="22222222-2222-4222-8222-222222222222"
OWNER="33333333-3333-4333-8333-333333333333"
DELEGATE="44444444-4444-4444-8444-444444444444"

class FakeApp:
    def initiate_auth_code_flow(self,**kwargs):
        return {"auth_uri":"https://login.microsoftonline.com/"+TENANT+"/oauth2/v2.0/authorize?state=s",
                "state":"expected","code_verifier":"private"}
    def acquire_token_by_auth_code_flow(self,flow,params):
        return {"access_token":"synthetic-token",
                "id_token_claims":{"tid":TENANT,"oid":OWNER}}
    def get_accounts(self):
        return [{"home_account_id":"synthetic"}]
    def acquire_token_silent(self,scopes,account):
        return {"access_token":"synthetic-graph-token"}

class IdentityTests(unittest.TestCase):
    def setUp(self):
        self.db=connect(":memory:")
        self.env=patch.dict(os.environ,{
            "COMPLIED_AUTH_MODE":"microsoft","COMPLIED_PUBLIC_ORIGIN":"https://internal.example",
            "COMPLIED_TENANT_ID":TENANT,"COMPLIED_CLIENT_ID":CLIENT,
            "COMPLIED_CLIENT_SECRET":"synthetic-config-secret","COMPLIED_OWNER_OID":OWNER,
            "COMPLIED_DELEGATE_OIDS":DELEGATE,"COMPLIED_TOKEN_KEY":Fernet.generate_key().decode()},clear=False)
        self.env.start()
        self.fake=patch.object(identity,"app",return_value=FakeApp())
        self.fake.start()
    def tearDown(self):
        self.fake.stop()
        self.env.stop()
        self.db.close()
    def test_owner_signin_connection_encrypted_cache_and_replay(self):
        _,browser=identity.begin(self.db,"login")
        with self.assertRaises(PermissionError):
            identity.finish(self.db,"wrong",{"state":"expected","code":"demo"})
        token,kind=identity.finish(self.db,browser,{"state":"expected","code":"demo"})
        self.assertEqual(kind,"login")
        self.assertEqual(authenticate(self.db,token)["role"],"owner")
        with self.assertRaises(PermissionError):
            identity.finish(self.db,browser,{"state":"expected","code":"demo"})
        _,browser=identity.begin(self.db,"connect",token)
        _,kind=identity.finish(self.db,browser,{"state":"expected","code":"demo"},token)
        self.assertEqual(kind,"connect")
        row=self.db.execute("SELECT encrypted_cache FROM microsoft_connections").fetchone()
        self.assertNotIn(b"synthetic-token",row[0])
        self.assertEqual(identity.graph_token(self.db,"ms:"+OWNER),"synthetic-graph-token")
        identity.disconnect(self.db,token)
        with self.assertRaises(PermissionError):
            identity.graph_token(self.db,"ms:"+OWNER)
    def test_state_role_and_browser_binding(self):
        _,browser=identity.begin(self.db,"login")
        with self.assertRaises(PermissionError):
            identity.finish(self.db,browser,{"state":"wrong","code":"demo"})
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM users").fetchone()[0],0)
        _,browser=identity.begin(self.db,"login")
        token,_=identity.finish(self.db,browser,{"state":"expected","code":"demo"})
        _,browser=identity.begin(self.db,"connect",token)
        with self.assertRaises(PermissionError):
            identity.finish(self.db,browser,{"state":"expected","code":"demo"},"wrong-session")
        self.assertFalse(identity.connected(self.db,"ms:"+OWNER))
        with patch.dict(os.environ,{"COMPLIED_OWNER_OID":DELEGATE,"COMPLIED_DELEGATE_OIDS":""}):
            with self.assertRaises(PermissionError):
                authenticate(self.db,token)
    def test_live_worker_requires_explicit_flag(self):
        from complied.microsoft_worker import run_once
        with self.assertRaises(PermissionError):
            run_once(self.db)
    def test_enabled_worker_dispatches_once_with_owner_connection(self):
        from complied.deadlines import add_obligation,add_task
        from complied.reminders import configure,enqueue
        from complied.microsoft_worker import run_once
        from complied.microsoft import GraphHTTPTransport
        _,browser=identity.begin(self.db,"login")
        session,_=identity.finish(self.db,browser,{"state":"expected","code":"demo"})
        _,browser=identity.begin(self.db,"connect",session)
        identity.finish(self.db,browser,{"state":"expected","code":"demo"},session)
        add_obligation(self.db,id="synthetic",title="Synthetic deadline",jurisdiction="Demo",
                       owner="Owner",status="applicable",source="urn:synthetic",reviewed=True)
        add_task(self.db,"synthetic","2026-10","2026-11-15")
        task_id=self.db.execute("SELECT id FROM tasks").fetchone()[0]
        configure(self.db,session,"owner@example.invalid","calendar-demo")
        enqueue(self.db,session,task_id,"calendar")
        with patch.dict(os.environ,{"COMPLIED_LIVE_SEND":"1"}):
            with patch.object(GraphHTTPTransport,"post",return_value=(201,{"id":"synthetic-event"})) as post:
                self.assertEqual(run_once(self.db),"created")
                self.assertIsNone(run_once(self.db))
                self.assertEqual(post.call_count,1)
        self.assertEqual(self.db.execute("SELECT status FROM reminder_outbox").fetchone()[0],"created")
