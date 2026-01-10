import pandas as pd
import pandas as pd
from google import genai
from google.genai import types
import os
from time import time, sleep
from collections import defaultdict
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


# LLM stuff
RHETORIC_SYSTEM_PROMPT = '''You are an expert discourse analyst. Given a JSON-formatted list of tweets, identify the dominant rhetorical strategy used for persuasion in each tweet. Assign exactly one of the following labels per tweet:
- logos: persuasion primarily through reasoning, causal claims, comparisons, or numerical evidence
- ethos: persuasion primarily through appeals to credibility/discreditability, authority, reputation, or moral character (including attacks on character)
- pathos: persuasion primarily through emotion, values, identity, fear, anger, pride, or moral outrage
Classify based on rhetorical function, not factual accuracy. If multiple strategies appear, choose the one that does the most persuasive work in shaping the reader’s judgment. Respond in the following format for each tweet, with no preambles:
 "This text employs {mode} because: {justification}"

Here are some examples:

Tweets: [
[id: 1, text: "Let's see if I got this right. We have a baby formula shortage in the US, and at the same time Bill Gates releases his Biomilq, breast milk substitute created in a lab, like his lab grown meat replacement. Meanwhile we send formula to Ukraine, stock pile it in border towns for illegals and Mexico has no shortage. Humm... is something going on? #Truth #TruthSeeker"],
[id: 2, text: "I am very happy to see some action occurring! Jordan said that Bragg received pressure from the Left to prosecute Trump, especially after the former president announced he would be running for president again in 2024. Shortly after the Trump presidential announcement, Bragg hired Matthew Colangelo, a senior official in President Joe Bidens Department of Justice. The Ohio congressman said that the pattern of Braggs actions demonstrates that the judicial system has been contorted to go after Trump. Alvin Braggs prosecution of President Trump was personal, was based on politics, and was wrong, Jordan said."],
[id: 3, text: "The Republican Party put all their money AGAINST MAGA candidates and got stomped. I no longer support Republicans. I support MAGA only. Republican establishment don‚Äôt waste your paper OR emails. You are against the MAGA movement and that‚Äôs okay. WE NOW OWN THIS PARTY AND WILL VOTE ALL YOUR A**ES OUT IN NOVEMBER. You have screwed the American people for the LAST TIME! MAGA!!"],
[id: 4, text: "40% of the money EVER printed in the United States HISTORY was printed in the last 15 months. THAT, fundamentally,  causes Inflation. The vast majority of that money went into the pockets of the wealthiest 1% of Americans. Interest Rates have doubled. True inflation, reflected by the CPI (Consumer Price Index) is almost 20%!!! Joe Biden and the Feds are systematically KILLING the Middle Class. ALL by design. #FJB #Trump2024"],
[id: 5, text: "#Juneteenth is a fake, neo-marxist holiday to promote Tribalism between different ethnicities in America.  There is no reason to respect it"],
[id: 6, text: "Trump is making his case to voters who traditionally support Democrats and have suffered for it, including blacks, Hispanics and in this case, young voters ‚and its resonating with them, which has the Democrats so terrified, all they can do is triple down on calling him a racist, Nazi Hitler. 3. When you listen to Trump unfiltered, hes nothing like the angry, fascist straw man the Democrats have invented. Hes well-informed, quick-witted and entertaining, and he doesnt insist on pre-screened questions like some people I could name. You can see why he was the #1 star on NBC before he became a Republican presidential candidate and they suddenly stopped sucking up to him and turned on him."]
]

Output: [
[id: 1, annotation: "This text employs logos because: it strings together comparative facts and causal claims (shortage, Biomilq, shipments) and uses rhetorical questioning to imply a logical pattern or conspiracy."],
[id: 2, annotation: "This text employs ethos because: it relies heavily on statements from an identified authority (Rep. Jim Jordan), references institutional affiliations (DOJ, Congress), and frames the argument around alleged abuses of credibility and moral integrity."],
[id: 3, annotation: "This text employs pathos because: it uses charged language, group identity, and exhortation to mobilize emotion and outrage rather than reasoned argument."],
[id: 4, annotation: "This text employs logos because: it foregrounds numerical claims and causal assertions (printing money leads to inflation) attempting an evidence-based argument, even though it mixes in hyperbolic moral accusations."],
[id: 5, annotation: "This text employs pathos because: it frames the holiday as illegitimate and threatening to values, using derogatory labels to provoke disgust and cultural fear rather than presenting factual critique."],
[id: 6, annotation: "This text employs ethos because: it emphasizes the subject’s credibility and character (career success, ‘well-informed’, entertaining) to build trust and authority, while contrasting that persona with opponents."]
]'''

