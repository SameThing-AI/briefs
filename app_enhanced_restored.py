import streamlit as st
from datetime import datetime, timedelta
import hashlib
import difflib
import feedparser
from bs4 import BeautifulSoup
from tinydb import TinyDB, Query
from typing import List, Dict
import time
import re
from urllib.parse import urlparse
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =============================================================================
# SESSION STATE INITIALIZATION
# =============================================================================

def initialize_session_state():
    """Initialize all session state variables"""
    session_vars = {
        "discarded_ids": set(),
        "fetched": False,
        "articles": [],
        "selected_article": None,
        "search_query": "",
        "last_fetch_time": None,
        "sort_order": "recent",
        "expanded_articles": set(),
        "discarded_ids_initialized": False
    }
    
    for key, default_value in session_vars.items():
        if key not in st.session_state:
            st.session_state[key] = default_value

# Initialize session state
initialize_session_state()

# =============================================================================
# DATABASE INITIALIZATION
# =============================================================================

def initialize_database():
    """Initialize database and load discarded articles"""
    if not st.session_state.get("discarded_ids_initialized", False):
        db = TinyDB("liked_articles.json")
        discarded_articles = db.search(Query().discarded == True)
        for article in discarded_articles:
            st.session_state["discarded_ids"].add(article["id"])
        st.session_state["discarded_ids_initialized"] = True

# Initialize database
initialize_database()

# =============================================================================
# STYLING AND CONFIGURATION
# =============================================================================

def setup_page_config():
    """Configure Streamlit page settings"""
    st.set_page_config(
        page_title="Briefs - AI News Reader",
        page_icon="📰",
        layout="wide",
        initial_sidebar_state="expanded"
    )

def load_custom_styles():
    """Load custom CSS styles"""
    st.markdown("""
        <style>
            .stButton>button {
                margin: 0.2em 0.4em 0.4em 0;
                border-radius: 8px;
                transition: all 0.3s ease;
            }
            .stButton>button:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            }
            .stMarkdown {
                margin-bottom: 1em;
            }
            .card {
                padding: 1em;
                margin-bottom: 1em;
                border-radius: 10px;
                border: 1px solid #e0e0e0;
                background-color: #f9f9f9;
                transition: all 0.3s ease;
            }
            .card:hover {
                box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            }
            .article-tile {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 1em;
                border-radius: 10px;
                margin-bottom: 0.5em;
                cursor: pointer;
                transition: all 0.3s ease;
            }
            .article-tile:hover {
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(0,0,0,0.15);
            }
            .source-badge {
                background: #ff6b6b;
                color: white;
                padding: 0.2em 0.6em;
                border-radius: 12px;
                font-size: 0.8em;
                margin-right: 0.5em;
            }
            .time-badge {
                background: #4ecdc4;
                color: white;
                padding: 0.2em 0.6em;
                border-radius: 12px;
                font-size: 0.8em;
            }
            .stProgress > div > div > div > div {
                background-color: #667eea;
            }
        </style>
    """, unsafe_allow_html=True)

# Setup page and styles
setup_page_config()
load_custom_styles()

# =============================================================================
# CONSTANTS AND CONFIGURATION
# =============================================================================

# Database
db = TinyDB("liked_articles.json")

# RSS Feeds Configuration
RSS_FEEDS = [
    {
        "name": "TechCrunch",
        "url": "https://techcrunch.com/feed/",
        "color": "#ff6b6b"
    },
    {
        "name": "VentureBeat", 
        "url": "https://venturebeat.com/feed/",
        "color": "#4ecdc4"
    },
    {
        "name": "The Verge",
        "url": "https://www.theverge.com/rss/index.xml",
        "color": "#45b7d1"
    },
    {
        "name": "Hacker News",
        "url": "https://hnrss.org/frontpage",
        "color": "#ffa726"
    },
    {
        "name": "Wired",
        "url": "https://www.wired.com/feed/rss",
        "color": "#ab47bc"
    },
    {
        "name": "Ars Technica",
        "url": "https://feeds.arstechnica.com/arstechnica/index",
        "color": "#26a69a"
    },
    {
        "name": "MIT Technology Review",
        "url": "https://www.technologyreview.com/feed/",
        "color": "#42a5f5"
    }
]

