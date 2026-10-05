import sys
import unittest
import urllib.error
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from complied.microsoft import GraphHTTPTransport,NoRedirect

class Response:
    status=201
    def __enter__(self): return self
    def __exit__(self,*args): pass
    def read(self,limit): return b'{"id":"synthetic-event"}'
class Opener:
    def __init__(self): self.request=None
    def open(self,request,timeout):
        self.request=request
        return Response()
class MicrosoftTransportTests(unittest.TestCase):
    def test_disabled_and_endpoint_allowlist(self):
        client=GraphHTTPTransport("synthetic",opener=Opener())
        with self.assertRaises(PermissionError): client.post("/me/sendMail",{})
        client.enabled=True
        for path in ["https://attacker.invalid","/users/other/sendMail","/me/calendars/../../events"]:
            with self.assertRaises(ValueError): client.post(path,{})
    def test_fixed_https_endpoint(self):
        opener=Opener()
        client=GraphHTTPTransport("synthetic",enabled=True,opener=opener)
        self.assertEqual(client.post("/me/calendars/demo/events",{}),(201,{"id":"synthetic-event"}))
        self.assertEqual(opener.request.full_url,"https://graph.microsoft.com/v1.0/me/calendars/demo/events")
        self.assertEqual(opener.request.get_method(),"POST")
    def test_redirects_denied(self):
        self.assertIsNone(NoRedirect().redirect_request(None,None,302,"",{},"https://attacker.invalid"))
