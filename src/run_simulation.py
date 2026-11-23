"""Run full Solarpunk Thermodynamic Micro-Data Center audit, export JSON, and plot 4-panel figure."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from matplotlib.ticker import FixedLocator, FuncFormatter, NullFormatter
from solarpunk_dc_engine import run_full_audit


def make_figure(audit: dict, out_path: Path) -> None:
    """Create 4-panel publication figure summarizing all four coupled physical subsystems."""
    m1 = audit["module1_thermodynamic_core"]
    m2 = audit["module2_radiative_sky_cooling"]
    m3 = audit["module3_mof_algae_symbiosis"]
    m4 = audit["module4_acoustic_metamaterial"]

    fig, axes = plt.subplots(2, 2, figsize=(13.5, 9.5), dpi=220)
    plt.subplots_adjust(hspace=0.34, wspace=0.25)

    # Panel (a): Power & Volume Compression (CMOS Hyperscale vs. Solarpunk Core)
    ax = axes[0, 0]
    labels = ["IT Power\n(kW)", "Total Grid Draw\n(kW)", "Rack Volume\n(x10 m^3 / 10)"]
    base_vals = [m1["p_it_baseline_kw"], m2["p_total_baseline_kw"], m1["volume_baseline_m3"] * 10.0]
    sol_vals = [m1["p_it_solarpunk_kw"], m2["p_total_solarpunk_kw"], m1["volume_solarpunk_m3"] * 10.0]
    x = np.arange(len(labels))
    w = 0.34
    b1 = ax.bar(x - w / 2, base_vals, w, color="#64748b", label="Baseline CMOS Bunker (PUE 1.42)")
    b2 = ax.bar(x + w / 2, sol_vals, w, color="#10b981", label="Solarpunk Markov+MPS Node (PUE 1.03)")
    for rect in b1:
        ax.text(rect.get_x() + rect.get_width() / 2, rect.get_height() + 2.5, f"{rect.get_height():.1f}", ha="center", va="bottom", fontsize=8.5)
    for rect in b2:
        ax.text(rect.get_x() + rect.get_width() / 2, rect.get_height() + 2.5, f"{rect.get_height():.1f}", ha="center", va="bottom", fontsize=8.5, fontweight="bold", color="#065f46")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=9.5)
    ax.set_ylim(0, 192)
    ax.set_ylabel("Magnitude (kW or 0.1 m^3)")
    ax.set_title("(a) Compute & Thermal Compression (Landauer/Markov/MPS)", fontsize=10.5, fontweight="bold")
    ax.grid(axis="y", alpha=0.25)
    ax.legend(fontsize=8.2, loc="upper right")

    # Panel (b): Selective 8-13 um Radiative Sky Cooling Flux Budget
    ax = axes[0, 1]
    flux_labels = ["IR Emit\nP_rad", "Sky Down\nP_atm", "Solar Abs\nP_sun", "Convect\nGain", "Net Sky\nq_net"]
    flux_vals = [m2["p_rad_wm2"], -m2["p_atm_wm2"], -m2["p_sun_abs_wm2"], -m2["p_conv_loss_wm2"], m2["q_net_wm2"]]
    colors = ["#0284c7", "#f59e0b", "#ef4444", "#22c55e", "#059669"]
    bars = ax.bar(flux_labels, flux_vals, color=colors, width=0.55)
    ax.axhline(0.0, color="black", linewidth=0.9)
    for rect, val in zip(bars, flux_vals):
        va = "bottom" if val >= 0 else "top"
        offset = 4.0 if val >= 0 else -5.0
        ax.text(rect.get_x() + rect.get_width() / 2, val + offset, f"{val:+.1f}", ha="center", va=va, fontsize=8.5, fontweight="bold")
    ax.set_ylim(-140, 260)
    ax.set_ylabel("Radiative / Thermal Flux (W/m^2)")
    ax.set_title("(b) 8-13 um Photonic Metasurface Sky Cooling (3 K Sink)", fontsize=10.5, fontweight="bold")
    ax.grid(axis="y", alpha=0.25)

    # Panel (c): Water Harvesting & Bio-Carbon Symbiosis (MOF-303 + Chlorella)
    ax = axes[1, 0]
    sym_labels = ["Water Balance\n(L/day x 0.1)", "CO2 Captured\n(kg/day)", "Dry Algae\n(kg/day)", "O2 Released\n(kg/day)"]
    sym_base = [-m3["water_consumed_baseline_l_day"] / 100.0, 0.0, 0.0, 0.0]
    sym_sol = [
        m3["water_harvested_solarpunk_l_day"] / 10.0,
        m3["co2_captured_kg_day"],
        m3["dry_biomass_kg_day"],
        m3["o2_released_kg_day"],
    ]
    x2 = np.arange(len(sym_labels))
    ax.bar(x2 - w / 2, sym_base, w, color="#94a3b8", label="Baseline Water Drain (-6,134 L/day)")
    b_sol = ax.bar(x2 + w / 2, sym_sol, w, color="#0ea5e9", label="Solarpunk MOF-303 + Photobioreactor")
    ax.axhline(0.0, color="black", linewidth=0.9)
    for rect in b_sol:
        ax.text(rect.get_x() + rect.get_width() / 2, rect.get_height() + 1.0, f"+{rect.get_height():.1f}", ha="center", va="bottom", fontsize=8.5, fontweight="bold", color="#0369a1")
    ax.set_xticks(x2)
    ax.set_xticklabels(sym_labels, fontsize=9.0)
    ax.set_ylim(-75, 42)
    ax.set_ylabel("Daily Regenerative Yield")
    ax.set_title(f"(c) Negative-WUE Water & Bio-Symbiosis (ERE = {m3['ere_solarpunk']:.3f})", fontsize=10.5, fontweight="bold")
    ax.grid(axis="y", alpha=0.25)
    ax.legend(fontsize=8.0, loc="lower right")

    # Panel (d): Acoustic Metamaterial Transmission Loss & Noise Suppression
    ax = axes[1, 1]
    freqs = np.array(m4["freqs_hz"])
    tl = np.array(m4["tl_db"])
    base_spl = np.array(m4["baseline_spl_db"])
    sol_spl = np.array(m4["solarpunk_spl_db"])

    ax.plot(freqs, base_spl, color="#ef4444", linewidth=1.8, label=f"Baseline Noise ({m4['noise_baseline_dba']:.1f} dBA)")
    ax.plot(freqs, sol_spl, color="#10b981", linewidth=2.0, label=f"Metamaterial Cloak ({m4['noise_solarpunk_dba']:.1f} dBA)")
    ax.axvspan(50.0, 250.0, color="#fef08a", alpha=0.35, label=f"50-250 Hz Bandgap (<TL> = {m4['mean_tl_50_250hz_db']:.1f} dB)")
    ax.axhline(35.0, color="#475569", linestyle="--", linewidth=1.1, label="Forest Silence Threshold (35 dBA)")
    ax.set_xscale("log")
    ax.xaxis.set_major_locator(FixedLocator([30, 50, 100, 200, 300, 500, 1000]))
    ax.xaxis.set_major_formatter(FuncFormatter(lambda val, pos: f"{int(val)}"))
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.set_xlim(30.0, 1000.0)
    ax.set_ylim(0.0, 90.0)
    ax.set_xlabel("Frequency (Hz)")
    ax.set_ylabel("Sound Pressure Level at 1 m (dB)")
    ax.set_title("(d) Ventilated Helmholtz-Fano Phononic Cloak", fontsize=10.5, fontweight="bold")
    ax.grid(True, which="both", alpha=0.25)
    ax.legend(fontsize=7.8, loc="upper right")

    fig.suptitle(
        "Paper 11: Solarpunk Thermodynamic Micro-Data Center Physical Audit (100 kW-eq Node)",
        fontsize=12.5,
        fontweight="bold",
        y=0.98,
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    audit = run_full_audit()

    results_path = root / "results" / "solarpunk_dc_audit.json"
    results_path.parent.mkdir(parents=True, exist_ok=True)
    results_path.write_text(json.dumps(audit, indent=2), encoding="utf-8")

    fig_path = root / "figures" / "fig1_solarpunk_thermodynamic_dc_audit.png"
    make_figure(audit, fig_path)

    manuscript_fig = root / "manuscript" / "fig1_solarpunk_thermodynamic_dc_audit.png"
    manuscript_fig.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(fig_path, manuscript_fig)

    m1 = audit["module1_thermodynamic_core"]
    m2 = audit["module2_radiative_sky_cooling"]
    m3 = audit["module3_mof_algae_symbiosis"]
    m4 = audit["module4_acoustic_metamaterial"]

    print(f"IT Power: {m1['p_it_baseline_kw']:.2f} kW -> {m1['p_it_solarpunk_kw']:.2f} kW ({m1['compute_reduction_factor']:.2f}x reduction)")
    print(f"Volume: {m1['volume_baseline_m3']:.2f} m^3 -> {m1['volume_solarpunk_m3']:.2f} m^3 ({m1['volume_reduction_pct']:.1f}% reduction)")
    print(f"PDRC Flux: {m2['q_net_wm2']:.2f} W/m^2 | Grid Power: {m2['p_total_baseline_kw']:.2f} -> {m2['p_total_solarpunk_kw']:.2f} kW | PUE: {m2['pue_solarpunk']:.3f}")
    print(f"MOF Water Harvest: +{m3['water_harvested_solarpunk_l_day']:.2f} L/day | WUE: {m3['wue_solarpunk_l_per_kwh']:.3f} L/kWh | ERE: {m3['ere_solarpunk']:.3f}")
    print(f"Algae Bio-Fixation: CO2 = {m3['co2_captured_kg_day']:.2f} kg/day | O2 = {m3['o2_released_kg_day']:.2f} kg/day | Biomass = {m3['dry_biomass_kg_day']:.2f} kg/day")
    print(f"Acoustic Cloak (50-250 Hz mean TL): {m4['mean_tl_50_250hz_db']:.2f} dB | Exterior Noise: {m4['noise_baseline_dba']:.1f} -> {m4['noise_solarpunk_dba']:.1f} dBA")


if __name__ == "__main__":
    main()
