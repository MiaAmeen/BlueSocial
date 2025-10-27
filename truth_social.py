import numpy
import pandas as pd
from textblob import TextBlob
from detoxify import Detoxify

# Input and output file paths
HOME = "/Users/destroyerofworlds/Desktop/NLP/PROJECT/BlueSocial/truth_social/"
input_file = HOME + "truths_cleaned.csv"
output_file = HOME + "truths_tagged.csv"

# Load the TSV file
df = pd.read_csv(input_file)
print(len(df), "rows loaded.")
TEXT = "text"

# Function to compute sentiment polarity
def get_sentiment(text):
  if pd.isna(text):
    return -1
  return TextBlob(str(text)).sentiment.polarity

def get_toxicity(text):
  if pd.isna(text):
    return -1
  print(text)
  return Detoxify('original').predict(str(text))['toxicity']

# Apply sentiment analysis row by row
df["toxicity"] = df[TEXT].apply(get_toxicity)
df["sentiment"] = df[TEXT].apply(get_sentiment)

# Save the new dataframe to a TSV file
df.to_csv(output_file, index=False)
print(f"Sentiment analysis complete! Results saved to {output_file}")
