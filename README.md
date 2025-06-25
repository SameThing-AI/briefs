# 📰 Briefs - AI-Powered News Reader

A sophisticated, intelligent news aggregator that fetches, deduplicates, and presents tech news from multiple RSS feeds in a clean, interactive interface.

![Briefs App](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![TinyDB](https://img.shields.io/badge/TinyDB-000000?style=for-the-badge&logo=json&logoColor=white)

## 🚀 Features

### 📰 **Multi-Source News Aggregation**
- **7 Premium Tech Sources**: TechCrunch, VentureBeat, The Verge, Hacker News, Wired, Ars Technica, MIT Technology Review
- **Smart Deduplication**: AI-powered similarity detection to eliminate duplicate articles
- **Real-time Fetching**: Fresh content with progress indicators

### 🎯 **Intelligent Content Processing**
- **Smart Summaries**: Auto-generated article summaries with highlighted key metrics
- **Quantifiable Highlighting**: Automatically bold numbers, percentages, and financial data
- **Timestamp Parsing**: Robust handling of various RSS date formats
- **Domain Extraction**: Clean source attribution

### 💾 **Personalized Experience**
- **Like System**: Save interesting articles for later reading
- **Discard Functionality**: Remove unwanted articles permanently
- **Read Tracking**: Mark articles as read with detailed analysis
- **Persistent Storage**: TinyDB-based local storage for user preferences

### 🔍 **Advanced Search & Organization**
- **Real-time Search**: Filter articles by title, summary, or source
- **Multiple Sort Options**: 
  - 🕒 Most Recent
  - 🔤 Alphabetical
  - 📰 By Source
- **Expandable Articles**: Click to view detailed summaries without scrolling

### 🎨 **Modern UI/UX**
- **Responsive Design**: Clean, modern interface with smooth animations
- **Interactive Elements**: Hover effects and visual feedback
- **Keyboard Shortcuts**: Quick navigation and actions
- **Progress Indicators**: Visual feedback during content fetching

## 📋 Table of Contents

- [Installation](#-installation)
- [Usage](#-usage)
- [Features in Detail](#-features-in-detail)
- [Architecture](#-architecture)
- [Configuration](#-configuration)
- [API Reference](#-api-reference)
- [Contributing](#-contributing)
- [License](#-license)

## 🛠️ Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd briefs
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv env
   source env/bin/activate  # On Windows: env\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   streamlit run app.py
   ```

5. **Open your browser**
   Navigate to `http://localhost:8501`

## 🎮 Usage

### Getting Started

1. **First Launch**: The app automatically fetches the latest articles from all sources
2. **Browse Articles**: Scroll through the main article list in the left column
3. **Expand Details**: Click any article tile to view detailed summary and actions
4. **Like Articles**: Use the ❤️ button to save articles to your liked collection
5. **Search & Filter**: Use the search bar in the sidebar to find specific content

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `r` | Refresh articles |
| `s` | Focus search bar |
| `Esc` | Clear selection |

### Article Actions

- **❤️ Like**: Save article to your collection
- **✅ Mark as Read**: Add detailed analysis and mark as read
- **🗑️ Discard**: Remove article from view permanently
- **🔄 Refresh**: Fetch latest articles
- **📄 Collapse**: Hide expanded article details

## 🔧 Features in Detail

### RSS Feed Integration

The app integrates with 7 premium tech news sources:

| Source | URL | Color |
|--------|-----|-------|
| TechCrunch | `techcrunch.com/feed/` | #ff6b6b |
| VentureBeat | `venturebeat.com/feed/` | #4ecdc4 |
| The Verge | `theverge.com/rss/index.xml` | #45b7d1 |
| Hacker News | `hnrss.org/frontpage` | #ffa726 |
| Wired | `wired.com/feed/rss` | #ab47bc |
| Ars Technica | `feeds.arstechnica.com/arstechnica/index` | #26a69a |
| MIT Technology Review | `technologyreview.com/feed/` | #42a5f5 |

### Content Processing Pipeline

1. **Fetch**: Retrieve articles from RSS feeds with progress tracking
2. **Parse**: Extract title, summary, link, and timestamp
3. **Clean**: Remove HTML tags and normalize text
4. **Deduplicate**: Group similar articles using sequence matching
5. **Enhance**: Highlight quantifiable data and format timestamps
6. **Store**: Save to local database with user interactions

### Data Persistence

- **TinyDB**: Lightweight JSON-based database
- **Session State**: Streamlit session management for UI state
- **User Preferences**: Liked articles, discarded items, read status

## 🏗️ Architecture

### Code Structure

```
briefs/
├── app.py                 # Main application file
├── requirements.txt       # Python dependencies
├── liked_articles.json    # Database file (auto-generated)
├── README.md             # This file
└── LICENSE               # License information
```

### Module Organization

```python
# Session State Initialization
initialize_session_state()

# Database Operations
initialize_database()
is_liked(), like_article(), discard_article()

# Content Processing
fetch_articles_with_progress()
deduplicate_articles()
summarize_entry()

# UI Components
render_sidebar()
render_article_list()
render_expanded_article()
```

### Key Components

- **Session Management**: Streamlit session state for UI persistence
- **Database Layer**: TinyDB for user data storage
- **RSS Parser**: Feedparser for RSS feed processing
- **Content Processing**: BeautifulSoup for HTML cleaning
- **UI Framework**: Streamlit for web interface

## ⚙️ Configuration

### RSS Feeds

Add or modify RSS feeds in the `RSS_FEEDS` configuration:

```python
RSS_FEEDS = [
    {
        "name": "Your Source",
        "url": "https://yoursource.com/feed/",
        "color": "#yourcolor"
    }
]
```

### Sort Options

Customize sorting options in `SORT_OPTIONS`:

```python
SORT_OPTIONS = {
    "recent": "🕒 Most Recent",
    "alphabetical": "🔤 Alphabetical",
    "source": "📰 By Source"
}
```

### Styling

Modify CSS styles in the `load_custom_styles()` function for custom theming.

## 📚 API Reference

### Core Functions

#### `initialize_session_state()`
Initialize all Streamlit session state variables.

#### `fetch_articles_with_progress() -> List[Dict]`
Fetch articles from RSS feeds with progress indicator.

#### `deduplicate_articles(articles: List[Dict]) -> List[List[Dict]]`
Group similar articles together using similarity matching.

#### `like_article(article: Dict)`
Save article to user's liked collection.

#### `discard_article(article_id: str)`
Mark article as discarded and hide from view.

### Database Operations

#### `is_liked(article_id: str) -> bool`
Check if article is in user's liked collection.

#### `is_discarded(article_id: str) -> bool`
Check if article has been discarded.

#### `get_article_stats() -> tuple`
Get statistics about liked articles and sources.

### UI Components

#### `render_sidebar()`
Render the sidebar with controls, search, and statistics.

#### `render_article_list()`
Render the main article list with sorting and filtering.

#### `render_expanded_article(article: Dict, is_liked_article: bool = False)`
Render detailed article view with actions.

## 🤝 Contributing

We welcome contributions! Here's how you can help:

### Development Setup

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes
4. Add tests if applicable
5. Commit your changes: `git commit -m 'Add amazing feature'`
6. Push to the branch: `git push origin feature/amazing-feature`
7. Open a Pull Request

### Code Style

- Follow PEP 8 guidelines
- Add docstrings to all functions
- Use type hints where appropriate
- Keep functions focused and single-purpose

### Feature Ideas

- [ ] Add more RSS sources
- [ ] Implement article sharing
- [ ] Add export functionality
- [ ] Create mobile-responsive design
- [ ] Add article recommendations
- [ ] Implement user accounts

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Streamlit** for the amazing web framework
- **Feedparser** for robust RSS parsing
- **BeautifulSoup** for HTML processing
- **TinyDB** for lightweight data storage
- **All RSS feed providers** for their excellent content

## 📞 Support

If you encounter any issues or have questions:

1. Check the [Issues](../../issues) page
2. Create a new issue with detailed information
3. Include your Python version and error messages

---

**Made with ❤️ for the tech community**

*Stay informed, stay ahead with Briefs.*
