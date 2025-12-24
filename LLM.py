import pandas as pd
import pandas as pd
from google import genai
from google.genai import types
import os
from time import time, sleep
from collections import defaultdict
import regex as re
import json

# LOAD THE DATA
HOME = "/Users/destroyerofworlds/Desktop/NLP/PROJECT/BlueSocial/data/"
TRUTHS = HOME + "truth_social/truths_cleaned_tagged.xlsx"
COMMENTS = HOME + "new_truths.xlsx"

# Column names
POPULARITY = "follow_ratio"
PROFILE = "profile_url"
TEXT = "content"
EXT_ID = "external_id"
SENTIMENT = "sentiment"
REPLIES = "reply_count"
LIKES = "like_count"
TOXICITY = "toxicity"
AM = "AM_output"
STANCE = "stance_output"
IS_URL = "is_url"
NG = "Sanity Check"
in_reply_to = "in_reply_to_id"

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
[id: 1, text: ".<emoji: rotating_light>Follow #RealDonaldTrump #Trump2024 #WeThePeople are calling for dropping all charges against #Trump NOW! President Trump is innocent and suffered too much. We saw EVIL. Evildoers are DemonCRATS (AGs and Kangaroo judges) FakeNews and more, they are crooked, totally compromised.   We must Defeat #CrookedBiden. America is DAMAGED! #BidenTrial #Bidenflation #Bidenomics #BidenBorderCrisis   #Trump2024TheOnlyChoice  #Trump2024toSaveAmerica SAVE AMERICA<emoji: us>SAVE OUR WORLD<emoji: earth_americas><emoji: earth_africa><emoji: earth_asia> GOD BLESS DJT<emoji: latin_cross>GOD BLESS AMERICA<emoji: latin_cross>  #A06114  #T4MAGAt  ~ @WenMaMa2"],
[id: 2, text: "If President Trump IS convicted of any of the 91 indictments in the 4 trials brought by corrupt DA's...Obama's killing American citizens overseas, O'Biden's Immigrant Invasion and rampant crime and Bush's needless Wars in Iraq and Afghanistan are fair game!  These fuckers don't realize the "Pandora's Box" they've opened!  We will prosecute them just as we used the #NukeOption after Hairless Reid authored it, the #MeToo when they went after xxx and Justice Kavanaugh and the #Ukraine Quid Pro Quo Joey bragged about on video, they set the precedent!  None of them will be 'immune!'  #NukeOption  #MeToo  #Ukraine"],
[id: 3, text: "There's not a study of those who got one, two, or three jabs because a lot of them have already taken a Dirt Nap‚..  Officially known as "Death from unknown causes"   Isn't it weird Congress and Senators didn't have to get the Jab and none of them died from Unknown Causes?"],
[id: 4, text: "In the fall of 2020, researchers at the Univ of Pittsburgh published a study titled, ‚ÄúDevelopment of humanized mouse and rat models with full-thickness human skin and autologous immune cells.‚Äù In studying how organs reacted to pathogens or infections on human skin, researchers grafted ‚Äúfull-thickness human skin‚Äù a/w/a thymuses, livers, and spleens from fetuses onto rodent bodies, creating what they call ‚Äúhumanized rat models.‚Äù  Humanized rats. Remains of unborn babies, purchased from Planned Parenthood and the like, had their scalps removed and subsequently attached to the heads of lab rats. As head of the NIH, not only did Collins approve this study and thus validate its objectives, but also provided taxpayer funds to pay for it.   One yr later, thanks to the work of pro-life undercover journalists, U of P admitted to removing the kidneys from born-alive babies while their hearts were still beating."],
[id: 5, text: "Hi! I‚Äôm not sure how to really use Truth. This is my husbands account. But we are need of assistance badly. My husband is a 100 percent disabled combat vet from the Iraq war. He suffers from severe PTSD. We have been having really bad financial issues over the last few months and things have only gotten worse. Recently because of all the stress and him having PTSD he tried to unalive him self. He is ok now and recovering in the hospital. If anyone can please help whether it‚Äôs sharing, donating or even just praying for our family. We do have children. Everything is in the description and updates on the go fund me. Please we are desperate. Thank you to anyone and everyone who can help in any way. #Trump2024 #USMC #VETERANS #GoFundMe #patriots #disabledveterans  https://links.truthsocial.com/link/112716168326232757"],
[id: 6, text: "Woman Horrified by What Happened After Building Owners Unfurl Biden-Harris Banner Right Above Her Store      #Donaldtrump #FJB #JoeBiden #News #Trump2024      https://links.truthsocial.com/link/112824968393584003"],
]

