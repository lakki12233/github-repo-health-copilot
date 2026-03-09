# 📊 GitHub Repo Health Copilot

![Built with Zerve](https://img.shields.io/badge/Built%20with-Zerve%20Agentic%20AI-6C63FF?style=for-the-badge)
![UI](https://img.shields.io/badge/UI-Streamlit-FF4B4B?style=for-the-badge&logo=streamlit)
![Data Source](https://img.shields.io/badge/Data-GitHub%20REST%20API-181717?style=for-the-badge&logo=github)
![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?style=for-the-badge&logo=python)

GitHub Repo Health Copilot is a real-time repository analytics dashboard for maintainers and engineering teams. It fetches live data from the GitHub REST API, computes repository health metrics, highlights stale issues and long-waiting pull requests, and presents the results in an interactive Streamlit interface with AI-assisted recommendations.

This project was prototyped and deployed using **Zerve**, which helped accelerate the workflow from data ingestion to analysis, reporting, and app deployment. The final dashboard was manually reviewed, refined, and tested on multiple public repositories.

---

## 🔗 Live Demo

- **Deployed App:** https://github-repo-health-copilot.hub.zerve.cloud/
- **GitHub Repository:** https://github.com/lakki12233/github-repo-health-copilot

---

## 📝 Why This Project

Open-source and engineering teams often struggle with:
- growing issue backlogs
- stale or untriaged bug reports
- pull requests waiting too long for review
- limited visibility into repository health

This dashboard helps maintainers quickly identify bottlenecks, prioritize cleanup work, and act on repository health signals using live GitHub data.

---

## ✨ Features

- **📈 KPI Cards**  
  View key repository health metrics at a glance, including:
  - Open issues
  - Stale issues (>30 days)
  - Average issue close time
  - Average PR merge time
  - Open PR count

- **📊 Interactive Analytics Charts**  
  Visualize important repo health trends:
  - Open issue age distribution
  - PR merge time distribution
  - Top issue labels
  - Contributor activity

- **⏳ Pull Requests Waiting Longest**  
  Ranked table of open PRs waiting the longest for review, including:
  - PR number
  - title
  - days open
  - comments
  - assignees
  - direct GitHub link

- **🤖 AI-Assisted Maintainer Recommendations**  
  Generates structured insights on:
  - top bottlenecks
  - highest-priority actions
  - actionable sprint recommendations
  - positive health signals

- **⚡ Smart Caching**  
  GitHub API responses are cached to reduce redundant requests and improve responsiveness.

- **🌐 Public Repository Support**  
  Works out of the box for public GitHub repositories. Optional GitHub authentication can improve API rate limits and reliability.

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Frontend / UI** | Streamlit |
| **Data Source** | GitHub REST API |
| **Data Processing** | Python, Pandas |
| **Visualization** | Matplotlib |
| **AI Recommendations** | LLM-assisted reporting |
| **Development Platform** | Zerve |

---

## 🚀 How It Works

1. The user enters a public GitHub repository in `owner/repo` format.
2. The app fetches recent issues and pull requests from the GitHub REST API.
3. Data is normalized and processed into repository health metrics.
4. Charts and KPI summaries are generated from the processed data.
5. The app produces AI-assisted maintainer recommendations based on the current repository state.
6. Results are shown in an interactive Streamlit dashboard.

---

## 📦 Local Setup

### Prerequisites

- Python 3.9+
- `pip`

### 1. Clone the Repository

~~~bash
git clone https://github.com/lakki12233/github-repo-health-copilot.git
cd github-repo-health-copilot
~~~

### 2. Create and Activate a Virtual Environment

#### macOS / Linux

~~~bash
python3 -m venv .venv
source .venv/bin/activate
~~~

#### Windows (PowerShell)

~~~powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
~~~

### 3. Install Dependencies

~~~bash
pip install -r requirements.txt
~~~

### 4. (Optional) Set a GitHub Token

Using a token is optional for public repositories, but it helps avoid rate limiting when refreshing frequently.

#### macOS / Linux

~~~bash
export GITHUB_TOKEN=your_personal_access_token_here
~~~

#### Windows (PowerShell)

~~~powershell
$env:GITHUB_TOKEN="your_personal_access_token_here"
~~~

### 5. Run the Streamlit App

~~~bash
streamlit run app/main.py
~~~

The app should open in your browser at:

~~~text
http://localhost:8501
~~~

---

## 💡 Usage

1. Open the app in your browser.
2. Enter any public GitHub repository in the sidebar using the format:

~~~text
owner/repo
~~~

Example:

~~~text
facebook/react
~~~

3. Click **Fetch / Refresh**.
4. Review:
   - KPI cards
   - analytics charts
   - long-waiting PR table
   - AI maintainer recommendations

### Example Repositories to Try

- `facebook/react`
- `python/cpython`
- `vercel/next.js`
- `kornia/kornia`

---

## 📁 Project Structure

~~~text
github-repo-health-copilot/
├── app/
│   └── main.py
├── requirements.txt
└── README.md
~~~

---

## 🔍 Example Insights the Dashboard Can Surface

- High stale issue rates indicating triage debt
- Slow issue close times suggesting ownership or prioritization gaps
- Open PR queues waiting too long for review
- Repeated labels showing concentrated problem areas
- Contributor activity patterns that highlight active maintainers or review bottlenecks

---

## ✅ Use Cases

This project can be useful for:
- open-source maintainers
- engineering managers
- developer productivity teams
- internal tooling experiments
- GitHub repository health reporting
- sprint triage and backlog cleanup

---

## 🧪 Notes

- The dashboard currently targets **public GitHub repositories**.
- GitHub API rate limits may affect repeated refreshes without authentication.
- AI-generated recommendations should be treated as decision support, not as a replacement for maintainer judgment.
- Metrics and report language may vary depending on repository labeling conventions and project workflow practices.

---

## 🏗️ Built With

This project was prototyped and deployed using **Zerve**, an AI-native analytics development environment. Zerve helped accelerate workflow creation, connect data retrieval with analysis, scaffold the reporting layer, and deploy the final Streamlit application quickly.

The resulting dashboard was then manually refined, validated, and tested across multiple public repositories to improve clarity, correctness, and usability.

---

## 🙌 Acknowledgments

- **GitHub REST API** for public repository data
- **Streamlit** for the dashboard interface
- **Zerve** for rapid analytics workflow prototyping and deployment

---

## 📬 Contact

**Krishna Sreepriya Menon**  
GitHub: https://github.com/lakki12233

---

## 📄 License

This project is intended for portfolio, evaluation, and learning purposes.

If you plan to open-source it formally, you can later add a license such as:
- MIT License
- Apache 2.0
- BSD 3-Clause
