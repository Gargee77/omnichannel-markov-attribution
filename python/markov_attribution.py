import os
from collections import defaultdict
import numpy as np
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv


START = "(start)"
CONV = "(conversion)"
NULL = "(null)"


def build_transition_counts(paths: list[list[str]], converted_flags: list[int]) -> dict[tuple[str, str], int]:
    """
    Count transitions for a first-order Markov chain.
    Each path is a sequence of channels like ["email","sms","push"].
    If converted_flags[i]==1 -> end at CONV else end at NULL.
    """
    counts = defaultdict(int)

    for seq, conv in zip(paths, converted_flags):
        if not seq:
            # no touches: start -> conversion/null
            counts[(START, CONV if conv else NULL)] += 1
            continue

        # start -> first
        counts[(START, seq[0])] += 1

        # internal transitions
        for a, b in zip(seq, seq[1:]):
            counts[(a, b)] += 1

        # last -> absorbing
        counts[(seq[-1], CONV if conv else NULL)] += 1

    return counts


def counts_to_prob_matrix(counts: dict[tuple[str, str], int]) -> tuple[list[str], np.ndarray]:
    states = sorted(set([s for s, _ in counts.keys()] + [t for _, t in counts.keys()]))
    idx = {s: i for i, s in enumerate(states)}

    mat = np.zeros((len(states), len(states)), dtype=float)

    # row-normalize
    row_sums = defaultdict(int)
    for (s, t), c in counts.items():
        row_sums[s] += c
    for (s, t), c in counts.items():
        mat[idx[s], idx[t]] = c / row_sums[s]

    return states, mat


def absorbing_conversion_probability(states: list[str], P: np.ndarray) -> float:
    """
    Probability of eventually reaching CONV from START.
    Works even if NULL is absent (all paths convert).
    """
    idx = {s: i for i, s in enumerate(states)}
    if START not in idx or CONV not in idx:
        return 0.0

    absorbing = [CONV]
    if NULL in idx:
        absorbing.append(NULL)

    transient = [s for s in states if s not in absorbing]

    # If there are no transient states, START must be absorbing-like
    if START in absorbing:
        return 1.0 if START == CONV else 0.0

    t_idx = {s: i for i, s in enumerate(transient)}
    a_idx = {s: i for i, s in enumerate(absorbing)}

    Q = np.zeros((len(transient), len(transient)))
    R = np.zeros((len(transient), len(absorbing)))

    for s in transient:
        for t in transient:
            Q[t_idx[s], t_idx[t]] = P[idx[s], idx[t]]
        for a in absorbing:
            R[t_idx[s], a_idx[a]] = P[idx[s], idx[a]]

    I = np.eye(len(transient))
    try:
        N = np.linalg.inv(I - Q)
    except np.linalg.LinAlgError:
        N = np.linalg.pinv(I - Q)

    B = N @ R

    if START in transient:
        # absorption into CONV (always index 0 because absorbing starts with CONV)
        return float(B[t_idx[START], a_idx[CONV]])

    return 0.0


def removal_effects(states: list[str], P: np.ndarray) -> dict[str, float]:
    """
    Standard Markov attribution via removal effect:
    effect(channel) = (p_base - p_removed(channel)) / p_base
    """
    base = absorbing_conversion_probability(states, P)
    if base <= 0:
        return {s: 0.0 for s in states}

    effects = {}
    for ch in states:
        if ch in (START, CONV, NULL):
            continue

        # Remove ch by redirecting any transition into ch to NULL,
        # and ch itself becomes unreachable effectively.
        states2 = [s for s in states if s != ch]
        idx = {s: i for i, s in enumerate(states)}
        idx2 = {s: i for i, s in enumerate(states2)}

        P2 = np.zeros((len(states2), len(states2)), dtype=float)

        for s in states2:
            row = np.zeros(len(states2), dtype=float)
            total = 0.0

            for t in states2:
                prob = P[idx[s], idx[t]]
                row[idx2[t]] += prob
                total += prob

            # Any probability mass that would have gone to removed state:
            # - send to NULL if it exists
            # - otherwise send to CONV (only-if-all-convert datasets) as a safe fallback
            prob_to_removed = P[idx[s], idx[ch]]
            if NULL in idx2:
                row[idx2[NULL]] += prob_to_removed
            elif CONV in idx2:
                row[idx2[CONV]] += prob_to_removed
            total += prob_to_removed

            # Renormalize row if totals drift (should already sum to 1)
            if total > 0:
                row = row / total

            P2[idx2[s], :] = row

        removed = absorbing_conversion_probability(states2, P2)
        effects[ch] = float((base - removed) / base)

    return effects


def main():
    load_dotenv()
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL not found in .env (repo root).")

    engine = create_engine(db_url)

    # Pull paths
    # Note: our synthetic data only has converted users in conversions table,
    # so we treat every row here as converted=1.
    query = """
      SELECT conversion_id, path, COALESCE(value, 0) AS value
      FROM v_paths_per_conversion
      WHERE path IS NOT NULL AND path <> ''
    """

    df = pd.read_sql(query, engine)

    # Parse paths
    paths = df["path"].astype(str).str.split(" > ").tolist()
    converted = [1] * len(paths)  # conversions table implies converted
    revenue = df["value"].astype(float).to_numpy()

    # Build chain and effects
    counts = build_transition_counts(paths, converted)
    states, P = counts_to_prob_matrix(counts)
    effects = removal_effects(states, P)

    # Convert effects into contributions
    # Weight contributions by total revenue for interpretability
    total_rev = float(revenue.sum()) if len(revenue) else 0.0
    effect_sum = sum(effects.values()) if effects else 0.0

    rows = []
    for ch, eff in effects.items():
        # If all effects are zero, split evenly to avoid divide by zero
        if effect_sum > 0:
            share = eff / effect_sum
        else:
            share = 1.0 / max(1, len(effects))

        contrib_rev = share * total_rev
        rows.append((ch, eff, share, contrib_rev))

    out = pd.DataFrame(rows, columns=["channel", "removal_effect", "share", "contribution_revenue"])
    out = out.sort_values("contribution_revenue", ascending=False).reset_index(drop=True)

    print("\nMarkov attribution (revenue-weighted):")
    print(out)

    # Write to attribution_results
    run_id = pd.Timestamp.utcnow().strftime("%Y%m%d_%H%M%S")
    model_name = "markov"

    with engine.begin() as conn:
        # store revenue contribution as 'contribution'
        for _, r in out.iterrows():
            conn.execute(
                text("""
                    INSERT INTO attribution_results (run_id, model_name, channel, contribution)
                    VALUES (:run_id, :model_name, :channel, :contribution)
                """),
                {
                    "run_id": run_id,
                    "model_name": model_name,
                    "channel": r["channel"],
                    "contribution": float(r["contribution_revenue"]),
                }
            )

    print(f"\nWrote Markov results to attribution_results with run_id={run_id}")


if __name__ == "__main__":
    main()