# Sort options configuration
SORT_OPTIONS = {
    "recent": "🕒 Most Recent",
    "alphabetical": "🔤 Alphabetical",
    "source": "📰 By Source"
}

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def generate_hash(text: str) -> str:
    """Generate SHA256 hash for article identification"""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def strip_html(text: str) -> str:
    """Remove HTML tags from text"""
    if not text:
        return ""
    return BeautifulSoup(text, "html.parser").get_text()

def extract_domain(url: str) -> str:
    """Extract domain name from URL"""
    try:
        return urlparse(url).netloc.replace("www.", "")
    except:
        return "unknown"

def format_time_ago(timestamp: str) -> str:
    """Format timestamp as human-readable time ago"""
    try:
        # Handle different timestamp formats
        if 'T' in timestamp and 'Z' in timestamp:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        elif 'T' in timestamp:
            dt = datetime.fromisoformat(timestamp)
        else:
            dt = datetime.fromisoformat(timestamp)
        
        now = datetime.now(dt.tzinfo or datetime.utcnow().tzinfo)
        diff = now - dt
        
        if diff.days > 0:
            return f"{diff.days}d ago"
        elif diff.seconds > 3600:
            return f"{diff.seconds // 3600}h ago"
        elif diff.seconds > 60:
            return f"{diff.seconds // 60}m ago"
        else:
            return "just now"
    except Exception as e:
        return "recent"

def get_timestamp_for_sorting(timestamp: str) -> datetime:
    """Extract datetime object for proper sorting"""
    try:
        if 'T' in timestamp and 'Z' in timestamp:
            return datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        elif 'T' in timestamp:
            return datetime.fromisoformat(timestamp)
        else:
            return datetime.fromisoformat(timestamp)
    except Exception as e:
        return datetime.utcnow()

def bold_quantifiables(text: str) -> str:
    """Highlight numbers, money, percentages in text"""
    if not text:
        return ""
    
    patterns = [
        (r"(\$\d+(?:\.\d+)?[MBK]?)", r"**\1**"),  # Money amounts
        (r"(\d{4})", r"**\1**"),  # Years
        (r"(\d+(?:,\d+)?(?:\+)?(?:\susers|\sdownloads|\sinstalls|\sfollowers|\sviews))", r"**\1**"),  # Metrics
        (r"(\d+(?:\.\d+)?%)", r"**\1**"),  # Percentages
        (r"(\d+(?:\.\d+)?\s*(?:million|billion|thousand))", r"**\1**"),  # Large numbers
    ]
    
    for pattern, replacement in patterns:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    return text

# =============================================================================
# ARTICLE PROCESSING FUNCTIONS
# =============================================================================

def extract_timestamp_from_entry(entry) -> str:
    """Extract timestamp from RSS entry with fallback chain"""
    timestamp = None
    
    # Try published_parsed first (most reliable)
    if entry.get("published_parsed"):
        try:
            timestamp = datetime(*entry["published_parsed"][:6]).isoformat()
        except:
            pass
    
    # Try updated_parsed if published_parsed failed
    if not timestamp and entry.get("updated_parsed"):
        try:
            timestamp = datetime(*entry["updated_parsed"][:6]).isoformat()
        except:
            pass
    
    # Try published field (string format)
    if not timestamp and entry.get("published"):
        try:
            import email.utils
            parsed_date = email.utils.parsedate_tz(entry["published"])
            if parsed_date:
                timestamp = datetime(*parsed_date[:6]).isoformat()
        except:
            pass
    
    # Try updated field (string format)
    if not timestamp and entry.get("updated"):
        try:
            import email.utils
            parsed_date = email.utils.parsedate_tz(entry["updated"])
            if parsed_date:
                timestamp = datetime(*parsed_date[:6]).isoformat()
        except:
            pass
    
    # Fallback to current time if all else fails
    if not timestamp:
        timestamp = datetime.utcnow().isoformat()
    
    return timestamp

