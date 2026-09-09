#!/usr/bin/env python3

import importlib.util
import math
import tempfile
import unittest
from pathlib import Path


PATH = Path(__file__).with_name("generate_crest_ensembles.py")
SPEC = importlib.util.spec_from_file_location("generate_crest_ensembles", PATH)
module = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(module)


class CrestEnsembleTest(unittest.TestCase):
    def test_inventory_has_complete_requested_domains(self) -> None:
        rows = module.inventory()
        self.assertEqual(sum(row["domain"] == "p7" for row in rows), 40)
        self.assertEqual(sum(row["domain"] == "cmcpor" for row in rows), 50)

    def test_multi_xyz_round_trip_and_cap(self) -> None:
        rows = [
            {"atom_count": 2, "comment": f"{-1.0 + i * 0.1}", "atoms": ["H 0 0 0", "H 0 0 1"]}
            for i in range(12)
        ]
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "ensemble.xyz"
            module.write_multi_xyz(path, rows[:10])
            parsed = module.parse_multi_xyz(path)
        self.assertEqual(len(parsed), 10)
        self.assertEqual(module.conformer_energy(parsed[0]["comment"]), -1.0)

    def test_closed_shell_azide_seed_is_written(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "seed.xyz"
            method = module.write_rdkit_seed("N#N=Nc1ccccc1CC", path, 7)
            parsed = module.parse_multi_xyz(path)
        self.assertIn(method, {"MMFF94", "UFF"})
        self.assertEqual(len(parsed), 1)

    def test_boltzmann_population_is_normalized_and_temperature_aware(self) -> None:
        population = module.boltzmann_population([-10.0, -9.999], 60)
        probabilities = [row["boltzmann_probability"] for row in population["conformers"]]
        self.assertTrue(math.isclose(sum(probabilities), 1.0))
        self.assertEqual(population["temperature_k"], 333.15)
        self.assertGreater(probabilities[0], probabilities[1])
        self.assertGreaterEqual(population["effective_conformer_count"], 1.0)
        self.assertLessEqual(population["effective_conformer_count"], 2.0)


if __name__ == "__main__":
    unittest.main()
