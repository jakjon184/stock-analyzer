"""Utility to pull market news headlines from popular finance and crypto outlets.

The script relies on RSS/Atom feeds exposed by each provider, so no API keys are
required.  Use the ``--category`` flag to limit the output to a single asset
class or run without arguments to fetch every configured feed.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import Iterable, List, Mapping, Sequence
from urllib.error import URLError
from urllib.request import urlopen
import xml.etree.ElementTree as ET


@dataclass(frozen=True)
class Source:
    """Simple data container describing a news feed."""

    name: str
    url: str


NEWS_SOURCES: Mapping[str, Sequence[Source]] = {
    "crypto": [
        Source("CoinDesk", "https://www.coindesk.com/arc/outboundfeeds/rss/"),
        Source("CoinTelegraph", "https://cointelegraph.com/rss"),
        Source("The Block", "https://www.theblock.co/rss.xml"),
        Source("Decrypt", "https://decrypt.co/feed"),
        Source("CryptoSlate", "https://cryptoslate.com/feed/"),
        Source("Messari", "https://messari.io/rss"),
        Source("CoinMarketCap", "https://coinmarketcap.com/headlines/news/feed/"),
        Source("CoinGecko", "https://www.coingecko.com/en/rss"),
    ],
    "stocks": [
        Source("Bloomberg Markets", "https://www.bloomberg.com/feeds/markets-news.rss"),
        Source("Reuters", "https://www.reuters.com/markets/us/rss"),
        Source("Financial Times", "https://www.ft.com/markets?format=rss"),
        Source("CNBC Markets", "https://www.cnbc.com/id/100003114/device/rss/rss.html"),
        Source("MarketWatch", "https://www.marketwatch.com/rss/topstories"),
        Source("Yahoo Finance", "https://finance.yahoo.com/news/rssindex"),
        Source("Seeking Alpha", "https://seekingalpha.com/market_currents.xml"),
        Source("Morningstar", "https://www.morningstar.com/rss"),
    ],
    "forex": [
        Source("ForexFactory", "https://www.forexfactory.com/ffcal_week_this.xml"),
        Source("Investing.com Forex", "https://www.investing.com/rss/news_25.rss"),
        Source("DailyFX", "https://www.dailyfx.com/feeds/market-news"),
        Source("FXStreet", "https://www.fxstreet.com/rss/news"),
        Source("TradingView Forex", "https://www.tradingview.com/feeds/press-releases/"),
    ],
    "all-in-one": [
        Source("TradingView", "https://www.tradingview.com/feeds/press-releases/"),
        Source("Investing.com", "https://www.investing.com/rss/news.rss"),
        Source("Yahoo Finance", "https://finance.yahoo.com/news/rssindex"),
        Source("Bloomberg", "https://www.bloomberg.com/feed/podcast/etf_report.xml"),
        Source("Reuters", "https://www.reuters.com/markets/us/rss"),
    ],
}


def _first_text(element: ET.Element, tag_suffix: str) -> str | None:
    tag_suffix = tag_suffix.lower()
    for child in element.iter():
        if child.tag.lower().endswith(tag_suffix):
            text = (child.text or "").strip()
            if text:
                return text
    return None


def _first_link(element: ET.Element) -> str | None:
    for child in element.iter():
        if not child.tag.lower().endswith("link"):
            continue
        href = child.attrib.get("href")
        if href:
            return href.strip()
        text = (child.text or "").strip()
        if text:
            return text
    return None


def fetch_entries(source: Source, limit: int) -> List[str]:
    """Fetch ``limit`` article titles for ``source``.

    Any network or parsing failure is converted into a short error message so
    that one misbehaving endpoint does not abort the entire run.
    """

    try:
        with urlopen(source.url, timeout=15) as response:
            payload = response.read()
    except URLError as exc:  # pragma: no cover - defensive network handling
        return [f"Error loading {source.name}: {exc.reason if hasattr(exc, 'reason') else exc}" ]

    try:
        root = ET.fromstring(payload)
    except ET.ParseError as exc:
        return [f"Unable to parse feed for {source.name}: {exc}"]

    entries = root.findall(".//item")
    if not entries:
        entries = root.findall(".//{*}entry")

    headlines = []
    for entry in entries[:limit]:
        title = _first_text(entry, "title") or "(no title)"
        link = _first_link(entry)
        if link:
            headlines.append(f"- {title} ({link})")
        else:
            headlines.append(f"- {title}")

    if not headlines:
        headlines.append("(No headlines returned)")

    return headlines


def iter_categories(requested: Iterable[str]) -> Iterable[tuple[str, Sequence[Source]]]:
    """Yield category/source pairs, expanding the ``all`` keyword if needed."""

    expanded = list(requested) or list(NEWS_SOURCES.keys())
    for category in expanded:
        key = category.lower()
        if key == "all":
            for cat_name, sources in NEWS_SOURCES.items():
                yield cat_name, sources
            continue

        sources = NEWS_SOURCES.get(key)
        if sources is None:
            raise SystemExit(f"Unknown category '{category}'. Valid options: {', '.join(sorted(NEWS_SOURCES))} or 'all'.")
        yield key, sources


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Pull the latest headlines from popular crypto, stock, forex and all-in-one news sources.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-c",
        "--category",
        nargs="*",
        help="One or more categories to pull (crypto, stocks, forex, all-in-one or all).",
        default=None,
    )
    parser.add_argument(
        "-l",
        "--limit",
        type=int,
        default=5,
        help="Maximum headlines to show for each feed.",
    )
    return parser


def main(args: Sequence[str] | None = None) -> None:
    parser = build_argument_parser()
    cli_args = parser.parse_args(args=args)
    limit = max(1, cli_args.limit)

    divider = "=" * 60
    for category, sources in iter_categories(cli_args.category or []):
        print(divider)
        print(category.upper())
        print(divider)
        for source in sources:
            print(source.name)
            print("-" * len(source.name))
            print("\n".join(fetch_entries(source, limit)))
            print()


if __name__ == "__main__":
    main()
