# 🧠 Multi-Research-Agent

A multi-agent AI research assistant that turns any topic into a sourced, reviewed research report. Four specialised steps (search, read, write, critique) work together in a single pipeline, with an interactive Streamlit interface.

## ✨ Features

- 🔍 **Search Agent**: finds recent, reliable sources on the web using Tavily
- 📄 **Reader Agent**: picks the most relevant URL and scrapes its content for deeper context
- ✍️ **Writer Chain**: drafts a structured report (Introduction, Key Findings, Conclusion, Sources)
- 🧐 **Critic Chain**: scores the report out of 10 and lists strengths and areas to improve
- 🎨 **Streamlit UI**: live pipeline tracker, results dashboard, report download and run history

## 🏗️ How it works

```
Topic ─▶ 🔍 Search Agent ─▶ 📄 Reader Agent ─▶ ✍️ Writer Chain ─▶ 🧐 Critic Chain ─▶ Report + Score
```

| Step | Component | Tool / Model |
|------|-----------|--------------|
| 1 | Search Agent | Tavily Search API |
| 2 | Reader Agent | Requests + BeautifulSoup |
| 3 | Writer Chain | Groq (`openai/gpt-oss-120b`) |
| 4 | Critic Chain | Groq (`openai/gpt-oss-120b`) |

## 🛠️ Tech Stack

Python · LangChain · Groq · Tavily · BeautifulSoup · Streamlit

## 📁 Project Structure

```
Multi-Research-Agent/
├── agents.py          # Agents and chains (search, reader, writer, critic)
├── tools.py           # web_search and scrape_url tools
├── pipeline.py        # Command-line pipeline
├── app.py             # Streamlit web interface
├── requirements.txt
└── .env               # API keys (not committed)
```

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/<your-username>/Multi-Research-Agent.git
cd Multi-Research-Agent
```

### 2. Create a virtual environment and install dependencies

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Add your API keys

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key
TAVILY_API_KEY=your_tavily_api_key
```

### 4. Run it

**Web interface**

```bash
streamlit run app.py
```

**Command line**

```bash
python pipeline.py
```

## 📸 Screenshots

_Add screenshots or a short demo GIF of the Streamlit app here._

## 🔮 Future Improvements

- Scrape multiple sources instead of one
- Let the critic's feedback trigger an automatic rewrite
- Export reports as PDF
- Add support for other LLM providers

## 📄 License

MIT