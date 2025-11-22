import numpy as np
import pandas as pd
import os
from PIL import Image, ImageOps


# LOAD THE DATA
HOME = "/Users/destroyerofworlds/Desktop/NLP/PROJECT/BlueSocial/"
input_file = HOME + "ANALYSIS.xlsx"
df = pd.read_excel(input_file)
print(len(df), "rows loaded.")

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

def word_clouds():
  from wordcloud import WordCloud
  import matplotlib.pyplot as plt

  mask = np.array(
    ImageOps.invert(Image.open("/Users/destroyerofworlds/Desktop/NLP/PROJECT/truth_logo.png").convert("L"))
  )
  texts = df[TEXT].dropna().tolist()
  combined_text = " ".join(texts)

  wordcloud = WordCloud(width=1000, height=1000, background_color="#fef3f3",
                        colormap="Reds", contour_width=2, contour_color="#300000", mask=mask).generate(combined_text)

  plt.figure(figsize=(10, 5))
  plt.imshow(wordcloud, interpolation='bilinear')
  plt.axis('off')
  plt.show()

def main():
  word_clouds()


main()
