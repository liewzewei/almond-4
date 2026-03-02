# Risk Calculation Logic

Based on the codebase analysis, the risk calculation for vehicles is a sophisticated multi-step pipeline orchestrated by the [RiskEngine](file:///c:/Users/liewz/Documents/GitHub/enam-tujuh/almond-4/core/engine.py#12-104) ([core/engine.py](file:///c:/Users/liewz/Documents/GitHub/enam-tujuh/almond-4/core/engine.py)). It evaluates anomalous vehicle behavior through research-grade motion features in BEV (Bird's Eye View) space, adapts to "normal" driving patterns on the fly, and computes an overall, smoothed risk score per vehicle. 

Here is a detailed breakdown of the complete process step-by-step:

## 1. Data Transformation and Tracking ([RiskEngine](file:///c:/Users/liewz/Documents/GitHub/enam-tujuh/almond-4/core/engine.py#12-104))
For each incoming video frame:
1. **Homography Estimation**: The system updates the homography matrix which accurately maps camera view pixels to physical 2D Bird's Eye View coordinates.
2. **Trajectory Tracking**: The `TrajectoryManager` updates the historical trajectory of active vehicles (up to 5 seconds) mapped into this physical BEV space.

## 2. Feature Extraction ([FeatureEngine](file:///c:/Users/liewz/Documents/GitHub/enam-tujuh/almond-4/core/motion/features.py#8-103))
For each vehicle track, physical motion features are calculated at every frame ([core/motion/features.py](file:///c:/Users/liewz/Documents/GitHub/enam-tujuh/almond-4/core/motion/features.py)). There are five core features extracted from the smoothed BEV coordinates over the past 3-second window:
* **SDLP (Standard Deviation of Lateral Position)**: Measures how much the vehicle drifts from its primary longitudinal path. High SDLP indicates weaving.
* **Lateral Band Energy**: Extracts the frequency composition of lateral movement and calculates the percentage of energy in high frequencies (upper 40%). High values hint at jerky/unstable steering corrections.
* **Steering Entropy**: Evaluates the predictability of the heading angle. Calculates the Shannon entropy over heading differences; elevated entropy signifies irregular and erratic steering behavior.
* **Speed CV (Coefficient of Variation)**: Calculated as the ratio of standard deviation in speed over average speed. Higher CV means the vehicle speed fluctuates abnormally (stop-and-go behavior or unsteady foot on pedal).
* **Jerk RMS**: The Root Mean Square of jerk (the temporal derivative of acceleration). Large jerk values typically represent harsh braking or aggressive acceleration.

## 3. Dynamic Baseline Adaptation ([OnlineRobustBaseline](file:///c:/Users/liewz/Documents/GitHub/enam-tujuh/almond-4/core/statistics/robust_baseline.py#6-62))
In typical environments, "normal" driving can vary. The system constantly builds and adapts its definition of "normal" for each feature dynamically using an [OnlineRobustBaseline](file:///c:/Users/liewz/Documents/GitHub/enam-tujuh/almond-4/core/statistics/robust_baseline.py#6-62) ([core/statistics/robust_baseline.py](file:///c:/Users/liewz/Documents/GitHub/enam-tujuh/almond-4/core/statistics/robust_baseline.py)).
* It collects normal samples for each feature up to `max_samples=500` (excluding data where the vehicle's `risk_score` is already $\geq 0.6$).
* It computes the **Median** and the **Sigma** via Median Absolute Deviation (MAD), producing robust statistics:
  * `Sigma = 1.4826 * MAD` (approximating standard deviation but less affected by extreme outliers).

## 4. Probability Mapping ([RiskProbabilityConverter](file:///c:/Users/liewz/Documents/GitHub/enam-tujuh/almond-4/core/statistics/probability.py#5-59))
Raw feature values are converted to an "abnormal probability" score distributed continuously between `0` and `1` using a Normal Cumulative Distribution Function (CDF) mapping ([core/statistics/probability.py](file:///c:/Users/liewz/Documents/GitHub/enam-tujuh/almond-4/core/statistics/probability.py)).
1. A **Z-score** is calculated: `Z = (Value - Median) / Sigma`.
2. The probability of anomaly is mapped: $A = 2 \times (\text{norm.cdf}(|Z|) - 0.5)$.
    * A Z-score close to 0 (normal) maps to ~ `0.0`.
    * A very high absolute Z-score (anomalous) scales asymptotically toward `1.0`.

## 5. Risk Fusion (Noisy-OR Logic) ([RiskFusionEngine](file:///c:/Users/liewz/Documents/GitHub/enam-tujuh/almond-4/core/statistics/risk_fusion.py#5-69))
The five feature probabilities (`A_i`) are fused into a single unified risk score per vehicle ([core/statistics/risk_fusion.py](file:///c:/Users/liewz/Documents/GitHub/enam-tujuh/almond-4/core/statistics/risk_fusion.py)).
1. **Noisy-OR Combination**: Instead of a simple weighted average, the fusion uses a Noisy-OR model:  
   $R_{\text{raw}} = 1 - \prod_{i} (1 - w_i \times A_i)$  
   *The default weights are: SDLP (0.25), Steering Entropy (0.25), Lateral Band Energy (0.20), Speed CV (0.20), and Jerk RMS (0.10).*
   This model effectively means that if *any single feature* is exceptionally anomalous, the total risk score rapidly increases, treating different risk features as independent indicators of danger.
2. **Exponential Smoothing**: To prevent flickers/noise, the raw risk score is temporally smoothed:  
   $R_t = \alpha R_{\text{raw}} + (1 - \alpha) R_{t-1}$  
   *(Default factor $\alpha = 0.4$)*

## 6. Alert Handling
Finally, the system checks if the fused risk exceeds a specific hazard threshold ([alert_threshold](file:///c:/Users/liewz/Documents/GitHub/enam-tujuh/almond-4/core/engine.py#38-41), typically `0.85`). If the condition persists continuously for at least `1.5` seconds, the system flags the vehicle with an active alert (`is_alert = True`).
