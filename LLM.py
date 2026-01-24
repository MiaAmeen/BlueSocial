import pandas as pd
import pandas as pd
from google import genai
from openai import OpenAI
from google.genai import types
import os
from time import time, sleep
from dotenv import load_dotenv
import requests

load_dotenv()

# LOAD THE DATA
HOME = "./data/"

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
AM_label = "AM_label"
SD = "SD_output"
SD_label = "SD_label"
IS_URL = "is_url"
NG = "Sanity Check"
in_reply_to = "in_reply_to_id"
PARENT_ID = "PARENT_ID"
PARENT_URL = "PARENT_URL"
PARENT_TEXT = "PARENT_content"

AM_CoT = """Ignore advertisements, tone, language quality, and factual accuracy. For each tweet, return your annotation in exactly the following format:
[id: <id>, annotation: The response is (argumentative/not argumentative) because: (brief justification)]"""

AM_Shots = """Ignore advertisements, tone, language quality, and factual accuracy. For each tweet, return your annotation in exactly the following format:
[id: <id>, annotation: (argumentative/not argumentative)]

Here are some example input/output pairs:

Tweets: [
[id: 1, text: ".<emoji: rotating_light>Follow #RealDonaldTrump #Trump2024 #WeThePeople are calling for dropping all charges against #Trump NOW! President Trump is innocent and suffered too much. We saw EVIL. Evildoers are DemonCRATS (AGs and Kangaroo judges) FakeNews and more, they are crooked, totally compromised.   We must Defeat #CrookedBiden. America is DAMAGED! #BidenTrial #Bidenflation #Bidenomics #BidenBorderCrisis   #Trump2024TheOnlyChoice  #Trump2024toSaveAmerica SAVE AMERICA<emoji: us>SAVE OUR WORLD<emoji: earth_americas><emoji: earth_africa><emoji: earth_asia> GOD BLESS DJT<emoji: latin_cross>GOD BLESS AMERICA<emoji: latin_cross>  #A06114  #T4MAGAt  ~ @WenMaMa2"],
[id: 2, text: "If President Trump IS convicted of any of the 91 indictments in the 4 trials brought by corrupt DA's...Obama's killing American citizens overseas, O'Biden's Immigrant Invasion and rampant crime and Bush's needless Wars in Iraq and Afghanistan are fair game!  These fuckers don't realize the "Pandora's Box" they've opened!  We will prosecute them just as we used the #NukeOption after Hairless Reid authored it, the #MeToo when they went after xxx and Justice Kavanaugh and the #Ukraine Quid Pro Quo Joey bragged about on video, they set the precedent!  None of them will be 'immune!'  #NukeOption  #MeToo  #Ukraine"],
[id: 3, text: "There's not a study of those who got one, two, or three jabs because a lot of them have already taken a Dirt Nap‚..  Officially known as "Death from unknown causes"   Isn't it weird Congress and Senators didn't have to get the Jab and none of them died from Unknown Causes?"],
[id: 4, text: "Wow! Fundraiser for the victims of Butler Rally has passed the $2.5 million. Keep helping, every $ counts! Thank you #MAGA <emoji: pray><emoji: us><emoji: heart> https://links.truthsocial.com/link/112786942059633018  #Trump2024 #TrumpAssassinationAttempt #PrayForTrump #GodWins #Maga4TheFelon"],
[id: 5, text: "Hi! I‚Äôm not sure how to really use Truth. This is my husbands account. But we are need of assistance badly. My husband is a 100 percent disabled combat vet from the Iraq war. He suffers from severe PTSD. We have been having really bad financial issues over the last few months and things have only gotten worse. Recently because of all the stress and him having PTSD he tried to unalive him self. He is ok now and recovering in the hospital. If anyone can please help whether it‚Äôs sharing, donating or even just praying for our family. We do have children. Everything is in the description and updates on the go fund me. Please we are desperate. Thank you to anyone and everyone who can help in any way. #Trump2024 #USMC #VETERANS #GoFundMe #patriots #disabledveterans  https://links.truthsocial.com/link/112716168326232757"],
[id: 6, text: "Woman Horrified by What Happened After Building Owners Unfurl Biden-Harris Banner Right Above Her Store      #Donaldtrump #FJB #JoeBiden #News #Trump2024      https://links.truthsocial.com/link/112824968393584003"],
]

Output: [
[id: 1, annotation: "argumentative"],
[id: 2, annotation: "argumentative"],
[id: 3, annotation: "argumentative"],
[id: 4, annotation: "non-argumentative"],
[id: 5, annotation: "non-argumentative"],
[id: 6, annotation: "non-argumentative"]
]"""

