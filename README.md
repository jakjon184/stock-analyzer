# stock-analyzer

Program that will analyze and give you tips to buy and sell stocks in real time.

## News fetcher

Use `news_fetcher.py` to pull the latest headlines from major crypto, stock,
forex and aggregated (all-in-one) sources. The script relies on the RSS feeds
published by each provider, so no API keys are required.

### Usage examples

```bash
# Fetch every category with the default (5) headlines per feed
python news_fetcher.py

# Only fetch crypto and forex headlines, limiting to 3 entries per feed
python news_fetcher.py --category crypto forex --limit 3
```
