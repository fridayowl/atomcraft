"""DFT job pipeline: input generation, job submission, output parsing."""
import os, subprocess, json, shutil, uuid
from datetime import datetime
from typing import Optional

JOBS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "dft_jobs")


def _ensure_jobs_dir():
    os.makedirs(JOBS_DIR, exist_ok=True)


def generate_vasp_inputs(formula: str, space_group: str, lattice: dict,
                          elements: list[str], job_dir: str) -> dict:
    """Generate VASP input files (POSCAR, INCAR, KPOINTS, POTCAR) using pymatgen."""
    from pymatgen.core.structure import Structure
    from pymatgen.core.lattice import Lattice
    from pymatgen.core.periodic_table import Element
    from pymatgen.io.vasp import Poscar, Incar, Kpoints, Potcar

    a = lattice.get("a", 5)
    b = lattice.get("b", a)
    c = lattice.get("c", a)
    alpha = lattice.get("alpha", 90)
    beta = lattice.get("beta", 90)
    gamma = lattice.get("gamma", 90)

    lat = Lattice.from_parameters(a, b, c, alpha, beta, gamma)
    els = [Element(e) for e in elements]
    # Simple placement at fractional coordinates
    frac_coords = [[(i + 0.5) / len(els), (i + 0.5) / len(els), (i + 0.5) / len(els)]
                   for i in range(len(els))]
    struct = Structure(lat, els, frac_coords)

    poscar = Poscar(struct)
    poscar.write_file(os.path.join(job_dir, "POSCAR"))

    incar = Incar({
        "SYSTEM": formula,
        "ENCUT": 520,
        "ISMEAR": 0,
        "SIGMA": 0.05,
        "PREC": "Accurate",
        "EDIFF": 1e-6,
        "EDIFFG": -0.01,
        "NSW": 100,
        "IBRION": 2,
        "ISIF": 3,
        "LREAL": "Auto",
        "LORBIT": 11,
        "LWAVE": False,
        "LCHARG": False,
        "KSPACING": 0.3,
    })
    incar.write_file(os.path.join(job_dir, "INCAR"))

    kpoints = Kpoints.automatic_density(struct, 2000)
    kpoints.write_file(os.path.join(job_dir, "KPOINTS"))

    try:
        potcar = Potcar(symbols=[e.symbol for e in els])
        potcar.write_file(os.path.join(job_dir, "POTCAR"))
    except Exception as e:
        # POTCAR generation may fail without pseudopotential files installed
        pass

    return {"status": "inputs_generated", "job_dir": job_dir, "formula": formula}


def generate_qe_inputs(formula: str, lattice: dict, elements: list[str],
                        job_dir: str) -> dict:
    """Generate Quantum ESPRESSO input files."""
    from pymatgen.core.structure import Structure
    from pymatgen.core.lattice import Lattice
    from pymatgen.core.periodic_table import Element
    from pymatgen.io.qe import PWInput

    a = lattice.get("a", 5)
    b = lattice.get("b", a)
    c = lattice.get("c", a)
    lat = Lattice.from_parameters(a, b, c, 90, 90, 90)
    els = [Element(e) for e in elements]
    frac_coords = [[(i + 0.5) / len(els), (i + 0.5) / len(els), (i + 0.5) / len(els)]
                   for i in range(len(els))]
    struct = Structure(lat, els, frac_coords)

    pwinput = PWInput(
        struct,
        pseudo_dir="./pseudos/",
        pseudo_type="pbe",
        control={"prefix": formula, "pseudo_dir": "./pseudos/"},
        system={"ecutwfc": 60, "ecutrho": 480, "occupations": "smearing",
                "smearing": "gaussian", "degauss": 0.02},
        electrons={"conv_thr": 1e-8},
        ions={"ion_dynamics": "bfgs"},
        cell={"cell_dynamics": "bfgs"},
    )
    with open(os.path.join(job_dir, "pw.in"), "w") as f:
        f.write(str(pwinput))

    return {"status": "qe_inputs_generated", "job_dir": job_dir, "formula": formula}


def submit_job(job_dir: str, scheduler: str = "local") -> dict:
    """Submit a DFT job. Supports 'local', 'slurm', 'pbs'."""
    if not os.path.exists(os.path.join(job_dir, "POSCAR")):
        return {"error": "No POSCAR found", "job_dir": job_dir}

    if scheduler == "local":
        # Check if VASP is available
        vasp_cmd = shutil.which("vasp_std") or shutil.which("vasp")
        if vasp_cmd:
            result = subprocess.run(
                [vasp_cmd],
                cwd=job_dir,
                capture_output=True,
                text=True,
                timeout=3600,
            )
            return {
                "status": "completed" if result.returncode == 0 else "failed",
                "returncode": result.returncode,
                "stdout": result.stdout[-500:],
                "stderr": result.stderr[-500:],
                "job_dir": job_dir,
            }
        else:
            # Create a submission script for later use
            script = (
                "#!/bin/bash\n"
                f"#SBATCH --job-name=dft_{os.path.basename(job_dir)}\n"
                "#SBATCH --ntasks=16\n"
                "#SBATCH --time=24:00:00\n"
                "#SBATCH --partition=compute\n"
                f"cd {job_dir}\n"
                "module load vasp\n"
                "mpirun vasp_std\n"
            )
            script_path = os.path.join(job_dir, "submit.sh")
            with open(script_path, "w") as f:
                f.write(script)
            os.chmod(script_path, 0o755)

            return {
                "status": "submission_script_created",
                "job_dir": job_dir,
                "script": script_path,
                "note": "VASP not found locally. Script ready for cluster submission.",
            }

    elif scheduler == "slurm":
        script = (
            "#!/bin/bash\n"
            f"#SBATCH --job-name=dft_{os.path.basename(job_dir)}\n"
            "#SBATCH --ntasks=32\n"
            "#SBATCH --time=48:00:00\n"
            "#SBATCH --partition=gpu\n"
            f"cd {job_dir}\n"
            "module load vasp/6.4\n"
            "srun vasp_std\n"
        )
        script_path = os.path.join(job_dir, "submit.slurm")
        with open(script_path, "w") as f:
            f.write(script)
        os.chmod(script_path, 0o755)
        return {"status": "slurm_script_created", "job_dir": job_dir, "script": script_path}

    return {"error": f"Unknown scheduler: {scheduler}"}


