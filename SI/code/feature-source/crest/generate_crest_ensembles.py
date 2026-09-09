#!/usr/bin/env python3
"""Generate resumable ten-conformer CREST ensembles for P7 and CMC-Por."""

from __future__ import annotations

import argparse
import concurrent.futures
import datetime as dt
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import tempfile
import threading
import time
from pathlib import Path
from typing import Any

from rdkit import Chem
from rdkit.Chem import AllChem


ROOT = Path(__file__).resolve().parents[3]
DATED_DIR = Path(__file__).resolve().parent
P7_RECORDS = ROOT / "data/jacs_2025/stage2/curated-reaction-records.jsonl"
P7_REPORTS = ROOT / "data/jacs_2025/stage1/panel"
CMC_RECORDS = ROOT / "data/expansion/catalyst_rerun/cmcpor/stage2-records.jsonl"
CMC_REPORTS = ROOT / "data/expansion/catalyst_rerun/cmcpor/stage1/reports"
DEFAULT_OUTPUT = DATED_DIR / "crest-10-conformers"
DEFAULT_CREST = ROOT / ".chem-env/bin/crest"
DEFAULT_XTB = ROOT / ".chem-env/bin/xtb"
LOG_LOCK = threading.Lock()
ENERGY_RE = re.compile(r"TOTAL ENERGY\s+(-?\d+(?:\.\d+)?)", re.IGNORECASE)
HARTREE_TO_KCAL_MOL = 627.509474
GAS_CONSTANT_KCAL_MOL_K = 0.00198720425864083


