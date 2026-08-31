# Pulls embedded images out of docx/pptx/pdf for separate OCR (catches tables-as-images
# that would otherwise be invisible to native text-layer extraction).

import zipfile
from io import BytesIO

import fitz  # PyMuPDF


class ExtractedImage:
    def __init__(self, page_number: int | None, content: bytes):
        self.page_number = page_number
        self.content = content


def extract_images(file_name: str, content: bytes) -> list[ExtractedImage]:
    extension = file_name.rsplit(".", 1)[-1].lower()
    if extension == "docx":
        return _extract_from_office_zip(content, media_prefix="word/media/")
    if extension == "pptx":
        return _extract_from_office_zip(content, media_prefix="ppt/media/")
    if extension == "pdf":
        return _extract_from_pdf(content)
    return []


def _extract_from_office_zip(content: bytes, *, media_prefix: str) -> list[ExtractedImage]:
    images = []
    with zipfile.ZipFile(BytesIO(content)) as archive:
        for name in archive.namelist():
            if name.startswith(media_prefix) and not name.endswith("/"):
                images.append(ExtractedImage(page_number=None, content=archive.read(name)))
    return images


def _extract_from_pdf(content: bytes) -> list[ExtractedImage]:
    images = []
    doc = fitz.open(stream=content, filetype="pdf")
    try:
        for page_number, page in enumerate(doc, start=1):
            for image in page.get_images(full=True):
                xref = image[0]
                extracted = doc.extract_image(xref)
                images.append(ExtractedImage(page_number=page_number, content=extracted["image"]))
    finally:
        doc.close()
    return images