AM_Shots_CoT = """Ignore advertisements, tone, language quality, and factual accuracy. For each tweet, return your annotation in exactly the following format:
[id: <id>, annotation: The response is (argumentative/not argumentative) because: (brief justification)]

Here are some example input/output pairs:

Tweets: [
[id: 1, text: ".<emoji: rotating_light>Follow #RealDonaldTrump #Trump2024 #WeThePeople are calling for dropping all charges against #Trump NOW! President Trump is innocent and suffered too much. We saw EVIL. Evildoers are DemonCRATS (AGs and Kangaroo judges) FakeNews and more, they are crooked, totally compromised.   We must Defeat #CrookedBiden. America is DAMAGED! #BidenTrial #Bidenflation #Bidenomics #BidenBorderCrisis   #Trump2024TheOnlyChoice  #Trump2024toSaveAmerica SAVE AMERICA<emoji: us>SAVE OUR WORLD<emoji: earth_americas><emoji: earth_africa><emoji: earth_asia> GOD BLESS DJT<emoji: latin_cross>GOD BLESS AMERICA<emoji: latin_cross>  #A06114  #T4MAGAt  ~ @WenMaMa2"],
[id: 2, text: "If President Trump IS convicted of any of the 91 indictments in the 4 trials brought by corrupt DA's...Obama's killing American citizens overseas, O'Biden's Immigrant Invasion and rampant crime and Bush's needless Wars in Iraq and Afghanistan are fair game!  These fuckers don't realize the "Pandora's Box" they've opened!  We will prosecute them just as we used the #NukeOption after Hairless Reid authored it, the #MeToo when they went after xxx and Justice Kavanaugh and the #Ukraine Quid Pro Quo Joey bragged about on video, they set the precedent!  None of them will be 'immune!'  #NukeOption  #MeToo  #Ukraine"],
[id: 3, text: "There's not a study of those who got one, two, or three jabs because a lot of them have already taken a Dirt Nap‚..  Officially known as "Death from unknown causes"   Isn't it weird Congress and Senators didn't have to get the Jab and none of them died from Unknown Causes?"],
[id: 4, text: "Wow! Fundraiser for the victims of Butler Rally has passed the $2.5 million. Keep helping, every $ counts! Thank you #MAGA <emoji: pray><emoji: us><emoji: heart> https://links.truthsocial.com/link/112786942059633018  #Trump2024 #TrumpAssassinationAttempt #PrayForTrump #GodWins #Maga4TheFelon"],
[id: 5, text: "Hi! I‚Äôm not sure how to really use Truth. This is my husbands account. But we are need of assistance badly. My husband is a 100 percent disabled combat vet from the Iraq war. He suffers from severe PTSD. We have been having really bad financial issues over the last few months and things have only gotten worse. Recently because of all the stress and him having PTSD he tried to unalive him self. He is ok now and recovering in the hospital. If anyone can please help whether it‚Äôs sharing, donating or even just praying for our family. We do have children. Everything is in the description and updates on the go fund me. Please we are desperate. Thank you to anyone and everyone who can help in any way. #Trump2024 #USMC #VETERANS #GoFundMe #patriots #disabledveterans  https://links.truthsocial.com/link/112716168326232757"],
[id: 6, text: "Woman Horrified by What Happened After Building Owners Unfurl Biden-Harris Banner Right Above Her Store      #Donaldtrump #FJB #JoeBiden #News #Trump2024      https://links.truthsocial.com/link/112824968393584003"],
]

Output: [
[id: 1, annotation: "The response is argumentative because: it presents a claim that Trump is innocent and a victim, supported by premises alleging corruption and wrongdoing by political opponents."],
[id: 2, annotation: "The response is argumentative because: it makes a claim that Trump’s opponents are culpable and outlines multiple historical and legal events as supporting premises."],
[id: 3, annotation: "The response is argumentative because: it claims that COVID vaccines are dangerous, supported by premises about deaths and exemptions for officials."],
[id: 4, annotation: "The response is not argumentative because: it is a report of fundraising progress and a call to action, without any claim supported by premises."],
[id: 5, annotation: "The response is not argumentative because: it is a personal plea for assistance, describing circumstances without making a claim supported by premises."],
[id: 6, annotation: "The response is not argumentative because: it is a descriptive headline and link sharing, with no claim supported by premises."]
]"""

