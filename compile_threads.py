import numpy as np
import pandas as pd
from api import Api as truthbrush
import os
import csv

'''
COLUMNS: 'url', 'external_id', 'timestamp', 'author_username', 'associated_tags',
      'tagged_accounts', 'status_links', 'media_urls', 'like_count',
      'reply_count', 'retruth_count', 'is_quote', 'is_retruth', 'is_reply',
      'replying_to', 'status', 'Keyword', 'Scraping Date'
'''
HOME = "./new_data/"
DATASET = "/Users/destroyerofworlds/Desktop/NLP/PROJECT/BlueSocial/truthsocial2024.xlsx"
SCRAPE_LOG = HOME + "./scrape_log.csv"

# Column names
URL = "url"
ID = "external_id"
REPLIES = "reply_count"
LIKES = "like_count"

# New Truth/Author Files
NEW_TRUTHS = HOME + "new_truths.csv"
TRUTH_FIELDS = ['created_at', 'edited_at', 'spoiler_text', 'language', 'id', 'in_reply_to_id', 'in_reply_to_account_id', 'sensitive', 'visibility', 'uri', 'url', 'replies_count', 'reblogs_count', 'favourites_count', 'favourited', 'upvotes_count', 'downvotes_count', 'votable', 'reaction', 'reblogged', 'muted', 'bookmarked', 'pinned', 'content', 'text', 'title', 'quote_id', 'reblog', 'application', 'mentions', 'tags', 'poll', 'quote', 'in_reply_to', 'emojis', 'card', 'group', 'media_attachments', 'tombstone', 'editable', 'tv', 'version', 'PARENT_ID'
]
NEW_AUTHORS = HOME + "new_authors.csv"
AUTHOR_FIELDS = [ "username", "followers_count", "following_count", 
  "created_at", "url", "id", "note", "bot", "verified"
]

# Set up Truth Social API client
username = os.getenv("TRUTHSOCIAL_USERNAME")
password = os.getenv("TRUTHSOCIAL_PASSWORD")
API = truthbrush(username=username, password=password)


def get_comments(post_url):
  '''
  Fetch comments from Truth Social using truthbrush.
  '''
  comment_objs = list(API.pull_comments(post_url, include_all=True))
  print(len(comment_objs), "comments fetched.")
  
  for comment_obj in comment_objs:
    write_truth(comment_obj, NEW_TRUTHS, TRUTH_FIELDS, parent_id=post_url)
    write_truth(comment_obj["account"], NEW_AUTHORS, AUTHOR_FIELDS) # Note: this does not check for duplicates


def write_truth(obj, file, fields, parent_id=None):
  with open(file, "a", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    row = {field: obj.get(field, None) for field in fields}
    if parent_id: row['PARENT_ID'] = parent_id
    writer.writerow(row)
    f.flush()


def meets_inclusion_criteria(row):
  return (row[REPLIES] >= 3)


def compile_thread(seed=None):
  for path, fields in [(NEW_TRUTHS, TRUTH_FIELDS), (NEW_AUTHORS, AUTHOR_FIELDS)]:
    if not os.path.exists(path):
      with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        f.flush()

  truths_df = pd.read_excel(DATASET).sample(frac=1, random_state=42).reset_index(drop=True)
  if seed: truths_df = truths_df[truths_df.index % 10 == seed]

  scrape_log = pd.read_csv(SCRAPE_LOG)
  SCRAPED = set(scrape_log.loc[scrape_log["scraped"] != "", "index"])

  for idx, row in truths_df.iterrows():
    if idx in SCRAPED or not meets_inclusion_criteria(row):
      continue
    
    try:
      get_comments(row[URL])
      success = 1
    except Exception as e:
      print(f"Error processing {row[URL]}:", e)
      success = 0

    scrape_log.loc[scrape_log["index"] == idx, "scraped"] = success
    scrape_log.to_csv(SCRAPE_LOG, index=False)
    SCRAPED.add(idx)

def main():
  import argparse
  parser = argparse.ArgumentParser()
  parser.add_argument(
      "--idx_seed",
      type=int,
      required=True,
  )
  args = parser.parse_args()

  compile_thread(args.idx_seed)


if __name__ == "__main__":
  main()