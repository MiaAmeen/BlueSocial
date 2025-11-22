import numpy as np
import pandas as pd
import pandas as pd
from detoxify import Detoxify
from google import genai
from google.genai import types
import os
from time import time, sleep

from nltk.sentiment import SentimentIntensityAnalyzer
import nltk

# LOAD THE DATA
HOME = "/Users/destroyerofworlds/Desktop/NLP/PROJECT/BlueSocial/truth_social/"
TRUTHS = HOME + "truths_cleaned_tagged.xlsx"
truths_df = pd.read_excel(TRUTHS, sheet_name="popularity_cutoff").sample(frac=1, random_state=42).reset_index(drop=True)
print(len(truths_df), "truths loaded.")

# Column names
POPULARITY = "follow_ratio"
PROFILE = "profile_url"
TEXT = "text"
EXT_ID = "external_id"
SENTIMENT = "sentiment"
REPLIES = "reply_count"
LIKES = "like_count"
TOXICITY = "toxicity"
AM = "AM_output"
IS_URL = "is_url"
NG = "Sanity Check"

# LLM stuff
SYSTEM_PROMPT = """I need you to help me annotate political tweets. Your task is to determine whether a given tweet contains an argument and, if so, to identify the primary mode(s) of persuasion employed.

A tweet is an argument if it contains a claim supported by premise(s).
- A claim is a main point, position, or proposition an author wants to convince the readers of. It is the statement being supported.
- A premise is a piece of evidence offered to provide support for, or justification of, the claim. The premise may employ one or more of the following three defined modes of persuasion:
  - Logos: the premise is factual evidence or logical reasoning.
  - Ethos: the premise is an emotional appeal to the audience.
  - Pathos: the premise is an appeal to the character and credibility of someone making the argument.

You may find advertisements in tweets promoting a user’s content. Even though they may be argumentative, please ignore them for this task. Please also ignore the tone, language quality, or factual accuracy of the tweet. Your primary criterion is the structural relationship between a claim and its premise(s), and the mode(s) of persuasion employed within the premises. Give a short justification for your judgement in the following structure: ‘The response is (argumentative/not argumentative) [if argumentative: (and employing (mode(s)))] because: (justification)’ without any preambles.

Here are some examples:

Tweet: I think cannabis should be legalized because it has real medical benefits!
The response is argumentative and employing logos because it contains a claim and premise, and the premise is a fact.

Tweet: I love donald trump
The response is not argumentative because it does not contain a claim or premise.
"""

USER_PROMPT = """Now, annotate this tweet:
Tweet: {}"""

client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
PEAK_REQ_PER_MIN = 10

def generate_content(input):
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT),
        contents=input
    )
    return response.text

def clean_data(df):
    nltk.download('vader_lexicon')
    sia = SentimentIntensityAnalyzer()

    def get_toxicity(text):
        if pd.isna(text): return None
        # print(text)
        return Detoxify('original').predict(str(text))['toxicity']
    
    def vader_sentiment(text):
        if pd.isna(text): return None
        # print(text)
        return sia.polarity_scores(text)['compound']

    df = df.drop_duplicates(subset=[PROFILE, TEXT]).copy()
    filtered_df = df[df[REPLIES] >= 1]
    filtered_df[SENTIMENT] = filtered_df[TEXT].apply(vader_sentiment)

    print(f"Number of posts: {len(filtered_df)}")
    print(f"Unique users: {filtered_df[PROFILE].nunique()}")

    # --- 4. Save cleaned data ---
    output_path = HOME + "truths_cleaned_tagged.xlsx"
    filtered_df.to_excel(output_path, index=False)
    print(f"✅ Cleaned data saved to: {output_path}")

    return filtered_df

def popularity_range(df):
    vals = df[df[POPULARITY] >= 0][POPULARITY]
    Q1 = vals.quantile(0.25)
    Q3 = vals.quantile(0.75)
    IQR = Q3 - Q1

    # Outlier thresholds
    # lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR

    # print("Q1 (25%):", Q1)
    # print("Q3 (75%):", Q3)
    # print("Lower bound:", lower_bound)
    # print("Upper bound:", upper_bound)

    return upper_bound

def meets_inclusion_criteria(row):
  return (row[AM] == "" or pd.isna(row[AM])) and row[REPLIES] >= 5 and row[NG] != 1 and row[IS_URL] == 1 and row[REPLIES] <= 100

def argument_mine(df):
    output_path = HOME + "gemini.csv"
    num_requests = 0
    last_api_call = None

    for idx, row in df.iterrows():
        if not meets_inclusion_criteria(row): continue

        try:
            if last_api_call:
                elapsed = time() - last_api_call
                if elapsed < 60 and num_requests >= PEAK_REQ_PER_MIN:
                    sleep(60 - elapsed)
                    num_requests = 0

            # API call
            output = generate_content(USER_PROMPT.format(row[TEXT]))
            last_api_call = time()
            num_requests += 1

            df.at[idx, AM] = output
            print(f"{row["row"]}, '{output}'")
            df.to_csv(output_path, index=False)

        except Exception as e:
            print(f"Error at index {idx}: {e}")

    return df


if __name__ == "__main__":
    # truths_df = clean_data(truths_df)
    argument_mine(truths_df)
