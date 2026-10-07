<div align="center">
  <h1>🏠 Saját Lakás vs. Albérlet Kalkulátor</h1>
  <p><strong>Advanced Real Estate & Financial Simulation Engine for the Hungarian Market</strong></p>
</div>

## 📖 About The Project

This is a comprehensive, interactive financial simulation platform built with **Flask** and **JavaScript**. It is designed to objectively compare the financial outcomes of buying a home versus renting and investing the difference in the stock market (ETFs). 

Tailored specifically for the **Hungarian macroeconomic environment**, it accounts for local taxation (TBSZ, SZJA), initial fees (vagyonszerzési illeték, ügyvédi díj), and real estate market dynamics. It also features an integration with **Google's Gemini AI** to provide smart location analysis and a financial chat assistant.

## ✨ Key Features

* **3 Distinct Simulation Scenarios:**
  1. **Buy for Living (Saját Lakás):** Standard mortgage, down payment, maintenance, and common costs.
  2. **Rent & Invest (Albérlet + ETF):** Renting a home and consistently investing the monthly savings into a tax-advantaged stock market portfolio (TBSZ).
  3. **Buy-To-Let (Befektetési célú vásárlás):** Pure investment perspective—buying a property to rent out, paying 15% SZJA on rental income, and reinvesting the cash flow into ETFs.
* **Granular Financial Metrics:** Calculates ROE (Return on Equity), LTV (Loan-to-Value) trajectory, Gross Yield, Price-to-Rent Ratio, and Inflation-adjusted Real Wealth.
* **"Dead Money" Analysis:** Visualizes unrecoverable costs (bank interest, maintenance, legal fees vs. paid rent) via interactive Doughnut charts.
* **Sensitivity Heatmap:** A 2D matrix comparing the final wealth difference based on varying ETF yields and property appreciation rates.
* **Dynamic Time Horizons:** Fully adjustable simulation length from 5 to 50 years with real-time UI updates.
* **AI Integration:** 
  * *Location Expert:* Gemini AI analyzes the provided Budapest/Hungarian address and suggests realistic annual appreciation rates.
  * *Financial Chatbot:* Context-aware AI assistant that can dynamically update simulation sliders based on natural language requests.

## 🛠️ Built With

* **Backend:** Python, Flask, NumPy (for vectorized financial calculations), Pydantic (data validation).
* **Frontend:** HTML5, Bootstrap 5, JavaScript, Chart.js (responsive charts).
* **AI:** Google GenAI SDK (Gemini Models).

## 🚀 Getting Started

### Prerequisites

* Python 3.9 or higher
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

## 🧠 Architecture Highlights

* **`core/engine.py`:** Contains the `QuantitativeSimulationEngine`, which uses vector math (NumPy arrays) to calculate 30+ year trajectories for loan amortization, compound interest, taxation, and discounted cash flows in milliseconds.
* **`schemas/simulation.py`:** Enforces strict typing and validation bounds for incoming API requests.
* **`services/ai_service.py`:** Manages the system prompts and structured interactions with the Gemini API to analyze property data and parse chat intent.
* **`static/js/app.js`:** The frontend controller, handling real-time form inputs, DOM updates, and Chart.js rendering without full page reloads.

## 📝 License

Distributed under the MIT License. See `LICENSE` for more information.
