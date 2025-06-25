import streamlit as st
from datetime import datetime
import hashlib
import random
from typing import List, Dict
# from sentence_transformers import SentenceTransformer, util
from tinydb import TinyDB, Query
import difflib

# Init
st.set_page_config(layout="wide")
# model = SentenceTransformer("all-MiniLM-L6-v2")
db = TinyDB("liked_articles.json")

# Dummy news data (replace with real API/scraper later)
def fetch_dummy_articles():
    base_articles = [
        {"title": "OpenAI launches new GPT-5 model", "content": "OpenAI has released GPT-5, featuring 3x faster inference and 50% lower costs."},
        {"title": "GPT-5 released by OpenAI", "content": "The new GPT-5 model offers faster inference speed and is cheaper for developers."},
        {"title": "Google launches AI search overhaul", "content": "Google Search now integrates AI summaries at the top of results, transforming the way we search."},
        {"title": "Anthropic secures $1.2B funding", "content": "Anthropic, creator of Claude AI, secures a $1.2 billion investment from Amazon to accelerate AI safety."},
    ]
    # Add timestamps
    for a in base_articles:
        a["timestamp"] = datetime.utcnow().isoformat()
    return base_articles

# Hash function to identify duplicates
def generate_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

# Deduplication logic
def deduplicate_articles(articles: List[Dict]):
    seen = []
    clusters = []

    for art in articles:
        text = art["title"] + art["content"]
        is_duplicate = False

        for cluster in clusters:
            existing_text = cluster[0]["title"] + cluster[0]["content"]
            similarity = difflib.SequenceMatcher(None, text, existing_text).ratio()
            if similarity > 0.85:
                cluster.append(art)
                is_duplicate = True
                break

        if not is_duplicate:
            clusters.append([art])

    return clusters


# Format summary for display
def summarize_article(article):
    # Here we'll just do a basic 2-liner mock
    title = f"🔹 {article['title']}"
    summary = f"{article['content']}"
    return title, summary

# Check local database
def is_liked(article_id):
    return db.search(Query().id == article_id)

# Mark article as liked
def like_article(article):
    article_id = article["id"]
    if not is_liked(article_id):
        db.insert({
            "id": article_id,
            "title": article["title"],
            "content": article["content"],
            "timestamp": article["timestamp"],
            "sources": article["sources"],
            "verbose": article.get("verbose", None)
        })

# Mark article as read (store verbose summary)
def mark_as_read(article_id, verbose_text):
    Article = Query()
    db.update({"verbose": verbose_text}, Article.id == article_id)

# Session state
if "fetched" not in st.session_state:
    st.session_state["fetched"] = False
if "articles" not in st.session_state:
    st.session_state["articles"] = []
if "selected_article" not in st.session_state:
    st.session_state["selected_article"] = None

# Handle refresh
def refresh():
    articles = fetch_dummy_articles()
    clusters = deduplicate_articles(articles)
    summarized = []
    for cluster in clusters:
        main = cluster[0]
        links = [a["title"] for a in cluster]
        id = generate_hash(main["title"])
        summarized.append({
            "id": id,
            "title": main["title"],
            "content": main["content"],
            "timestamp": main["timestamp"],
            "sources": links,
            "verbose": None,
        })
    st.session_state["articles"] = summarized
    st.session_state["fetched"] = True
    st.session_state["selected_article"] = None

# UI Layout
col1, col2 = st.columns([1, 3])

with col1:
    st.markdown("## 🔄 Refresh")
    if st.button("Refresh News"):
        refresh()
    if not st.session_state["fetched"]:
        refresh()

    st.markdown("### 📅 Today")
    for art in st.session_state["articles"]:
        if not is_liked(art["id"]):
            if st.button(f"{art['title']}", key=art["id"]):
                st.session_state["selected_article"] = art

    st.markdown("### 📂 Past (Liked)")
    for liked in db.all():
        if st.button(f"{liked['title']}", key=liked["id"]):
            st.session_state["selected_article"] = liked

with col2:
    article = st.session_state.get("selected_article", None)
    if article:
        st.markdown(f"## {article['title']}")
        st.markdown(f"**📝 Summary:** {article['content']}")
        st.markdown("**🔗 Sources:**")
        for s in article["sources"]:
            st.markdown(f"- {s}")
        st.markdown("---")

        if not is_liked(article["id"]):
            if st.button("❤️ Like"):
                like_article(article)
                st.rerun()

        if not article.get("verbose"):
            if st.button("✅ Mark as Read"):
                verbose_text = f"This is a longer summary for: {article['title']}.\n\n{article['content']} (more details would go here)"
                mark_as_read(article["id"], verbose_text)
                article["verbose"] = verbose_text
                st.rerun()
        else:
            st.markdown("**📚 Verbose Summary (Saved):**")
            st.markdown(article["verbose"])

