from PyPDF2 import PdfMerger, PdfReader
from io import BytesIO

def merge_pdf_bytes(pages: list[bytes]) -> bytes:
    merger = PdfMerger()
    for p in pages:
        merger.append(PdfReader(BytesIO(p)))
    out = BytesIO()
    merger.write(out)
    merger.close()
    return out.getvalue()
