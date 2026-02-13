"""
Bitcoin Scenario Analysis Generator
Calls Claude API with web search to produce a fresh weekly analysis.
Outputs structured JSON to data/analyses/YYYY-MM-DD.json and updates data/index.json
"""

import anthropic
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# ── Paths ──
ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data" / "analyses"
INDEX_FILE = ROOT / "data" / "index.json"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# ── Claude API Setup ──
client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env

ANALYSIS_PROMPT = """Tu es un analyste senior spécialisé en macroéconomie et marchés crypto.
Effectue une recherche approfondie sur l'état actuel du Bitcoin et produis une analyse structurée.

RECHERCHES À EFFECTUER :
1. Prix actuel du Bitcoin, variation 24h, market cap, volume
2. Fear & Greed Index actuel
3. Dernières analyses de JPMorgan, Goldman Sachs, Standard Chartered, Bernstein, Fidelity sur Bitcoin
4. Données on-chain récentes (Glassnode, CryptoQuant) : flux ETF, activité whales, hash rate
5. Conditions macro : taux Fed, politique monétaire, liquidité globale
6. Actualités réglementaires crypto récentes
7. Consensus des analystes sur les prix à court et moyen terme

IMPORTANT : Base tes scénarios sur les données réelles que tu trouves, pas sur des hypothèses.

PRODUIS UN JSON STRICT avec cette structure exacte (pas de markdown, pas de texte autour, UNIQUEMENT le JSON) :

{
  "generated_at": "ISO 8601 timestamp",
  "data_sources": ["liste des sources consultées"],

  "market_snapshot": {
    "price_usd": number,
    "change_24h_pct": number,
    "market_cap_usd": number,
    "volume_24h_usd": number,
    "fear_greed_index": number,
    "fear_greed_label": "string",
    "dominance_pct": number,
    "ath": number,
    "ath_date": "string",
    "drawdown_from_ath_pct": number,
    "months_since_halving": number
  },

  "macro_context": {
    "fed_rate": "string (ex: 3.25-3.50%)",
    "fed_outlook": "string (résumé politique monétaire)",
    "global_liquidity_trend": "expanding | contracting | neutral",
    "sp500_trend": "string",
    "dxy_trend": "string",
    "key_macro_events": ["liste d'événements macro récents importants"]
  },

  "onchain_signals": {
    "etf_flows_weekly": "string (ex: +1.2B$ ou -500M$)",
    "whale_accumulation": "string (résumé)",
    "miner_behavior": "string",
    "exchange_reserves_trend": "increasing | decreasing | stable",
    "key_onchain_insights": ["liste d'insights"]
  },

  "regulatory_update": {
    "us_regulation": "string (résumé)",
    "global_regulation": "string (résumé)",
    "key_regulatory_events": ["liste d'événements"]
  },

  "institutional_views": [
    {
      "firm": "string",
      "target": "string",
      "timeframe": "string",
      "stance": "bullish | bearish | neutral",
      "key_argument": "string"
    }
  ],

  "scenarios": {
    "pessimiste": {
      "probability_pct": number,
      "top_usd": number,
      "bottom_low_usd": number,
      "bottom_high_usd": number,
      "end_year_usd": number,
      "drawdown_max_pct": number,
      "bottom_timing": "string",
      "next_cycle_top_usd": number,
      "context": "string (2-3 phrases)",
      "narrative": "string (3-5 phrases)",
      "aligned_analysts": ["liste"],
      "key_conditions": ["liste de conditions requises"]
    },
    "neutre": {
      "probability_pct": number,
      "top_current_cycle_usd": number,
      "bottom_low_usd": number,
      "bottom_high_usd": number,
      "end_year_usd": number,
      "drawdown_max_pct": number,
      "bottom_timing": "string",
      "next_cycle_top_low_usd": number,
      "next_cycle_top_high_usd": number,
      "next_cycle_top_timing": "string",
      "context": "string",
      "narrative": "string",
      "aligned_analysts": ["liste"],
      "key_conditions": ["liste"]
    },
    "optimiste": {
      "probability_pct": number,
      "top_low_usd": number,
      "top_high_usd": number,
      "bottom_low_usd": number,
      "bottom_high_usd": number,
      "end_year_usd": number,
      "drawdown_max_pct": number,
      "bottom_timing": "string",
      "super_cycle_target_usd": number,
      "context": "string",
      "narrative": "string",
      "aligned_analysts": ["liste"],
      "key_conditions": ["liste"]
    }
  },

  "consensus": {
    "market_sentiment": "string (résumé du sentiment)",
    "institutional_consensus_range": "string (ex: 150k-250k$)",
    "fair_value_median_usd": number,
    "key_debate": "string (le débat principal du moment)"
  },

  "risks": {
    "downside": [
      {"risk": "string", "description": "string", "probability": "low | medium | high"}
    ],
    "upside": [
      {"risk": "string", "description": "string", "probability": "low | medium | high"}
    ]
  },

  "trajectory_projections": {
    "labels": ["liste de 10 labels temporels ex: 'ATH Oct25', 'Actuel', 'Été 2026', ..."],
    "pessimiste": [10 numbers],
    "neutre": [10 numbers],
    "optimiste": [10 numbers]
  },

  "weekly_summary": "string (résumé de 3-5 phrases des points clés de cette semaine)"
}
"""


