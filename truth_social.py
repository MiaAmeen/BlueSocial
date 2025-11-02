import numpy
import pandas as pd
from textblob import TextBlob
from detoxify import Detoxify
from truthbrush import truthbrush
import os

# LOAD THE DATA
HOME = "/Users/destroyerofworlds/Desktop/NLP/PROJECT/BlueSocial/truth_social/"
input_file = HOME + "truths_cleaned.csv"
output_file = HOME + "truths_sentiment_tagged.csv"
df = pd.read_csv(input_file)
print(len(df), "rows loaded.")

# Column names
TEXT = "text"
TOXICITY = "toxicity"
SENTIMENT = "sentiment"

# Set up Truth Social API client
username = os.getenv("TRUTHSOCIAL_USERNAME")
password = os.getenv("TRUTHSOCIAL_PASSWORD")
API = truthbrush.Api(username=username, password=password)

def save_sentiment():
  '''
  Get sentiment polarity for each Truth using TextBlob.
  Returns a float within the range [-1.0, 1.0] where -1 indicates negative sentiment and 1 indicates positive sentiment.
  '''
  def get_sentiment(text):
    if pd.isna(text): return -1
    print(text)
    return TextBlob(str(text)).sentiment.polarity
  
  df[SENTIMENT] = df[TEXT].apply(get_sentiment)

def save_toxicity():
  '''
  Get toxicity score for each Truth using Detoxify.
  '''
  def get_toxicity(text):
    if pd.isna(text): return -1
    print(text)
    return Detoxify('original').predict(str(text))['toxicity']
  
  df[TOXICITY] = df[TEXT].apply(get_toxicity)


def get_comments(post_url):
  '''
  Fetch comments from Truth Social using truthbrush.
  '''
  rtn = API.pull_comments(post_url, include_all=True)
  return list(rtn)

def main():
  # post_id = "https://truthsocial.com/@Qanon76/posts/114415124864156240"
  # print(get_comments(post_id))

  # # Save the new dataframe to a TSV file
  save_sentiment()
  df.to_csv(output_file, index=False)

main()
