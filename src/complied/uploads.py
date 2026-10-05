"""Strict, small multipart parser for the two monthly browser uploads."""
import re
from email import policy
from email.parser import BytesParser

MAX_REQUEST=150000
BOUNDARY=re.compile(r"multipart/form-data;\s*boundary=(?:\"([A-Za-z0-9'()+_,./:=?_-]{1,70})\"|([A-Za-z0-9'()+_,./:=?_-]{1,70}))\s*\Z",re.I)

def parse_upload(content_type,body):
    if not isinstance(body,bytes) or not 0<len(body)<=MAX_REQUEST:
        raise ValueError("Upload exceeds the request limit")
    matched=BOUNDARY.fullmatch(content_type)
    if not matched:
        raise ValueError("Expected multipart/form-data with a boundary")
    boundary=matched.group(1) or matched.group(2)
    message=BytesParser(policy=policy.default).parsebytes(
        b"MIME-Version: 1.0\r\nContent-Type: multipart/form-data; boundary=\""+
        boundary.encode("ascii")+b"\"\r\n\r\n"+body)
    if not message.is_multipart() or message.defects or message.preamble and message.preamble.strip() or message.epilogue and message.epilogue.strip():
        raise ValueError("Malformed upload")
    parts={}
    for part in message.iter_parts():
        name=part.get_param("name",header="content-disposition")
        if (part.defects or part.is_multipart() or part.get_content_disposition()!="form-data"
            or name not in ("csrf","ivy","pantops") or name in parts):
            raise ValueError("Unexpected or duplicate upload field")
        if part.get("Content-Transfer-Encoding","").lower() not in ("","binary","8bit"):
            raise ValueError("Encoded upload fields are unsupported")
        payload=part.get_payload(decode=True)
        if not isinstance(payload,bytes) or len(payload)>65536:
            raise ValueError("Invalid upload field size")
        parts[name]=payload
    if set(parts)!={"csrf","ivy","pantops"}:
        raise ValueError("Both store reports and request token are required")
    try:
        parts["csrf"]=parts["csrf"].decode("utf-8")
    except UnicodeError as exc:
        raise ValueError("Invalid request token") from exc
    if len(parts["csrf"])>256:
        raise ValueError("Invalid request token")
    return parts
