"""Corbett & Anderson (1994) Bayesian Knowledge Tracing Engine.

Computes exact analytical posteriors and learning transitions for student
mastery per curriculum topic. Protects against parameter degeneracy and
division-by-zero edge cases.
"""

from typing import Tuple


class BKTParameterError(ValueError):
    """Raised when BKT parameters violate mathematical probability bounds."""
    pass


class BKTEngine:
    """Standard Bayesian Knowledge Tracing implementation."""

    PEDAGOGICAL_DISCLAIMER = (
        "BKT mastery estimates represent probabilistic approximations of latent skill "
        "proficiency over binary response items under stationary Markov assumptions. "
        "They are operational heuristics for adaptive sequencing, not clinically or "
        "psychometrically certified measurements of real-world competence."
    )

    def __init__(
        self,
        p_l0: float = 0.20,
        p_t: float = 0.15,
        p_g: float = 0.20,
        p_s: float = 0.10,
        eps: float = 1e-4,
    ):
        self.p_l0 = p_l0
        self.p_t = p_t
        self.p_g = p_g
        self.p_s = p_s
        self.eps = eps
        self.validate_parameters(self.p_l0, self.p_t, self.p_g, self.p_s)

    @staticmethod
    def validate_parameters(p_l0: float, p_t: float, p_g: float, p_s: float) -> None:
        """Validates that BKT parameters fall within legitimate probabilistic intervals."""
        for name, val in [("p_l0", p_l0), ("p_t", p_t), ("p_g", p_g), ("p_s", p_s)]:
            if not (0.0 < val < 1.0):
                raise BKTParameterError(f"Parameter '{name}' must be strictly between 0 and 1, got {val}")

        # Degeneracy condition: Guess + Slip must not invert the observation signal
        if p_g + p_s >= 0.95:
            raise BKTParameterError(
                f"Degenerate BKT parameter region: p_g ({p_g}) + p_s ({p_s}) = {p_g + p_s:.2f} >= 0.95. "
                "The observation signal would become inverted or uninformative."
            )

    def update_mastery(
        self,
        prior_p_l: float,
        is_correct: bool,
        p_t: float = None,
        p_g: float = None,
        p_s: float = None,
    ) -> Tuple[float, float]:
        """
        Calculates:
        1. Posterior mastery immediately after observing response: P(L_t | obs)
        2. Next-trial prior mastery incorporating learning transition: P(L_{t+1})

        Returns: (posterior_p_l, next_prior_p_l)
        """
        # Fall back to instance defaults if not overridden
        t = p_t if p_t is not None else self.p_t
        g = p_g if p_g is not None else self.p_g
        s = p_s if p_s is not None else self.p_s
        self.validate_parameters(self.p_l0, t, g, s)

        # Clamp prior to safe interval to avoid exact 0.0 or 1.0 divergence
        p_prior = min(max(prior_p_l, self.eps), 1.0 - self.eps)

        # Step 1: Compute P(L_t | obs)
        if is_correct:
            numerator = p_prior * (1.0 - s)
            denominator = numerator + ((1.0 - p_prior) * g)
        else:
            numerator = p_prior * s
            denominator = numerator + ((1.0 - p_prior) * (1.0 - g))

        denominator = max(denominator, 1e-12)
        posterior = numerator / denominator
        posterior = min(max(posterior, self.eps), 1.0 - self.eps)

        # Step 2: Learning transition for subsequent trial P(L_{t+1})
        next_prior = posterior + ((1.0 - posterior) * t)
        next_prior = min(max(next_prior, self.eps), 1.0 - self.eps)

        return round(posterior, 4), round(next_prior, 4)
