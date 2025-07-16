# Argentine Bond Carry Trade Analyzer

A comprehensive web application for analyzing Argentine bond carry trade opportunities based on real-time market data.

## Features

- **Real-time Data**: Fetches live data from data912.com API (MEP rates, bonds, notes)
- **Carry Trade Analysis**: Calculates carry trade metrics for S-series and T-series Argentine bonds
- **Interactive Table**: Color-coded performance indicators with multiple scenario analysis
- **Visualization**: Breakeven vs currency band ceiling chart with bond annotations
- **Professional UI**: Financial dashboard styling similar to logos-serviciosfinancieros.com.ar

## Core Functionality

### Data Table Columns
- **Ticker**: Bond identifier
- **Precio**: Current bond price
- **Días al vencimiento**: Days to maturity
- **TEM**: Monthly effective rate
- **Carry scenarios**: Return analysis at different exchange rates (1000, 1100, 1200, 1300, 1400)
- **Carry Techo**: Return at currency band ceiling

### Currency Band Calculation
- Fixed crawling peg bands since 04/14/2025
- Upper band: +1% monthly progression (1400 * 1.01^(days/30))
- Dynamic ceiling calculation for carry scenarios

## Installation

1. **Install dependencies**:
   ```bash
   pip install -r backend/requirements.txt
   ```

2. **Run the application**:
   ```bash
   python run_server.py
   ```

3. **Access the web interface**:
   Open your browser to `http://localhost:8000`

## Technical Architecture

### Backend (FastAPI)
- **config.py**: Bond tickers, payoff values, API endpoints
- **data_fetcher.py**: Real-time data fetching from data912.com
- **carry_calculator.py**: Core calculation engine with exact notebook logic
- **main.py**: FastAPI application with REST endpoints

### Frontend (HTML/CSS/JS)
- **Responsive design** with professional financial styling
- **Interactive data table** with color-coded performance indicators
- **Real-time chart** showing MEP breakeven vs band ceiling
- **Auto-refresh** functionality (5-minute intervals)

## API Endpoints

- `GET /`: Main web interface
- `GET /api/carry-data`: Carry trade table data with color limits
- `GET /api/chart-data`: Chart data for breakeven visualization  
- `GET /api/health`: Health check endpoint

## Data Sources

- **data912.com API**: Real-time MEP rates and Argentine bond/note prices
- **Fixed parameters**: Bond expiration dates, payoff values, currency band settings

## Color Coding

The table uses a red-yellow-green gradient to indicate performance:
- **Green**: Positive carry above threshold
- **Yellow**: Neutral carry performance
- **Red**: Negative carry below threshold

## Development

The application replicates the exact calculation logic from the original Jupyter notebook while providing a scalable, web-based interface for real-time analysis.

### Key Calculations
- **TEM**: Monthly effective rate based on bond price and payoff
- **Carry Trade**: Return calculation at different exchange rate scenarios
- **Band Ceiling**: Dynamic calculation based on crawling peg progression
- **MEP Breakeven**: Exchange rate at which investment breaks even

## Usage

1. The application automatically loads current market data on startup
2. Use the "Actualizar" button to refresh data manually
3. Table cells are color-coded to highlight the best opportunities
4. Chart shows the relationship between breakeven rates and band ceiling
5. Data auto-refreshes every 5 minutes

## Requirements

- Python 3.8+
- FastAPI
- Pandas
- Requests
- Matplotlib (for backend calculations)
- Modern web browser with JavaScript enabled