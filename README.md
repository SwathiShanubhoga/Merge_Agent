# 🔗 Sales Merge Agent

A beginner-friendly Streamlit app that merges **Sales**, **Products**, and **Stores** files into one combined dataset using their common key columns (e.g. `product_id`, `store_id`).

This README is written for someone with **zero Python experience**. Follow it top to bottom.

---

## 📁 What's in this folder

```
sales-merge-agent/
├── app.py                  ← the actual app (Streamlit code)
├── requirements.txt        ← list of Python libraries the app needs
├── .gitignore               ← tells Git which files to ignore
├── sample_data/
│   ├── sales.csv
│   ├── products.csv
│   └── stores.csv
└── README.md               ← this file
```

---

## Step 1: Install the tools

You need two things installed on your computer:

1. **Python** (the programming language)
   - Go to https://www.python.org/downloads/
   - Download the latest version, run the installer.
   - ⚠️ IMPORTANT: on the first install screen, tick the box **"Add Python to PATH"** before clicking Install.

2. **VS Code** (the code editor)
   - Go to https://code.visualstudio.com/
   - Download and install it.
   - Open VS Code → go to the Extensions icon (left sidebar, looks like 4 squares) → search **"Python"** → install the Microsoft Python extension.

To check Python installed correctly, open a terminal (in VS Code: `Terminal` menu → `New Terminal`) and type:
```
python --version
```
You should see something like `Python 3.12.x`. If you get an error, restart VS Code (or your computer) and try again.

---

## Step 2: Open this project in VS Code

1. Open VS Code.
2. `File → Open Folder` → select this `sales-merge-agent` folder.
3. You should see all the files listed above in the left sidebar (Explorer panel).

---

## Step 3: Create a virtual environment (a clean, isolated Python setup)

In the VS Code terminal (`Terminal → New Terminal`), run:

```bash
python -m venv venv
```

This creates a folder called `venv` — a private Python environment just for this project.

Activate it:

- **Windows:**
  ```bash
  venv\Scripts\activate
  ```
- **Mac/Linux:**
  ```bash
  source venv/bin/activate
  ```

You'll know it worked because your terminal line will now start with `(venv)`.

---

## Step 4: Install the required libraries

With `(venv)` active, run:

```bash
pip install -r requirements.txt
```

This installs:
- `streamlit` — turns Python scripts into web apps
- `pandas` — handles reading/merging tabular data (like Excel, but in code)
- `openpyxl` — lets pandas read/write `.xlsx` Excel files

---

## Step 5: Run the app

Still in the terminal, run:

```bash
streamlit run app.py
```

Your browser should automatically open a page at `http://localhost:8501` showing the app. If it doesn't open automatically, copy that URL into your browser.

### Try it out
- Tick the **"Use built-in sample data"** checkbox to test instantly, OR
- Upload your own 3 files (Sales, Products, Stores) using the upload boxes.
- Click **"Merge Files"**.
- Click **"Download Merged File"** to save the result as a CSV.

To stop the app, go back to the terminal and press `Ctrl + C`.

---

## Step 6: Understand what the app is doing (for your badge writeup)

The core merge logic in `app.py`:

```python
# Step 1: merge sales with products, using product_id as the common key
merged = pd.merge(sales_df, products_df, on=key1, how="left")

# Step 2: merge that result with stores, using store_id as the common key
merged = pd.merge(merged, stores_df, on=key2, how="left")
```

- `pd.merge()` is like a VLOOKUP in Excel, but for two entire tables at once.
- `on=key1` tells pandas which column to match rows on (e.g. `product_id`).
- `how="left"` means: keep every row from Sales, and just attach matching details from Products/Stores. If a match isn't found, those columns come back empty (`NaN`) instead of dropping the row.

The app also **auto-detects common columns** between file pairs using:
```python
common = list(set(df1.columns) & set(df2.columns))
```
This finds column names that exist in both files — a simple way to guess the join key without hardcoding it.

---

## Step 7: Push this project to GitHub

1. **Create a GitHub account** (if you don't have one): https://github.com/join

2. **Create a new repository:**
   - Go to https://github.com/new
   - Name it e.g. `sales-merge-agent`
   - Leave it public (or private, your choice)
   - Do NOT tick "Add a README" (we already have one) — just click **Create repository**.
   - GitHub will show you a page with commands — keep that tab open.

3. **Install Git** (if not already installed):
   - https://git-scm.com/downloads
   - Install with default options.

4. **In VS Code terminal**, from inside your project folder, run these one by one:

```bash
git init
git add .
git commit -m "Initial commit: Sales Merge Agent Streamlit app"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/sales-merge-agent.git
git push -u origin main
```

Replace `YOUR-USERNAME` with your actual GitHub username (copy the exact URL GitHub showed you in step 2).

5. Refresh your GitHub repo page in the browser — your files should now be there! 🎉

> Note: `venv/` is excluded automatically via `.gitignore`, so you won't accidentally upload your whole Python environment (that's normal practice — anyone cloning your repo just runs `pip install -r requirements.txt` themselves).

---

## Step 8 (Optional): Deploy it live for free

If your badge wants a live working link, not just code:

1. Push your code to GitHub (Step 7 above).
2. Go to https://share.streamlit.io/
3. Sign in with GitHub, click **"New app"**, pick your `sales-merge-agent` repo, set main file as `app.py`.
4. Click **Deploy**. You'll get a public URL like `https://sales-merge-agent.streamlit.app`.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `streamlit: command not found` | Make sure `(venv)` is active — re-run the activate command from Step 3 |
| `python` not recognized | Reinstall Python and tick "Add Python to PATH" |
| Merge shows blank/NaN values | Your key columns don't actually match values (e.g. `P001` vs `p001`) — check for typos or case differences |
| Git push asks for password and fails | GitHub no longer accepts account passwords for Git — use a Personal Access Token instead: https://github.com/settings/tokens |
