"""
Copula-Based Correlation Engine

Implements Gaussian copula for generating correlated multivariate samples.
Ensures realistic inter-variable dependencies (e.g., purchases correlated
with sales, business age correlated with turnover).
"""

import numpy as np
from scipy import stats


class GaussianCopula:
    """
    Gaussian Copula for generating correlated samples from
    arbitrary marginal distributions.

    Process:
    1. Define correlation matrix in the normal space
    2. Generate correlated normal samples
    3. Transform to uniform via Φ (normal CDF)
    4. Transform uniform to target marginals via inverse CDF
    """

    def __init__(self, correlation_matrix: np.ndarray):
        """
        Args:
            correlation_matrix: n×n positive-definite correlation matrix
        """
        self.correlation_matrix = np.array(correlation_matrix)
        self.n_vars = self.correlation_matrix.shape[0]

        # Validate
        assert self.correlation_matrix.shape[0] == self.correlation_matrix.shape[1], \
            "Correlation matrix must be square"
        eigvals = np.linalg.eigvalsh(self.correlation_matrix)
        if np.any(eigvals < -1e-10):
            # Force positive semi-definite
            self.correlation_matrix = self._nearest_psd(self.correlation_matrix)

    def _nearest_psd(self, matrix):
        """Find nearest positive semi-definite matrix."""
        eigvals, eigvecs = np.linalg.eigh(matrix)
        eigvals = np.maximum(eigvals, 0)
        return eigvecs @ np.diag(eigvals) @ eigvecs.T

    def generate_correlated_uniforms(self, n_samples: int) -> np.ndarray:
        """
        Generate correlated uniform samples via Gaussian copula.

        Args:
            n_samples: Number of sample vectors to generate

        Returns:
            n_samples × n_vars array of correlated uniform [0,1] values
        """
        # Step 1: Generate correlated normal samples
        mean = np.zeros(self.n_vars)
        normal_samples = np.random.multivariate_normal(
            mean, self.correlation_matrix, size=n_samples
        )

        # Step 2: Transform to uniform via normal CDF
        uniform_samples = stats.norm.cdf(normal_samples)

        return uniform_samples

    def generate_samples(self, n_samples: int,
                         marginals: list) -> np.ndarray:
        """
        Generate correlated samples with specified marginal distributions.

        Args:
            n_samples: Number of samples
            marginals: List of scipy.stats distributions (one per variable)
                       Each must have a .ppf() method (inverse CDF)

        Returns:
            n_samples × n_vars array of correlated samples
        """
        assert len(marginals) == self.n_vars, \
            f"Need {self.n_vars} marginals, got {len(marginals)}"

        uniforms = self.generate_correlated_uniforms(n_samples)
        samples = np.zeros_like(uniforms)

        for i, marginal in enumerate(marginals):
            samples[:, i] = marginal.ppf(uniforms[:, i])

        return samples


# ─── Pre-built correlation structures ──────────────────────────────────────────

def get_purchase_sales_copula() -> GaussianCopula:
    """
    Copula for purchase-sales correlation.
    Purchases are highly correlated with sales (ρ=0.85).
    """
    corr = np.array([
        [1.0, 0.85],
        [0.85, 1.0],
    ])
    return GaussianCopula(corr)


def get_business_profile_copula() -> GaussianCopula:
    """
    Copula for business profile variables:
    [age, turnover, loan_count, vendor_count]

    Correlations:
    - age ↔ turnover: moderate positive (0.5)
    - age ↔ loan_count: moderate positive (0.4)
    - turnover ↔ vendor_count: moderate positive (0.55)
    - age ↔ vendor_count: weak positive (0.3)
    """
    corr = np.array([
        [1.00, 0.50, 0.40, 0.30],  # age
        [0.50, 1.00, 0.35, 0.55],  # turnover
        [0.40, 0.35, 1.00, 0.20],  # loan_count
        [0.30, 0.55, 0.20, 1.00],  # vendor_count
    ])
    return GaussianCopula(corr)


def generate_correlated_purchases(monthly_sales: list,
                                  is_fraud: bool = False) -> list:
    """
    Generate monthly purchases correlated with monthly sales.

    Args:
        monthly_sales: List of 36 monthly sales values
        is_fraud: If True, introduces mismatch patterns

    Returns:
        List of 36 monthly purchase values
    """
    n = len(monthly_sales)
    sales_arr = np.array(monthly_sales)

    if is_fraud:
        # Fraudulent: low correlation, random mismatch
        noise = np.random.normal(0, 0.3, n)
        ratio = np.random.uniform(0.1, 0.3) + noise
        ratio = np.clip(ratio, 0.05, 1.5)
        purchases = sales_arr * ratio
    else:
        # Legitimate: high correlation with realistic ratio
        base_ratio = np.random.uniform(0.50, 0.80)
        noise = np.random.normal(0, 0.05, n)
        ratio = base_ratio + noise
        ratio = np.clip(ratio, 0.30, 0.95)
        purchases = sales_arr * ratio

    return [max(0, float(p)) for p in purchases]
