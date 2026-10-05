import http.client
import secrets
import sys
import tempfile
import threading
import unittest
from http.server import HTTPServer
from pathlib import Path
from urllib.parse import urlencode
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from complied.deadlines import connect
from complied.access import create_user,authenticate
from complied.editor import handler_for

class EditorHTTPTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.path=str(Path(self.temp.name)/"test.sqlite3")
        self.password=secrets.token_urlsafe(24)
        db=connect(self.path)
        create_user(db,"demo","owner",self.password)
        db.close()
        self.server=HTTPServer(("127.0.0.1",0),handler_for(self.path))
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True)
        self.thread.start()
        self.origin="http://127.0.0.1:"+str(self.server.server_port)
    def tearDown(self):
        self.server.shutdown()
        self.thread.join()
        self.server.server_close()
        self.temp.cleanup()
    def request(self,method,path,fields=None,cookie=None,origin=True,host=None):
        connection=http.client.HTTPConnection("127.0.0.1",self.server.server_port)
        headers={"Host":host or "127.0.0.1:"+str(self.server.server_port)}
        if cookie: headers["Cookie"]=cookie
        if origin: headers["Origin"]=self.origin
        body=urlencode(fields) if fields else None
        if fields: headers["Content-Type"]="application/x-www-form-urlencoded"
        connection.request(method,path,body,headers)
        response=connection.getresponse()
        result=response.status,dict(response.getheaders()),response.read().decode()
        connection.close()
        return result
    def test_login_edit_csrf_and_logout(self):
        status,headers,_=self.request("GET","/")
        self.assertEqual((status,headers["Location"]),(303,"/login"))
        status,headers,_=self.request("POST","/login",{"user":"demo","password":self.password})
        self.assertEqual(status,303)
        cookie=headers["Set-Cookie"].split(";")[0]
        self.assertIn("HttpOnly",headers["Set-Cookie"])
        db=connect(self.path)
        csrf=authenticate(db,cookie.split("=",1)[1])["csrf"]
        db.close()
        fields=dict(id="new",title="Synthetic",jurisdiction="Demo",owner="Demo")
        self.assertEqual(self.request("POST","/create",fields,cookie)[0],403)
        self.assertEqual(self.request("POST","/create",dict(fields,csrf=csrf),cookie,origin=False)[0],403)
        self.assertEqual(self.request("POST","/create",dict(fields,csrf=csrf),cookie)[0],303)
        self.assertIn("Synthetic",self.request("GET","/register",cookie=cookie)[2])
        self.assertEqual(self.request("POST","/logout",{"csrf":csrf},cookie)[0],303)
        self.assertEqual(self.request("GET","/register",cookie=cookie)[0],303)
    def test_untrusted_host_and_unknown_route(self):
        self.assertEqual(self.request("GET","/",host="attacker.invalid")[0],403)
        self.assertEqual(self.request("POST","/payment",{"action":"send"})[0],404)

    def test_schedule_preview_http(self):
        from complied.deadlines import add_obligation
        db=connect(self.path)
        add_obligation(db,id="d",title="Demo",jurisdiction="Demo",owner="Demo",status="applicable",source="urn:demo",reviewed=True)
        db.close()
        status,headers,_=self.request("POST","/login",{"user":"demo","password":self.password})
        cookie=headers["Set-Cookie"].split(";")[0]
        db=connect(self.path)
        csrf=authenticate(db,cookie.split("=",1)[1])["csrf"]
        db.close()
        self.assertIn("Preview schedule",self.request("GET","/schedules",cookie=cookie)[2])
        fields=dict(csrf=csrf,obligation_id="d",anchor="2026-01-01",effective_start="2026-01-01",
                    effective_end="2027-01-01",first_period="2026-10",count="1",period_months="1",
                    due_day="15",due_month_offset="0",short_month="reject",roll="none",
                    calendar_start="",calendar_end="",holidays="",source="urn:demo",reason="Synthetic")
        status,_,body=self.request("POST","/schedule-preview",fields,cookie)
        self.assertEqual(status,200)
        self.assertIn("2026-11-15",body)
        db=connect(self.path)
        proposal=db.execute("SELECT id FROM schedule_proposals").fetchone()[0]
        self.assertEqual(db.execute("SELECT COUNT(*) FROM tasks").fetchone()[0],0)
        db.close()
        self.assertEqual(self.request("POST","/schedule-confirm",dict(csrf=csrf,proposal_id=proposal),cookie)[0],303)
