#!/usr/bin/env python3

import importlib.util
import unittest
from pathlib import Path

import numpy as np


MODULE_PATH = Path(__file__).with_name("pose_probability.py")
SPEC = importlib.util.spec_from_file_location("pose_probability", MODULE_PATH)
pose_probability = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(pose_probability)


class PoseProbabilityTest(unittest.TestCase):
    def test_boltzmann_weights_are_normalized_and_favor_low_energy(self) -> None:
        weights = pose_probability.boltzmann_weights([-10.0, -9.999], [0.5, 0.5], 333.15)
        self.assertAlmostEqual(float(weights.sum()), 1.0)
        self.assertGreater(weights[0], weights[1])

    def test_prior_degeneracy_affects_equal_energy_population(self) -> None:
        weights = pose_probability.boltzmann_weights([-10.0, -10.0], [0.8, 0.2], 333.15)
        np.testing.assert_allclose(weights, [0.8, 0.2])

    def test_uncertain_summary_is_reproducible(self) -> None:
        left = pose_probability.uncertain_population_summary([-10.0, -9.999], [0.5, 0.5], 333.15, draws=50)
        right = pose_probability.uncertain_population_summary([-10.0, -9.999], [0.5, 0.5], 333.15, draws=50)
        self.assertEqual(left, right)
        self.assertAlmostEqual(sum(left["mean_weights"]), 1.0)
        self.assertGreaterEqual(left["effective_pose_count_kish"], 1.0)

    def test_reaction_ready_kernel_rewards_close_linear_clear_geometry(self) -> None:
        good = (
            pose_probability.sigmoid((3.0 - 2.5) / 0.30)
            * pose_probability.sigmoid((175.0 - 145.0) / 8.0)
            * pose_probability.sigmoid((1.8 - 1.25) / 0.15)
        )
        poor = (
            pose_probability.sigmoid((3.0 - 4.0) / 0.30)
            * pose_probability.sigmoid((110.0 - 145.0) / 8.0)
            * pose_probability.sigmoid((1.0 - 1.25) / 0.15)
        )
        self.assertGreater(good, poor)


if __name__ == "__main__":
    unittest.main()
