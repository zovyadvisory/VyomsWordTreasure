# vyoms_word_treasure_free.py – LangGraph with only FREE APIs (Wordnik version)

import requests
import random
from typing import TypedDict, List
from langgraph.graph import StateGraph, END
import os
from bs4 import BeautifulSoup
from collections import Counter


# 1. Define the state
class WordState(TypedDict):
    word: str
    definitions: List[str]
    word_type: str
    variants: List[str]
    synonyms: List[str]
    antonyms: List[str]
    examples: List[str]

# 2. Dictionary node using dictionaryapi.dev
from collections import Counter

def dictionary_node(state: WordState) -> dict:
    word = state["word"]
    url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
    response = requests.get(url)

    if response.status_code != 200:
        return {"definitions": ["Definition not found."], "word_type": "Unknown"}

    data = response.json()
    meanings = data[0].get("meanings", [])

    definitions = []
    pos_list = []

    for meaning in meanings:
        pos = meaning.get("partOfSpeech", "unknown")
        pos_list.append(pos)

        defs = meaning.get("definitions", [])
        for d in defs:
            if "definition" in d:
                definitions.append(d["definition"])

    # Find most frequent part of speech
    most_common_pos = Counter(pos_list).most_common(1)[0][0] if pos_list else "Unknown"

    return {
        "definitions": definitions[:3],
        "word_type": ", ".join(sorted(set(pos_list)))
    }

# 3. Variants using Datamuse rel_trg
def generate_variants_node(state: WordState) -> dict:
    word = state["word"]
    resp = requests.get(f"https://api.datamuse.com/words?rel_trg={word}").json()
    variants = [r["word"] for r in resp][:5]
    return {"variants": variants}

# 4. Thesaurus using Datamuse API
def thesaurus_node(state: WordState) -> dict:
    word = state["word"]
    syns = requests.get("https://api.datamuse.com/words?rel_syn=" + word).json()
    ants = requests.get("https://api.datamuse.com/words?rel_ant=" + word).json()
    synonyms = [s["word"] for s in syns][:5]
    antonyms = [a["word"] for a in ants][:5]
    return {"synonyms": synonyms, "antonyms": antonyms}

# 5. Examples using dictionary scraping
from bs4 import BeautifulSoup

def generate_examples_node(state: WordState) -> dict:
    word = state["word"]
    url = f"https://sentence.yourdictionary.com/{word}"

    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")

        # Find all sentence <p> tags in the result list
        examples = []
        for item in soup.find_all("div", class_="sentence-item"):
            sentence = item.find("p")
            if sentence and word.lower() in sentence.text.lower():
                examples.append(sentence.text.strip())

        if examples:
            return {"examples": examples[:3]}
        else:
            return {"examples": [f"No examples found for '{word}'."]}

    except Exception as e:
        return {"examples": [f"Error fetching examples: {str(e)}"]}

# 6. Build LangGraph
builder = StateGraph(WordState)

builder.add_node("dictionary_lookup", dictionary_node)
builder.add_node("generate_variants", generate_variants_node)
builder.add_node("thesaurus_lookup", thesaurus_node)
builder.add_node("generate_examples", generate_examples_node)

builder.set_entry_point("dictionary_lookup")
builder.add_edge("dictionary_lookup", "generate_variants")
builder.add_edge("generate_variants", "thesaurus_lookup")
builder.add_edge("thesaurus_lookup", "generate_examples")
builder.add_edge("generate_examples", END)

word_graph_free = builder.compile()

if __name__ == "__main__":
    result = word_graph_free.invoke({
        "word": "bright",
        "definitions": [],
        "word_type": "",
        "variants": [],
        "synonyms": [],
        "antonyms": [],
        "examples": []
    })
    print(result)
