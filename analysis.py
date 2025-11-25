import numpy as np
import pandas as pd
import os
from collections import defaultdict
from PIL import Image, ImageOps
import matplotlib.pyplot as plt

from nltk.sentiment import SentimentIntensityAnalyzer
import nltk

import plotly.graph_objects as go
import seaborn as sns


# LOAD THE DATA
HOME = "/Users/destroyerofworlds/Desktop/NLP/PROJECT/BlueSocial/"
input_file = HOME + "ANALYSIS.xlsx"

# Column names
TEXT = "text"
TOXICITY = "toxicity"
SENTIMENT = "sentiment"
LLM_OUTPUT = "AM_output"
PM = "PM_label"
FOLLOWER_RATIO = "follow_ratio"
lIKES = "like_count"
COMMENTS = "num_comments"
USER = "profile_url"
URL = "url"
  

def word_clouds(df):
  from wordcloud import WordCloud
  import matplotlib.pyplot as plt

  mask = np.array(
    ImageOps.invert(Image.open("/Users/destroyerofworlds/Desktop/NLP/PROJECT/reddit_logo.png").convert("L"))
  )
  texts = df["comment_body"].dropna().tolist()
  combined_text = " ".join(texts)

  wordcloud = WordCloud(width=1000, height=1000, background_color="#f5e4ff",
                        colormap="Purples", contour_width=2, contour_color="#1f0032", mask=mask).generate(combined_text)

  plt.figure(figsize=(10, 5))
  plt.imshow(wordcloud, interpolation='bilinear')
  plt.axis('off')
  plt.show()


def regression_features():
  nltk.download('vader_lexicon')
  sia = SentimentIntensityAnalyzer()

  posts = pd.read_excel(HOME + "regression.xlsx")
  comments = pd.read_excel(HOME + "new_truths.xlsx")
  comments['author'] = comments['url'].str.split('/').str[3]

  reply_lookup = defaultdict(list)
  for _, row in comments.iterrows():
    reply_lookup[row["in_reply_to_id"]].append(row["id"])

  for idx, post in posts.iterrows():
    post_id = post["external_id"]
    
    def dfs(node_id, depth=0):
      children = reply_lookup.get(node_id, [])
      if not children:
        return [depth]  # leaf node, return depth of this path
      depths = []
      for child in children:
        depths.extend(dfs(child, depth + 1))
      return depths

    all_depths = dfs(post_id)
    if all_depths:
      max_depth = max(all_depths)
      avg_depth = sum(all_depths) / len(all_depths)
    else:
      max_depth = 0
      avg_depth = 0

    posts.at[idx, "max_depth"] = max_depth
    posts.at[idx, "avg_depth"] = avg_depth

    post_comments = comments[comments["in_reply_to_id"] == post_id]
    posts.at[idx, "unique_users"] = post_comments["author"].nunique()
    
    sentiments = post_comments['content'].apply(lambda x: sia.polarity_scores(str(x))['compound'])
    posts.at[idx, "avg_comment_sentiment"] = sentiments.mean()

  posts.to_excel(HOME + "regression_features.xlsx", sheet_name="analysis", index=False)


def build_conversation_threads(df):
  df = df[df["stance_label"].isin(["FOR", "AGAINST"])].copy()

  # Build a lookup dict: id -> row
  lookup = df.set_index("id").to_dict("index")
  rows = []

  # Step 1: loop through all last comments (nth_comment == "n")
  last_comments = df[df["nth_comment"] == "n"]
  for _, last_row in last_comments.iterrows():
    last_id = last_row["id"]
    last_stance = last_row["stance_label"]

    # Step 2: get second-to-last by following one hop
    second_id = last_row["in_reply_to_id"]
    if second_id not in lookup: 
      continue
    stance_second = lookup[second_id]["stance_label"]

    # Step 3: walk up until you find the first_comment (nth_comment == 1)
    first_id = second_id
    parent = lookup[second_id]["in_reply_to_id"]

    while parent in lookup:
        if lookup[parent]["nth_comment"] == "1":
          first_id = parent
          break
        first_id = parent
        parent = lookup[parent]["in_reply_to_id"]

    stance_first = lookup[first_id]["stance_label"]

    # Step 4: conversation ID = the last node (unique per thread)
    conv_id = f"conv_{last_id}"
    rows.append({
      "conversation_id": conv_id,
      "first": stance_first,
      "second_last": stance_second,
      "last": last_stance
    })

  return pd.DataFrame(rows)


