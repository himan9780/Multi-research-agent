"""
Multi-Research-Agent  ·  Streamlit UI
Run with:  streamlit run app.py
"""

import re
import time
from datetime import datetime

import streamlit as st

from agents import build_reader_agent, build_search_agent, writer_chain, critic_chain


# ──────────────────────────────────────────────────────────────
# Page config
# ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Multi-Research-Agent",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ──────────────────────────────────────────────────────────────
# Styling & animations
# ──────────────────────────────────────────────────────────────
CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700&display=swap');

html, body, [class*="css"] { font-family: 'Space Grotesk', sans-serif; }

/* ---------- Hero ---------- */
.hero { text-align: center; padding: 1.5rem 0 0.5rem 0; }

.hero-emoji {
    font-size: 3.4rem;
    display: inline-block;
    animation: float 3.2s ease-in-out infinite;
}

.hero-title {
    font-size: 3.1rem;
    font-weight: 700;
    letter-spacing: -0.02em;
    margin: 0.2rem 0 0.4rem 0;
    background: linear-gradient(270deg, #38bdf8, #818cf8, #f472b6, #fbbf24, #34d399);
    background-size: 600% 600%;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: aurora 10s ease infinite;
}

.hero-sub {
    font-size: 1.1rem;
    opacity: 0.75;
    max-width: 640px;
    margin: 0 auto 1.2rem auto;
}

@keyframes float {
    0%, 100% { transform: translateY(0); }
    50%      { transform: translateY(-10px); }
}

@keyframes aurora {
    0%   { background-position: 0% 50%; }
    50%  { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

/* ---------- Pipeline stepper (the signature element) ---------- */
.stepper {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 14px;
    margin: 1.2rem 0 1.6rem 0;
}

.step {
    position: relative;
    padding: 16px 14px;
    border-radius: 14px;
    border: 1.5px solid rgba(148, 163, 184, 0.25);
    background: rgba(148, 163, 184, 0.06);
    transition: all 0.4s ease;
    text-align: center;
}

.step .icon  { font-size: 1.9rem; display: block; margin-bottom: 4px; }
.step .name  { font-weight: 700; font-size: 0.98rem; }
.step .desc  { font-size: 0.8rem; opacity: 0.7; margin-top: 2px; }
.step .badge { font-size: 0.75rem; margin-top: 8px; display: block; opacity: 0.8; }

.step.pending { opacity: 0.55; }

.step.active {
    border-color: #818cf8;
    background: rgba(129, 140, 248, 0.14);
    animation: pulse 1.6s ease-in-out infinite;
}

.step.active .icon { animation: wiggle 1.2s ease-in-out infinite; }

.step.done {
    border-color: #34d399;
    background: rgba(52, 211, 153, 0.12);
}

@keyframes pulse {
    0%, 100% { box-shadow: 0 0 0 0 rgba(129, 140, 248, 0.45); }
    50%      { box-shadow: 0 0 0 10px rgba(129, 140, 248, 0); }
}

@keyframes wiggle {
    0%, 100% { transform: rotate(0deg); }
    25%      { transform: rotate(-8deg); }
    75%      { transform: rotate(8deg); }
}

/* ---------- Result cards ---------- */
.feedback-card {
    padding: 18px 22px;
    border-radius: 14px;
    border-left: 5px solid #f472b6;
    background: rgba(244, 114, 182, 0.08);
}

.pill {
    display: inline-block;
    padding: 4px 12px;
    margin: 3px 4px 3px 0;
    border-radius: 999px;
    font-size: 0.82rem;
    background: rgba(129, 140, 248, 0.16);
    border: 1px solid rgba(129, 140, 248, 0.35);
}

/* ---------- Buttons ---------- */
div.stButton > button[kind="primary"] {
    background: linear-gradient(90deg, #6366f1, #ec4899);
    border: none;
    font-weight: 700;
    transition: transform 0.15s ease, box-shadow 0.15s ease;
}

div.stButton > button[kind="primary"]:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 22px rgba(99, 102, 241, 0.4);
}

/* ---------- Respect reduced-motion setting ---------- */
@media (prefers-reduced-motion: reduce) {
    * { animation: none !important; transition: none !important; }
}

/* ---------- Mobile ---------- */
@media (max-width: 760px) {
    .stepper { grid-template-columns: repeat(2, 1fr); }
    .hero-title { font-size: 2.2rem; }
}
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────
STEPS = [
    ("🔍", "Search Agent", "Finds recent sources"),
    ("📄", "Reader Agent", "Scrapes the best page"),
    ("✍️", "Writer Chain", "Drafts the report"),
    ("🧐", "Critic Chain", "Scores the draft"),
]

EXAMPLE_TOPICS = [
    "🏥 AI in healthcare",
    "⚡ Solid-state batteries",
    "🌍 Carbon capture technology",
    "🧬 CRISPR gene therapy",
]


# ──────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────
def to_text(content) -> str:
    """Agent messages can be a plain string or a list of content blocks."""
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and "text" in block:
                parts.append(block["text"])
        return "\n".join(parts)

    return str(content)


def render_stepper(slot, current: int) -> None:
    """
    Draw the 4-step pipeline tracker.
    current = index of the active step (0-3). Use 4 when everything is done.
    """
    cards = []

    for index, (icon, name, desc) in enumerate(STEPS):
        if index < current:
            state, badge = "done", "✅ Done"
        elif index == current:
            state, badge = "active", "⏳ Working..."
        else:
            state, badge = "pending", "💤 Waiting"

        cards.append(
            f'<div class="step {state}">'
            f'<span class="icon">{icon}</span>'
            f'<div class="name">{name}</div>'
            f'<div class="desc">{desc}</div>'
            f'<span class="badge">{badge}</span>'
            f"</div>"
        )

    slot.markdown(f'<div class="stepper">{"".join(cards)}</div>', unsafe_allow_html=True)


def extract_score(feedback: str):
    """Pull the 'Score: X/10' value out of the critic's reply."""
    match = re.search(r"Score:\s*(\d+(?:\.\d+)?)\s*/\s*10", feedback)
    return float(match.group(1)) if match else None


def extract_urls(text: str) -> list:
    """Return unique URLs found in the text, keeping their order."""
    urls = re.findall(r"https?://[^\s)\]>\"']+", text)
    return list(dict.fromkeys(url.rstrip(".,;") for url in urls))


# ──────────────────────────────────────────────────────────────
# Pipeline runner (same flow as pipeline.py, with live UI updates)
# ──────────────────────────────────────────────────────────────
def run_pipeline(topic: str, stepper_slot, status_slot) -> dict:
    state = {"topic": topic}
    started = time.time()

    # Step 1 - search agent
    render_stepper(stepper_slot, 0)
    status_slot.info("🔍 The search agent is looking for recent, reliable sources...")

    search_agent = build_search_agent()
    search_result = search_agent.invoke({
        "messages": [("user", f"Find recent, reliable and detailed information about: {topic}")]
    })
    state["search_results"] = to_text(search_result["messages"][-1].content)
    st.toast("Sources found!", icon="🔍")

    # Step 2 - reader agent
    render_stepper(stepper_slot, 1)
    status_slot.info("📄 The reader agent is scraping the most relevant page...")

    reader_agent = build_reader_agent()
    reader_result = reader_agent.invoke({
        "messages": [(
            "user",
            f"Based on the following search results about '{topic}', "
            f"pick the most relevant URL and scrape it for deeper content.\n\n"
            f"Search Results:\n{state['search_results'][:800]}",
        )]
    })
    state["scraped_content"] = to_text(reader_result["messages"][-1].content)
    st.toast("Page scraped!", icon="📄")

    # Step 3 - writer chain
    render_stepper(stepper_slot, 2)
    status_slot.info("✍️ The writer is drafting your report...")

    research_combined = (
        f"SEARCH RESULTS : \n {state['search_results']} \n\n"
        f"DETAILED SCRAPED CONTENT : \n {state['scraped_content']}"
    )
    state["report"] = writer_chain.invoke({
        "topic": topic,
        "research": research_combined,
    })
    st.toast("Report drafted!", icon="✍️")

    # Step 4 - critic chain
    render_stepper(stepper_slot, 3)
    status_slot.info("🧐 The critic is reviewing the report...")

    state["feedback"] = critic_chain.invoke({"report": state["report"]})

    # Finished
    render_stepper(stepper_slot, 4)
    status_slot.success("🎉 Research complete!")

    state["elapsed"] = time.time() - started
    state["timestamp"] = datetime.now().strftime("%d %b, %H:%M")
    return state


# ──────────────────────────────────────────────────────────────
# Results view
# ──────────────────────────────────────────────────────────────
def render_results(result: dict) -> None:
    score = extract_score(result["feedback"])
    urls = extract_urls(result["search_results"] + " " + result["report"])
    word_count = len(result["report"].split())

    st.markdown(f"### 📊 Results for *{result['topic']}*")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("⭐ Critic score", f"{score:g}/10" if score is not None else "N/A")
    col2.metric("📝 Report length", f"{word_count} words")
    col3.metric("🔗 Sources found", len(urls))
    col4.metric("⏱️ Time taken", f"{result['elapsed']:.0f}s")

    tab_report, tab_feedback, tab_search, tab_scraped = st.tabs(
        ["📑 Final Report", "🧐 Critic Feedback", "🔍 Search Results", "📄 Scraped Content"]
    )

    safe_name = re.sub(r"\W+", "_", result["topic"])[:40]

    with tab_report:
        st.markdown(result["report"])
        st.download_button(
            label="⬇️ Download report (.md)",
            data=result["report"],
            file_name=f"research_report_{safe_name}.md",
            mime="text/markdown",
        )

    with tab_feedback:
        if score is not None:
            st.progress(score / 10, text=f"Quality score: {score:g} / 10")
        st.markdown('<div class="feedback-card">', unsafe_allow_html=True)
        st.markdown(result["feedback"])
        st.markdown("</div>", unsafe_allow_html=True)

    with tab_search:
        if urls:
            st.markdown("**Sources discovered**")
            st.markdown(
                "".join(f'<span class="pill">🔗 {url[:60]}</span>' for url in urls),
                unsafe_allow_html=True,
            )
            st.divider()
        st.markdown(result["search_results"])

    with tab_scraped:
        st.markdown(result["scraped_content"])


# ──────────────────────────────────────────────────────────────
# Session state
# ──────────────────────────────────────────────────────────────
if "current" not in st.session_state:
    st.session_state.current = None

if "history" not in st.session_state:
    st.session_state.history = []

if "topic_input" not in st.session_state:
    st.session_state.topic_input = ""


def set_topic(text: str) -> None:
    """Callback for the example-topic buttons (strips the leading emoji)."""
    st.session_state.topic_input = text.split(" ", 1)[1]


def load_history(index: int) -> None:
    st.session_state.current = st.session_state.history[index]


# ──────────────────────────────────────────────────────────────
# Sidebar
# ──────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🧠 About")
    st.write(
        "A multi-agent research assistant. Four specialised steps work "
        "together to turn a topic into a reviewed, sourced report."
    )

    st.markdown("### 🧩 How it works")
    st.markdown(
        "1. 🔍 **Search agent** queries the web with Tavily\n"
        "2. 📄 **Reader agent** scrapes the best result\n"
        "3. ✍️ **Writer chain** drafts a structured report\n"
        "4. 🧐 **Critic chain** scores and critiques it"
    )

    st.markdown("### 🛠️ Tech stack")
    st.markdown(
        '<span class="pill">🐍 Python</span>'
        '<span class="pill">🦜 LangChain</span>'
        '<span class="pill">⚡ Groq</span>'
        '<span class="pill">🌐 Tavily</span>'
        '<span class="pill">🍲 BeautifulSoup</span>'
        '<span class="pill">🎈 Streamlit</span>',
        unsafe_allow_html=True,
    )

    if st.session_state.history:
        st.markdown("### 🕘 Recent runs")
        for i, item in reversed(list(enumerate(st.session_state.history))):
            st.button(
                f"{item['topic'][:28]} · {item['timestamp']}",
                key=f"history_{i}",
                on_click=load_history,
                args=(i,),
                use_container_width=True,
            )


# ──────────────────────────────────────────────────────────────
# Main page
# ──────────────────────────────────────────────────────────────
st.markdown(
    """
    <div class="hero">
        <div class="hero-emoji">🧠</div>
        <div class="hero-title">Multi-Research-Agent</div>
        <div class="hero-sub">
            Give it a topic. Four AI steps search, read, write and critique,
            then hand you a sourced research report. 🚀
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

topic = st.text_input(
    "Research topic",
    key="topic_input",
    placeholder="e.g. Recent breakthroughs in AI for healthcare",
    label_visibility="collapsed",
)

st.caption("✨ Need an idea? Try one of these:")
example_cols = st.columns(len(EXAMPLE_TOPICS))
for col, example in zip(example_cols, EXAMPLE_TOPICS):
    col.button(example, on_click=set_topic, args=(example,), use_container_width=True)

start = st.button("🚀 Start research", type="primary", use_container_width=True)

stepper_slot = st.empty()
status_slot = st.empty()

if start:
    if not topic.strip():
        st.warning("⚠️ Enter a topic first, then press Start research.")
    else:
        try:
            result = run_pipeline(topic.strip(), stepper_slot, status_slot)
            st.session_state.current = result
            st.session_state.history.append(result)
            st.balloons()
        except Exception as error:
            status_slot.empty()
            st.error(f"❌ Something went wrong while running the pipeline: {error}")
            st.caption("Check your GROQ_API_KEY and TAVILY_API_KEY in the .env file, then try again.")

elif st.session_state.current:
    render_stepper(stepper_slot, 4)

if st.session_state.current:
    render_results(st.session_state.current)
else:
    st.info("👆 Enter a topic above (or pick an example) to start your first research run.")
