import numpy as np
import pandas as pd
import pandas as pd
from detoxify import Detoxify
from google import genai
from google.genai import types
import os
from time import time, sleep
from collections import defaultdict
import regex as re
import json

from nltk.sentiment import SentimentIntensityAnalyzer
import nltk

# LOAD THE DATA
HOME = "/Users/destroyerofworlds/Desktop/NLP/PROJECT/BlueSocial/"
TRUTHS = HOME + "truth_social/truths_cleaned_tagged.xlsx"
COMMENTS = HOME + "new_truths.xlsx"

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
STANCE = "stance_output"
IS_URL = "is_url"
NG = "Sanity Check"

# LLM stuff
AM_SYSTEM_PROMPT = """I need you to help me annotate some political tweets. Your task is to determine whether a given tweet contains an argument and, if so, to identify the primary mode(s) of persuasion employed.

A tweet is an argument if it contains a claim supported by premise(s).
- A claim is a main point, position, or proposition an author wants to convince the readers of. It is the statement being supported.
- A premise is a piece of evidence offered to provide support for, or justification of, the claim. The premise may employ one or more of the following three defined modes of persuasion:
  - Logos: the premise is factual evidence or logical reasoning.
  - Ethos: the premise is an emotional appeal to the audience.
  - Pathos: the premise is an appeal to the character and credibility of someone making the argument.

You may find advertisements in tweets promoting a user's content. Even though they may be argumentative, please ignore them for this task. Please also ignore the tone, language quality, or factual accuracy of the tweet. Your primary criterion is the structural relationship between a claim and its premise(s), and the mode(s) of persuasion employed within the premises. Give a short justification for your judgement in the following structure: ‘The response is (argumentative/not argumentative) [if argumentative: (and employing (mode(s)))] because: (justification)' without any preambles.

Here are some examples:

Tweets: [
[id: 1, text: 'I think cannabis should be legalized because it has real medical benefits!'],
[id: 2, text: 'I love donald trump'],
]

Output: [
[id: 1, annotation: The response is argumentative and employing logos because it contains a claim and premise, and the premise is a fact.],
[id: 2, annotation: The response is not argumentative because it does not contain a claim or premise.],
]
"""

AM_USER_PROMPT = """Now, annotate these tweets:
Tweets: [
{}
]
"""

STANCE_SYSTEM_PROMPT = """You are given an argument and a list of tweets. For each tweet, determine:
1. Whether the claim contained in the tweet is FOR or AGAINST the argument. A claim is the main point or position the tweet expresses in response to the argument.
    FOR: the claim supports the argument.
    AGAINST: the claim refutes the argument.
    Ignore promotional or self-advertising content; do not classify them as FOR or AGAINST.
2. If the tweet contains a premise, identify the mode(s) of persuasion in the premise(s). A premise is a piece of evidence offered to provide support for, or justification of, the claim. It may use one of these three modes:
    Logos: factual evidence or logical reasoning.
    Ethos: appeal to credibility or authority.
    Pathos: emotional appeal.

Please ignore the tone, language quality, or factual accuracy of the tweet. For each tweet you annotate, give a short justification for your judgement in the following structure, without any preambles:
[id: X, Stance: "The response is FOR/AGAINST [and employing (mode(s))] because: (short justification)"]

Here are some examples:

Argument: "I think cannabis should be legalized because it has real medical benefits!"

Tweets: [
  [id: 1, Response: "You're crazy if you think we should let drug dealers just walk the streets"],
  [id: 2, Response: "my grandma's doctor started prescribing her medicinal cannabis ever since she got cancer, and it's been really helping her thru chemo"],
  [id: 3, Response: "i second this"]
]

Output: [
  [id: 1, Stance: "The response is AGAINST the argument and employs Pathos because it contains a claim that refutes the argument ('You're crazy') and appeals to emotion through disgust at letting drug dealers 'walk the streets'."],
  [id: 2, Stance: "The response is FOR the argument and employs Ethos because it contains a claim that supports the argument ('it's been really helping her') and appeals to the credibility of a doctor who prescribed cannabis."],
  [id: 3, Stance: "The response is FOR the argument because it contains a claim that supports the argument ('i second this')."]
]
"""

STANCE_USER_PROMPT = """Now, annotate these tweets, given the argument:
Argument: {}
Tweets: [
  {}
]
"""

client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'), project=os.getenv('GEMINI_PROJECT_ID'))
PEAK_REQ_PER_MIN = 10

def generate_content(input, SYSTEM_PROMPT=AM_SYSTEM_PROMPT):
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

def has_meaningful_text(text):
    if not text or not isinstance(text, str):
        return False

    text_clean = re.sub(r"http\S+|www\.\S+", "", text) # Remove URLs    
    text_clean = re.sub(r"<emoji:\s*[^>]+>", "", text_clean)
    text_clean = re.sub(r"[^\w\s]", "", text_clean) # Remove emojis and non-word symbols
    text_clean = re.sub(r"\d+", "", text_clean) # Remove numbers
    text_clean = text_clean.strip() # Strip whitespace
    
    return bool(re.search(r"[A-Za-z]", text_clean)) # Check if any alphabetic characters remain


def meets_inclusion_criteria(row):
  return has_meaningful_text(row["text"]) and row["reply_count"] >= 5 and \
  (row["AM_label"] == "" or pd.isna(row["AM_label"])) and (row["AM_output"] == "" or pd.isna(row["AM_output"]))
# and row["comments_scraped"] == 1 and row["AM_label"] == 1

