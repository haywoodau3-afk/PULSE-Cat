#!/usr/bin/env python3

import importlib.util
import unittest
from pathlib import Path

import numpy


PATH = Path(__file__).with_name("p7_crest_xtb_benchmark.py")
SPEC = importlib.util.spec_from_file_location("p7_crest_xtb_benchmark", PATH)
module = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(module)


class P7CrestXtbBenchmarkTest(unittest.TestCase):
    def test_geometry_features_are_rotation_invariant(self) -> None:
        symbols = ["C", "C", "H"]
        coordinates = numpy.asarray([[0.0, 0.0, 0.0], [2.0, 0.0, 0.0], [0.0, 1.0, 0.0]])
        rotation = numpy.asarray([[0.0, -1.0, 0.0], [1.0, 0.0, 0.0], [0.0, 0.0, 1.0]])
        first = module.geometry_features(symbols, coordinates)
        second = module.geometry_features(symbols, coordinates @ rotation.T)
        self.assertEqual(first.keys(), second.keys())
        for key in first:
            self.assertAlmostEqual(first[key], second[key])

    def test_electronic_features_extract_frontier_orbitals(self) -> None:
        payload = {
            "total energy": -2.0,
            "electronic energy": -2.5,
            "HOMO-LUMO gap / eV": 3.0,
            "dipole / a.u.": [3.0, 4.0, 0.0],
            "partial charges": [-0.2, 0.2],
            "atomic dipole moments": [[1.0, 0.0, 0.0], [0.0, 2.0, 0.0]],
            "number of electrons": 4,
            "orbital energies / eV": [-8.0, -5.0, -2.0],
            "fractional occupation": [2.0, 2.0, 0.0],
        }
        features = module.electronic_features(payload, ["N", "C"])
        self.assertEqual(features["crest_xtb.homo_ev"], -5.0)
        self.assertEqual(features["crest_xtb.lumo_ev"], -2.0)
        self.assertEqual(features["crest_xtb.dipole_norm_au"], 5.0)


if __name__ == "__main__":
    unittest.main()
