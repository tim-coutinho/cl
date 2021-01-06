import json
import logging
import re
from argparse import ArgumentParser

import requests
from bs4 import BeautifulSoup

cli = True
base_url = "https://seattle.craigslist.org"
categories = {
    "all": "sso",
    "appliances": "app",
    "art": "art",
    "antiques": "atq",
    "auto": "pts",
    "aviation": "avo",
    "baby": "bab",
    "bikes": "bik",
    "bikeparts": "bop",
    "boats": "boa",
    "boatparts": "bpo",
    "books": "bks",
    "business": "bfs",
    "cars": "cto",
    "clothes": "clo",
    "collectibles": "clt",
    "computer": "sys",
    "computerparts": "sop",
    "electronics": "ele",
    "free": "zip",
    "furniture": "fuo",
    "general": "for",
    "health": "hab",
    "heavy": "hvo",
    "jewelry": "jwl",
    "materials": "mat",
    "motorcycles": "mcy",
    "motorcycleparts": "mpo",
    "music": "msg",
    "household": "hsh",
    "phones": "mob",
    "photovideo": "pho",
    "RVs": "rvs",
    "sports": "spo",
    "tickets": "tix",
    "tools": "tls",
    "toys": "tag",
    "trailers": "tro",
    "videogames": "vgm",
    "wanted": "wan",
    "wheels": "wto",
}


def main(argv=None):
    logging.getLogger().setLevel(logging.INFO)
    parser = ArgumentParser()
    parser.add_argument("query", nargs="+")
    parser.add_argument("-c", "--category", default="music")
    parser.add_argument("-d", "--details", nargs="+", default=[])
    parser.add_argument("--max_price")
    parser.add_argument("--min_price", default=100)
    args = vars(parser.parse_args(argv)) if argv else vars(parser.parse_args())
    details = re.compile("|".join(args.pop("details")), re.I)
    category = categories[args.pop("category")]
    cli = False if argv else True

    posts = {}
    for query in args.pop("query"):
        options = "&".join([f"{k}={v}" for k, v in args.items() if v is not None])
        url = f"/search/{category}?query={query}&{options}"
        posts.update(get_posts(url, details))
    if cli:
        with open("posts.json", "w") as f:
            json.dump(posts, f, indent=4)
    return posts


def get_posts(query, details):
    if not query:
        return {}
    posts = {}
    url = f"{base_url}{query}"
    soup = BeautifulSoup(requests.get(url).text, features="html.parser")
    more = soup.select_one("a.button.next").get("href")
    for post in soup.select("div.result-info"):
        link = post.select_one(".result-title").get("href")
        # startswith ensures only local postings
        if not link.startswith(base_url) or link in posts:
            continue
        title = post.select_one(".result-title").text
        soup2 = BeautifulSoup(requests.get(link).text, features="html.parser")
        body = soup2.select_one("section#postingbody")
        if not body:
            continue
        description = body.text.strip().lstrip("QR Code Link to This Post\n\n\n")
        if not any([not details, details.search(title), details.search(description)]):
            continue
        log(title)
        cost = post.select_one(".result-price").text
        posts[link] = {"cost": cost, "description": description, "title": title}
    return {**posts, **get_posts(more, details)}


def log(msg):
    logging.info(msg) if not cli else print(msg)


if __name__ == "__main__":
    main()