def parse_vasp_output(job_dir: str) -> dict:
    """Parse VASP output files for energy, forces, structure."""
    result = {"job_dir": job_dir}

    # Try parsing OUTCAR
    outcar_path = os.path.join(job_dir, "OUTCAR")
    if os.path.exists(outcar_path):
        with open(outcar_path) as f:
            content = f.read()
        import re
        energy_match = re.search(r"energy\s+without\s+entropy\s*=\s*([-\d.]+)", content)
        if energy_match:
            result["energy"] = float(energy_match.group(1))

        eform_match = re.search(r"E0\s*=\s*([-\d.]+)", content)
        if eform_match:
            result["energy_per_atom"] = float(eform_match.group(1))

        bg_match = re.search(r"band\s+gap\s*:?\s*([-\d.]+)", content)
        if bg_match:
            result["band_gap"] = float(bg_match.group(1))

    # Try parsing vasprun.xml
    vasprun_path = os.path.join(job_dir, "vasprun.xml")
    if os.path.exists(vasprun_path):
        try:
            from pymatgen.io.vasp import Vasprun
            vrun = Vasprun(vasprun_path)
            result["final_energy"] = vrun.final_energy
            result["completed"] = vrun.converged
            if hasattr(vrun, "structures") and vrun.structures:
                result["final_structure"] = vrun.structures[-1].as_dict()
        except Exception:
            pass

    # Try parsing OSZICAR for last energy
    oszicar_path = os.path.join(job_dir, "OSZICAR")
    if os.path.exists(oszicar_path):
        with open(oszicar_path) as f:
            lines = f.readlines()
        for line in reversed(lines):
            parts = line.strip().split()
            if len(parts) >= 3 and parts[0].isdigit():
                try:
                    result["last_energy"] = float(parts[2])
                except ValueError:
                    pass
                break

    result["has_converged"] = result.get("completed", False)
    return result


def create_dft_job(formula: str, space_group: str, lattice: dict,
                    elements: list[str], engine: str = "vasp") -> dict:
    """Full DFT job pipeline: inputs → submit → parse."""
    _ensure_jobs_dir()
    job_id = str(uuid.uuid4())[:8]
    formula_slug = formula.replace(" ", "_")
    job_dir = os.path.join(JOBS_DIR, f"{formula_slug}_{job_id}")
    os.makedirs(job_dir, exist_ok=True)

    job_info = {
        "job_id": job_id,
        "formula": formula,
        "engine": engine,
        "created_at": datetime.utcnow().isoformat(),
        "job_dir": job_dir,
    }

    if engine == "vasp":
        input_result = generate_vasp_inputs(formula, space_group, lattice, elements, job_dir)
        job_info.update(input_result)
        if "error" not in input_result:
            submit_result = submit_job(job_dir, scheduler="local")
            job_info.update(submit_result)

            # Try to parse if completed
            if submit_result.get("status") == "completed":
                parse_result = parse_vasp_output(job_dir)
                job_info.update(parse_result)
    else:
        input_result = generate_qe_inputs(formula, lattice, elements, job_dir)
        job_info.update(input_result)

    # Save job info
    with open(os.path.join(job_dir, "job_info.json"), "w") as f:
        json.dump(job_info, f, indent=2, default=str)

    return job_info


class DFTOrchestrator:
    """Manages DFT validation of generated candidates."""

    def __init__(self):
        self._ensure_dirs()

    def _ensure_dirs(self):
        _ensure_jobs_dir()

    def validate_candidate(self, candidate: dict, engine: str = "vasp") -> dict:
        formula = candidate.get("formula", "")
        sg = candidate.get("space_group", "P1")
        lattice = candidate.get("lattice_parameters", {"a": 5, "b": 5, "c": 5})
        elements = candidate.get("elements", [])
        return create_dft_job(formula, sg, lattice, elements, engine=engine)

    def batch_validate(self, candidates: list[dict], engine: str = "vasp") -> list[dict]:
        results = []
        for c in candidates:
            result = self.validate_candidate(c, engine=engine)
            results.append(result)
            print(f"  DFT job for {c.get('formula','')}: {result.get('status','failed')}")
        return results

    def get_job_status(self, job_dir: str) -> dict:
        info_path = os.path.join(job_dir, "job_info.json")
        if os.path.exists(info_path):
            with open(info_path) as f:
                return json.load(f)
        # Try parsing output
        return parse_vasp_output(job_dir)
