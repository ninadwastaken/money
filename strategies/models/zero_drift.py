"""Zero-drift lognormal baseline; 60-second settlement-average approximation.
Method: github.com/schen9999/btc-15m-engine/backend/app/core/math_engine.py
Uses minute-return EWMA rather than the source's second-return EWMA.
"""
import math
from statistics import NormalDist


def probability(spot, target, seconds_left, sigma, averaging_seconds=60):
    values = (spot, target, seconds_left, sigma)
    if not all(math.isfinite(x) for x in values) or spot <= 0 or target <= 0 or sigma < 0:
        raise ValueError('Invalid model inputs')
    if averaging_seconds not in (0,60) or seconds_left <= 0:
        raise ValueError('Unsupported settlement window or expiry')
    if seconds_left < averaging_seconds:
        raise ValueError('Final minute requires observed partial settlement average')
    if sigma == 0:
        return float(spot >= target)
    variance_time = seconds_left - 2*averaging_seconds/3
    drift_time = seconds_left - averaging_seconds/2
    z = (math.log(spot/target) - .5*sigma*sigma*drift_time)/(sigma*math.sqrt(variance_time))
    return min(1-1e-9, max(1e-9, NormalDist().cdf(z)))


def volatility(prices, decay=.94):
    if len(prices) < 61 or not 0 < decay < 1:
        raise ValueError('Need at least 60 minute returns and valid decay')
    returns = [math.log(b/a) for a,b in zip(prices, prices[1:])]
    variance = returns[0]**2
    for r in returns[1:]:
        variance = decay*variance + (1-decay)*r*r
    return math.sqrt(variance/60)