def load_previous_analysis():
    """Load the most recent analysis for changelog comparison."""
    if not INDEX_FILE.exists():
        return None
    try:
        index = json.loads(INDEX_FILE.read_text())
        if index and len(index) > 0:
            latest_file = DATA_DIR / index[0]["filename"]
            if latest_file.exists():
                return json.loads(latest_file.read_text())
    except Exception:
        pass
    return None


def generate_analysis():
    """Call Claude API with web search to generate Bitcoin analysis."""
    print("Calling Claude API with web search...")

    previous = load_previous_analysis()
    context_msg = ""
    if previous:
        prev_price = previous.get("market_snapshot", {}).get("price_usd", "N/A")
        prev_date = previous.get("generated_at", "N/A")
        context_msg = f"\n\nCONTEXTE : La dernière analyse date du {prev_date}, le prix était de {prev_price}$. Compare avec les données actuelles."

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=16000,
        tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 15}],
        messages=[
            {
                "role": "user",
                "content": ANALYSIS_PROMPT + context_msg
            }
        ]
    )

    # Extract JSON from response
    result_text = ""
    for block in response.content:
        if block.type == "text":
            result_text += block.text

    # Try to parse JSON - handle potential markdown wrapping
    json_str = result_text.strip()
    if json_str.startswith("```"):
        # Remove markdown code fences
        lines = json_str.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        json_str = "\n".join(lines)

    try:
        analysis = json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}")
        print(f"Raw response (first 500 chars): {json_str[:500]}")
        # Try to find JSON in the response
        start = json_str.find("{")
        end = json_str.rfind("}") + 1
        if start >= 0 and end > start:
            analysis = json.loads(json_str[start:end])
        else:
            raise ValueError("Could not extract valid JSON from Claude response")

    # Override months_since_halving with correct calculation
    # Bitcoin halving date: April 19, 2024
    from datetime import date
    halving_date = date(2024, 4, 19)
    today = date.today()
    months_since = (today.year - halving_date.year) * 12 + (today.month - halving_date.month)
    if today.day < halving_date.day:
        months_since -= 1
    if "market_snapshot" in analysis:
        analysis["market_snapshot"]["months_since_halving"] = months_since

    return analysis


