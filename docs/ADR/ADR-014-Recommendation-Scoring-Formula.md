# ADR-014: Recommendation Scoring Formula

**Status:** Proposed  
**Date:** 2026-06-28  
**Sprint:** Week 9 – Context Engine v2.0  
**Author:** Cognify Technical Co-founder & CTO  

---

## Context

To make recommendation ranking deterministic, pedagogically sound, and highly explainable, we require a standardized mathematical scoring model. This formula must combine inputs from all primary Cognify modules and apply real-time adjustments based on environmental context signals.

---

## Decision

The Context Engine v2.0 recommendation scoring is divided into two phases: **Base Cognitive Prioritization** (Additive Weighting) and **Environmental Context Calibration** (Multiplicative Adjustment).

### Phase 1: Base Cognitive Score ($S_{base}$)

For a given student $s$ and concept $c$, the base priority score is a weighted linear combination of six normalized indicators:

$$S_{base}(s, c) = w_{mem} \cdot M_{risk}(s, c) + w_{apd} \cdot P_{impt}(c) + w_{mcp} \cdot S_{sev}(s, c) + w_{qqi} \cdot Q_{cal}(c) + w_{teach} \cdot T_{prior}(s, c) + w_{exam} \cdot E_{wt}(c)$$

Subject to the constraint:
$$w_{mem} + w_{apd} + w_{mcp} + w_{qqi} + w_{teach} + w_{exam} = 1.0$$

#### Component Formulations:

1. **Memory Risk Indicator ($M_{risk}$):**
   Derived from the student's retrieval strength $R(t)$ from the Educational Memory Engine:
   $$M_{risk}(s, c) = 1.0 - R_c(t)$$
   If $c$ has no record, $M_{risk} = 0.5$ (neutral uncertainty).

2. **APD Prerequisite Importance ($P_{impt}$):**
   Derived from the Automatic Prerequisite Discovery graph. Calculated as the out-degree density of concept $c$ (how many other concepts depend on it):
   $$P_{impt}(c) = \min\left(1.0, \frac{\text{Out-degree of } c \text{ with relation } \text{'prerequisite\_of'}}{5}\right)$$

3. **Misconception Severity ($S_{sev}$):**
   If student $s$ has an active misconception cluster associated with concept $c$:
   $$S_{sev}(s, c) = \text{Severity Weight of } mcp(c)$$
   Mapped values:
   - `Critical` = 1.0
   - `High` = 0.75
   - `Medium` = 0.5
   - `Low` = 0.25
   - No active misconception = 0.0

4. **QQI Calibration Indicator ($Q_{cal}$):**
   Represents the calibration density of the concept. If the concept has highly calibrated questions (high QQI confidence and delta stability), we prioritize diagnostic assessment to maintain high-precision feedback loops:
   $$Q_{cal}(c) = \text{Average QQI Score of questions in } c / 100.0$$

5. **Teacher Priority ($T_{prior}$):**
   Derived from manual intervention notes or reviewer flags stored in `teacher_notes`:
   $$T_{prior}(s, c) = \min\left(1.0, \text{Count of active teacher notes targeting } c \times 0.5\right)$$

6. **Exam/Curriculum Weight ($E_{wt}$):**
   Derived from the assessment blueprints:
   $$E_{wt}(c) = \frac{\text{Questions allocated to topic } c \text{ in blueprint}}{\text{Total blueprint question count}}$$

---

### Phase 2: Environmental Context Calibration ($S_{final}$)

The base score is calibrated by environmental context multipliers based on the student's device type, network quality, time of day, and class size:

$$S_{final}(s, c) = S_{base}(s, c) \times M_{device}(D, A) \times M_{network}(N, A) \times M_{time}(H, A) \times M_{class}(S, A)$$

Where:
- $D \in \{\text{mobile}, \text{tablet}, \text{desktop}\}$ is the active device.
- $N \in \{\text{poor}, \text{average}, \text{good}, \text{excellent}\}$ is the network quality.
- $H \in [0, 23]$ is the session start hour.
- $S \ge 1$ is the concurrent class size.
- $A \in \{\text{Remediation}, \text{Practice}, \text{Review}\}$ is the recommended action type.

#### Multiplier Matrices:

1. **Device Multipliers ($M_{device}$):**
   | Action Type | Mobile | Tablet | Desktop |
   |---|---|---|---|
   | **Remediation** (Heavy Text/Video) | 0.6 | 0.9 | 1.0 |
   | **Practice** (Interactive Tasks) | 0.8 | 1.0 | 1.0 |
   | **Review** (Flashcards/Micro-quizzes) | 1.2 | 1.1 | 1.0 |

2. **Network Multipliers ($M_{network}$):**
   | Action Type | Poor | Average | Good | Excellent |
   |---|---|---|---|---|
   | **Remediation** (Rich Assets) | 0.2 | 0.7 | 1.0 | 1.0 |
   | **Practice** (Standard Assets) | 0.7 | 0.9 | 1.0 | 1.0 |
   | **Review** (Text Only) | 1.1 | 1.0 | 1.0 | 1.0 |

3. **Time-of-Day Multipliers ($M_{time}$):**
   - **Late Night (21:00 - 05:00):** Prioritize Reviews ($1.2$), penalize heavy new Remediation ($0.5$).
   - **School Hours (08:00 - 15:00):** Prioritize Remediation ($1.1$) and Practice ($1.1$).
   - **Standard Off-hours:** $1.0$ for all actions.

4. **Class-Size Multipliers ($M_{class}$):**
   - **Large Class ($S \ge 20$):** Prioritize independent Practice ($1.1$), penalize actions requiring high teacher oversight ($0.7$).
   - **Small/Individual Class ($S < 20$):** Prioritize complex Remediation ($1.1$).

---

## Consequences

### Positive
- **Explainability:** Calculating contributions separately allows the system to generate an audit log showing exactly why a recommendation was created:
  > "Recommendation for concept 'Algebra' generated (Score: 0.82). Base priority (0.78) driven by high Memory Risk (0.80) and active Misconception (severity High, 0.75). Calibrated upward (x1.2) due to Mobile device micro-practice suitability."
- **Configurability:** All weights $w_i$ and multiplier matrices are stored in `context_recommendations_config`, enabling updates without code changes.

### Negative
- **Calibration Complexity:** Extreme environment parameters could scale the final score above $1.0$ or below $0.0$.
- **Mitigation:** We apply a strict clamping function: $S_{final} = \min(1.0, \max(0.0, S_{final}))$.
