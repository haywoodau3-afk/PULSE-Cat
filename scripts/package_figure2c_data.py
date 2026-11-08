#!/usr/bin/env python3
"""Package the retained Figure 2C pose, density, and overlay inputs.

The package is a copy, not a move. Source caches remain untouched. Each
substrate gets one multi-model XYZ trajectory containing the 200 retained
frozen-core assemblies, plus the corresponding Stage 2pp NPZ and SVG density
view. The shared-overlay directories point to/copy the 13 paired records.
"""

from __future__ import annotations

import csv
import hashlib
import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "figures" / "figure2c_data"
P7_DENSITY = ROOT / "data" / "jacs_2025" / "stage2pp" / "density"
P7_SVG = ROOT / "data" / "jacs_2025" / "stage2pp" / "svg"
P7_REPORTS = ROOT / "data" / "jacs_2025" / "stage1" / "panel"
CMC_DENSITY = ROOT / "data" / "expansion" / "catalyst_rerun" / "cmcpor_uff_full" / "stage2pp" / "density"
CMC_SVG = ROOT / "data" / "expansion" / "catalyst_rerun" / "cmcpor_uff_full" / "stage2pp" / "svg"
CMC_REPORTS = ROOT / "data" / "expansion" / "catalyst_rerun" / "cmcpor_uff_full" / "stage1" / "reports"
OVERLAY_INDEX = ROOT / "output" / "supporting-information" / "tables" / "si_pose_overlay_index.csv"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_xyz_frame(path: Path) -> tuple[int, list[str]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if len(lines) < 2:
        raise ValueError(f"Invalid XYZ file: {path}")
    atom_count = int(lines[0].strip())
    atoms = lines[2:2 + atom_count]
    if len(atoms) != atom_count:
        raise ValueError(f"XYZ atom count mismatch in {path}")
    return atom_count, atoms


def report_for(domain: str, substrate_id: str) -> Path:
    if domain == "fe_p7cl":
        return P7_REPORTS / f"stage-1-smoke-{substrate_id}.json"
    return CMC_REPORTS / f"stage-1-smoke-cmcpor-uff-{substrate_id}.json"


def source_artifacts(domain: str, substrate_id: str) -> tuple[Path, Path, Path]:
    if domain == "fe_p7cl":
        report = report_for(domain, substrate_id)
        density = P7_DENSITY / f"{substrate_id}.npz"
        svg = P7_SVG / f"{substrate_id}.svg"
    else:
        report = report_for(domain, substrate_id)
        density = CMC_DENSITY / f"{substrate_id}.npz"
        svg = CMC_SVG / f"{substrate_id}.svg"
    for path in (report, density, svg):
        if not path.exists():
            raise FileNotFoundError(path)
    return report, density, svg


def write_trajectory(report: dict, domain: str, substrate_id: str, destination: Path) -> list[dict[str, object]]:
    pose_records = sorted(report["pose_records"], key=lambda row: int(row["score_rank"]))
    if len(pose_records) != 200:
        raise ValueError(f"{domain}/{substrate_id}: expected 200 retained poses, found {len(pose_records)}")
    metadata: list[dict[str, object]] = []
    with destination.open("w", encoding="utf-8") as output:
        for frame, pose in enumerate(pose_records, start=1):
            source = ROOT / pose["fe_bound_assembly_xyz_path"]
            if not source.exists():
                raise FileNotFoundError(source)
            atom_count, atoms = read_xyz_frame(source)
            comment = (
                f"{domain} substrate={substrate_id} pose_id={pose['pose_id']} "
                f"frame={frame} selection_bucket={pose['selection_bucket']} "
                f"score_rank={pose['score_rank']} uff_pose_score={pose['uff_pose_score']:.6f}"
            )
            output.write(f"{atom_count}\n{comment}\n")
            output.write("\n".join(atoms))
            output.write("\n")
            metadata.append({
                "domain": domain,
                "substrate_id": substrate_id,
                "frame": frame,
                "pose_id": pose["pose_id"],
                "selection_bucket": pose["selection_bucket"],
                "score_rank": pose["score_rank"],
                "uff_pose_score": pose["uff_pose_score"],
                "fe_n_distance_angstrom": pose["fe_n_distance_angstrom"],
                "minimum_core_substrate_distance_angstrom": pose["minimum_core_substrate_distance_angstrom"],
                "source_xyz": pose["fe_bound_assembly_xyz_path"],
                "source_sha256": sha256(source),
            })
    return metadata


def copy_file(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def load_overlays() -> list[dict[str, str]]:
    with OVERLAY_INDEX.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def package() -> None:
    if OUT.exists() and any(OUT.iterdir()):
        raise SystemExit(f"Refusing to overwrite non-empty package: {OUT}")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "ensembles" / "fe_p7cl").mkdir(parents=True)
    (OUT / "ensembles" / "fe_cmcporcl").mkdir(parents=True)
    (OUT / "occupancy" / "fe_p7cl").mkdir(parents=True)
    (OUT / "occupancy" / "fe_cmcporcl").mkdir(parents=True)
    (OUT / "references").mkdir(parents=True)

    p7_ids = sorted(path.stem for path in P7_DENSITY.glob("*.npz"))
    cmc_ids = sorted(path.stem for path in CMC_DENSITY.glob("*.npz"))
    overlays = load_overlays()
    p7_to_pair = {row["p7_substrate_id"]: row["canonical_overlap_group"] for row in overlays}
    cmc_to_pair = {row["cmcpor_substrate_id"]: row["canonical_overlap_group"] for row in overlays}

    # Reference catalyst structures used by the frozen-core assemblies.
    reference_files = {
        "fe_p7cl_reference.xyz": ROOT / "data" / "jacs_2025" / "reference-geometry" / "jacs-p7-2B.xyz",
        "fe_cmcporcl_reference.xyz": ROOT / "data" / "expansion" / "catalyst_rerun" / "cmcpor" / "reference-geometry" / "4B1-cmcpor-reference-reordered.xyz",
    }
    for filename, source in reference_files.items():
        copy_file(source, OUT / "references" / filename)

    package_rows: list[dict[str, object]] = []
    pose_rows: list[dict[str, object]] = []
    for domain, ids in (("fe_p7cl", p7_ids), ("fe_cmcporcl", cmc_ids)):
        for substrate_id in ids:
            report_path, density_path, svg_path = source_artifacts(domain, substrate_id)
            report = json.loads(report_path.read_text(encoding="utf-8"))
            trajectory = OUT / "ensembles" / domain / f"{substrate_id}_all_200.xyz"
            pose_rows.extend(write_trajectory(report, domain, substrate_id, trajectory))
            density_out = OUT / "occupancy" / domain / f"{substrate_id}.npz"
            svg_out = OUT / "occupancy" / domain / f"{substrate_id}.svg"
            copy_file(density_path, density_out)
            copy_file(svg_path, svg_out)
            buckets = {row["selection_bucket"] for row in report["pose_records"]}
            package_rows.append({
                "domain": domain,
                "catalyst": "Fe(P7)Cl" if domain == "fe_p7cl" else "Fe(CMC-Por)Cl",
                "substrate_id": substrate_id,
                "shared_overlay_group": p7_to_pair.get(substrate_id, cmc_to_pair.get(substrate_id, "")),
                "pose_count": len(report["pose_records"]),
                "low_energy_count": sum(row["selection_bucket"] == "low_energy" for row in report["pose_records"]),
                "high_energy_count": sum(row["selection_bucket"] == "high_energy" for row in report["pose_records"]),
                "ensemble_xyz": str(trajectory.relative_to(OUT)),
                "occupancy_npz": str(density_out.relative_to(OUT)),
                "occupancy_svg": str(svg_out.relative_to(OUT)),
                "stage1_report": str(report_path.relative_to(ROOT)),
                "stage2pp_density_source": str(density_path.relative_to(ROOT)),
                "stage2pp_svg_source": str(svg_path.relative_to(ROOT)),
                "selection_buckets": ";".join(sorted(buckets)),
            })

    fieldnames = [
        "domain", "catalyst", "substrate_id", "shared_overlay_group", "pose_count",
        "low_energy_count", "high_energy_count", "ensemble_xyz", "occupancy_npz",
        "occupancy_svg", "stage1_report", "stage2pp_density_source", "stage2pp_svg_source",
        "selection_buckets",
    ]
    write_csv(OUT / "manifest.csv", package_rows, fieldnames)
    pose_fields = [
        "domain", "substrate_id", "frame", "pose_id", "selection_bucket", "score_rank",
        "uff_pose_score", "fe_n_distance_angstrom", "minimum_core_substrate_distance_angstrom",
        "source_xyz", "source_sha256",
    ]
    write_csv(OUT / "pose_metadata.csv", pose_rows, pose_fields)

    # Shared overlays are small, reviewable pair packages. They duplicate only
    # the 13 paired trajectories/density files so a pair can be handed to a
    # chemistry package without resolving the top-level manifest.
    overlay_rows: list[dict[str, object]] = []
    for index, row in enumerate(overlays, start=1):
        p7_id, cmc_id = row["p7_substrate_id"], row["cmcpor_substrate_id"]
        pair_dir = OUT / "shared_overlays" / f"{index:02d}_{p7_id}__{cmc_id}"
        pair_dir.mkdir(parents=True, exist_ok=True)
        p7_ensemble = OUT / "ensembles" / "fe_p7cl" / f"{p7_id}_all_200.xyz"
        cmc_ensemble = OUT / "ensembles" / "fe_cmcporcl" / f"{cmc_id}_all_200.xyz"
        p7_npz = OUT / "occupancy" / "fe_p7cl" / f"{p7_id}.npz"
        cmc_npz = OUT / "occupancy" / "fe_cmcporcl" / f"{cmc_id}.npz"
        p7_svg = OUT / "occupancy" / "fe_p7cl" / f"{p7_id}.svg"
        cmc_svg = OUT / "occupancy" / "fe_cmcporcl" / f"{cmc_id}.svg"
        for source, name in ((p7_ensemble, f"fe_p7cl_{p7_id}_all_200.xyz"), (cmc_ensemble, f"fe_cmcporcl_{cmc_id}_all_200.xyz"), (p7_npz, f"fe_p7cl_{p7_id}.npz"), (cmc_npz, f"fe_cmcporcl_{cmc_id}.npz"), (p7_svg, f"fe_p7cl_{p7_id}.svg"), (cmc_svg, f"fe_cmcporcl_{cmc_id}.svg")):
            copy_file(source, pair_dir / name)
        overlay_rows.append({
            "overlay_index": index,
            "canonical_overlap_group": row["canonical_overlap_group"],
            "p7_substrate_id": p7_id,
            "cmcpor_substrate_id": cmc_id,
            "pair_directory": str(pair_dir.relative_to(OUT)),
            "p7_xyz": f"fe_p7cl_{p7_id}_all_200.xyz",
            "cmcpor_xyz": f"fe_cmcporcl_{cmc_id}_all_200.xyz",
            "p7_npz": f"fe_p7cl_{p7_id}.npz",
            "cmcpor_npz": f"fe_cmcporcl_{cmc_id}.npz",
            "p7_svg": f"fe_p7cl_{p7_id}.svg",
            "cmcpor_svg": f"fe_cmcporcl_{cmc_id}.svg",
        })
        (pair_dir / "README.md").write_text(
            f"# Shared overlay {index:02d}: {p7_id} vs {cmc_id}\n\n"
            f"Canonical shared-substrate identity:\n\n`{row['canonical_overlap_group']}`\n\n"
            "The two multi-model XYZ files contain the same substrate identity sampled in the two catalyst environments. "
            "The NPZ files are the numerical Stage 2pp occupancy fields; the SVG files are the corresponding rendered views.\n",
            encoding="utf-8",
        )
    write_csv(OUT / "shared_overlay_manifest.csv", overlay_rows, list(overlay_rows[0]))

    (OUT / "occupancy_grid.json").write_text(json.dumps({
        "coordinate_convention": "azimuth_free_cylindrical_nitrene_transferred_h_axis",
        "z_edges_angstrom": [-8.0 + 0.5 * index for index in range(41)],
        "rho_edges_angstrom": [0.0 + 0.5 * index for index in range(21)],
        "views": ["nitrene", "activation", "n_to_h", "h_to_n"],
        "channels": ["all_heavy", "carbon", "hetero", "halogen", "hydrogen", "reactive_c", "reactive_h"],
        "strata": ["top_100", "bottom_100", "all_200", "top_minus_bottom"],
        "occupancy_type": "vdw_scaled_gaussian_atom_occupancy",
        "catalyst_atoms_in_density_fields": False,
        "pose_weighting": "equal_total_weight_per_geometry_cluster_within_stratum",
    }, indent=2) + "\n", encoding="utf-8")

    readme = """# Figure 2C data package

This folder contains the source data needed to redraw the three visual layers
of Figure 2C:

1. `ensembles/`: multi-model XYZ trajectories for the 200 retained frozen-core
   catalyst-bound poses for every record (41 Fe(P7)Cl and 50 Fe(CMC-Por)Cl).
2. `occupancy/`: the numerical Stage 2pp occupancy arrays (`.npz`) and their
   matching rendered spatial-density views (`.svg`).
3. `shared_overlays/`: self-contained pair folders for the 13 canonical
   substrate identities present in both catalyst datasets.

## How to use the files

- In a chemistry viewer, open any `*_all_200.xyz` as a multi-model trajectory
  or ensemble. Each frame is one retained Fe-bound assembly. The comment line
  stores the substrate ID, pose ID, UFF rank, UFF score, and low/high-energy
  selection bucket.
- Use `manifest.csv` to map each substrate to its XYZ trajectory and occupancy
  files. Use `pose_metadata.csv` when filtering or recoloring frames by UFF
  stratum or pose score.
- For a shared-substrate overlay, open the two XYZ trajectories in one viewer
  and use the matching `.svg` or `.npz` files from the same
  `shared_overlays/NN_<p7>__<cmcpor>/` folder.
- The `.npz` arrays are numerical occupancy fields, not native molecular
  coordinates. They contain Stage 2pp fields and profiles; use the matching
  SVG for a ready-made view or load the arrays with NumPy in a plotting script.

## Interpretation and provenance

Each substrate has 200 retained poses: 100 low-UFF and 100 high-UFF poses after
validity and clash screening. The XYZ files are copied from the retained
frozen-core assemblies; no structures were generated or altered by this
packaging step. Occupancy fields summarize sampled spatial occupancy. They are
not electron density, transition structures, Boltzmann populations, or
experimentally assigned selectivity-determining interactions.

The package-level mappings are in `manifest.csv` and
`shared_overlay_manifest.csv`. Catalyst reference structures are in
`references/`. The axis convention and NPZ key vocabulary are in
`occupancy_grid.json`.
"""
    (OUT / "README.md").write_text(readme, encoding="utf-8")

    package_manifest = {
        "schema": "figure2c-data-package-v1",
        "record_count": len(package_rows),
        "pose_count": len(pose_rows),
        "shared_overlay_count": len(overlay_rows),
        "pose_count_per_record": 200,
        "source_contract": "Stage 1 retained frozen-core Fe-bound assemblies + Stage 2pp occupancy artifacts",
        "interpretation": "geometric occupancy; not electron density, transition structures, or Boltzmann populations",
        "files": {
            "manifest": "manifest.csv",
            "pose_metadata": "pose_metadata.csv",
            "shared_overlay_manifest": "shared_overlay_manifest.csv",
        },
    }
    (OUT / "package_manifest.json").write_text(json.dumps(package_manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Packaged {len(package_rows)} records, {len(pose_rows)} poses, and {len(overlay_rows)} shared overlays in {OUT}")


if __name__ == "__main__":
    package()
