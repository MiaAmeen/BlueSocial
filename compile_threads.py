import glob
import pandas as pd
from api import Api as truthbrush
import os
import csv

# Directories and file paths
HOME = "./data/"
DATASET = HOME + "TS24-clean.xlsx"
SCRAPE_LOG = HOME + "scrape_log.csv"
NEW_TRUTHS = HOME + "new_truths.csv"
NEW_AUTHORS = HOME + "new_authors.csv"

# Column names
URL = "url"
ID = "external_id"
REPLIES = "reply_count"
LIKES = "like_count"

# The API fetches many fields; these are the ones we found useful for truth/author data.
TRUTH_FIELDS = ['created_at', 'edited_at', 'language', 'id', 'in_reply_to_id', 'in_reply_to_account_id', 'url', 'replies_count', 'favourites_count', 'content', 'sensitive', 'quote_id', 'mentions', 'tags', 'emojis', 'card', 'media_attachments', 'PARENT_ID'
]
AUTHOR_FIELDS = [ "username", "followers_count", "following_count", 
  "created_at", "url", "id", "note", "bot", "verified"
]

# Collect all usernames/corresponding passwords from environment variables
usernames = os.getenv("TRUTHSOCIAL_USERNAMES", "").split(",")
passwords = os.getenv("TRUTHSOCIAL_PASSWORDS", "").split(",")

def get_comments(post_url, new_truths=NEW_TRUTHS, new_authors=NEW_AUTHORS):
  '''
  Fetch comments from Truth Social using truthbrush.
  :param post_url: URL of the Truth Social post
  :param new_truths: Path to CSV file to append new comment metada
  :param new_authors: Path to CSV file to append new author metadata
  :return: Number of comments fetched
  '''
  comment_objs = list(API.pull_comments(post_url, include_all=True))
  n = len(comment_objs)
  
  for comment_obj in comment_objs:
    write_truth(comment_obj, new_truths, TRUTH_FIELDS, parent_id=post_url)
    write_truth(comment_obj["account"], new_authors, AUTHOR_FIELDS) # Note: this does not check for duplicates
  
  return n


def write_truth(obj, file, fields, parent_id=None):
  '''
  Write a truth or author object to CSV.
  :param obj: Dictionary object representing the truth or author
  :param file: Path to CSV file
  :param fields: List of fields/columns to write
  :param parent_id: Optional parent ID to include (for truths)
  :return: None
  '''
  with open(file, "a", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fields)
    row = {field: obj.get(field, None) for field in fields}
    if parent_id: row['PARENT_ID'] = parent_id
    writer.writerow(row)
    f.flush()


def compile_thread(seed=0):
  '''
  Compile threads by scraping comments from Truth Social posts.
  Each seed corresponds to a different user account for scraping.

  :param seed: Integer seed to determine which shard of data to process
  :return: None
  '''
  new_truths = HOME + f"new_truths-{seed}.csv"
  new_authors = HOME + f"new_authors-{seed}.csv"

  for path, fields in [(new_truths, TRUTH_FIELDS), (new_authors, AUTHOR_FIELDS)]:
    if not os.path.exists(path):
      with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        f.flush()
  
    # def _meets_inclusion_criteria(row):
    #   return (row[REPLIES] >= 3)

  # Load and filter dataset
  print("Loading dataset...")
  truths_df = pd.read_excel(DATASET).sample(frac=1, random_state=42).reset_index(drop=True)
  print("Dataset loaded.")

  # # Shard dataset by seed
  truths_df = truths_df[truths_df.index % 10 == seed]

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
  ''' 
  Combine all new_truths-*.csv and new_authors-*.csv into single files, deduplicating by post/author URL. 
  '''
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

    dup = combined.duplicated(subset=[URL]).sum()
    print(f"Duplicate rows: {dup}")

    combined = combined.drop_duplicates(subset=[URL], ignore_index=True)
    print(f"TOTAL rows after deduplication: {len(combined)}")

    combined.to_csv(f"{HOME}{output_name}", index=False)

  concat_files("new_truths*.csv", "new_truths-all.csv")
  concat_files("new_authors*.csv", "new_authors-all.csv")


def collect_authors(authors_list, output_file="missing_authors.csv"):
  '''
  Scrape author metadata for a list of usernames.
  
  :param authors_list: List of string author usernames to scrape
  :param output_file: Output CSV file path
  :return: None
  '''
  authors = set(authors_list)
  print(len(authors), "unique authors to fetch.")
  for author in authors:
    try:
      author_info = API.lookup(user_handle=author)
      write_truth(author_info, HOME + output_file, AUTHOR_FIELDS)
      print(author)
    except Exception as e:
      print(f"Failed to fetch author {author}: {e}")


def merge_scrape_logs():
  '''
  Merge all scrape_log-*.csv files into a single scrape_log.csv, combining scraped/output columns.
  '''
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
  main()