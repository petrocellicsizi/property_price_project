<div align="center">
  <h1>🏡 Saját Lakás vs. Albérlet Kalkulátor (BME Projekt)</h1>
  <p><strong>Advanced Real Estate & Financial Simulation Engine for the Hungarian Market</strong></p>
  
  ![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
  ![Flask](https://img.shields.io/badge/flask-%23000.svg?style=flat&logo=flask&logoColor=white)
  ![Coverage](https://img.shields.io/badge/coverage-84%25-brightgreen.svg)
  ![Bootstrap](https://img.shields.io/badge/bootstrap-%238511FA.svg?style=flat&logo=bootstrap&logoColor=white)
  ![Gemini](https://img.shields.io/badge/Google_Gemini-AI-orange)
</div>

## 📖 About The Project

This is a comprehensive, interactive financial simulation platform built with **Flask** and **JavaScript**. It is designed to objectively compare the financial outcomes of buying a home versus renting and investing the difference in the stock market (ETFs). 

Tailored specifically for the **Hungarian macroeconomic environment**, it accounts for local taxation (TBSZ, SZJA), initial fees (vagyonszerzési illeték, ügyvédi díj), and real estate market dynamics. It also features an integration with **Google's Gemini AI** to provide smart location analysis, quantitative adjustments, and a financial chat assistant.

## ✨ Key Features

* **🏙️ 3 Distinct Simulation Scenarios:**
  1. **Buy for Living (Saját Lakás):** Standard mortgage, down payment, maintenance, and common costs.
  2. **Rent & Invest (Albérlet + ETF):** Renting a home and consistently investing the monthly savings into a tax-advantaged stock market portfolio (TBSZ).
  3. **Buy-To-Let (Befektetési célú vásárlás):** Pure investment perspective—buying a property to rent out, paying 15% SZJA on rental income, and reinvesting the cash flow into ETFs.
* **📊 Granular Financial Metrics:** Calculates ROE (Return on Equity), LTV (Loan-to-Value) trajectory, Gross Yield, Price-to-Rent Ratio, and Inflation-adjusted Real Wealth.
* **💸 "Dead Money" Analysis:** Visualizes unrecoverable costs (bank interest, maintenance, legal fees vs. paid rent) via interactive Doughnut charts.
* **🤖 Gemini AI Integration:** 
  * *Notes Evaluator:* Gemini AI analyzes subjective extra info (e.g. "Danube panorama", "Needs renovation") and automatically adjusts quantitative metrics (e.g. +15% rent, +300.000 Ft renovation cost).
  * *Robust Fallbacks:* Strict heuristic parsing and zero-out logic guarantees UI stability even if the LLM hallucinates or if the user leaves fields empty.
* **📈 Historical Backtesting:** A unique module that simulates how a property vs. S&P 500 would have performed starting from historical years (e.g., 2004) up to the present.

## 🛠️ Built With

* **Backend:** Python, Flask, pytest
* **Frontend:** HTML5, Bootstrap 5, JavaScript, Chart.js (responsive charts)
* **AI:** Google GenAI SDK (Gemini Models)

## 🚀 Getting Started

### Prerequisites

* Python 3.9+
* [Gemini API Key](https://aistudio.google.com/) for the AI features.

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/property-price-calculator.git
   cd property-price-calculator
   ```

2. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   Create a `.env` file in the root directory and add your Gemini API key:
   ```env
   GEMINI_API_KEY=your_api_key_here
   ```

5. Run the application:
   ```bash
   python app.py
   ```

6. Open your browser and navigate to `http://127.0.0.1:5000`.

## 🧪 Testing (84% Coverage)

The project includes an extensive test suite verifying financial logic, edge cases, and API robustness.

Run the tests using `pytest`:
```bash
# Run all tests
pytest

# Run tests with coverage report
pytest --cov=core --cov=utils --cov=api --cov=app
```

## 📂 Project Structure

```text
calc_flask/
├── api/                  # API endpoints and routing
├── core/                 # Core simulation engines & AI integration
│   ├── engine.py         # 30-year DCF simulation engine
│   ├── historical_engine.py # Backtesting engine based on historical data
│   └── gemini_service.py # Google Gemini API integration & fallbacks
├── data/                 # Local JSON data stores (historical indices)
├── static/               # Frontend assets
│   ├── css/              # Custom styling
│   └── js/               # Frontend controller (app.js)
├── templates/            # HTML Jinja2 templates (dashboard, chat)
├── tests/                # Comprehensive Pytest suite (Financials, API, UI, AI)
├── utils/                # Quantitative helpers (Finance, Algorithms)
├── app.py                # Flask Application Factory & Main routes
└── requirements.txt      # Python dependencies
```

## 🏗️ Architecture Highlights

* **`core/engine.py`:** Contains the main simulation engine, calculating 30+ year trajectories for loan amortization, compound interest, taxation (TBSZ/SZJA), and discounted cash flows.
* **`utils/finance.py`:** Standalone math functions for computing PMT, effective monthly interest rates, and loan-to-value ratios securely.
* **`core/gemini_service.py`:** Manages structured interactions with the Gemini API to analyze unstructured property notes and enforce zero-hallucination overrides.
* **`static/js/app.js`:** The frontend controller, handling real-time form synchronizations, two-way data bindings, and Chart.js rendering without full page reloads.

## 📜 License

Distributed under the MIT License.
