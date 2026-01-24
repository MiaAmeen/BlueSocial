# BlueSocial

Code for the BlueSocial paper (dataset scraping + LLM annotation).  
**Status:** Work-in-progress (full release coming soon).

## Overview
This repository contains:
- Scripts for scraping Truth Social posts/comments using multiple scraper “bots” concurrently
- LLM annotation code for labeling stance and argument presence

## Project Structure
- `data/`  
  Input files are read from here and output files are written here.
- `api.py`  
  Core logic for interacting with Truth Social API endpoints. (Adapted from Truthbrush / Stanford’s framework.)
- `compile_threads.py`  
  Coordinates multi-bot scraping, logging, and writing scraped rows to disk.
- `LLM.py`  
  LLM annotation pipeline for argument mining + stance detection, including prompts and model configs.

## Requirements
- Python **3.10+** recommended (tested with Python 3.13)

## Installation (MacOS / Linux)
1) Clone the repo:
```bash
git clone https://github.com/MiaAmeen/BlueSocial.git
cd BlueSocial
```
2) Create and activate a virtual environment:
```bash
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
```
3) Copy the contents of the .env_copy file into a .env file.
You can include multiple truthsocial username/password combinations (in order), as long as they're comma separated.
```bash
TRUTHSOCIAL_USERNAMES=
TRUTHSOCIAL_PASSWORDS=
```
Add at least one API key depending on the LLM you use:
```bash
GEMINI_API_KEY=
DEEPSEEK_API_KEY=
OPENAI_API_KEY=
```

## Usage (WIP)
python3 compile_threads.py
python3 LLM.py


This project is intended for research use.
Scraping may be rate-limited. Use responsibly and follow platform policies.


## Contact
Questions or feedback are welcome!  
📩 [fameen@ncsu.edu](mailto:fameen@ncsu.edu)