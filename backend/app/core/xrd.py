import math
import numpy as np
from typing import Optional


def simulate_xrd_pattern(space_group: str, lattice_params: dict,
                         elements: list[str],
                         wavelength: float = 1.5406) -> dict:
    a = lattice_params.get("a", 5.0)
    b = lattice_params.get("b", a)
    c = lattice_params.get("c", a)

    d_spacings = _compute_d_spacings(space_group, a, b, c)
    intensities = _simulate_intensities(d_spacings, elements, wavelength)

    peaks = []
    for d, i in zip(d_spacings, intensities):
        if i > 0.01:
            two_theta = 2 * math.degrees(math.asin(wavelength / (2 * d))) if d > wavelength / 2 else 0
            if two_theta > 0:
                peaks.append({
                    "two_theta": round(two_theta, 2),
                    "d_spacing": round(d, 4),
                    "intensity": round(i, 4),
                    "hkl": _assign_miller_indices(space_group, len(peaks)),
                })

    return {
        "wavelength": wavelength,
        "peaks": peaks,
        "num_peaks": len(peaks),
        "space_group": space_group,
    }


def _compute_d_spacings(sg: str, a: float, b: float, c: float) -> list[float]:
    spacings = []
    hkl_list = [
        (1,0,0),(0,1,0),(0,0,1),(1,1,0),(1,0,1),(0,1,1),
        (1,1,1),(2,0,0),(0,2,0),(0,0,2),(2,1,0),(2,0,1),
        (1,2,0),(0,2,1),(1,0,2),(0,1,2),(2,1,1),(1,2,1),
        (1,1,2),(2,2,0),(3,0,0),(2,2,1),(3,1,0),(3,1,1),
    ]

    for h, k, l_ in hkl_list:
        if "cubic" in sg.lower() or sg in ["Fm-3m", "Pm-3m", "Fd-3m", "Im-3m"]:
            d = a / math.sqrt(h*h + k*k + l_*l_) if (h*h + k*k + l_*l_) > 0 else 0
        elif "tetragonal" in sg.lower() or sg in ["I4/mmm", "P4/mmm"]:
            d = 1.0 / math.sqrt((h*h + k*k)/(a*a) + (l_*l_)/(c*c)) if ((h*h + k*k)/(a*a) + (l_*l_)/(c*c)) > 0 else 0
        elif "hexagonal" in sg.lower() or sg in ["P6_3/mmc", "P6/mmm"]:
            d = 1.0 / math.sqrt(4*(h*h + h*k + k*k)/(3*a*a) + l_*l_/(c*c)) if ... else 0
            denom = 4*(h*h + h*k + k*k)/(3*a*a) + l_*l_/(c*c)
            d = 1.0 / math.sqrt(denom) if denom > 0 else 0
        else:
            d = a / math.sqrt(h*h + k*k + l_*l_) if (h*h + k*k + l_*l_) > 0 else 0

        if d > 0:
            spacings.append(d)

    return sorted(spacings, reverse=True)[:30]


def _simulate_intensities(d_spacings: list[float], elements: list[str],
                           wavelength: float) -> list[float]:
    n_elements = max(len(elements), 1)
    intensities = []
    for i, d in enumerate(d_spacings):
        f = n_elements * 10 * math.exp(-d / 2)
        lp = (1 + math.cos(math.radians(20))**2) / (math.sin(math.radians(20))**2 * math.cos(math.radians(20)))
        two_theta = 2 * math.degrees(math.asin(wavelength / (2 * d))) if d > wavelength / 2 else 0
        if two_theta > 0:
            lp_factor = (1 + math.cos(math.radians(two_theta))**2) / (math.sin(math.radians(two_theta))**2 * math.cos(math.radians(two_theta/2)))
            intensity = abs(f * lp_factor) * (0.5 + 0.5 * math.sin(i * 1.5))
            intensities.append(intensity)

    max_i = max(intensities) if intensities else 1
    return [i / max_i for i in intensities]


def _assign_miller_indices(sg: str, index: int) -> list[int]:
    indices = [(1,0,0),(0,1,0),(0,0,1),(1,1,0),(1,0,1),(0,1,1),
               (1,1,1),(2,0,0),(0,2,0),(0,0,2),(2,1,0),(2,0,1)]
    if index < len(indices):
        return list(indices[index])
    return [index+1, 0, 0]