Output: [
[id: 1, annotation: The response is argumentative and employing Ethos, Pathos because: it advances the claim that charges should be dropped and that “President Trump is innocent,” and supports that claim with emotional appeals (e.g., “SAVE AMERICA,” “suffered too much,” “GOD BLESS”) and attacks on opponents’ character/credibility (e.g., “Evildoers…DemonCRATS,” “crooked, totally compromised”), which function as premises.],
[id: 2, annotation: The response is argumentative and employing Logos because: it makes a conditional claim about prosecuting political opponents if Trump is convicted and supports it by citing precedents and examples (“we used the #NukeOption…#MeToo…Ukraine Quid Pro Quo”) (logos).],
[id: 3, annotation: The response is argumentative and employing Logos because: it asserts the claim that vaccine recipients have died (“a lot of them have already taken a Dirt Nap…Death from unknown causes”) which is presented as factual evidence (logos).],
[id: 4, annotation: The response is argumentative and employing Logos, Pathos because: it claims NIH/U. of Pittsburgh funded and carried out grotesque fetal-tissue experiments and supports this with citation of a specific published study and later investigative claims (logos), while using graphic, emotional descriptions (scalps removed, born-alive babies) to persuade (pathos).],
[id: 5, annotation: The response is not argumentative because: it is a personal plea for assistance without any claim or premise.],
[id: 6, annotation: The response is not argumentative because: it reads like a linked headline/summary reporting someone’s reaction without any claim or premise.],
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
PEAK_REQ_PER_MIN = 150

def generate_content(input, SYSTEM_PROMPT=AM_SYSTEM_PROMPT):
    response = client.models.generate_content(
        model="gemini-2.5-pro",
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT),
        contents=input
    )
    return response.text

def meets_inclusion_criteria(row):
  return row["comments_scraped"] >= 3 and \
  (row["AM_label"] == "" or pd.isna(row["AM_label"])) and (row["AM_output"] == "" or pd.isna(row["AM_output"]))
    # return row["AM_label"] == 1

def argument_mine(df):

    def extract_output(input_indices, output):
        pattern = r"\[id:\s*(\d+),\s*annotation:\s*(.*?)\],"
        matches = re.findall(pattern, output, flags=re.DOTALL)
        match_dict = {int(post_id): annotation.strip() for post_id, annotation in matches}
        for idx, post_id in input_indices.items():
            if post_id in match_dict:
                df.loc[idx, AM] = match_dict[post_id]
                print(f"{post_id}, {match_dict[post_id]}")
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
            ext_id = int(row[EXT_ID])
            input_indices[idx] = ext_id
            input_str += f"[id: {ext_id}, text: \"{row[TEXT].replace('"', "'")}\"]\n"

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


def stance_detect(df, comments):
    def extract_output(output):
        # 1. Extract all [id: ..., Stance: "..."] blocks using regex
        pattern = r"\[id:\s*(\d+),\s*Stance:\s*\"(.*?)\"\]"
        matches = re.findall(pattern, output, flags=re.DOTALL)
        for comment_id, stance_text in matches:
            comment_id = int(comment_id)
            if comment_id in comments[EXT_ID].values:
                comments.loc[comments[EXT_ID] == comment_id, STANCE] = stance_text
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
                    formatted_tweets.append(f'[id: {c[EXT_ID]}, Response: "{json.dumps(c["content"])}"]')
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


def get_comment_levels(comments, parent_id, reply_lookup):
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
        row = comments[comments[EXT_ID] == last_reply]
        previous_row = row.iloc[0][in_reply_to]
        if previous_row != parent_id and previous_row not in direct_replies \
            and previous_row not in last_replies:
            second_to_last_replies.append(previous_row)
    second_to_last_replies = set(second_to_last_replies)

    comments.loc[comments[EXT_ID].isin(last_replies), "nth_comment"] = "n"
    comments.loc[comments[EXT_ID].isin(second_to_last_replies), "nth_comment"] = "n-1"

    # return {
    #     "original_id": parent_id,
    #     "direct_replies": list(set(direct_replies)),
    #     "second_to_last_replies": list(set(second_to_last_replies)),
    #     "last_replies": list(set(last_replies))
    # }


def all_comment_levels(posts, comments):
    """
    Reads input files, constructs the reply tree, and computes comment levels for all parent tweets.
    """
    reply_lookup = defaultdict(list)
    for _, row in comments.iterrows():
        reply_lookup[row[in_reply_to]].append(row[EXT_ID])

    for _, row in posts.iterrows():
        parent_id = row[EXT_ID]
        if parent_id not in reply_lookup: continue
        get_comment_levels(comments, parent_id=parent_id, reply_lookup=reply_lookup)

    comments.to_csv(HOME + "new_truths_with_n.csv", index=False)

if __name__ == "__main__":
    posts = pd.read_excel(HOME + "TS24_min-replies-content.xlsx")
    argument_mine(posts)
