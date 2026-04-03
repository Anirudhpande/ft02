"""
Gaussian Mixture Model Engine

Generates realistic multimodal distributions for business features
such as revenue ranges, loan sizes, and business age clusters.

Uses sklearn GaussianMixture for fitting and sampling.
"""

import numpy as np
from sklearn.mixture import GaussianMixture


class GMMSampler:
    """
    A pre-configured GMM sampler that generates values from
    a multimodal distribution defined by component parameters.
    """

    def __init__(self, means: list, covariances: list, weights: list,
                 clip_min: float = None, clip_max: float = None):
        """
        Initialize GMM with specified component parameters.

        Args:
            means: List of component means
            covariances: List of component variances
            weights: List of component weights (must sum to 1)
            clip_min: Minimum allowed value (clips output)
            clip_max: Maximum allowed value (clips output)
        """
        self.n_components = len(means)
        self.clip_min = clip_min
        self.clip_max = clip_max

        # Build sklearn GMM with fixed parameters
        self.gmm = GaussianMixture(
            n_components=self.n_components,
            covariance_type="diag",
            max_iter=1,  # We set params directly, no fitting needed
        )

        # Manually set the parameters
        self.gmm.means_ = np.array(means).reshape(-1, 1)
        self.gmm.covariances_ = np.array(covariances).reshape(-1, 1)
        self.gmm.weights_ = np.array(weights)
        self.gmm.precisions_cholesky_ = np.sqrt(
            1.0 / self.gmm.covariances_
        )
        self.gmm.converged_ = True
        self.gmm.n_iter_ = 1

    def sample(self, n_samples: int = 1) -> np.ndarray:
        """
        Generate samples from the GMM distribution.

        Args:
            n_samples: Number of samples to generate

        Returns:
            1D numpy array of sampled values
        """
        samples, _ = self.gmm.sample(n_samples)
        samples = samples.flatten()

        if self.clip_min is not None:
            samples = np.maximum(samples, self.clip_min)
        if self.clip_max is not None:
            samples = np.minimum(samples, self.clip_max)

        return samples

    def sample_one(self) -> float:
        """Generate a single sample."""
        return float(self.sample(1)[0])


def create_revenue_sampler(params: dict) -> GMMSampler:
    """
    Create a GMM sampler for monthly revenue generation.

    Args:
        params: Dict with 'means', 'covariances', 'weights' lists

    Returns:
        Configured GMMSampler
    """
    return GMMSampler(
        means=params["means"],
        covariances=params["covariances"],
        weights=params["weights"],
        clip_min=10000,   # Minimum monthly revenue: ₹10,000
        clip_max=5000000, # Maximum monthly revenue: ₹50,00,000
    )


def create_age_sampler(params: dict) -> GMMSampler:
    """
    Create a GMM sampler for business age.

    Args:
        params: Dict with 'mean' and 'std'

    Returns:
        Configured GMMSampler with 2 components
    """
    # Two-component model: young startups + established businesses
    return GMMSampler(
        means=[params["mean"] - 1, params["mean"] + 5],
        covariances=[params["std"] ** 2, (params["std"] * 1.5) ** 2],
        weights=[0.6, 0.4],
        clip_min=params["min"],
        clip_max=params["max"],
    )


def create_loan_size_sampler(mean: float, std: float) -> GMMSampler:
    """
    Create a GMM sampler for loan sizes with 3 tiers.

    Args:
        mean: Base mean loan size
        std: Base standard deviation

    Returns:
        Configured GMMSampler
    """
    return GMMSampler(
        means=[mean * 0.3, mean, mean * 2.5],
        covariances=[(std * 0.5) ** 2, std ** 2, (std * 2) ** 2],
        weights=[0.45, 0.40, 0.15],
        clip_min=10000,
        clip_max=10000000,
    )