def now() -> str:
    return dt.datetime.now(dt.UTC).isoformat()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def emit(output: Path, event: str, **fields: Any) -> None:
    payload = {"timestamp": now(), "event": event, **fields}
    line = json.dumps(payload, sort_keys=True)
    with LOG_LOCK:
        output.mkdir(parents=True, exist_ok=True)
        with (output / "progress.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(line + "\n")
        with (output / "run.log").open("a", encoding="utf-8") as stream:
            stream.write(f"{payload['timestamp']} {event} " + " ".join(f"{key}={value}" for key, value in fields.items()) + "\n")
        print(line, flush=True)


def report_substrate_id(report: dict[str, Any]) -> str | None:
    ids = report.get("pose_generation_run", {}).get("substrate_ids", [])
    if len(ids) == 1:
        return ids[0]
    return report.get("substrate_record", {}).get("substrate_id")


def inventory() -> list[dict[str, Any]]:
    domains = [
        ("p7", P7_RECORDS, P7_REPORTS, "fe-p7-cl"),
        ("cmcpor", CMC_RECORDS, CMC_REPORTS, "cmcpor-fecl"),
    ]
    work = []
    for domain, records_path, reports_dir, catalyst_id in domains:
        records = {row["substrate_id"]: row for row in read_jsonl(records_path) if row["catalyst_id"] == catalyst_id}
        reports: dict[str, tuple[Path, dict[str, Any]]] = {}
        for report_path in sorted(reports_dir.glob("*.json")):
            report = read_json(report_path)
            substrate_id = report_substrate_id(report)
            if substrate_id in records:
                reports[substrate_id] = (report_path, report)
        missing = sorted(set(records) - set(reports))
        if missing:
            raise ValueError(f"{domain}: missing Stage 1 reports for {missing}")
        for substrate_id in sorted(records):
            report_path, report = reports[substrate_id]
            poses = sorted(report["pose_records"], key=lambda row: int(row["score_rank"]))
            if not poses:
                raise ValueError(f"{domain}/{substrate_id}: Stage 1 report has no poses")
            work.append(
                {
                    "domain": domain,
                    "catalyst_id": catalyst_id,
                    "substrate_id": substrate_id,
                    "reaction_id": records[substrate_id]["reaction_id"],
                    "temperature_c": records[substrate_id].get("condition", {}).get("temperature_c"),
                    "nitrene_smiles": records[substrate_id]["structure"]["nitrene_smiles"],
                    "azide_smiles": records[substrate_id]["structure"]["azide_smiles"],
                    "report_path": report_path,
                    "seed_pose_id": poses[0]["pose_id"],
                }
            )
    return work


def write_rdkit_seed(smiles: str, path: Path, seed: int) -> str:
    molecule = Chem.MolFromSmiles(smiles)
    if molecule is None:
        raise ValueError(f"Could not parse seed SMILES: {smiles}")
    molecule = Chem.AddHs(molecule)
    parameters = AllChem.ETKDGv3()
    parameters.randomSeed = seed
    if AllChem.EmbedMolecule(molecule, parameters) != 0:
        raise ValueError(f"Could not embed seed SMILES: {smiles}")
    if AllChem.MMFFHasAllMoleculeParams(molecule):
        AllChem.MMFFOptimizeMolecule(molecule)
        force_field = "MMFF94"
    else:
        AllChem.UFFOptimizeMolecule(molecule)
        force_field = "UFF"
    conformer = molecule.GetConformer()
    lines = [str(molecule.GetNumAtoms()), f"RDKit {force_field} seed from aryl-azide precursor"]
    for atom in molecule.GetAtoms():
        point = conformer.GetAtomPosition(atom.GetIdx())
        lines.append(f"{atom.GetSymbol():<2} {point.x: .10f} {point.y: .10f} {point.z: .10f}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return force_field


def parse_multi_xyz(path: Path) -> list[dict[str, Any]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    structures = []
    index = 0
    while index < len(lines):
        if not lines[index].strip():
            index += 1
            continue
        atom_count = int(lines[index].strip())
        if index + atom_count + 1 >= len(lines):
            raise ValueError(f"{path}: truncated XYZ block at line {index + 1}")
        comment = lines[index + 1]
        atoms = lines[index + 2 : index + 2 + atom_count]
        if len(atoms) != atom_count:
            raise ValueError(f"{path}: incomplete XYZ atom block")
        structures.append({"atom_count": atom_count, "comment": comment, "atoms": atoms})
        index += atom_count + 2
    return structures


def write_multi_xyz(path: Path, structures: list[dict[str, Any]]) -> None:
    text = "".join(
        f"{row['atom_count']}\n{row['comment']}\n" + "\n".join(row["atoms"]) + "\n"
        for row in structures
    )
    path.write_text(text, encoding="utf-8")


def conformer_energy(comment: str) -> float | None:
    try:
        return float(comment.split()[0])
    except (ValueError, IndexError):
        return None


def boltzmann_population(energies_hartree: list[float], temperature_c: float | None) -> dict[str, Any]:
    """Return stable normalized populations for the retained substrate minima."""
    temperature_k = 298.15 if temperature_c is None else float(temperature_c) + 273.15
    if temperature_k <= 0:
        raise ValueError(f"Invalid ensemble temperature: {temperature_k} K")
    if not energies_hartree:
        return {
            "temperature_k": temperature_k,
            "temperature_source": "default_298.15_K" if temperature_c is None else "experimental_condition",
            "effective_conformer_count": 0.0,
            "conformers": [],
        }
    minimum = min(energies_hartree)
    deltas = [(energy - minimum) * HARTREE_TO_KCAL_MOL for energy in energies_hartree]
    raw_weights = [math.exp(-delta / (GAS_CONSTANT_KCAL_MOL_K * temperature_k)) for delta in deltas]
    denominator = sum(raw_weights)
    probabilities = [weight / denominator for weight in raw_weights]
    return {
        "temperature_k": temperature_k,
        "temperature_source": "default_298.15_K" if temperature_c is None else "experimental_condition",
        "effective_conformer_count": 1.0 / sum(probability * probability for probability in probabilities),
        "conformers": [
            {
                "conformer_index": index,
                "energy_hartree": energy,
                "relative_energy_kcal_mol": delta,
                "boltzmann_probability": probability,
            }
            for index, (energy, delta, probability) in enumerate(
                zip(energies_hartree, deltas, probabilities, strict=True), start=1
            )
        ],
    }


def gfn2_rerank(
    structures: list[dict[str, Any]], work: Path, xtb: Path, threads: int,
    timeout_seconds: int, output: Path, domain: str, substrate_id: str,
) -> list[tuple[float, dict[str, Any]]]:
    ranked = []
    for index, structure in enumerate(structures, start=1):
        conformer_dir = work / "gfn2-rerank" / f"{index:04d}"
        conformer_dir.mkdir(parents=True, exist_ok=True)
        conformer_path = conformer_dir / "conformer.xyz"
        write_multi_xyz(conformer_path, [structure])
        try:
            completed = subprocess.run(
            [str(xtb), conformer_path.name, "--gfn", "2", "--alpb", "ether", "--chrg", "0", "--uhf", "0"],
                cwd=conformer_dir,
                text=True,
                capture_output=True,
                check=False,
                timeout=timeout_seconds,
                env={**os.environ, "OMP_NUM_THREADS": str(threads)},
            )
        except subprocess.TimeoutExpired:
            completed = None
        matches = ENERGY_RE.findall(completed.stdout) if completed is not None else []
        if completed is not None and completed.returncode == 0 and matches:
            ranked.append((float(matches[-1]), structure))
        if index % 10 == 0 or index == len(structures):
            emit(
                output, "rerank_progress", domain=domain, substrate_id=substrate_id,
                attempted=index, total=len(structures), successful=len(ranked),
            )
    return sorted(ranked, key=lambda row: row[0])


def success_metadata(path: Path, expected_count: int) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        value = read_json(path)
    except (json.JSONDecodeError, OSError):
        return None
    if value.get("status") in {"success", "underfilled"} and value.get("retained_conformer_count", 0) > 0:
        return value
    return None


def run_one(
    item: dict[str, Any], output: Path, crest: Path, xtb: Path, retain_count: int,
    threads: int, timeout_seconds: int, quick_flag: str, sampling_method: str,
) -> dict[str, Any]:
    domain = item["domain"]
    substrate_id = item["substrate_id"]
    destination = output / domain / substrate_id
    metadata_path = destination / "metadata.json"
    existing = success_metadata(metadata_path, retain_count)
    if existing is not None:
        emit(output, "skip_complete", domain=domain, substrate_id=substrate_id, retained=existing["retained_conformer_count"])
        return existing
    destination.mkdir(parents=True, exist_ok=True)
    emit(output, "substrate_start", domain=domain, substrate_id=substrate_id, seed_pose_id=item["seed_pose_id"])
    started = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix=f"crest-{domain}-{substrate_id}-") as temporary:
        work = Path(temporary)
        seed = work / "input.xyz"
        deterministic_seed = int(hashlib.sha256(f"{domain}:{substrate_id}".encode()).hexdigest()[:7], 16)
        seed_force_field = write_rdkit_seed(item["azide_smiles"], seed, deterministic_seed)
        command = [
            str(crest), seed.name, f"--{sampling_method}", "--alpb", "ether", "--chrg", "0", "--uhf", "0",
            quick_flag, "--legacy", "--nocross", "--ewin", "30", "-T", str(threads), "--xnam", str(xtb),
        ]
        stdout_path = destination / "crest.stdout.log"
        stderr_path = destination / "crest.stderr.log"
        timed_out = False
        with stdout_path.open("w", encoding="utf-8") as stdout, stderr_path.open("w", encoding="utf-8") as stderr:
            process = subprocess.Popen(
                command, cwd=work, stdout=stdout, stderr=stderr, text=True,
                env={**os.environ, "OMP_NUM_THREADS": str(threads)},
            )
            next_heartbeat = 30.0
            while process.poll() is None:
                elapsed = time.perf_counter() - started
                if elapsed >= timeout_seconds:
                    process.terminate()
                    try:
                        process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()
                    timed_out = True
                    break
                if elapsed >= next_heartbeat:
                    stdout.flush()
                    phase = "crest_running"
                    if stdout_path.exists():
                        recent = stdout_path.read_text(encoding="utf-8", errors="replace").splitlines()[-120:]
                        markers = [
                            line.strip() for line in recent
                            if line.strip().startswith(("Starting Meta-MD", "Starting MD", "Optimizing all", "CREGEN>", "MTD Iteration"))
                        ]
                        if markers:
                            phase = markers[-1]
                    emit(
                        output, "substrate_heartbeat", domain=domain, substrate_id=substrate_id,
                        elapsed_seconds=round(elapsed, 1), phase=phase,
                    )
                    next_heartbeat += 30.0
                time.sleep(1.0)
            returncode = 124 if timed_out else int(process.returncode)
        wall_seconds = time.perf_counter() - started
        ensemble_path = work / "crest_conformers.xyz"
        if returncode == 0 and ensemble_path.exists():
            structures = parse_multi_xyz(ensemble_path)
            emit(
                output, "crest_search_finish", domain=domain, substrate_id=substrate_id,
                generated_unique=len(structures), search_wall_seconds=round(wall_seconds, 3),
            )
            ranked = gfn2_rerank(
                structures, work, xtb, threads, timeout_seconds, output, domain, substrate_id
            )
            retained = []
            for energy, structure in ranked[:retain_count]:
                retained.append({**structure, "comment": f"{energy:.12f} GFN2-xTB ALPB(ether) Eh"})
            write_multi_xyz(destination / "conformers.xyz", retained)
            energies = [energy for energy, _ in ranked[:retain_count]]
            populations = boltzmann_population(energies, item["temperature_c"])
            write_json(
                destination / "gfn2-rerank.json",
                {
                    "attempted": len(structures),
                    "successful": len(ranked),
                    "retained_energies_hartree": energies,
                    "population_model": populations,
                },
            )
            if (work / "crest.energies").exists():
                shutil.copy2(work / "crest.energies", destination / "crest.energies")
            status = "success" if len(retained) == retain_count else "underfilled"
        else:
            structures, retained, energies = [], [], []
            populations = boltzmann_population([], item["temperature_c"])
            status = "timeout" if timed_out else "failed"
            for diagnostic in work.glob("*.log"):
                shutil.copy2(diagnostic, destination / f"internal-{diagnostic.name}")
        result = {
            "schema_version": "crest-ten-conformer-result-v1",
            "status": status,
            "domain": domain,
            "catalyst_id": item["catalyst_id"],
            "substrate_id": substrate_id,
            "reaction_id": item["reaction_id"],
            "temperature_c": item["temperature_c"],
            "nitrene_smiles": item["nitrene_smiles"],
            "azide_smiles": item["azide_smiles"],
            "seed_pose_id": item["seed_pose_id"],
            "seed_generation": f"deterministic RDKit ETKDGv3 plus {seed_force_field}",
            "seed_random_seed": deterministic_seed,
            "stage1_report_path": str(item["report_path"].relative_to(ROOT)),
            "method": f"CREST iMTD quick/{sampling_method.upper()} legacy external-xTB sampling; no genetic crossing; 30 kcal/mol search window; GFN2-xTB/ALPB ether reranking",
            "molecular_charge": 0,
            "unpaired_electrons": 0,
            "requested_conformer_count": retain_count,
            "generated_unique_conformer_count": len(structures),
            "retained_conformer_count": len(retained),
            "retained_comment_energies": energies,
            "population_model": populations,
            "wall_seconds": wall_seconds,
            "returncode": returncode,
            "timed_out": timed_out,
            "threads": threads,
            "command": command,
            "conformers_xyz_path": str((destination / "conformers.xyz").relative_to(ROOT)) if retained else None,
            "conformers_xyz_sha256": sha256(destination / "conformers.xyz") if retained else None,
            "stdout_log_path": str(stdout_path.relative_to(ROOT)),
            "stderr_log_path": str(stderr_path.relative_to(ROOT)),
        }
        write_json(metadata_path, result)
    emit(
        output, "substrate_finish", domain=domain, substrate_id=substrate_id, status=status,
        generated=len(structures), retained=len(retained), wall_seconds=round(wall_seconds, 3),
    )
    return result


def build_manifest(output: Path, items: list[dict[str, Any]], results: list[dict[str, Any]], args: argparse.Namespace) -> dict[str, Any]:
    counts: dict[str, int] = {}
    for result in results:
        counts[result["status"]] = counts.get(result["status"], 0) + 1
    manifest = {
        "schema_version": "crest-ten-conformer-manifest-v1",
        "created_at": now(),
        "scope": {"p7": sum(row["domain"] == "p7" for row in items), "cmcpor": sum(row["domain"] == "cmcpor" for row in items)},
        "requested_substrate_count": len(items),
        "requested_conformers_per_substrate": args.retain_count,
        "status_counts": counts,
        "retained_conformer_total": sum(row.get("retained_conformer_count", 0) for row in results),
        "aggregate_worker_seconds": sum(row.get("wall_seconds", 0.0) for row in results),
        "method": f"aryl-azide precursor; CREST 3.0.2 legacy iMTD quick/{args.sampling_method.upper()}; no genetic crossing; 30 kcal/mol search window; GFN2-xTB/ALPB ether reranking; charge 0; UHF 0",
        "results": [
            {key: row.get(key) for key in ("domain", "substrate_id", "status", "retained_conformer_count", "wall_seconds", "conformers_xyz_path")}
            for row in results
        ],
    }
    write_json(output / "manifest.json", manifest)
    return manifest


def main(args: argparse.Namespace) -> int:
    output = args.output if args.output.is_absolute() else ROOT / args.output
    items = inventory()
    if args.domain != "all":
        items = [row for row in items if row["domain"] == args.domain]
    if args.substrate_id:
        items = [row for row in items if row["substrate_id"] == args.substrate_id]
    if args.limit is not None:
        items = items[: args.limit]
    emit(output, "run_start", substrate_count=len(items), workers=args.workers, retain_count=args.retain_count)
    execute = lambda item: run_one(
        item, output, args.crest, args.xtb, args.retain_count, args.threads, args.timeout_seconds,
        args.quick_flag, args.sampling_method,
    )
    if args.workers == 1:
        results = [execute(item) for item in items]
    else:
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
            results = list(executor.map(execute, items))
    manifest = build_manifest(output, items, results, args)
    emit(output, "run_finish", status_counts=manifest["status_counts"], retained_total=manifest["retained_conformer_total"])
    return 0 if set(manifest["status_counts"]) <= {"success", "underfilled"} else 1


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser()
    value.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    value.add_argument("--crest", type=Path, default=DEFAULT_CREST)
    value.add_argument("--xtb", type=Path, default=DEFAULT_XTB)
    value.add_argument("--domain", choices=("all", "p7", "cmcpor"), default="all")
    value.add_argument("--substrate-id")
    value.add_argument("--limit", type=int)
    value.add_argument("--retain-count", type=int, default=10)
    value.add_argument("--workers", type=int, default=4)
    value.add_argument("--threads", type=int, default=1)
    value.add_argument("--timeout-seconds", type=int, default=1800)
    value.add_argument("--quick-flag", choices=("--quick", "--squick", "--mquick"), default="--quick")
    value.add_argument("--sampling-method", choices=("gfn2", "gfn1", "gfnff"), default="gfn2")
    return value


if __name__ == "__main__":
    raise SystemExit(main(parser().parse_args()))
