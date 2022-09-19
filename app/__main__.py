import os

from app import BASE_PATH
import app
from app.crawlers import IssueCrawler
from app.ebook_writer import EbookMaker
import argparse


"""
Crawl and scrape articles from uncanny-magazine.com, and convert them into a
proper retail-like ePub file. The free online content is released in two stages bi-monthly.
While this software is useful for those who do not have access to Amazon, or a credit/debit card, 
This software must not be used for commercial gain.

This software was written for educational and private-use.

If you like the content Please Support the Author's and Site by purchasing a copy or through donations.
"""
__author__ = "Glen DeSouza"
__email__ = "glen_katalyst@protonmail.com"


def main(url: str):
    """Enter the desired issue url to begin downloading"""

    URL = url

    issue = URL.split("/")[-2]

    for s_dir in ["chapters", "images"]:
        os.makedirs(os.path.join(BASE_PATH, issue, s_dir), exist_ok=True)

    issue_path = os.path.join(BASE_PATH, issue)
    issue_data = IssueCrawler(issue_url=URL, path=issue_path).get_issue()

    uncannymag = EbookMaker(
        issue_title=issue,
        meta_data=issue_data,
        issue_path=issue_path,
    )
    uncannymag.create_ebook()


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        prog="python -m app ISSUE_URL",
        description="Enter an issue URL from the page at https://www.uncannymagazine.com/issues/\n \
            Example: python -m app https://www.uncannymagazine.com/issues/uncanny-magazine-issue-eight/",
    )
    parser.add_argument(
        dest="url", type=str, help="URL for the issue you want to download"
    )

    args = parser.parse_args()

    main(args.url)
