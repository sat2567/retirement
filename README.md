# Retirement Planner Tracker

A comprehensive Streamlit web application for retirement planning with multiple financial scenarios and calculations.

## Features

### 🎯 Planning Scenarios

1. **Corpus to Monthly Withdrawal**
   - Calculate sustainable monthly withdrawal from retirement corpus
   - Inflation-adjusted withdrawals using growing annuity formulas
   - Shows month-by-month corpus depletion

2. **Withdrawal to Corpus Duration**
   - Determine how long your corpus will last with given withdrawals
   - Accounts for inflation increase in withdrawal amounts
   - Simulates until corpus depletion

3. **Monthly Savings to Corpus**
   - Calculate final retirement corpus from SIP investments
   - Supports annual step-up in SIP amounts
   - Shows corpus growth over time

4. **Custom Cashflow Analysis**
   - Upload custom monthly cashflow schedules via CSV
   - Calculate Present Value / Future Value
   - Supports both inflows (positive) and outflows (negative)

### 💡 Key Features

- **Interactive UI**: Sidebar inputs with real-time calculations
- **Visualizations**: Interactive charts showing corpus changes over time
- **Data Export**: Download month-by-month calculations as CSV
- **Currency Formatting**: Indian Rupee formatting (₹, Lakhs, Crores)
- **Manual Calculations**: All financial formulas implemented without external libraries

## Installation & Usage

### Prerequisites
- Python 3.7+
- pip package manager

### Setup
1. Clone or download this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Run the Application
```bash
streamlit run app.py
```

The app will open in your default web browser at `http://localhost:8501`

## Financial Formulas Implemented

### Growing Annuity (Inflation-Adjusted Withdrawals)
```
PV = PMT × [(1 - ((1+g)/(1+r))^n) / (r - g)]
```
Where:
- PV = Present Value (starting corpus)
- PMT = Payment (monthly withdrawal)
- r = monthly return rate
- g = monthly inflation rate
- n = number of periods

### Future Value with Step-up SIP
```
FV = Σ(SIP_i × (1 + r)^(n-i))
```
Where SIP amounts increase annually by step-up percentage.

### Rate Conversions
Annual rates are converted to monthly using:
```
monthly_rate = (1 + annual_rate/100)^(1/12) - 1
```

## CSV Format for Custom Cashflow

Create a CSV file with a single column named "Cashflow":
```csv
Cashflow
50000
-30000
25000
60000
-40000
```

- Positive values = Money coming in (investments, income)
- Negative values = Money going out (expenses, withdrawals)

## Technical Details

- **Framework**: Streamlit for web interface
- **Visualization**: Plotly for interactive charts
- **Data Processing**: Pandas for calculations and data manipulation
- **Styling**: Custom CSS for improved UI/UX

## Project Structure

```
retirement-planner/
├── app.py              # Main Streamlit application
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

## Usage Tips

1. **Start Simple**: Begin with default values to understand each scenario
2. **Realistic Assumptions**: Use historical market returns (8-12% for equity)
3. **Consider Inflation**: Factor in 6-7% annual inflation for India
4. **Regular Updates**: Revisit calculations as your financial situation changes
5. **Export Data**: Download CSV files for detailed analysis in Excel/Sheets

## Contributing

Feel free to submit issues, feature requests, or pull requests to improve this retirement planning tool.

## License

This project is open source and available under the MIT License.