def argument_mine(df):

    def extract_output(input_indices, output):
        pattern = r"\[id:\s*(\d+),\s*annotation:\s*(.*?)\]"
        matches = re.findall(pattern, output, flags=re.DOTALL)

        match_dict = {int(pid): ann.strip() for pid, ann in matches}
        for idx, post_id in input_indices.items():
            post_id = int(post_id)

            if post_id in match_dict:
                df.loc[idx, AM] = match_dict[post_id]
            else:
                df.loc[idx, AM] = "ERROR: HALLUCINATION"
        df.to_csv(HOME + "gemini_argmine.csv", index=False)

    num_requests = 0
    last_api_call = None

    eligible_indices = [idx for idx, row in df.iterrows() if meets_inclusion_criteria(row)]
    batch_size = 10

    for start in range(0, len(eligible_indices), batch_size):
        batch_idxs = eligible_indices[start:start + batch_size]

        input_str = ""
        input_indices = {}

        for idx in batch_idxs:
            row = df.loc[idx]
            ext_id = row['external_id']
            input_indices[idx] = ext_id
            input_str += f"[id: {ext_id}, text: \"{row['text'].replace('"', "'")}\"]\n"

        try:
            if last_api_call:
                elapsed = time() - last_api_call
                if elapsed < 60 and num_requests >= PEAK_REQ_PER_MIN:
                    sleep(60 - elapsed)
                    num_requests = 0

            output = generate_content(AM_USER_PROMPT.format(input_str), SYSTEM_PROMPT=AM_SYSTEM_PROMPT)
            last_api_call = time()
            num_requests += 1

            extract_output(input_indices, output)

        except Exception as e:
            print(f"ERROR during batch starting at index {start}: {e}")

    return df


def stance_detect(df):
    def extract_output(output):
        # 1. Extract all [id: ..., Stance: "..."] blocks using regex
        pattern = r"\[id:\s*(\d+),\s*Stance:\s*\"(.*?)\"\]"
        matches = re.findall(pattern, output, flags=re.DOTALL)
        for comment_id, stance_text in matches:
            comment_id = int(comment_id)
            if comment_id in comments[id_col].values:
                comments.loc[comments[id_col] == comment_id, STANCE] = stance_text
        comments.to_csv(HOME + "new_truths_stances.csv", index=False)

    batch_size = 30
    for idx, row in df.iterrows():
        if not meets_inclusion_criteria(row): continue
        try:
            curr_comments = comments[comments["PARENT_ID"] == row["url"]]
            curr_comments = curr_comments[curr_comments["nth_comment"].notna()]
            curr_comments = curr_comments[
                curr_comments["stance_output"].isna() | (curr_comments["stance_output"] == "")
            ]
            if curr_comments.empty: continue

            for i in range(0, len(curr_comments), batch_size):
                batch = curr_comments.iloc[i:i + batch_size]
                formatted_tweets = []
                for _, c in batch.iterrows():
                    formatted_tweets.append(f'[id: {c["id"]}, Response: "{json.dumps(c["content"])}"]')
                tweets_str = ",\n".join(formatted_tweets)

                input_str = STANCE_USER_PROMPT.format(
                    row["text"].replace('"', '\\"'),  # argument placeholder
                    tweets_str        # tweets placeholder
                )
                output = generate_content(input_str, SYSTEM_PROMPT=STANCE_SYSTEM_PROMPT)
                extract_output(output)
            
            print(f"{row['url']}: {len(curr_comments)}")

        except Exception as e:
            print(f"Error at index {idx}: {e}")

    return df


def get_comment_levels(parent_id, reply_lookup):
    """
    Computes direct, second-to-last, and last replies for a single parent tweet.
    """
    def dfs(node_id):
        children = reply_lookup.get(node_id, [])
        if not children:
            return [node_id]
        all_last = []
        for child in children:
            all_last.extend(dfs(child))
        return all_last

    direct_replies = reply_lookup.get(parent_id, [])
    last_replies = [r for r in dfs(parent_id) if r not in direct_replies and r != parent_id]

    second_to_last_replies = []
    for last_reply in last_replies:
        row = comments[comments[id_col] == last_reply]
        previous_row = row.iloc[0][in_reply_to]
        if previous_row != parent_id and previous_row not in last_replies \
            and previous_row not in second_to_last_replies and previous_row not in direct_replies:
            second_to_last_replies.append(previous_row)

    comments.loc[comments[id_col].isin(last_replies), "nth_comment"] = "n"
    comments.loc[comments[id_col].isin(second_to_last_replies), "nth_comment"] = "n-1"

    # return {
    #     "original_id": parent_id,
    #     "direct_replies": list(set(direct_replies)),
    #     "second_to_last_replies": list(set(second_to_last_replies)),
    #     "last_replies": list(set(last_replies))
    # }


def all_comment_levels():
    """
    Reads input files, constructs the reply tree, and computes comment levels for all parent tweets.
    """
    reply_lookup = defaultdict(list)
    for _, row in comments.iterrows():
        reply_lookup[row[in_reply_to]].append(row[id_col])

    for _, row in posts.iterrows():
        if row["num_comments"] < 1: continue
        parent_id = row[parent_id_col]
        get_comment_levels(parent_id=parent_id, reply_lookup=reply_lookup)

    comments.to_csv(HOME + "new_truths_with_n.csv", index=False)

if __name__ == "__main__":
    # truths_df = clean_data(truths_df)
    truths_df = pd.read_excel(TRUTHS, sheet_name="popularity_cutoff").sample(frac=1, random_state=42).reset_index(drop=True)
    print(len(truths_df), "truths loaded.")
    argument_mine(truths_df)

    # all_comment_levels()
    # posts = pd.read_excel(HOME + "ANALYSIS.xlsx")
    # comments = pd.read_excel(HOME + "new_truths.xlsx")
    # parent_id_col = "external_id"
    # in_reply_to = "in_reply_to_id"
    # id_col = "id"
    # stance_detect(posts)
