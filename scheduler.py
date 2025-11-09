from estimator import estimate_co2

REGION_LATENCY = {"Northern":70,"Western":90,"Southern":80,"Eastern":120}
REGION_COST = {"Northern":3.0,"Western":2.8,"Southern":3.2,"Eastern":2.5}
REGIONS = list(REGION_LATENCY.keys())

def choose_region(duration_s, sla_ms=2000):
    """Hybrid carbon-aware scheduler."""
    best, best_score = None, float("inf")
    for region in REGIONS:
        latency = REGION_LATENCY[region]
        if latency > sla_ms: continue
        _, co2 = estimate_co2(duration_s, region, mode="hybrid")
        cost = REGION_COST[region]
        score = 0.7*co2 + 0.2*(latency/1000.0) + 0.1*cost
        if score < best_score:
            best_score, best = score, {
                "region": region, "co2_g": round(co2,6),
                "latency_ms": latency, "score": round(score,6)
            }
    return best

if __name__ == "__main__":
    print(choose_region(2.5, 2000))
