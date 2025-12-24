import glob
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
HOME="./data/"
# HOME = "/share/csc591007f25/fameen/BlueSocial/data/"
DATASET = HOME + "TS24-clean.xlsx"
SCRAPE_LOG = HOME + "scrape_log.csv"
NEW_TRUTHS = HOME + "new_truths.csv"
NEW_AUTHORS = HOME + "new_authors.csv"

# Column names
URL = "url"
ID = "external_id"
REPLIES = "reply_count"
LIKES = "like_count"

# New Truth/Author Files
TRUTH_FIELDS = ['created_at', 'edited_at', 'language', 'id', 'in_reply_to_id', 'in_reply_to_account_id', 'url', 'replies_count', 'favourites_count', 'content', 'sensitive', 'quote_id', 'mentions', 'tags', 'emojis', 'card', 'media_attachments', 'PARENT_ID'
]
AUTHOR_FIELDS = [ "username", "followers_count", "following_count", 
  "created_at", "url", "id", "note", "bot", "verified"
]

# Set up Truth Social API client
usernames = os.getenv("TRUTHSOCIAL_USERNAMES", "").split(",")
passwords = os.getenv("TRUTHSOCIAL_PASSWORDS", "").split(",")

def get_comments(post_url, new_truths=NEW_TRUTHS, new_authors=NEW_AUTHORS):
  '''
  Fetch comments from Truth Social using truthbrush.
  '''
  comment_objs = list(API.pull_comments(post_url, include_all=True))
  n = len(comment_objs)
  
  for comment_obj in comment_objs:
    write_truth(comment_obj, new_truths, TRUTH_FIELDS, parent_id=post_url)
    write_truth(comment_obj["account"], new_authors, AUTHOR_FIELDS) # Note: this does not check for duplicates
  
  return n


def write_truth(obj, file, fields, parent_id=None):
  with open(file, "a", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    row = {field: obj.get(field, None) for field in fields}
    if parent_id: row['PARENT_ID'] = parent_id
    writer.writerow(row)
    f.flush()


def meets_inclusion_criteria(row):
  return (row[REPLIES] >= 3)


def compile_thread(seed=0, min_replies=3):
  new_truths = HOME + f"new_truths-{seed}.csv"
  new_authors = HOME + f"new_authors-{seed}.csv"

  for path, fields in [(new_truths, TRUTH_FIELDS), (new_authors, AUTHOR_FIELDS)]:
    if not os.path.exists(path):
      with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        f.flush()

  # Load and filter dataset
  print("Loading dataset...")
  truths_df = pd.read_excel(DATASET).sample(frac=1, random_state=42).reset_index(drop=True)
  print("Dataset loaded.")

  # # Shard dataset by seed
  truths_df = truths_df[truths_df.index % 5 == seed]

  # Load scrape log
  scrape_log = pd.read_csv(SCRAPE_LOG)
  SCRAPED = set(scrape_log.loc[scrape_log["scraped"].isin([0, 1]), "row"])
  print(f"Processed so far: {len(SCRAPED)} truths.")

  print("Row, Success, Output")
  for _, row in truths_df.iterrows():
    row_id = row["row"]
    if row_id in SCRAPED: continue

    try:
      success, output = 1, get_comments(row[URL], new_truths, new_authors)
    except Exception as e:
      success, output = 0, e
    
    print(f"{row_id},{success},{output}")

    mask = scrape_log["row"] == row_id
    scrape_log.loc[mask, ["scraped", "output"]] = [success, output]
    scrape_log.to_csv(f"{HOME}scrape_log-{seed}.csv", index=False)
    SCRAPED.add(row_id)


def combine_threads():
  def concat_files(pattern, output_name):
    files = sorted(glob.glob(os.path.join(HOME, pattern)))

    dfs = []
    print(f"\nConcatenating {pattern}")
    for f in files:
      df = pd.read_csv(f)
      print(f"  {os.path.basename(f)} → {len(df)} rows")
      dfs.append(df)

    combined = pd.concat(dfs, ignore_index=True)
    print(f"TOTAL rows after concat: {len(combined)}")

    combined.to_csv(f"{HOME}{output_name}", index=False)

  concat_files("new_authors-*.csv", "new_authors-all.csv")
  concat_files("new_truths-*.csv", "new_truths-all.csv")


def merge_scrape_logs():
  files = sorted(glob.glob(os.path.join(HOME, "scrape_log-*.csv")))

  merged = None
  for f in files:
    df = pd.read_csv(f)
    if merged is None:
      merged = df
    else:
      merged["scraped"] = merged["scraped"].combine_first(df["scraped"])
      merged["output"] = merged["output"].combine_first(df["output"])

  merged.to_csv(f"{HOME}scrape_log.csv", index=False)
  return merged


def main():
  global API

  import argparse
  parser = argparse.ArgumentParser()
  parser.add_argument(
    "--seed",
    type=int,
    default=0
  )
  args = parser.parse_args()

  usr, pw = usernames[args.seed], passwords[args.seed]
  try:
    API = truthbrush(username=usr, password=pw, silent=False)
    token = API.get_auth_id(usr, pw)
    print(f"Authenticated as {usr} with {pw}: {token}")
  except Exception as _:
    quit(1)

  compile_thread(args.seed)


if __name__ == "__main__":
  # combine_threads()
  # merge_scrape_logs()

  main()