AM_SYSTEM_PROMPT = """You are an expert annotator. Given a list of tweets, annotate each tweet as either argumentative or non-argumentative. A tweet is argumentative if it contains a claim supported by premise(s). Use the following definitions:
- Claim: main point or position the author wants readers to accept.
- Premise: statement offered as support or justification for the claim. Implicit premises count if they clearly support the claim.
{}"""

AM_USER_PROMPT = """Now, annotate these tweets:
Tweets: [
{}
]
"""

SD_CoT = """Please ignore the tone, language quality, or factual accuracy of the tweet. For each reply, return a JSON-style list item using the following structure:
[id: <id>, annotation: "The response is FOR/AGAINST because: (short justification)"]
"""

SD_Shots = """Please ignore the tone, language quality, or factual accuracy of the tweet. For each reply, return a JSON-style list item using the following structure:
[id: <id>, annotation: "FOR/AGAINST/NEUTRAL"]

Here are some examples: 
[
[Tweet: "This whole case is a sham. Anyone paying attention can see the fix was in from day one. Judges, prosecutors, all compromised. This is what political persecution looks like in America. #Lawfare #BananaRepublic",
Replies: [
[id: 1, text: "Yep. When courts stop pretending to be neutral, this is exactly the result. Same playbook every time."],
[id: 2, text: "America feels broken lately tbh"]
]],
[Tweet: "Smart, capable, and respected worldwide. She actually understands foreign policy, unlike the clown she’s running against. #VoteBlue",
Replies: [
[id: 3, text: "Her grandfather owned plantations btw, but sure call her a saint"],
[id: 4, text: "anyone who still backs trump is delusional. this woman will destroy him in debates"],
[id: 5, text: "lol respected?? her polling numbers are garbage. you ppl live in fantasy land"]
]],
[Tweet: "Anyone else just see that bright spiral thing in the sky?? looked unreal 👀👽",
Replies: [
[id: 6, text: "Pretty sure that was a SpaceX launch, saw the same thing last year"]
]],
]

Output: [
[id: 1, annotation: "FOR"],
[id: 2, annotation: "NEUTRAL"],
[id: 3, annotation: "AGAINST"],
[id: 4, annotation: "FOR."],
[id: 5, annotation: "AGAINST"],
[id: 6, annotation: "NEUTRAL"]
]
"""

SD_Shots_CoT = """Please ignore the tone, language quality, or factual accuracy of the tweet. For each reply, return a JSON-style list item using the following structure:
[id: <id>, annotation: "The response is FOR/AGAINST because: (short justification)"]

Here are some examples: 
[
[Tweet: "This whole case is a sham. Anyone paying attention can see the fix was in from day one. Judges, prosecutors, all compromised. This is what political persecution looks like in America. #Lawfare #BananaRepublic",
Replies: [
[id: 1, text: "Yep. When courts stop pretending to be neutral, this is exactly the result. Same playbook every time."],
[id: 2, text: "America feels broken lately tbh"]
]],
[Tweet: "Smart, capable, and respected worldwide. She actually understands foreign policy, unlike the clown she’s running against. #VoteBlue",
Replies: [
[id: 3, text: "Her grandfather owned plantations btw, but sure call her a saint"],
[id: 4, text: "anyone who still backs trump is delusional. this woman will destroy him in debates"],
[id: 5, text: "lol respected?? her polling numbers are garbage. you ppl live in fantasy land"]
]],
[Tweet: "Anyone else just see that bright spiral thing in the sky?? looked unreal 👀👽",
Replies: [
[id: 6, text: "Pretty sure that was a SpaceX launch, saw the same thing last year"]
]],
]

Output: [
[id: 1, annotation: "The response is FOR because: it agrees that the legal case is politically motivated and supports the original claim of corruption."],
[id: 2, annotation: "The response is NEUTRAL because: it expresses general concern but does not take a stance on the claim made in the tweet."],
[id: 3, annotation: "The response is AGAINST because: it challenges the positive portrayal in the tweet by introducing critical information about the subject."],
[id: 4, annotation: "The response is FOR because: it endorses the tweet’s positive claim and reinforces support against the opposing figure."],
[id: 5, annotation: "The response is AGAINST because: it directly disputes the claim that the subject is respected or competent."],
[id: 6, annotation: "The response is NEUTRAL because: the original tweet expresses uncertainty rather than a clear claim, and the reply provides an explanation without taking a stance."]
]
"""