AM_SYSTEM_PROMPT = """You are an expert annotator. Given a list of tweets, annotate each tweet as either argumentative or non-argumentative. A tweet is argumentative if it contains a claim supported by premise(s). Use the following definitions:
- Claim: main point or position the author wants readers to accept.
- Premise: statement offered as support or justification for the claim. Implicit premises count if they clearly support the claim.
Ignore advertisements, tone, language quality, and factual accuracy. For each tweet, return your annotation in exactly the following format:
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

AM_USER_PROMPT = """Now, annotate these tweets:
Tweets: [
{}
]
"""

STANCE_SYSTEM_PROMPT = """You are given pairs of tweets and their replies. For each reply, determine its stance toward the main claim or premise (if any) expressed in the corresponding tweet. Stance labels are:
- FOR: The reply clearly supports or agrees with the claim/premises made in the tweet.
- AGAINST: The reply clearly opposes, challenges, or rejects the claim/premises made in the tweet.
- NEUTRAL: A reply is neutral if one of the following conditions is satisfied: The tweet expresses no clear claim/premise; the reply is irrelevant, off-topic, vague, or merely expressive; the reply does not clearly support or oppose the tweet’s claim/premises, or the reply is promotional or self-advertising content.

Please ignore the tone, language quality, or factual accuracy of the tweet. For each reply, return a JSON-style list item using the following structure:
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

STANCE_USER_PROMPT = """Now, annotate these replies, given their parent tweets:
{}
"""

client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'), project=os.getenv('GEMINI_PROJECT_ID'))
PEAK_REQ_PER_MIN = 20

def generate_content(input, SYSTEM_PROMPT):
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT),
        contents=input
    )
    return response.text


OLLAMA_URL = "http://localhost:11434/api/generate"
DS1 = "deepseek-r1:1.5b"
DS2 = "deepseek-r1:7b"
def call_ollama(input, SYSTEM_PROMPT, MODEL=DS1):
    payload = {
        "model": MODEL,
        "prompt": input,
        "system": SYSTEM_PROMPT
    }
    response = requests.post(OLLAMA_URL, json=payload)
    response.raise_for_status()

    print(response.json()["load_duration"])
    return response.json()["response"]


def meets_inclusion_criteria(row):
#   return row["comments_scraped"] >= 3 and (row["AM_output"] == "" or pd.isna(row["AM_output"]))
#   return row["AM_output"] == "" or pd.isna(row["AM_output"])
    # return row["Source"] == "Truth Social"
    return row["AM?"] == 1 and row["reply_depth"] != "ORPHAN"
    # return True


def argument_mine(df):
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

            output = generate_content(AM_USER_PROMPT.format(input_str), SYSTEM_PROMPT=AM_SYSTEM_PROMPT)
            last_api_call = time()
            num_requests += 1

            extract_output(input_indices, output)

        except Exception as e:
            print(f"ERROR during batch starting at index {start}: {e}")

    return df


def merge_outputs(df_x, df_c):
    df_excel = df_x.set_index("row")
    df_csv = df_c.set_index("row")

    conflicts = []
    new_outputs_added = 0
    for row_id, csv_val in df_csv["AM_output"].items():
        if pd.isna(csv_val) or csv_val == "" or row_id not in df_excel.index: continue

        excel_val = df_excel.at[row_id, "AM_output"]
        if pd.isna(excel_val) or excel_val == "":
            df_excel.at[row_id, "AM_output"] = csv_val
            new_outputs_added += 1

        elif str(excel_val) != str(csv_val):
            conflicts.append(row_id)
    final_total_outputs = df_excel["AM_output"].notna().sum()
    df_excel.reset_index().to_excel(HOME + "gemini_argmine.xlsx", index=False)

    print(f"\nNew outputs added: {new_outputs_added}")
    print(f"Final total outputs: {final_total_outputs}")


def stance_detect(df):
    def _meets_inclusion_criteria(row):
        return row["AM?"] == 1 and row["reply_depth"] != "ORPHAN" and \
            (pd.isna(row[SD]) or row[SD] == "") and row[TEXT] != "" and not pd.isna(row[TEXT]) \
            and row["PARENT_comments"] >= 3

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
            df.loc[idx, SD] = result
            print(f"{post_id}, {result}")

        df[[EXT_ID, SD]].to_csv(HOME + "SD_output.csv", index=False)

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
            parent_text = row[PARENT_TEXT].replace('"', "'")

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
                SYSTEM_PROMPT=STANCE_SYSTEM_PROMPT
            )

            last_api_call = time()
            num_requests += 1

            extract_output(input_indices, output)

        except Exception as e:
            print(f"ERROR during batch starting at index {start}: {e}")

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


def main():
    # print("API key in use: ", os.getenv('GEMINI_API_KEY'))
    # print("Project ID in use: ", os.getenv('GEMINI_PROJECT_ID'))
    
    # posts = pd.read_excel(HOME + "TS24-clean.xlsx", sheet_name="AM", dtype={TEXT: str})
    # argument_mine(posts)

    # comments = pd.read_excel(HOME + "new_truths-all.xlsx", sheet_name="Sheet1", dtype={TEXT: str})
    # stance_detect(comments)

    prompt = "testing..."
    print(call_ollama(prompt, SYSTEM_PROMPT="You are a helpful assistant."))


if __name__ == "__main__":
    main()
    # comments = pd.read_excel(HOME + "new_truths-all.xlsx", sheet_name="Sheet1")
    
    # stance_detect(posts)
    # merge_outputs(posts, pd.read_csv(HOME + "gemini_argmine.csv"))