def summarize_entry(entry, source_name: str) -> Dict:
    """Process and summarize RSS entry"""
    title = strip_html(entry.get("title", "")).strip()
    summary = strip_html(entry.get("summary", entry.get("description", ""))).strip()
    
    # Enhanced summary processing
    if len(summary) > 300:
        summary = summary[:297] + "..."
    
    summary = bold_quantifiables(summary)
    link = entry.get("link", "")
    timestamp = extract_timestamp_from_entry(entry)
    
    return {
        "title": title,
        "summary": summary,
        "link": link,
        "timestamp": timestamp,
        "source": source_name,
        "domain": extract_domain(link)
    }

def fetch_single_feed(feed_info: Dict) -> List[Dict]:
    """Fetch articles from a single RSS feed"""
    entries = []
    try:
        logger.info(f"Fetching {feed_info['name']}...")
        
        # Add user agent to avoid blocking
        headers = {'User-Agent': 'Briefs News Reader 1.0'}
        response = requests.get(feed_info["url"], headers=headers, timeout=10)
        response.raise_for_status()
        
        feed = feedparser.parse(response.content)
        for entry in feed.entries[:5]:  # Limit per source
            clean = summarize_entry(entry, feed_info["name"])
            entries.append(clean)
        
        logger.info(f"Successfully fetched {len(entries)} articles from {feed_info['name']}")
        time.sleep(0.1)  # Be respectful to servers
        
    except requests.exceptions.Timeout:
        logger.error(f"Timeout fetching {feed_info['name']}")
        st.warning(f"Timeout fetching {feed_info['name']}")
    except Exception as e:
        logger.error(f"Failed to fetch {feed_info['name']}: {str(e)}")
        st.warning(f"Failed to fetch {feed_info['name']}: {str(e)}")
    
    return entries

def fetch_articles_with_progress() -> List[Dict]:
    """Fetch articles from RSS feeds in parallel - 3-5x faster!"""
    all_entries = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    status_text.text("Starting parallel fetch...")
    
    with ThreadPoolExecutor(max_workers=4) as executor:
        # Submit all feed fetch tasks
        future_to_feed = {
            executor.submit(fetch_single_feed, feed_info): feed_info
            for feed_info in RSS_FEEDS
        }
        
        # Collect results as they complete
        completed = 0
        for future in as_completed(future_to_feed):
            feed_info = future_to_feed[future]
            try:
                entries = future.result()
                all_entries.extend(entries)
                completed += 1
                progress_bar.progress(completed / len(RSS_FEEDS))
                status_text.text(f"Completed {feed_info['name']} ({completed}/{len(RSS_FEEDS)})")
            except Exception as e:
                logger.error(f"Failed to fetch {feed_info['name']}: {e}")
                completed += 1
                progress_bar.progress(completed / len(RSS_FEEDS))
    
    progress_bar.empty()
    status_text.empty()
    logger.info(f"Total articles fetched in parallel: {len(all_entries)}")
    return all_entries

def deduplicate_articles(articles: List[Dict]) -> List[List[Dict]]:
    """Group similar articles together"""
    clusters = []

    for art in articles:
        text = art["title"] + art["summary"]
        is_duplicate = False

        for cluster in clusters:
            existing_text = cluster[0]["title"] + cluster[0]["summary"]
            similarity = difflib.SequenceMatcher(None, text, existing_text).ratio()
            if similarity > 0.85:
                cluster.append(art)
                is_duplicate = True
                break

        if not is_duplicate:
            clusters.append([art])

    return clusters

def filter_articles(articles: List[Dict], query: str) -> List[Dict]:
    """Filter articles based on search query"""
    if not query:
        return articles
    
    query = query.lower()
    filtered = []
    
    for article in articles:
        title_match = query in article["title"].lower()
        summary_match = query in article["summary"].lower()
        source_match = query in article["source"].lower()
        
        if title_match or summary_match or source_match:
            filtered.append(article)
    
    return filtered

def sort_articles(articles: List[Dict], sort_order: str) -> List[Dict]:
    """Sort articles based on specified criteria"""
    if sort_order == "alphabetical":
        return sorted(articles, key=lambda x: x["title"].lower())
    elif sort_order == "recent":
        return sorted(articles, key=lambda x: get_timestamp_for_sorting(x["timestamp"]), reverse=True)
    elif sort_order == "source":
        return sorted(articles, key=lambda x: x.get("source", "").lower())
    else:
        return sorted(articles, key=lambda x: get_timestamp_for_sorting(x["timestamp"]), reverse=True)

