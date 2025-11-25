import numpy
import pandas as pd
from api import Api as truthbrush
import os
import csv
import glob

# LOAD THE DATA
HOME = "/Users/destroyerofworlds/Desktop/NLP/PROJECT/BlueSocial/truth_social/"

# Column names
URL = "url"
ARG_BOOL = "AM_label"
IS_URL = "is_url"
REPLIES = "reply_count"
NG = "Sanity Check"
SCRAPED = "comments_scraped"

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
    # TODO: AVOID DUPLICATE AUTHORS !!!!!
    write_truth(comment_obj["account"], NEW_AUTHORS, AUTHOR_FIELDS)
      
def write_truth(obj, file, fields, parent_id=None):
  with open(file, "a", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    row = {field: obj.get(field, None) for field in fields}
    if parent_id: row['PARENT_ID'] = parent_id
    writer.writerow(row)
    f.flush()

def meets_inclusion_criteria(row):
  return row[ARG_BOOL] == 1 and row[REPLIES] >= 5 and row[NG] != 1 and row[IS_URL] == 1 \
    and row[SCRAPED] == 0

def compile_thread():
  for path, fields in [(NEW_TRUTHS, TRUTH_FIELDS), (NEW_AUTHORS, AUTHOR_FIELDS)]:
    if not os.path.exists(path):
      with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        f.flush()

  TRUTHS = HOME + "truths_cleaned_tagged.xlsx"
  truths_df = pd.read_excel(TRUTHS, sheet_name="popularity_cutoff").sample(frac=1, random_state=42).reset_index(drop=True)
  print(len(truths_df), "truths loaded.")

  for idx, row in truths_df.iterrows():
    if not meets_inclusion_criteria(row): continue
    
    try:
      get_comments(row[URL])
      truths_df.at[idx, SCRAPED] = 1

    except Exception as e:
      print(f"Error processing {row[URL]}:", e)
      truths_df.at[idx, SCRAPED] = -1
    
    truths_df.to_csv(HOME + "truthbrush.csv", index=False)

def combine_csv(type):
  files = glob.glob(f"./new_data/new_{type}*.csv")

  dfs = []
  for f in files:
    df = pd.read_csv(f)
    dfs.append(df)

  all_data = pd.concat(dfs, ignore_index=True)
  if type == "authors": all_data = all_data.drop_duplicates(subset=["username"])
  all_data.to_csv(f"new_{type}.csv", index=False)

## LAST EXECUTION: new_truths.csv and new_authors.csv had 1722 rows.
def main():
  compile_thread()
  # combine_csv("truths")

main()
