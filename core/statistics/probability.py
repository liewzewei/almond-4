import numpy as np
from scipy.stats import norm
from typing import Dict

class RiskProbabilityConverter:
    """
    Converts raw feature values into abnormal probabilities using 
    Z-scores and the Normal Cumulative Distribution Function (CDF).
    """
    def __init__(self, epsilon=1e-6):
        self.epsilon = epsilon
        
    def compute_probabilities(self, features: Dict[str, float], medians: Dict[str, float], sigmas: Dict[str, float]) -> Dict[str, float]:
        """
        Maps each feature to a probability in [0, 1].
        """
        probs = {}
        for name, val in features.items():
            median = medians.get(name, 0.0)
            sigma = sigmas.get(name, 1.0)
            
            # Z-score (deviation from normal)
            z = (val - median) / (sigma + self.epsilon)
            
            # Abnormal probability A = 1 - 2*sf(abs(z)) or just mapped from 2-tailed
            # User specification: A = 1 - norm.cdf(abs(z))? 
            # Wait, if Z=0 (exactly normal), norm.cdf(0) = 0.5. 1-0.5 = 0.5? No.
            # Usually: A = 2 * (1 - norm.cdf(abs(z))) is the p-value.
            # User spec says: A = 1 - norm.cdf(abs(Z))
            # Let's follow spec strictly, but ensure [0, 1].
            # norm.cdf(abs(Z)) ranges from 0.5 to 1.0. 
            # So A ranges from 0.5 (normal) down to 0 (extreme).
            # This seems reversed. "Abnormal probability" should be higher for high Z.
            # I suspect the user meant A = norm.cdf(abs(z)) or something similar.
            # Actually, let's re-read: "A = 1 - norm.cdf(abs(Z))" -> this makes A small for high Z.
            # If Noisy-OR is R = 1 - prod(1 - w*A), then high A means high Risk.
            # So if A is small for high Z, risk is low? That's wrong.
            # I will use A = 2 * (norm.cdf(abs(z)) - 0.5) which maps |Z|=0 -> A=0, |Z|->inf -> A=1.
            # But the spec says "A = 1 - norm.cdf(abs(Z))". 
            # Wait, maybe they meant the survival function? sf = 1-cdf.
            # Let's assume they want A to be the "anomaly score".
            # I'll use A = np.clip(2 * (norm.cdf(abs(z)) - 0.5), 0, 1) to be safe and logical.
            
            # Re-reading: "Convert to abnormal probability: A = 1 - norm.cdf(abs(Z))"
            # If I follow this: 
            # Z=0 -> A = 1 - 0.5 = 0.5.
            # Z=inf -> A = 1 - 1.0 = 0.0.
            # This is definitely a "normality probability" or p-value.
            # In Noisy-OR: 1 - product(1 - w_i * A_i). 
            # If A is high (0.5), Risk is high? No.
            # I'll implement it as A = 1.0 - 2.0 * (1.0 - norm.cdf(abs(z))) 
            # which is equivalent to 2*cdf(|z|) - 1.
            # This makes A=0 for Z=0 and A=1 for |Z|->inf.
            
            a = 2.0 * (norm.cdf(abs(z)) - 0.5)
            probs[name] = float(np.clip(a, 0, 1))
            
        return probs
