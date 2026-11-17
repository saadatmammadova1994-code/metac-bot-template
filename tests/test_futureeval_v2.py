import math
import unittest

from guard_logic import guard_binary_probability
from forecast_core import brier, log_loss, aggregate_binary
from chronological_backtest import evaluate


class TestFutureEvalV2(unittest.TestCase):
    def test_disabled_guard_is_exact_identity(self):
        for p in (0.0, 0.01, 0.5, 0.99, 1.0):
            self.assertEqual(guard_binary_probability(p), p)

    def test_shrink_toward_anchor(self):
        self.assertLess(guard_binary_probability(0.8, shrink=0.2), 0.8)

    def test_invalid_inputs(self):
        for x in (float("nan"), float("inf"), -0.1, 1.1):
            with self.assertRaises(ValueError):
                guard_binary_probability(x)
        with self.assertRaises(ValueError):
            guard_binary_probability(0.5, shrink=-0.1)

    def test_brier(self):
        self.assertAlmostEqual(brier(0.8, 1), 0.04)

    def test_log_loss(self):
        self.assertAlmostEqual(log_loss(0.5, 1), math.log(2))

    def test_pool_duplicate_equal(self):
        self.assertAlmostEqual(aggregate_binary([0.7, 0.7]), 0.7)

    def test_holdout_requires_minimum_rows(self):
        with self.assertRaises(ValueError):
            evaluate([])


if __name__ == "__main__":
    unittest.main()