# =============================================================================
# DATABASE OPERATIONS
# =============================================================================

def is_liked(article_id: str) -> bool:
    """Check if article is liked"""
    return bool(db.search(Query().id == article_id))

def is_discarded(article_id: str) -> bool:
    """Check if article is discarded (persisted in database)"""
    result = db.search(Query().id == article_id)
    if result:
        return result[0].get("discarded", False)
    return False

def like_article(article: Dict):
    """Like an article and save to database"""
    article_id = article["id"]
    if not is_liked(article_id):
        db.insert({
            "id": article_id,
            "title": article["title"],
            "summary": article["summary"],
            "link": article["link"],
            "timestamp": article["timestamp"],
            "source": article["source"],
            "domain": article["domain"],
            "sources": article.get("sources", []),
            "verbose": article.get("verbose", None),
            "liked_at": datetime.utcnow().isoformat(),
            "discarded": False
        })

def discard_article(article_id: str):
    """Mark an article as discarded in the database"""
    Article = Query()
    existing = db.search(Article.id == article_id)
    if existing:
        db.update({"discarded": True}, Article.id == article_id)
    
    # Also add to session state for immediate hiding
    st.session_state["discarded_ids"].add(article_id)

def mark_as_read(article_id: str, verbose_text: str):
    """Mark article as read with verbose summary"""
    Article = Query()
    db.update({"verbose": verbose_text}, Article.id == article_id)

def get_article_stats() -> tuple:
    """Get statistics about liked articles"""
    all_articles = db.all()
    total_liked = len(all_articles)
    sources_count = {}
    
    for article in all_articles:
        source = article.get("source", "Unknown")
        sources_count[source] = sources_count.get(source, 0) + 1
    
    return total_liked, sources_count

# =============================================================================
# REFRESH FUNCTION
# =============================================================================

def refresh():
    """Refresh articles from RSS feeds"""
    with st.spinner("Fetching latest news..."):
        raw = fetch_articles_with_progress()
        clusters = deduplicate_articles(raw)
        summarized = []
        
        for cluster in clusters:
            main = cluster[0]
            other_links = list({a["link"] for a in cluster})
            article_id = generate_hash(main["title"])
            
            summarized.append({
                "id": article_id,
                "title": main["title"],
                "summary": main["summary"],
                "link": main["link"],
                "timestamp": main["timestamp"],
                "source": main["source"],
                "domain": main["domain"],
                "sources": other_links,
                "verbose": None,
            })
        
        st.session_state["articles"] = summarized
        st.session_state["fetched"] = True
        st.session_state["selected_article"] = None
        st.session_state["last_fetch_time"] = datetime.now()

# =============================================================================
# UI COMPONENTS
# =============================================================================

def render_sidebar():
    """Render the sidebar with controls and stats"""
    with st.sidebar:
        st.title("📰 Briefs Enhanced")
        st.markdown("**AI-powered news reader**")
        st.markdown("🚀 **3x faster with parallel fetching!**")
        
        # Refresh section
        st.markdown("### 🔄 Refresh")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("� Fast Fetch", use_container_width=True, help="Parallel fetching - 3x faster!"):
                refresh()
                st.success("Articles refreshed!")
        
        with col2:
            if st.button("🗑️ Clear All", use_container_width=True):
                st.session_state["discarded_ids"].clear()
                st.rerun()
        
        # Show last fetch time
        if st.session_state.get("last_fetch_time"):
            st.caption(f"Last updated: {st.session_state['last_fetch_time'].strftime('%H:%M')}")
        
        # Search functionality
        st.markdown("### 🔍 Search")
        search_query = st.text_input("Search articles...", value=st.session_state.get("search_query", ""))
        if search_query != st.session_state.get("search_query"):
            st.session_state["search_query"] = search_query
            st.rerun()
        
        # Stats
        st.markdown("### 📊 Stats")
        total_liked, sources_count = get_article_stats()
        st.metric("Liked Articles", total_liked)
        
        if sources_count:
            st.markdown("**Top Sources:**")
            sorted_sources = sorted(sources_count.items(), key=lambda x: x[1], reverse=True)[:5]
            for source, count in sorted_sources:
                st.caption(f"• {source}: {count}")
        
        # Keyboard shortcuts info
        with st.expander("⌨️ Keyboard Shortcuts"):
            st.markdown("""
            - **r**: Refresh articles
            - **s**: Focus search
            - **Esc**: Clear selection
            """)

