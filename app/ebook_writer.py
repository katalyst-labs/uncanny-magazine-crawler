import os
import uuid
from string import Template

from ebooklib import epub
from ebooklib.utils import guess_type

from app.utils import make_chapter

from app.templates import template
import logging

logger = logging.getLogger(__name__)


class EbookMaker:
    """Create an ePub file"""

    def __init__(self, issue_title: str, meta_data: dict, issue_path: str) -> None:
        self.issue_title = issue_title
        self.data = meta_data
        self.issue_path = issue_path

        self.book = epub.EpubBook()
        self.book.FOLDER_NAME = "OEBPS"

        # Set the compulsory meta-data needed to initialise an e-Book.

        self.book.set_identifier(str(uuid.uuid4()))
        self.book.set_title(issue_title)
        self.book.set_language("en")

        self.book.add_author("Uncanny Magazine - Editorial Board")

        self.book.add_metadata(
            "DC",
            "description",
            "Uncanny Magazine is an online Science Fiction and Fantasy magazine featuring passionate SF/F fiction and poetry, gorgeous prose, provocative nonfiction, and a deep investment in the diverse SF/F culture.",
        )
        self.book.add_metadata(
            None,
            "meta",
            "",
            {"name": "generator", "content": "uncanny-mag-scraper 0.1a"},
        )

    def create_ebook(self):

        # Create and add the cover page.

        cover_page = epub.EpubHtml(
            title=f"Cover - {self.issue_title}",
            file_name="chapters/cover.xhtml",
            lang="en",
        )
        cover_t = Template(template.COVER_TEMPLATE).substitute(self.data)
        cover_page.set_content(cover_t)

        # Set Cover Thumbnail

        cover_thumbnail = self.data["cover_url_thumbnail"]
        self.book.set_cover(
            cover_thumbnail,
            open(f"{self.issue_path}/images/{cover_thumbnail}", "rb").read(),
            create_page=False,
        )

        # Create and add the intro / about-cover-artist chapter.

        intro_page = epub.EpubHtml(
            title="Introduction", file_name="chapters/intro.xhtml", lang="en"
        )
        intro_t = Template(template.INTRO_TEMPLATE).substitute(self.data)
        # intro_content = intro_t.substitute(self.intro_page)
        intro_page.set_content(intro_t)

        self.book.add_item(cover_page)
        self.book.add_item(intro_page)

        # Add all images

        images_dir = os.path.join(self.issue_path, "images")
        for img_file in os.listdir(images_dir):
            img = epub.EpubItem(
                uid=str(uuid.uuid4()),
                file_name=f"images/{img_file}",
                media_type=guess_type(img_file)[0],
                content=open(f"{images_dir}/{img_file}", "rb").read(),
            )

            self.book.add_item(img)

        # Add remaining articles as chapters
        toc = []
        chapters_list = []

        chapters_dir = os.path.join(self.issue_path, "chapters")
        for section in self.data["articles"]:
            s = self.data["articles"][section]
            chapters = []
            for i in s:
                section, title, url = section, i["title"], i["url"].split("/")[-2]
                chapters.append(
                    make_chapter(
                        title=title,
                        file_name=f"{url}",
                        content=open(f"{chapters_dir}/{url}.xhtml", "rb").read(),
                    )
                )
            chapters_list = chapters_list + chapters
            toc.append((epub.Section(section), tuple(chapters)))

        for c in chapters_list:
            self.book.add_item(c)

        style = template.STYLESHEET

        nav_css = epub.EpubItem(
            uid="style_nav",
            file_name="style/nav.css",
            media_type="text/css",
            content=style,
        )
        self.book.add_item(nav_css)

        toc.insert(0, epub.Link("text/cover.xhtml", "Cover", "cover-page"))
        toc.insert(1, epub.Link("text/intro.xhtml", "Introduction", "intro-page"))

        self.book.toc = toc
        self.book.spine = [cover_page, "nav", intro_page] + chapters_list

        self.book.add_item(epub.EpubNcx())
        self.book.add_item(epub.EpubNav())

        epub.write_epub(f"{self.issue_title}.epub", self.book)
