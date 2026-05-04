name: Nightly BBC6 Scraper

on:
  schedule:
    - cron: '58 22 * * *'  # 22:58 UTC = 23:58 Irish Summer Time
  workflow_dispatch:   #enables manual runs

jobs:
  run-script:
    runs-on: ubuntu-latest

    steps:
      - name: Check out repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run script
        run: python main.py

      # --- NEW: saves the output files back into your repo each night ---
      - name: Commit output files
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add output/
          git diff --cached --quiet || git commit -m "Nightly update: $(date -u +'%Y-%m-%d')"
          git push