STANCE_SYSTEM_PROMPT = """You are given pairs of tweets and their replies. For each reply, determine its stance toward the main claim or premise (if any) expressed in the corresponding tweet. Stance labels are:
- FOR: The reply clearly supports or agrees with the claim/premises made in the tweet.
- AGAINST: The reply clearly opposes, challenges, or rejects the claim/premises made in the tweet.
- NEUTRAL: A reply is neutral if one of the following conditions is satisfied: The tweet expresses no clear claim/premise; the reply is irrelevant, off-topic, vague, or merely expressive; the reply does not clearly support or oppose the tweet’s claim/premises, or the reply is promotional or self-advertising content.

{}
"""

STANCE_USER_PROMPT = """Now, annotate these replies, given their parent tweets:
{}
"""

# API CLIENT CONFIGURATIONS
PEAK_REQ_PER_MIN = 20
OLLAMA_URL = "http://localhost:11434/api/generate"
gemini_client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'), project=os.getenv('GEMINI_PROJECT_ID'))
DS_client = OpenAI(api_key=os.environ.get('DEEPSEEK_API_KEY'), base_url="https://api.deepseek.com")
openai_client = OpenAI()

# MODELS
GEMINI = "gemini-2.5-flash"
# DS1 = "deepseek-r1:1.5b"
DS2 = "deepseek-r1:7b"
# DS3 = "deepseek-chat"
GPT = "o3-mini-2025-01-31"

def generate_content(input, SYSTEM_PROMPT, MODEL=GEMINI):
    '''
    Generate content using the specified LLM model/API endpoint.
    
    :param input: Input prompt string
    :param SYSTEM_PROMPT: System prompt string
    :param MODEL: LLM model to use
    :return: Generated content string
    '''
    match MODEL:
        case "gemini-2.5-flash":
            response = gemini_client.models.generate_content(
                model=MODEL,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT),
                contents=input
            )
            return response.text

        case "deepseek-r1:1.5b" | "deepseek-r1:7b":
            payload = {
                "model": MODEL,
                "prompt": input,
                "system": SYSTEM_PROMPT,
                "stream": False,
                "format": "JSON"
            }
            response = requests.post(OLLAMA_URL, json=payload)
            response.raise_for_status()
            return response.json()["response"]

        case "deepseek-chat" | "o3-mini-2025-01-31":
            client = openai_client if "o3" in MODEL else DS_client
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": input},
                ],
                stream=False
            )
            return response.choices[0].message.content


def argument_mine(df, prompting_method=SD_Shots_CoT, model=GPT):
    '''
    Perform argument mining on the given DataFrame of posts.
    
    :param df: DataFrame containing posts to annotate
    :param prompting_method: Prompting method (CoT, Shots, Shots_CoT) to use for annotation
    :param model: LLM model to use
    :return: DataFrame with added AM_output column
    '''
    def _meets_inclusion_criteria(row):
        return (row["AM_output"] == "" or pd.isna(row["AM_output"]))
    
    def extract_output(input_indices, output):
        id_positions = {}
        for post_id in set(input_indices.values()):
            pos = output.find(str(post_id))
            if pos != -1:
                id_positions[post_id] = pos

        sorted_ids = sorted(id_positions.items(), key=lambda x: x[1])
        extracted = {}
        for i, (post_id, start) in enumerate(sorted_ids):
            end = sorted_ids[i + 1][1] if i + 1 < len(sorted_ids) else len(output)
            extracted[post_id] = output[start:end].strip()

        for idx, post_id in input_indices.items():
            result = extracted.get(post_id, "ERROR: HALLUCINATION")
            df.loc[idx, AM] = result
            print(f"{post_id}, {result}")

        df[[EXT_ID, AM]].to_csv(HOME + "AM_output.csv", index=False)

    num_requests = 0
    last_api_call = None

    eligible_indices = [idx for idx, row in df.iterrows() if _meets_inclusion_criteria(row)]
    print(f"Total eligible posts: {len(eligible_indices)}")
    batch_size = 20
    for start in range(0, len(eligible_indices), batch_size):
        batch_idxs = eligible_indices[start:start + batch_size]

        input_str = ""
        input_indices = {}
        for idx in batch_idxs:
            row = df.loc[idx]
            ext_id = int(row[EXT_ID])
            input_indices[idx] = ext_id
            input_str += f"[id: {ext_id}, text: \"{str(row[TEXT]).replace('"', "'")}\"],\n"

        try:
            if last_api_call:
                elapsed = time() - last_api_call
                if elapsed < 60 and num_requests >= PEAK_REQ_PER_MIN:
                    sleep(60 - elapsed)
                    num_requests = 0

            output = generate_content(input=AM_USER_PROMPT.format(input_str), 
                                      SYSTEM_PROMPT=AM_SYSTEM_PROMPT.format(prompting_method),
                                      MODEL=model)
            last_api_call = time()
            num_requests += 1

            extract_output(input_indices, output)

        except Exception as e:
            print(f"ERROR during batch starting at index {start}: {e}")

    return df


