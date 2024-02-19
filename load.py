from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer

import datetime
import feedparser
import os
import requests
import json

TB_APPEND_TOKEN=os.getenv("TB_APPEND_TOKEN")
TB_READ_TOKEN=os.getenv("TB_READ_TOKEN")

timestamp = datetime.datetime.now().isoformat()
url = "https://www.tinybird.co/blog-posts/rss.xml"
feed = feedparser.parse(url)

model = SentenceTransformer("all-MiniLM-L6-v2")

posts = []
for entry in feed.entries:
    doc = BeautifulSoup(requests.get(entry.link).content, features="html.parser")
    if (content := doc.find(id="content")):
        embedding = model.encode([content.get_text()])
        posts.append(json.dumps({
            "timestamp": timestamp,
            "title": entry.title,
            "url": entry.link,
            "embedding": embedding.mean(axis=0).tolist()
        }))

def send_posts(posts):
    params = {
        "name": "posts",
        "token": TB_APPEND_TOKEN
    }
    data = "\n".join(posts)
    r = requests.post("https://api.us-east.tinybird.co/v0/events", params=params, data=data)
    print(r.status_code)

send_posts(posts)

def get_similars(title):
    params = {
        "title": title,
        "token": TB_READ_TOKEN
    }
    r = requests.get("https://api.us-east.tinybird.co/v0/pipes/similar_posts.json", params)

    return r.json()["data"]

similars_1 = get_similars(feed.entries[0].title)
similars_2 = get_similars("Resolving a year-long ClickHouse lock contention")

print(json.dumps(similars_1, indent=2))
print(json.dumps(similars_2, indent=2))
