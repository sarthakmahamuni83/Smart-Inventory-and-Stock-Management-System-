# Smart Inventory & Stock Management System

A read-only retail inventory analytics mini-project built with Streamlit, Python/Pandas and a C++17 DSA engine.

## Dataset

The supplied Kaggle dataset is included at `dataset/sales_data.csv`.

- 76,000 records
- 16 columns
- 5 stores and 20 products
- Date range: 2022-01-01 to 2024-01-30
- No missing values or duplicate full rows were found during initial inspection.

The dataset is treated as **read-only**. The application does not add, edit, or delete dataset records.

## Requirements

- Python 3.10 or newer
- VS Code
- A C++17 compiler available as `g++` (MinGW-w64 on Windows, GCC on Linux, or Clang configured with a `g++` command on macOS)

## Run in VS Code

Open this extracted project folder in VS Code.

### 1. Create and activate a virtual environment

Windows PowerShell:
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

macOS / Linux:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install Python packages

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Check the C++ compiler

```bash
g++ --version
```

If this command is not recognized, install a C++ compiler and make sure `g++` is added to PATH. The app attempts to compile `cpp/inventory_engine.cpp` automatically when it starts.

### 4. Start the website

```bash
streamlit run app.py
```

Streamlit will show a local URL, usually `http://localhost:8501`.

## Demo login

This is intentionally simple demonstration authentication:

- Username: any non-empty username
- Password: any exactly 8-digit numeric value, for example `12345678`

This is not production-grade security and should not be used to protect real accounts or sensitive information.

## Website sections

1. Dashboard
2. Product & Inventory
3. Sales Tracking
4. Smart Reorder
5. Demand Forecasting
6. Price & Discount Analysis

## DSA implementation in C++

`cpp/inventory_engine.cpp` demonstrates:

- `unordered_map` for Product ID lookup (hash map)
- `vector` for storing latest store-product records
- `sort` for ranking / low-stock ordering

The Streamlit app invokes the compiled C++ program for Product ID lookup. If the compiler is unavailable, Python-based dashboard and analytics pages still load, but the C++ lookup is unavailable until the compiler is installed.

## Forecast and reorder assumptions

- The current inventory snapshot uses the latest available date for each Store ID + Product ID pair.
- Demand forecasting uses the mean demand from the latest 7 recorded days as a simple baseline for the next 7 days.
- Reorder point uses recent 30-day average demand, demand variability, and an adjustable assumed supplier lead time.
- Suggested order quantity targets a selected number of days of demand coverage.
- These are educational estimates, not guaranteed predictions or actual purchase orders.

## Troubleshooting

- If `streamlit` is not found, activate the virtual environment and rerun `pip install -r requirements.txt`.
- If the C++ lookup is unavailable, check `g++ --version`, then restart Streamlit.
- If the page shows a missing dataset error, ensure `dataset/sales_data.csv` remains in the `dataset` folder.
