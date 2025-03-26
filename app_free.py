# app_free.py – Streamlit UI using the FREE backend version

import streamlit as st
import random
import json
import os

from vyoms_word_treasure_free import word_graph_free  # FREE version of LangGraph pipeline

# --- Streamlit Page Config ---
st.set_page_config(
    page_title="Vyom's Word Treasure",
    layout="centered",
    page_icon="📋"
)

# --- CSS Styling ---
st.markdown("""
<style>
    .title {
        font-size: 36px;
        color: #DAA520;
        text-align: center;
        font-family: 'Arial', cursive;
    }
    .bubble {
        padding: 1rem;
        border-radius: 15px;
        margin-bottom: 1rem;
    }
    .def { background-color: #FFF8DC; }
    .type { background-color: #E0FFFF; }
    .variant { background-color: #FFEFD5; }
    .syn { background-color: #F0FFF0; }
    .ant { background-color: #FDEDEC; }
    .ex { background-color: #F5F5DC; }
</style>
""", unsafe_allow_html=True)

st.markdown("<div class='title'>🌟 Vyom's Word Treasure </div>", unsafe_allow_html=True)

# --- State Storage ---
FAVORITES_FILE = "favorites.json"
COINS_FILE = "coins.txt"

if os.path.exists(FAVORITES_FILE):
    with open(FAVORITES_FILE, "r") as f:
        favorites = json.load(f)
else:
    favorites = {}

if os.path.exists(COINS_FILE):
    with open(COINS_FILE, "r") as f:
        coins = int(f.read())
else:
    coins = 0

import requests
from bs4 import BeautifulSoup

@st.cache_data(ttl=3600)
def fetch_word_of_the_day():
    url = "https://www.merriam-webster.com/word-of-the-day"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    # Fallback: Get <title> tag and extract the first word before "|"
    title = soup.find("title")
    if title and "Word of the Day" in title.text:
        word = title.text.split(":")[1].split("|")[0].strip()
        return word

    return "Not found"

# --- TTS using browser (Streamlit-safe) ---
def speak_word(word: str):
    escaped_word = word.replace('"', '\"')
    st.components.v1.html(f"""
        <script>
            document.addEventListener("DOMContentLoaded", function() {{
                const btn = document.getElementById("speak-btn");
                if (btn) {{
                    btn.onclick = function() {{
                        const msg = new SpeechSynthesisUtterance("{escaped_word}");
                        msg.lang = "en-US";
                        window.speechSynthesis.speak(msg);
                    }};
                }}
            }});
        </script>
        <button id='speak-btn'>🔊 Click to hear the Word</button>
    """, height=60)

# --- Word of the Day ---
word_of_the_day = fetch_word_of_the_day()

with st.expander("🌍 Word of the Day"):
    st.markdown(f"<b>{word_of_the_day}</b>", unsafe_allow_html=True)
    if st.button("Use Word of the Day", key="wotd_button"):
        st.session_state["word"] = word_of_the_day

# --- Input ---
word = st.text_input("What word shall we explore today?", value=st.session_state.get("word", ""), key="word")

col1, col2 = st.columns([1, 1])
with col1:
    run_button = st.button("📋 Unlock Treasure!")
with col2:
    save_button = st.button("📁 Save to Flashcards")

# --- Run the flow ---
if run_button and word:
    with st.spinner("Looking up..."):
        initial_state = {
            "word": word,
            "definitions": [],
            "word_type": "",
            "variants": [],
            "synonyms": [],
            "antonyms": [],
            "examples": []
        }
        result = word_graph_free.invoke(initial_state)
        st.session_state["result"] = result

    coins += 1
    with open(COINS_FILE, "w") as f:
        f.write(str(coins))

    st.markdown(f"<h3 style='color:#DAA520;'>🌊 Treasure for: <i>{word}</i></h3>", unsafe_allow_html=True)

# --- Show result if available ---
if "result" in st.session_state:
    result = st.session_state["result"]

    st.markdown("<div class='bubble def'><b>📖 Definitions:</b><br>" + "<br>".join(result["definitions"]) + "</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='bubble type'><b>🔢 Word Type:</b> {result['word_type']}</div>", unsafe_allow_html=True)

    if result["variants"]:
        st.markdown("<div class='bubble variant'><b>📚 Other Forms:</b><br>" + ", ".join(result["variants"]) + "</div>", unsafe_allow_html=True)

    if result["synonyms"]:
        st.markdown("<div class='bubble syn'><b>🌿 Synonyms:</b><br>" + ", ".join(result["synonyms"]) + "</div>", unsafe_allow_html=True)

    if result["antonyms"]:
        st.markdown("<div class='bubble ant'><b>❌ Antonyms:</b><br>" + ", ".join(result["antonyms"]) + "</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='bubble ant'><b>❌ Antonyms:</b><br><i>No antonyms found.</i></div>", unsafe_allow_html=True)

    if result["examples"]:
        st.markdown("<div class='bubble ex'><b>🎨 Examples:</b><br>" + "<br>".join(result["examples"]) + "</div>", unsafe_allow_html=True)

    if st.button("🎤 Audio", key="hear_word_button"):
        speak_word(word)

# --- Save to Flashcards ---
if save_button and word and "result" in st.session_state:
    favorites[word] = st.session_state["result"]
    with open(FAVORITES_FILE, "w") as f:
        json.dump(favorites, f)
    st.success(f"'{word}' saved to flashcards!")

# --- Flashcard Viewer ---
with st.expander("📁 My Word Treasure Chest"):
    if favorites:
        for w, data in favorites.items():
            st.markdown(f"### 🌟 {w.title()}")
            st.markdown("<div class='bubble def'><b>📖 Definitions:</b><br>" + "<br>".join(data["definitions"]) + "</div>", unsafe_allow_html=True)
    else:
        st.info("You haven't saved any words yet.")

# --- Footer ---
st.markdown("""
<hr style="margin-top:3rem;">
<div style='text-align: center; font-size: 16px;'>
🌟 You've earned <b>{}</b> word coins! Keep collecting!
</div>
<div style='text-align: center; font-size: 14px; margin-top: 10px;'>
Made with ❤️ by Appa for Vyom 🌟
</div>
""".format(coins), unsafe_allow_html=True)