def sankey():
  comments = pd.read_excel(HOME + "new_truths.xlsx")
  df = build_conversation_threads(comments)
  df = df.dropna(subset=["first", "second_last", "last"])

  # Define node labels for each step
  df["first_node"] = df["first"] + "_first"
  df["second_node"] = df["second_last"] + "_second"
  df["last_node"] = df["last"] + "_last"

  # Count transitions: first -> second
  trans1 = df.groupby(["first_node", "second_node"]).size().reset_index(name="count")
  trans2 = df.groupby(["second_node", "last_node"]).size().reset_index(name="count")

  # Build unique labels
  labels = list(pd.unique(pd.concat([trans1["first_node"], trans1["second_node"], trans2["last_node"]], ignore_index=True)))
  label_to_index = {label: i for i, label in enumerate(labels)}

  # Rebuild source, target indices based on new mapping
  source, target, value = [], [], []
  for _, row in trans1.iterrows():
      source.append(label_to_index[row["first_node"]])
      target.append(label_to_index[row["second_node"]])
      value.append(row["count"])
  for _, row in trans2.iterrows():
      source.append(label_to_index[row["second_node"]])
      target.append(label_to_index[row["last_node"]])
      value.append(row["count"])

  # Example: color FOR as green, AGAINST as red
  colors_map = {
      "AGAINST_first": "#B67676",   # dark red
      "AGAINST_second": "#D29999",  # orange red
      "AGAINST_last": "#FBCED5",     # pink
      "FOR_first": "#72A181",       # dark green
      "FOR_second": "#8FBE9E",      # lime green
      "FOR_last": "#B0D4BB"       # pale green
  }

  # Node colors (rebuild for new label ordering)
  node_colors = [colors_map[label] for label in labels]
  link_colors = [colors_map[labels[s]] for s in source]

  # Create the Sankey diagram
  fig = go.Figure(go.Sankey(
      node=dict(
          pad=40,
          thickness=25,
          line=dict(color="black", width=0.3),
          label=labels,
          color=node_colors
      ),
      link=dict(
          source=source,
          target=target,
          value=value,
          color=link_colors,
          hovertemplate='%{source.label} → %{target.label}<br>Count: %{value}<extra></extra>'
      )
  ))

  fig.update_layout(
    title_text="3-Step Stance Trajectory Sankey Diagram",
    font_size=12,
    height=700,
    width=1200
  )

  # Save and open
  fig.write_html("stance_sankey_3step.html")
  import webbrowser
  webbrowser.open("stance_sankey_3step.html")

  print("Sankey diagram created and saved as stance_sankey_3step.html")


import pandas as pd
import matplotlib.pyplot as plt

import pandas as pd
import matplotlib.pyplot as plt

def bar_graph():
    import pandas as pd
    import matplotlib.pyplot as plt

    # Load comments
    comments = pd.read_excel(HOME + "new_truths.xlsx")
    comments = comments.dropna(subset=["nth_comment", "p_label"])
    
    # Load posts and filter
    posts = pd.read_excel(HOME + "ANALYSIS.xlsx")
    posts = posts[
        (posts['comments_scraped'] == 1) &
        (posts['num_comments'] > 4) &
        (posts['PM_label'].notna()) &
        (posts['PM_label'] != "")
    ]
    
    # Map comment levels
    level_map = {1: "first_reply", "n-1": "second_last_reply", "n": "last_reply"}
    comments["level"] = comments["nth_comment"].map(level_map)
    
    # Expand comments into individual persuasion modes
    rows = []
    for _, row in comments.iterrows():
        level = row["level"]
        for char in str(row["p_label"]):
            rows.append({"level": level, "mode": char})
    expanded_df = pd.DataFrame(rows)
    
    # Expand posts as "original_post" level
    post_rows = []
    for _, row in posts.iterrows():
        pm_label = str(row["PM_label"])
        for char in pm_label:
            post_rows.append({"level": "original_post", "mode": char})
    posts_expanded_df = pd.DataFrame(post_rows)
    
    # Concatenate
    expanded_df = pd.concat([expanded_df, posts_expanded_df], ignore_index=True)
    
    # Count and convert to percentages
    count_df = expanded_df.groupby(["level", "mode"]).size().unstack(fill_value=0)
    
    # Reorder columns for stacking: ethos (bottom), pathos (middle), logos (top)
    percent_df = count_df.div(count_df.sum(axis=1), axis=0) * 100
    percent_df = percent_df[["e", "p", "l"]]  # order columns
    percent_df = percent_df.reindex(["original_post", "first_reply", "second_last_reply", "last_reply"])
    
    # Colors and full names for legend
    colors = {"e": "#8E44AD", "p": "#3498DB", "l": "#E74C3C"}  # purple, blue, red
    full_names = {"e": "Ethos", "p": "Pathos", "l": "Logos"}
    
    # Plot
    ax = percent_df.plot(
        kind="bar",
        stacked=True,
        figsize=(8,6),
        color=[colors[c] for c in percent_df.columns]
    )
    ax.set_xlabel("Comment Level")
    ax.set_ylabel("Percentage of Persuasion Modes")
    ax.set_title("Evolution of Persuasion Modes Across Comment Levels")
    
    # Update legend with full names
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles, [full_names[label] for label in labels], title="Persuasion Mode")
    
    plt.xticks(rotation=0)
    plt.tight_layout()
    plt.show()


def main():
  # df = pd.read_excel(input_file)
  # print(len(df), "rows loaded.")
  # df = pd.read_csv("/Users/destroyerofworlds/Desktop/NLP/PROJECT/reddit_arguments.csv")
  # df = df.drop_duplicates(subset = ["comment_body", "root_comment_id"])
  # df = df[df["argument_annotation"] == "ARGUMENT"]
  # word_clouds(df)
  # regression_features()
  # sankey()
  bar_graph()

main()
