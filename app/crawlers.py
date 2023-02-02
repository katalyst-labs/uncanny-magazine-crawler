import json
import logging
import os
from string import Template

import requests
from bs4 import BeautifulSoup

from app.templates import template
from app.utils import download_image, sanitize

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36"
}


class IssueCrawler:
    """Scrape meta-data and articles links required for a complete issue"""

    def __init__(self, issue_url: str, path: str) -> None:

        self.issue_url = issue_url
        self.issue_path = path
        r = requests.get(url=self.issue_url, headers=HEADERS)
        r.raise_for_status()

        self._soup = BeautifulSoup(r.content, "html.parser")

    _contents = {}
    # Build the Cover Section

    def get_issue(self) -> dict:
        """Extract data and save as JSON file."""

        cover = self._soup.find("div", class_="featured_issue_thumbnail").find("img")

        # NOTE the .replace("-340x510", ...) reveals a much larger image on the server.
        # This may not always be the case, manually tested on 4 -5 issues.
        cover_url = cover["src"].replace("-340x510", "")
        cover_url_thumbnail = cover["src"]

        self._contents["cover_url"] = download_image(
            url=cover_url, path=self.issue_path
        )
        self._contents["cover_url_thumbnail"] = download_image(
            url=cover_url_thumbnail, path=self.issue_path
        )
        self._contents["cover_alt_text"] = cover["alt"]

        # The introduction Section
        issue_content = self._soup.find("div", class_="issue_content")
        self._contents["issue_title"] = issue_content.find("h2").get_text()

        self._contents["issue_intro_text"] = " ".join(
            [str(p) for p in issue_content.find_all("p", recursive=False)]
        )

        # The cover artist section

        cover_artist = issue_content.find("article", class_="about_artist")
        self._contents["cover_section_title"] = cover_artist.find("h3").get_text()

        self._contents["cover_artist_img"] = download_image(
            cover_artist.find("img")["src"], path=self.issue_path
        )
        cover_artist.find("img").decompose()

        self._contents["cover_artist_bio"] = f'{cover_artist.find("p")}'

        widgets = issue_content.find_all("div", class_="widget")

        self._contents["articles"] = {}

        for items in widgets:
            _chapters = []

            heading = items.find("h3").get_text()
            chap_links = list(items.find_all("p", recursive=False))
            for chap in chap_links:
                title = chap.find("a", href=True).get_text()
                url = chap.find("a", href=True)["href"]
                _chapters.append({"title": title, "url": url})

                ArticleScraper(
                    url=url, title=title, section=heading, path=self.issue_path
                ).save_article()
            self._contents["articles"].update({heading: _chapters})

        with open(
            f'{self.issue_path}/{self._contents["issue_title"]}_test.json',
            "w",
            encoding="UTF-8",
        ) as f:
            f.write(json.dumps(self._contents))

        return self._contents


class ArticleScraper:
    """Crawl and extract data from the individual articles"""

    fallback_img = "quill-ink-paper.jpg"

    def __init__(self, url: str, title: str, section: str, path: str) -> None:
        self.url = url
        self.title = title
        self.section = section
        self.issue_path = path
        self.out_file = self.url.split("/")[-2] + ".xhtml"

        r = requests.get(url=self.url, headers=HEADERS)
        r.raise_for_status()
        self._soup = BeautifulSoup(r.content, "html.parser")
        for tag in self._soup():
            for attribute in ["style"]:
                del tag[attribute]

    _article = {}

    def save_article(self):
        """Save each article as an xhtml file in the issue_path / chapters directory"""

        article = self._soup.find("article", class_="article")

        self._article["title"] = article.find("h2").get_text().strip()
        self._article["page_title"] = self.title

        # FIXME Use .get_text(' ', strip=True) ??
        self._article["byline"] = sanitize(article.find("h4").get_text())

        self._article["article_text"] = " ".join(
            [
                sanitize(str(p)) + "\n"
                for p in article.find("div", class_="entry-content").find_all(
                    "p", recursive=False
                )
            ]
        )

        try:
            author_img = self._soup.find("div", class_="bio_image").find("img")["src"]
            self._article["author_img"] = download_image(
                url=author_img, path=self.issue_path
            )
        except TypeError as e:
            self._article["author_img"] = self.fallback_img
            with open(f"{self.issue_path}/images/{self.fallback_img}", "wb") as fb:
                fb.write(template.DEFAULT_COVER_IMAGE)

        self._article["author_name"] = (
            self._soup.find("div", class_="bio_entry").find("h2").get_text().strip()
        )

        self._article["author_bio"] = (
            self._soup.find("div", class_="bio_entry").find("p").get_text().strip()
        )

        final_output = Template(template.ARTICLE_TEMPLATE).substitute(
            self._article
        )

        with open(
            os.path.join(self.issue_path, "chapters", self.out_file),
            "w",
            encoding="UTF-8",
        ) as output:
            output.write(final_output)