def generate_changelog(current, previous):
    """Generate a changelog comparing current analysis to previous."""
    if not previous:
        return [{"type": "info", "message": "Première analyse — pas de comparaison disponible."}]

    changes = []
    curr_snap = current.get("market_snapshot", {})
    prev_snap = previous.get("market_snapshot", {})

    # Price change
    if curr_snap.get("price_usd") and prev_snap.get("price_usd"):
        p_curr, p_prev = curr_snap["price_usd"], prev_snap["price_usd"]
        pct = round((p_curr - p_prev) / p_prev * 100, 1)
        changes.append({
            "metric": "Prix BTC",
            "from": p_prev, "to": p_curr,
            "change_pct": pct,
            "direction": "up" if pct > 0 else "down"
        })

    # Drawdown
    if curr_snap.get("drawdown_from_ath_pct") and prev_snap.get("drawdown_from_ath_pct"):
        d_curr, d_prev = curr_snap["drawdown_from_ath_pct"], prev_snap["drawdown_from_ath_pct"]
        changes.append({
            "metric": "Drawdown depuis ATH",
            "from": d_prev, "to": d_curr,
            "change_pts": round(d_curr - d_prev, 1),
            "direction": "up" if d_curr > d_prev else "down"
        })

    # Fear & Greed
    if curr_snap.get("fear_greed_index") and prev_snap.get("fear_greed_index"):
        f_curr, f_prev = curr_snap["fear_greed_index"], prev_snap["fear_greed_index"]
        changes.append({
            "metric": "Fear & Greed",
            "from": f_prev, "to": f_curr,
            "change_pts": f_curr - f_prev,
            "direction": "up" if f_curr > f_prev else "down"
        })

    # Scenario probabilities shifts
    for scenario in ["pessimiste", "neutre", "optimiste"]:
        curr_sc = current.get("scenarios", {}).get(scenario, {})
        prev_sc = previous.get("scenarios", {}).get(scenario, {})
        curr_prob = curr_sc.get("probability_pct", 0)
        prev_prob = prev_sc.get("probability_pct", 0)
        if abs(curr_prob - prev_prob) >= 2:
            changes.append({
                "metric": f"Probabilité {scenario}",
                "from": prev_prob, "to": curr_prob,
                "change_pts": round(curr_prob - prev_prob, 1),
                "direction": "up" if curr_prob > prev_prob else "down"
            })

    # Bottom estimates shifts
    for scenario in ["pessimiste", "neutre", "optimiste"]:
        curr_sc = current.get("scenarios", {}).get(scenario, {})
        prev_sc = previous.get("scenarios", {}).get(scenario, {})
        curr_bot = curr_sc.get("bottom_low_usd", 0)
        prev_bot = prev_sc.get("bottom_low_usd", 0)
        if prev_bot and abs(curr_bot - prev_bot) / prev_bot > 0.05:
            changes.append({
                "metric": f"Bottom {scenario} (bas)",
                "from": prev_bot, "to": curr_bot,
                "change_pct": round((curr_bot - prev_bot) / prev_bot * 100, 1),
                "direction": "up" if curr_bot > prev_bot else "down"
            })

    return changes


def save_analysis(analysis, changelog):
    """Save analysis to JSON file and update index."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    filename = f"{today}.json"

    # Add changelog to analysis
    analysis["changelog"] = changelog

    # Save analysis file
    filepath = DATA_DIR / filename
    filepath.write_text(json.dumps(analysis, indent=2, ensure_ascii=False))
    print(f"Analysis saved to {filepath}")

    # Update index
    index = []
    if INDEX_FILE.exists():
        try:
            index = json.loads(INDEX_FILE.read_text())
        except Exception:
            index = []

    entry = {
        "date": today,
        "filename": filename,
        "generated_at": analysis.get("generated_at", datetime.now(timezone.utc).isoformat()),
        "price_usd": analysis.get("market_snapshot", {}).get("price_usd"),
        "fear_greed": analysis.get("market_snapshot", {}).get("fear_greed_index"),
        "drawdown_pct": analysis.get("market_snapshot", {}).get("drawdown_from_ath_pct"),
        "summary": analysis.get("weekly_summary", "")
    }

    # Remove existing entry for today if re-running
    index = [e for e in index if e["date"] != today]
    index.insert(0, entry)

    INDEX_FILE.write_text(json.dumps(index, indent=2, ensure_ascii=False))
    print(f"Index updated ({len(index)} analyses)")

    return filepath


def main():
    print("=" * 60)
    print("BTC Scenario Analysis Generator")
    print(f"Date: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print("=" * 60)

    # Load previous for comparison
    previous = load_previous_analysis()
    if previous:
        print(f"Previous analysis found: {previous.get('generated_at', 'unknown')}")
    else:
        print("No previous analysis found (first run)")

    # Generate new analysis
    analysis = generate_analysis()
    print("Analysis generated successfully")

    # Generate changelog
    changelog = generate_changelog(analysis, previous)
    print(f"Changelog: {len(changelog)} changes detected")

    # Save
    filepath = save_analysis(analysis, changelog)
    print(f"\nDone! Analysis saved to: {filepath}")

    # Print summary
    snap = analysis.get("market_snapshot", {})
    print(f"\n--- Summary ---")
    print(f"BTC Price: ${snap.get('price_usd', 'N/A'):,.0f}")
    print(f"Drawdown: {snap.get('drawdown_from_ath_pct', 'N/A')}%")
    print(f"Fear & Greed: {snap.get('fear_greed_index', 'N/A')}")
    print(f"Weekly: {analysis.get('weekly_summary', 'N/A')}")


if __name__ == "__main__":
    main()