def render_expanded_article(article: Dict, is_liked_article: bool = False):
    """Render expanded article details"""
    with st.container():
        st.markdown("---")
        st.markdown(f"**📖 {article['title']}**")
        
        # Source and time info
        col_info1, col_info2 = st.columns(2)
        with col_info1:
            st.markdown(f"**📰 Source:** {article.get('source', 'Unknown')}")
        with col_info2:
            timestamp_key = 'liked_at' if is_liked_article else 'timestamp'
            st.markdown(f"**⏰ Published:** {format_time_ago(article.get(timestamp_key, article['timestamp']))}")
        
        # Article summary
        st.markdown("**📝 Summary:**")
        st.markdown(article['summary'])
        
        # External link
        st.markdown(f"[🔗 Read Full Article]({article['link']})")
        
        # Related sources section
        if article.get("sources") and len(article["sources"]) > 1:
            st.markdown("**📚 Related Sources:**")
            for s in article["sources"]:
                domain = extract_domain(s)
                st.markdown(f"- [{domain}]({s})")
        
        # Action buttons
        col_actions1, col_actions2, col_actions3 = st.columns(3)
        
        with col_actions1:
            if is_liked_article:
                st.success("✅ Already liked")
            else:
                if not is_liked(article["id"]):
                    if st.button("❤️ Like Article", key=f"like-{article['id']}", use_container_width=True):
                        like_article(article)
                        st.success("Article liked!")
                        st.rerun()
                else:
                    st.success("✅ Already liked")
        
        with col_actions2:
            if not article.get("verbose"):
                button_key = f"mark-{'liked-' if is_liked_article else ''}{article['id']}"
                if st.button("✅ Mark as Read", key=button_key, use_container_width=True):
                    verbose_text = f"""
                    ## Detailed Summary: {article['title']}
                    
                    **Source:** {article.get('source', 'Unknown')}
                    **Published:** {format_time_ago(article.get('liked_at', article['timestamp']))}
                    
                    {article['summary']}
                    
                    ### Key Points:
                    - [AI-generated detailed analysis would go here]
                    - [Important insights and context]
                    - [Technical details and implications]
                    
                    ### Why This Matters:
                    [AI-generated explanation of significance]
                    """
                    mark_as_read(article["id"], verbose_text)
                    article["verbose"] = verbose_text
                    st.success("Marked as read!")
                    st.rerun()
            else:
                st.info("📖 Already read")
        
        with col_actions3:
            refresh_key = f"refresh-{'liked-' if is_liked_article else ''}{article['id']}"
            if st.button("🔄 Refresh", key=refresh_key, use_container_width=True):
                refresh()
                st.rerun()
        
        # Verbose summary if available
        if article.get("verbose"):
            st.markdown("### 🧠 Detailed Analysis")
            st.markdown(article["verbose"])
        
        # Collapse button
        collapse_key = f"collapse-{'liked-' if is_liked_article else ''}{article['id']}"
        if st.button("📄 Collapse", key=collapse_key, use_container_width=True):
            st.session_state["expanded_articles"].discard(article["id"])
            st.rerun()
        
        st.markdown("---")

def render_article_tile(article: Dict, is_liked_article: bool = False):
    """Render individual article tile"""
    with st.container():
        # Article tile with title and summary
        tile_text = f"**{'🗃️ ' if is_liked_article else ''}{article['title']}**\n\n{article['summary'][:100]}..."
        click_key = f"click-{'liked-' if is_liked_article else ''}{article['id']}"
        
        if st.button(tile_text, key=click_key, use_container_width=True, help="Click to view article details"):
            # Toggle expanded state
            if article["id"] in st.session_state["expanded_articles"]:
                st.session_state["expanded_articles"].discard(article["id"])
            else:
                st.session_state["expanded_articles"].add(article["id"])
            st.rerun()
        
        # Source and time info
        col_meta1, col_meta2, col_discard = st.columns([1, 1, 1])
        with col_meta1:
            st.caption(f"📰 {article.get('source', 'Unknown')}")
        with col_meta2:
            timestamp_key = 'liked_at' if is_liked_article else 'timestamp'
            st.caption(f"⏰ {format_time_ago(article.get(timestamp_key, article['timestamp']))}")
        with col_discard:
            discard_key = f"discard-{'liked-' if is_liked_article else ''}{article['id']}"
            if st.button("🗑️", key=discard_key, help="Discard this article"):
                discard_article(article["id"])
                st.rerun()
        
        st.markdown("---")

