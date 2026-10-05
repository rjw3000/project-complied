import http.client
import os
import secrets
import sys
import tempfile
import threading
import unittest
from http.server import HTTPServer
from pathlib import Path
from unittest.mock import patch
from urllib.parse import urlencode
from cryptography.fernet import Fernet
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from complied.deadlines import connect
from complied.access import authenticate
from complied.editor import handler_for
from complied import microsoft_identity as identity
from test_microsoft_identity import FakeApp,TENANT,CLIENT,OWNER,DELEGATE

class HostedMicrosoftHTTPTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.path=str(Path(self.temp.name)/"db.sqlite3")
        self.env=patch.dict(os.environ,{
            "COMPLIED_AUTH_MODE":"microsoft","COMPLIED_PUBLIC_ORIGIN":"https://internal.example",
            "COMPLIED_TENANT_ID":TENANT,"COMPLIED_CLIENT_ID":CLIENT,
            "COMPLIED_CLIENT_SECRET":"synthetic-config-secret","COMPLIED_OWNER_OID":OWNER,
            "COMPLIED_DELEGATE_OIDS":DELEGATE,"COMPLIED_TOKEN_KEY":Fernet.generate_key().decode()},clear=False)
        self.env.start()
        self.fake=patch.object(identity,"app",return_value=FakeApp())
        self.fake.start()
        self.server=HTTPServer(("127.0.0.1",0),handler_for(self.path))
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True)
        self.thread.start()
    def tearDown(self):
        self.server.shutdown()
        self.thread.join()
        self.server.server_close()
        self.fake.stop()
        self.env.stop()
        self.temp.cleanup()
    def request(self,method,path,fields=None,cookies=""):
        connection=http.client.HTTPConnection("127.0.0.1",self.server.server_port)
        headers={"Host":"internal.example","Origin":"https://internal.example"}
        if cookies: headers["Cookie"]=cookies
        if fields is not None:
            headers["Content-Type"]="application/x-www-form-urlencoded"
        connection.request(method,path,urlencode(fields) if fields is not None else None,headers)
        response=connection.getresponse()
        result=response.status,response.getheaders(),response.read().decode()
        connection.close()
        return result
    def test_microsoft_signin_connect_calendar_and_disconnect(self):
        self.assertEqual(self.request("GET","/login")[0],303)
        self.assertEqual(self.request("POST","/login",{"user":"local","password":"irrelevant"})[0],403)
        status,headers,_=self.request("GET","/auth/microsoft")
        self.assertEqual(status,303)
        flow_cookie=next(value for key,value in headers if key=="Set-Cookie").split(";")[0]
        self.assertTrue(flow_cookie.startswith("complied_flow="))
        self.assertIn("Secure",next(value for key,value in headers if key=="Set-Cookie"))
        status,headers,_=self.request("GET","/auth/callback?code=demo&state=expected",cookies=flow_cookie)
        self.assertEqual(status,303)
        session=next(value for key,value in headers if key=="Set-Cookie" and value.startswith("complied_session=")).split(";")[0]
        self.assertIn("Secure",next(value for key,value in headers if key=="Set-Cookie" and value.startswith("complied_session=")))
        db=connect(self.path)
        csrf=authenticate(db,session.split("=",1)[1])["csrf"]
        db.close()
        self.assertIn("Connect Microsoft reminders",self.request("GET","/reminders",cookies=session)[2])
        status,headers,_=self.request("POST","/connect-microsoft",{"csrf":csrf},cookies=session)
        self.assertEqual(status,303)
        flow_cookie=next(value for key,value in headers if key=="Set-Cookie").split(";")[0]
        self.assertEqual(self.request("GET","/auth/callback?code=demo&state=expected",cookies=flow_cookie)[0],403)
        status,_,_=self.request("GET","/auth/callback?code=demo&state=expected",cookies=session+"; "+flow_cookie)
        self.assertEqual(status,303)
        self.assertIn("Browse Microsoft calendars",self.request("GET","/reminders",cookies=session)[2])
        with patch("complied.microsoft_identity.graph_token",return_value="synthetic"),patch("complied.microsoft.GraphHTTPTransport.get_calendars",return_value=[{"id":"calendar-1","name":"Dedicated calendar"}]):
            self.assertIn("Dedicated calendar",self.request("GET","/microsoft-calendars",cookies=session)[2])
            self.assertEqual(self.request("POST","/configure-reminders",{"csrf":csrf,"recipient":"owner@example.com","calendar_id":"calendar-1"},cookies=session)[0],303)
            self.assertEqual(self.request("POST","/configure-reminders",{"csrf":csrf,"recipient":"owner@example.com","calendar_id":"unknown"},cookies=session)[0],409)
        self.assertEqual(self.request("POST","/disconnect-microsoft",{"csrf":csrf},cookies=session)[0],303)
        self.assertIn("Connect Microsoft reminders",self.request("GET","/reminders",cookies=session)[2])
    def test_callback_replay_and_host_rejection(self):
        status,headers,_=self.request("GET","/auth/microsoft")
        cookie=next(value for key,value in headers if key=="Set-Cookie").split(";")[0]
        self.assertEqual(self.request("GET","/auth/callback?code=demo&state=wrong",cookies=cookie)[0],403)
        self.assertEqual(self.request("GET","/auth/callback?code=demo&state=expected",cookies=cookie)[0],403)
