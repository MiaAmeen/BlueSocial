import numpy
import pandas as pd
from truthbrush import truthbrush
import os
import csv

# LOAD THE DATA
HOME = "/Users/destroyerofworlds/Desktop/NLP/PROJECT/BlueSocial/truth_social/"
TRUTHS = HOME + "truths_cleaned.csv"
AUTHORS = HOME + "users.tsv"
truths_df = pd.read_csv(TRUTHS)
authors_df = pd.read_csv(AUTHORS)
print(len(truths_df), "truths loaded.")
print(len(authors_df), "authors loaded.")

# Column names
URL = "url"
USERNAME = "username"
EXT_ID = "external_id"

# New Truth/Author Files
NEW_TRUTHS = HOME + "new_truths.csv"
TRUTH_FIELDS = [ "created_at", "language", "id",
  "in_reply_to_id", "in_reply_to_account_id", "sensitive",
  "visibility", "url", "replies_count",
  "favourites_count", "votable", "reaction",
  "reblogged", "content", "text",
  "title", "quote_id", "reblog",
]
NEW_AUTHORS = HOME + "new_authors.csv"
AUTHOR_FIELDS = [ "account.username", "account.followers_count", "account.following_count", 
  "account.created_at", "account.url", "account.id", "account.note", "account.bot", "account.verified"
]
for path, fields in [(NEW_TRUTHS, TRUTH_FIELDS), (NEW_AUTHORS, AUTHOR_FIELDS)]:
  if not os.path.exists(path):
    with open(path, "w", newline="", encoding="utf-8") as f:
      writer = csv.DictWriter(f, fieldnames=fields)
      writer.writeheader()

# Set up Truth Social API client
username = os.getenv("TRUTHSOCIAL_USERNAME")
password = os.getenv("TRUTHSOCIAL_PASSWORD")
API = truthbrush.Api(username=username, password=password)

def get_comments(post_url):
  '''
  Fetch comments from Truth Social using truthbrush.
  '''
  
  rtn = API.pull_comments(post_url, include_all=True)
  return list(rtn)

def write_truth(obj):
  if obj.get("id") in truths_df[EXT_ID].values: return

  with open(NEW_TRUTHS, "a", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=TRUTH_FIELDS)
    row = {field: obj.get(field) for field in TRUTH_FIELDS}
    writer.writerow(row)

def write_author(obj):
  if obj.get("username") in authors_df[USERNAME].values: return

  with open(NEW_AUTHORS, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=AUTHOR_FIELDS)
    row = {field: obj.get(field) for field in AUTHOR_FIELDS}
    writer.writerow(row)

def compile_thread():
  for _, row in truths_df.iterrows():
    url = row[URL]
    comments = get_comments(url)

    for comment in comments:
      write_truth(comment)
      write_author(comment.get("account", {}))


def main():
  pass

main()