def stance_detect(df, prompting_method=SD_Shots_CoT, model=GPT):
    '''
    Perform stance detection on the given DataFrame of replies.

    :param df: DataFrame containing replies to annotate
    :param prompting_method: Prompting method (CoT, Shots, Shots_CoT) to use for annotation
    :param model: LLM model to use
    :return: DataFrame with added SD_output column
    '''
    def _meets_inclusion_criteria(row):
        return True

    def extract_output(input_indices, output):
        id_positions = {}
        for post_id in set(input_indices.values()):
            pos = output.find(str(post_id))
            if pos != -1:
                id_positions[post_id] = pos

        sorted_ids = sorted(id_positions.items(), key=lambda x: x[1])
        extracted = {}
        for i, (post_id, start) in enumerate(sorted_ids):
            end = sorted_ids[i + 1][1] if i + 1 < len(sorted_ids) else len(output)
            extracted[post_id] = output[start:end].strip()

        rows_to_append = []
        for idx, post_id in input_indices.items():
            result = extracted.get(post_id, "ERROR: HALLUCINATION")
            df.loc[idx, SD] = result
            print(f"{post_id}, {result}")
            rows_to_append.append({EXT_ID: post_id, SD: result})

        append_df = pd.DataFrame(rows_to_append)
        append_df.to_csv("SD_OUTPUT_FIXED.csv", mode='a', index=False, header=not os.path.exists("SD_OUTPUT_FIXED.csv"))

    df = df.sort_values(by=["reply_depth", PARENT_URL]).reset_index(drop=True)
    num_requests = 0
    last_api_call = None

    eligible_indices = [idx for idx, row in df.iterrows() if _meets_inclusion_criteria(row)]
    batch_size = 25

    print(f"Total eligible replies for stance detection: {len(eligible_indices)}")
    for start in range(0, len(eligible_indices), batch_size):
        batch_idxs = eligible_indices[start:start + batch_size]

        input_indices = {}
        input_str = "["
        curr_text = None

        for idx in batch_idxs:
            row = df.loc[idx]
            ext_id = int(row[EXT_ID])
            parent_text = str(row[PARENT_TEXT]).replace('"', "'")

            if parent_text != curr_text:
                if curr_text is not None:
                    input_str += "]],\n"  # close previous Replies block and Tweet block

                input_str += f'[Tweet: "{parent_text}", Replies: [\n'
                curr_text = parent_text

            input_indices[idx] = ext_id
            reply_text = str(row[TEXT]).replace('"', "'")
            input_str += f'[id: {ext_id}, text: "{reply_text}"],\n'

        input_str += "]]]"  # close last Replies + Tweet + outer block

        try:
            pass
            if last_api_call:
                elapsed = time() - last_api_call
                if elapsed < 60 and num_requests >= PEAK_REQ_PER_MIN:
                    sleep(60 - elapsed)
                    num_requests = 0

            output = generate_content(
                STANCE_USER_PROMPT.format(input_str),
                SYSTEM_PROMPT=STANCE_SYSTEM_PROMPT.format(prompting_method),
                MODEL=model
            )

            last_api_call = time()
            num_requests += 1

            extract_output(input_indices, output)


        except Exception as e:
            print(f"ERROR during batch starting at index {start}: {e}")

    return df


def main():
    comments = pd.read_excel(HOME + "new_truths-all.xlsx", sheet_name="Sheet1", dtype={TEXT: str})
    stance_detect(comments, prompting_method=SD_Shots_CoT, model=GEMINI) 


if __name__ == "__main__":
    main()
