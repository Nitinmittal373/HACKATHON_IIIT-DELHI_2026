"""Build small PDFs for tests, so no real brochure or agreement is ever stored in the repo."""


def make_pdf(lines: list[str]) -> bytes:
    """A one-page PDF with the lines as text (Helvetica, plain ASCII)."""
    shown = " ".join(f"({escape(line)}) Tj T*" for line in lines)
    stream = f"BT /F1 11 Tf 40 780 Td 14 TL {shown} ET".encode("latin-1")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R "
        b"/Resources << /Font << /F1 5 0 R >> >> >>",
        b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for number, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += b"%d 0 obj\n" % number + body + b"\nendobj\n"
    xref = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objects) + 1)
    for offset in offsets:
        out += b"%010d 00000 n \n" % offset
    out += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (
        len(objects) + 1,
        xref,
    )
    return bytes(out)


def escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


# A made-up brochure page: a MahaRERA number, a Karnataka number and the sort of personal
# details that must never come back out of the API.
BROCHURE = [
    "Sunrise Heights Phase 2 - Thane West",
    "MahaRERA Reg. No. P51900008345 | www.example.test",
    "Sales: Mr. Test Person 9876543210, test.person@example.test",
    "Karnataka RERA PRM/KA/RERA/1251/446/PR/170915/000176 (sister project)",
    "Buyer PAN ABCDE1234F Aadhaar 1234 5678 9012",
]
