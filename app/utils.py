import os
import uuid

import requests
from ebooklib import epub
from ebooklib.utils import guess_type


def get_content(file_name: str) -> bytes:
    with open(file_name, "rb") as f:
        return f.read()


def make_chapter(title: str, file_name: str, content: bytes):
    """Creates individual chapters to insert in the ePub file"""
    chapter = epub.EpubHtml(
        title=title, file_name=f"chapters/{file_name}.xhtml", lang="en"
    )
    chapter.set_content(content)
    return chapter


def add_item(file_name: str, content: bytes):
    """Adds media and non HTML files to ePub"""
    return epub.EpubItem(
        uid=str(uuid.uuid4()),
        file_name=f"images/{file_name}",
        media_type=guess_type(file_name[0]),
        content=content,
    )


def download_image(url: str, path: str, file_name: str = None, key: int = -1):
    """Downloads Images to the Images Directory. PATH MUST BE DEFINED!!!"""
    if not file_name:
        file_name = url.split("/")[key]
        file_path = os.path.join(path, "images", file_name)
        if os.path.exists(file_path):
            return file_name
    r = requests.get(url=url)
    with open(f"{file_path}", "wb") as img:
        img.write(r.content)
    return file_name


def sanitize(string: str) -> str:
    """Sanatizer function to clean extractes text from unwanted spaces etc."""
    string = string.strip()
    string = string.replace("&", "&amp;")
    return " ".join(string.split())
