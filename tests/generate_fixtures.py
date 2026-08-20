import os
import docx
from pathlib import Path
import base64

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"

MINIMAL_PDF_B64 = b"""
JVBERi0xLjcKCjEgMCBvYmogICUgZW50cnkgcG9pbnQKPDwKICAvVHlwZSAvQ2F0YWxvZwog
IC9QYWdlcyAyIDAgUgo+PgplbmRvYmoKCjIgMCBvYmogCjw8CiAgL1R5cGUgL1BhZ2VzCiAg
L01lZGlhQm94IFsgMCAwIDIwMCAyMDAgXQogIC9Db3VudCAxCiAgL0tpZHMgWyAzIDAgUiBd
Cj4+CmVuZG9iagoKMyAwIG9iaiAKPDwKICAvVHlwZSAvUGFnZQogIC9QYXJlbnQgMiAwIFIK
ICAvUmVzb3VyY2VzIDw8CiAgICAvRm9udCA8PAogICAgICAvRjEgNCAwIFIgCiAgICA+Pgog
ID4+CiAgL0NvbnRlbnRzIDUgMCBSCj4+CmVuZG9iagoKNCAwIG9iaiAKPDwKICAvVHlwZSAv
Rm9udAogIC9TdWJ0eXBlIC9UeXBlMQogIC9CYXNlRm9udCAvVGltZXMtUm9tYW4KPj4KZW5k
b2JqCgo1IDAgb2JqICAlIHBhZ2UgY29udGVudAo8PAogIC9MZW5ndGggNDQKPj4Kc3RyZWFt
CkJUCjcwIDUwIFRECi9GMSAxMiBUZgooSGVsbG8sIHdvcmxkISkgVGoKRVQKZW5kc3RyZWFt
CmVuZG9iagoKeHJlZgowIDYKMDAwMDAwMDAwMCA2NTUzNSBmIAowMDAwMDAwMDEwIDAwMDAw
IG4gCjAwMDAwMDAwNjggMDAwMDAgbiAKMDAwMDAwMDE1MSAwMDAwMCBuIAowMDAwMDAwMjkx
IDAwMDAwIG4gCjAwMDAwMDAzOTMgMDAwMDAgbiAKdHJhaWxlcgo8PAogIC9TaXplIDYKICAv
Um9vdCAxIDAgUgo+PgpzdGFydHhyZWYKNDg2CiUlRU9GCg==
"""

NO_TEXT_PDF_B64 = b"""
JVBERi0xLjcKCjEgMCBvYmogICUgZW50cnkgcG9pbnQKPDwKICAvVHlwZSAvQ2F0YWxvZwog
IC9QYWdlcyAyIDAgUgo+PgplbmRvYmoKCjIgMCBvYmogCjw8CiAgL1R5cGUgL1BhZ2VzCiAg
L01lZGlhQm94IFsgMCAwIDIwMCAyMDAgXQogIC9Db3VudCAxCiAgL0tpZHMgWyAzIDAgUiBd
Cj4+CmVuZG9iagoKMyAwIG9iaiAKPDwKICAvVHlwZSAvUGFnZQogIC9QYXJlbnQgMiAwIFIK
ICAvUmVzb3VyY2VzIDw8Pj4KICAvQ29udGVudHMgNCAwIFIKPj4KZW5kb2JqCgo0IDAgb2Jq
Cjw8CiAgL0xlbmd0aCAxMAo+PgpzdHJlYW0KLyAlIGVtcHR5CmVuZHN0cmVhbQplbmRvYmoK
CnhyZWYKMCA1CjAwMDAwMDAwMDAgNjU1MzUgZiAKMDAwMDAwMDAxMCAwMDAwMCBuIAowMDAw
MDAwMDY4IDAwMDAwIG4gCjAwMDAwMDAxNTEgMDAwMDAgbiAKMDAwMDAwMDI1OCAwMDAwMCBu
IAp0cmFpbGVyCjw8CiAgL1NpemUgNQogIC9Sb290IDEgMCBSCj4+CnN0YXJ0eHJlZgozMTgK
JSVFT0YK
"""

def create_fixtures():
    os.makedirs(FIXTURE_DIR, exist_ok=True)
    
    # 1. Valid PDF
    with open(FIXTURE_DIR / "valid.pdf", "wb") as f:
        f.write(base64.b64decode(MINIMAL_PDF_B64))
        
    # 2. No Text PDF (scanned/image only equivalent)
    with open(FIXTURE_DIR / "no_text.pdf", "wb") as f:
        f.write(base64.b64decode(NO_TEXT_PDF_B64))
        
    # 3. Valid DOCX
    doc = docx.Document()
    doc.add_paragraph("Hello, DOCX!")
    doc.save(FIXTURE_DIR / "valid.docx")
    
    # 4. Unsupported file
    with open(FIXTURE_DIR / "unsupported.txt", "w") as f:
        f.write("Just some text")
        
    # 5. Empty file
    with open(FIXTURE_DIR / "empty.pdf", "wb") as f:
        pass
        
    # 6. Corrupted PDF
    with open(FIXTURE_DIR / "corrupted.pdf", "wb") as f:
        f.write(b"%PDF-1.4\n%This is completely broken and invalid binary.")
        
    # 7. Corrupted DOCX
    with open(FIXTURE_DIR / "corrupted.docx", "wb") as f:
        f.write(b"Not a zip file at all")

if __name__ == "__main__":
    create_fixtures()
    print("Fixtures created.")