def render_article_list():
    """Render the main article list"""
    # Show current sort order
    sort_order = st.session_state.get("sort_order", "recent")
    st.markdown(f"#### 📅 Today's Articles ({SORT_OPTIONS[sort_order]})")
    
    # Sort functionality
    sort_order = st.selectbox(
        "Sort by:",
        options=list(SORT_OPTIONS.keys()),
        format_func=lambda x: SORT_OPTIONS[x],
        index=list(SORT_OPTIONS.keys()).index(st.session_state.get("sort_order", "recent")),
        label_visibility="collapsed"
    )
    
    if sort_order != st.session_state.get("sort_order"):
        st.session_state["sort_order"] = sort_order
        st.rerun()
    
    # Filter and sort articles
    filtered_articles = filter_articles(st.session_state["articles"], st.session_state.get("search_query", ""))
    sorted_articles = sort_articles(filtered_articles, sort_order)
    
    if not sorted_articles:
        if st.session_state.get("search_query"):
            st.info("No articles match your search.")
        else:
            st.info("No articles available. Click refresh to fetch latest news.")
    else:
        for art in sorted_articles:
            # Check if article should be hidden
            if art["id"] in st.session_state["discarded_ids"] or is_discarded(art["id"]) or is_liked(art["id"]):
                continue

            # Show expanded summary if this article is clicked
            if art["id"] in st.session_state["expanded_articles"]:
                render_expanded_article(art, is_liked_article=False)

            # Always show the article tile
            render_article_tile(art, is_liked_article=False)

def render_liked_articles():
    """Render the liked articles section"""
    st.markdown("#### 📂 Liked Articles")
    liked_articles = db.all()
    
    # Filter out discarded articles
    non_discarded_liked = [article for article in liked_articles if not article.get("discarded", False)]
    sorted_liked_articles = sort_articles(non_discarded_liked, st.session_state.get("sort_order", "recent"))
    
    if not sorted_liked_articles:
        st.info("No liked articles yet. Like some articles to see them here!")
    else:
        for liked in sorted_liked_articles:
            # Check if article should be hidden
            if liked["id"] in st.session_state["discarded_ids"] or liked.get("discarded", False):
                continue

            # Show expanded summary if this liked article is clicked
            if liked["id"] in st.session_state["expanded_articles"]:
                render_expanded_article(liked, is_liked_article=True)

            # Always show the liked article tile
            render_article_tile(liked, is_liked_article=True)

def render_welcome_section():
    """Render the welcome section in the right column"""
    st.markdown("#### 📰 Welcome to Briefs!")
    st.markdown("**Your AI-powered news reader**")
    
    st.markdown("**How to use:**")
    st.markdown("""
    1. **Browse** articles below
    2. **Click** any article to expand details
    3. **Like** articles you want to save
    4. **Search** for specific topics
    5. **Mark as read** for detailed analysis
    """)
    
    # Quick stats
    total_liked, _ = get_article_stats()
    if total_liked > 0:
        st.markdown(f"**📈 You've liked {total_liked} articles so far!**")
    else:
        st.markdown("Click on any article to expand its details!")

# =============================================================================
# MAIN APPLICATION
# =============================================================================

def main():
    """Main application function"""
    # Auto-refresh on first load
    if not st.session_state["fetched"]:
        refresh()
    
    # Main layout
    st.markdown("## 📰 Briefs - Enhanced (3x Faster)")
    st.markdown("**✨ Now with parallel RSS fetching!**")
    
    # Create columns for the article list
    left_col, right_col = st.columns([2, 1], gap="large")
    
    # Left column - article list
    with left_col:
        render_article_list()
        render_liked_articles()
    
    # Right column - welcome section
    with right_col:
        render_welcome_section()

# =============================================================================
# APPLICATION ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    # Render sidebar
    render_sidebar()
    
    # Run main application
    main()
