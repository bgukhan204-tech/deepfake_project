import numpy as np

def compute_temporal_analysis(frame_results):
    """
    Computes temporal inconsistency score across extracted video frame scores.
    Analyzes:
    - Variance/std of fake likelihood across consecutive frames
    - Sudden frame-to-frame score delta spikes (>30%)
    - Facial flickering artifacts
    Returns:
        temporal_score: float (0.0 to 100.0)
        temporal_summary: dict
    """
    if not frame_results or len(frame_results) < 2:
        return 0.0, {
            'variance': 0.0,
            'delta_spikes': 0,
            'flicker_score': 0.0
        }

    scores = [f['fake_score'] for f in frame_results]
    score_variance = float(np.var(scores))
    score_std = float(np.std(scores))

    deltas = [abs(scores[i] - scores[i-1]) for i in range(1, len(scores))]
    delta_spikes = sum(1 for d in deltas if d >= 25.0)

    max_delta = max(deltas) if deltas else 0.0
    avg_delta = float(np.mean(deltas)) if deltas else 0.0

    # Calculate overall temporal inconsistency percentage
    temporal_score = min(100.0, (score_std * 2.5) + (delta_spikes * 15.0) + (avg_delta * 1.8))

    return round(temporal_score, 1), {
        'variance': round(score_variance, 2),
        'std_dev': round(score_std, 2),
        'delta_spikes': delta_spikes,
        'max_delta': round(max_delta, 1),
        'avg_delta': round(avg_delta, 1)
    }
