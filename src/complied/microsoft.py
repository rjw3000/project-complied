"""Explicit operator Graph transport; no stored tokens or automatic sending."""
import argparse
import getpass
import json
import re
import urllib.error
import urllib.request
from complied.access import authorize,login,logout
from complied.deadlines import connect
from complied.reminders import MicrosoftGraphAdapter,dispatch_one,list_outbox

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        return None

class GraphHTTPTransport:
    def __init__(self,access_token,*,enabled=False,opener=None):
        self.access_token=access_token
        self.enabled=enabled
        self.opener=opener or urllib.request.build_opener(NoRedirect())
    def get_calendars(self):
        if not self.enabled or not self.access_token or any(c in self.access_token for c in "\r\n"):
            raise PermissionError("Microsoft calendar access unavailable")
        request=urllib.request.Request(
            "https://graph.microsoft.com/v1.0/me/calendars?$select=id,name&$top=50",
            headers={"Authorization":"Bearer "+self.access_token,"Accept":"application/json"})
        try:
            response=self.opener.open(request,timeout=30)
        except urllib.error.URLError as exc:
            raise ValueError("Microsoft calendars unavailable") from exc
        with response:
            raw=response.read(65537)
            if response.status!=200 or len(raw)>65536:
                raise ValueError("Microsoft calendars unavailable")
            values=json.loads(raw).get("value",[])
            if not isinstance(values,list) or len(values)>50:
                raise ValueError("Invalid Microsoft calendar list")
            result=[]
            for item in values:
                if (not isinstance(item,dict) or not isinstance(item.get("id"),str) or
                    not isinstance(item.get("name"),str) or
                    not 0<len(item["id"])<=1000 or not 0<len(item["name"])<=200 or
                    any(ord(char)<32 for char in item["id"]+item["name"])):
                    raise ValueError("Invalid Microsoft calendar")
                result.append({"id":item["id"],"name":item["name"]})
            return result

    def post(self,path,body):
        if not self.enabled:
            raise PermissionError("Microsoft transport is disabled")
        if not self.access_token or any(c in self.access_token for c in "\r\n"):
            raise ValueError("Invalid delegated token")
        if not (path=="/me/sendMail" or re.fullmatch(r"/me/calendars/[A-Za-z0-9%._~-]+/events",path)):
            raise ValueError("Unsupported Graph endpoint")
        request=urllib.request.Request("https://graph.microsoft.com/v1.0"+path,
                    data=json.dumps(body).encode(),method="POST",
                    headers={"Authorization":"Bearer "+self.access_token,
                             "Content-Type":"application/json"})
        try:
            with self.opener.open(request,timeout=30) as response:
                status=response.status
                if status==202:
                    return status,{}
                raw=response.read(1048577)
                if len(raw)>1048576:
                    raise ValueError("Graph response too large")
                return status,json.loads(raw) if raw else {}
        except urllib.error.HTTPError as error:
            # Never persist or log response bodies or request authorization.
            return error.code,{}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db",default="var/demo.sqlite3")
    parser.add_argument("--execute",action="store_true",help="Explicitly send at most one due queued request")
    parser.add_argument("--user",help="Local account authorizing this operation")
    args=parser.parse_args()
    db=connect(args.db)
    token=None
    try:
        if not args.execute:
            print(json.dumps(list_outbox(db),indent=2))
            return
        if not args.user:
            raise ValueError("--user required for execution")
        token,_=login(db,args.user,getpass.getpass("Local account password: "))
        authorize(db,token,"reminders")
        # The authorized operator provides a delegated token obtained through a reviewed
        # Entra app. OAuth provisioning/refresh remains a setup gate.
        graph_token=getpass.getpass("Microsoft delegated access token (not stored): ")
        transport=GraphHTTPTransport(graph_token,enabled=True)
        result=dispatch_one(db,MicrosoftGraphAdapter(transport.post))
        print(json.dumps({"outcome":result or "no_due_request"}))
    finally:
        if token: logout(db,token)
        db.close()

if __name__=="__main__":
    main()
