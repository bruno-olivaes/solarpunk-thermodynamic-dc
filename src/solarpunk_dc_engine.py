"""Physical simulation engine for Solarpunk Thermodynamic Micro-Data Centers (Paper 11).

Couples four first-principles subsystems:
1. Thermodynamic & Markov-Blanket Sparse Compute Core (Landauer, Crooks, MPS, Paper 10).
2. Selective 8-13 um Passive Radiative Sky Cooling to the 3 K cosmic sink (Paper 2, Fan/Capasso).
3. Two-Stage Pinch Exergy Cascade: MOF-303 atmospheric water harvesting (2025 Chemistry Nobel)
   and Chlorella vulgaris photobioreactor symbiosis (Paper 9, 2024 Chemistry Nobel).
4. Sub-wavelength Ventilated Phononic Crystal / Helmholtz-Fano Acoustic Metamaterial Cloak.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, asdict
from typing import Dict, Any

import numpy as np

# Fundamental CODATA constants
K_B = 1.380649e-23        # Boltzmann constant [J/K]
H_PLANCK = 6.62607015e-34 # Planck constant [J*s]
C_LIGHT = 2.99792458e8    # Speed of light [m/s]


@dataclass
class SolarpunkNodeConfig:
    """Configuration for a 100 kW-equivalent computational node."""
    p_it_baseline_kw: float = 100.0
    pue_baseline: float = 1.42
    wue_baseline_l_per_kwh: float = 1.80
    volume_baseline_m3: float = 12.50
    noise_baseline_dba: float = 78.5

    # Core parameters
    t_core_k: float = 302.0
    probabilistic_workload_frac: float = 0.45
    markov_active_duty: float = 0.25
    markov_idle_leak: float = 0.05
    mps_compression_factor: float = 2.80
    thermo_analog_gain: float = 250.0
    io_memory_floor_frac: float = 0.0559
    immersion_volume_m3: float = 1.75

    # Radiative Sky Cooling (PDRC)
    t_amb_k: float = 298.15
    t_panel_k: float = 304.15
    pdrc_area_m2: float = 45.0
    solar_irradiance_wm2: float = 950.0
    solar_reflectance: float = 0.97
    emissivity_window: float = 0.94
    emissivity_out: float = 0.08
    tau_atm_zenith_window: float = 0.86
    h_conv_wm2k: float = 4.0
    pump_power_kw: float = 0.30

    # Exergy Cascade: MOF-303 Water Harvester + Chlorella Photobioreactor
    mof_heat_fraction: float = 0.42
    algae_heat_fraction: float = 0.32
    mof_desorption_enthalpy_kj_kg: float = 2580.0
    mof_regen_efficiency: float = 0.72
    pbr_area_m2: float = 120.0
    pbr_areal_productivity_kg_m2_day: float = 0.148

    # Acoustic Metamaterial Cloak (Helmholtz-Fano Phononic Array)
    duct_stages: int = 5
    stage_pitch_m: float = 0.08
    sound_speed_ms: float = 343.0
    resonator_q: float = 4.5
    resonator_alpha: float = 1.65


def compute_thermodynamic_core(cfg: SolarpunkNodeConfig) -> Dict[str, Any]:
    """Compute Landauer floor, Markov-blanket sparse compute power, and physical volume."""
    e_landauer_j = K_B * cfg.t_core_k * math.log(2.0)

    # Effective duty cycle across Markov blankets (1st-order Landau-Ginzburg gating, Paper 10)
    f_duty_eff = cfg.markov_active_duty + (1.0 - cfg.markov_active_duty) * cfg.markov_idle_leak

    # Deterministic tensor subspace compressed via MPS (Paper 4) + Markov blanket sparsity
    p_det_base = cfg.p_it_baseline_kw * (1.0 - cfg.probabilistic_workload_frac)
    p_det_sol = p_det_base * (f_duty_eff / cfg.mps_compression_factor)

    # Probabilistic sampling/attention offloaded to Crooks-Boltzmann analog thermodynamic gates
    p_prob_base = cfg.p_it_baseline_kw * cfg.probabilistic_workload_frac
    p_prob_sol = p_prob_base / cfg.thermo_analog_gain

    # Static HBM / optical interconnect / Markov router floor
    p_io_sol = cfg.p_it_baseline_kw * cfg.io_memory_floor_frac

    p_it_solarpunk_kw = p_det_sol + p_prob_sol + p_io_sol
    compute_reduction_factor = cfg.p_it_baseline_kw / p_it_solarpunk_kw
    volume_reduction_pct = 100.0 * (1.0 - cfg.immersion_volume_m3 / cfg.volume_baseline_m3)

    # Crooks entropy production factor per thermodynamic gate update (Sigma ~ ln(G) bridge)
    # CMOS baseline operates ~1e8 * k_B T ln 2; Solarpunk hybrid shrinks effective mean dissipation/op
    cmos_landauer_ratio = 1.0e8
    solarpunk_landauer_ratio = cmos_landauer_ratio / compute_reduction_factor

    return {
        "e_landauer_j_per_bit": e_landauer_j,
        "p_it_baseline_kw": cfg.p_it_baseline_kw,
        "p_det_solarpunk_kw": float(p_det_sol),
        "p_prob_solarpunk_kw": float(p_prob_sol),
        "p_io_solarpunk_kw": float(p_io_sol),
        "p_it_solarpunk_kw": float(p_it_solarpunk_kw),
        "compute_reduction_factor": float(compute_reduction_factor),
        "f_duty_effective": float(f_duty_eff),
        "volume_baseline_m3": cfg.volume_baseline_m3,
        "volume_solarpunk_m3": cfg.immersion_volume_m3,
        "volume_reduction_pct": float(volume_reduction_pct),
        "cmos_landauer_ratio": cmos_landauer_ratio,
        "solarpunk_landauer_ratio": float(solarpunk_landauer_ratio),
    }


def _planck_spectral_radiance(lam_m: np.ndarray, temp_k: float) -> np.ndarray:
    """Blackbody spectral radiance I_bb(lambda, T) in W / (m^2 * sr * m)."""
    x = (H_PLANCK * C_LIGHT) / (lam_m * K_B * temp_k)
    x = np.clip(x, 1e-6, 700.0)
    return (2.0 * H_PLANCK * (C_LIGHT ** 2)) / ((lam_m ** 5) * np.expm1(x))


def compute_radiative_sky_cooling(cfg: SolarpunkNodeConfig, p_it_sol_kw: float) -> Dict[str, Any]:
    """Evaluate 8-13 um selective photonic metasurface radiative sky cooling & facility PUE."""
    lam_um = np.linspace(2.5, 45.0, 900)
    lam_m = lam_um * 1e-6
    in_window = (lam_um >= 8.0) & (lam_um <= 13.0)

    eps_s = np.where(in_window, cfg.emissivity_window, cfg.emissivity_out)
    # Zenith atmospheric transmittance model: transparent inside 8-13 um, opaque outside
    tau_zen = np.where(in_window, cfg.tau_atm_zenith_window, 0.02)

    # Hemispherical integration over zenith angle theta in [0, pi/2)
    theta = np.linspace(0.0, 0.495 * np.pi, 60)
    cos_t = np.cos(theta)
    sin_t = np.sin(theta)

    ibb_panel = _planck_spectral_radiance(lam_m, cfg.t_panel_k)
    ibb_amb = _planck_spectral_radiance(lam_m, cfg.t_amb_k)

    # Panel radiated power P_rad = pi * integral(eps_s * I_bb(T_s) dlam)
    p_rad_wm2 = math.pi * float(np.trapezoid(eps_s * ibb_panel, lam_m))

    # Downwelling atmospheric radiation P_atm = 2*pi * int cos(t)sin(t) dt * int eps_s * eps_atm(t) * I_bb(T_amb) dlam
    # Vectorized over (theta, lambda)
    eps_atm_2d = 1.0 - np.power(tau_zen[None, :], 1.0 / cos_t[:, None])
    inner_lam = np.trapezoid(eps_s[None, :] * eps_atm_2d * ibb_amb[None, :], lam_m, axis=1)
    p_atm_wm2 = 2.0 * math.pi * float(np.trapezoid(cos_t * sin_t * inner_lam, theta))

    p_sun_abs_wm2 = (1.0 - cfg.solar_reflectance) * cfg.solar_irradiance_wm2
    p_conv_gain_or_loss_wm2 = cfg.h_conv_wm2k * (cfg.t_amb_k - cfg.t_panel_k)  # negative if T_panel > T_amb

    q_net_wm2 = p_rad_wm2 - p_atm_wm2 - p_sun_abs_wm2 - p_conv_gain_or_loss_wm2
    q_rejected_max_kw = (q_net_wm2 * cfg.pdrc_area_m2) / 1000.0

    q_unrecycled_kw = p_it_sol_kw * (1.0 - cfg.mof_heat_fraction - cfg.algae_heat_fraction)
    p_total_base_kw = cfg.p_it_baseline_kw * cfg.pue_baseline
    p_total_sol_kw = p_it_sol_kw + cfg.pump_power_kw
    pue_solarpunk = p_total_sol_kw / p_it_sol_kw

    return {
        "p_rad_wm2": float(p_rad_wm2),
        "p_atm_wm2": float(p_atm_wm2),
        "p_sun_abs_wm2": float(p_sun_abs_wm2),
        "p_conv_loss_wm2": float(p_conv_gain_or_loss_wm2),
        "q_net_wm2": float(q_net_wm2),
        "pdrc_area_m2": cfg.pdrc_area_m2,
        "q_rejected_max_kw": float(q_rejected_max_kw),
        "q_unrecycled_kw": float(q_unrecycled_kw),
        "passive_headroom_kw": float(q_rejected_max_kw - q_unrecycled_kw),
        "p_total_baseline_kw": float(p_total_base_kw),
        "p_total_solarpunk_kw": float(p_total_sol_kw),
        "total_grid_reduction_factor": float(p_total_base_kw / p_total_sol_kw),
        "pue_baseline": cfg.pue_baseline,
        "pue_solarpunk": float(pue_solarpunk),
    }


def compute_mof_algae_symbiosis(
    cfg: SolarpunkNodeConfig,
    p_it_sol_kw: float,
    p_total_sol_kw: float,
    p_total_base_kw: float,
) -> Dict[str, Any]:
    """Evaluate 2-stage Pinch Exergy Cascade: MOF-303 water harvesting & algae symbiosis."""
    q_mof_kw = p_it_sol_kw * cfg.mof_heat_fraction
    q_algae_kw = p_it_sol_kw * cfg.algae_heat_fraction
    q_reused_kw = q_mof_kw + q_algae_kw

    # Stage 1: MOF-303 (2025 Chemistry Nobel) water harvesting via 48-55 C chip condenser
    q_mof_kj_day = q_mof_kw * 86400.0
    water_harvested_l_day = (q_mof_kj_day * cfg.mof_regen_efficiency) / cfg.mof_desorption_enthalpy_kj_kg

    e_sol_day_kwh = p_total_sol_kw * 24.0
    e_base_day_kwh = p_total_base_kw * 24.0

    wue_solarpunk = -water_harvested_l_day / e_sol_day_kwh
    water_consumed_base_l_day = cfg.wue_baseline_l_per_kwh * e_base_day_kwh

    # Green Grid Energy Reuse Effectiveness: ERE = (P_total - Q_reused) / P_IT
    ere_solarpunk = (p_total_sol_kw - q_reused_kw) / p_it_sol_kw

    # Stage 2: Chlorella vulgaris photobioreactor facade + 2024 Nobel carbonic anhydrase
    dry_biomass_kg_day = cfg.pbr_area_m2 * cfg.pbr_areal_productivity_kg_m2_day
    co2_captured_kg_day = dry_biomass_kg_day * 1.83
    o2_released_kg_day = dry_biomass_kg_day * 1.33

    return {
        "q_mof_kw": float(q_mof_kw),
        "q_algae_kw": float(q_algae_kw),
        "q_reused_kw": float(q_reused_kw),
        "ere_baseline": cfg.pue_baseline,
        "ere_solarpunk": float(ere_solarpunk),
        "water_consumed_baseline_l_day": float(water_consumed_base_l_day),
        "water_harvested_solarpunk_l_day": float(water_harvested_l_day),
        "wue_baseline_l_per_kwh": cfg.wue_baseline_l_per_kwh,
        "wue_solarpunk_l_per_kwh": float(wue_solarpunk),
        "dry_biomass_kg_day": float(dry_biomass_kg_day),
        "co2_captured_kg_day": float(co2_captured_kg_day),
        "o2_released_kg_day": float(o2_released_kg_day),
    }


def _a_weighting_db(freqs_hz: np.ndarray) -> np.ndarray:
    """Standard IEC 61672 A-weighting curve in dB."""
    f2 = freqs_hz ** 2
    ra_num = (12194.0 ** 2) * (f2 ** 2)
    ra_den = (
        (f2 + 20.6 ** 2)
        * np.sqrt((f2 + 107.7 ** 2) * (f2 + 737.9 ** 2))
        * (f2 + 12194.0 ** 2)
    )
    ra = ra_num / ra_den
    return 20.0 * np.log10(ra) + 2.0


def compute_acoustic_metamaterial_cloak(cfg: SolarpunkNodeConfig) -> Dict[str, Any]:
    """Compute transfer-matrix acoustic transmission loss and A-weighted exterior dBA."""
    freqs = np.linspace(30.0, 1000.0, 486)
    res_freqs = np.array([58.0, 78.0, 104.0, 136.0, 175.0, 222.0, 285.0])

    # Complex shunt admittance Y(f) of 7-resonator Helmholtz-Fano lattice cell
    y_cell = np.zeros_like(freqs, dtype=np.complex128)
    for fj in res_freqs:
        ratio = freqs / fj
        denom = (1.0 - ratio ** 2) + 1j * (ratio / cfg.resonator_q)
        y_cell += (1j * ratio * cfg.resonator_alpha) / denom

    k_wave = 2.0 * math.pi * freqs / cfg.sound_speed_ms
    kd = k_wave * cfg.stage_pitch_m

    tl_db = np.zeros_like(freqs)
    for idx in range(len(freqs)):
        cos_kd = math.cos(kd[idx])
        sin_kd = math.sin(kd[idx])
        t_duct = np.array([[cos_kd, 1j * sin_kd], [1j * sin_kd, cos_kd]], dtype=np.complex128)
        t_shunt = np.array([[1.0 + 0j, 0.0 + 0j], [y_cell[idx], 1.0 + 0j]], dtype=np.complex128)
        t_unit = t_duct @ t_shunt
        t_tot = np.linalg.matrix_power(t_unit, cfg.duct_stages)
        coeff = 0.5 * (t_tot[0, 0] + t_tot[0, 1] + t_tot[1, 0] + t_tot[1, 1])
        tl_meta = 20.0 * math.log10(max(abs(coeff), 1.0))
        # Ventilated porous aerogel-mineral acoustic labyrinth turns on across mid/high bands
        tl_porous = 45.0 / (1.0 + math.exp(-(freqs[idx] - 200.0) / 40.0))
        tl_db[idx] = tl_meta + tl_porous

    # Construct realistic baseline datacenter spectrum peaking in 60-240 Hz chiller/fan band
    # Scaled precisely so total baseline A-weighted level equals cfg.noise_baseline_dba
    raw_spl = (
        76.0 * np.exp(-0.5 * ((freqs - 120.0) / 55.0) ** 2)
        + 68.0 * np.exp(-0.5 * ((freqs - 240.0) / 140.0) ** 2)
        + 50.0
    )
    a_wt = _a_weighting_db(freqs)
    raw_a_lin = np.power(10.0, (raw_spl + a_wt) / 10.0)
    raw_total_dba = 10.0 * math.log10(float(np.sum(raw_a_lin)))
    shift_db = cfg.noise_baseline_dba - raw_total_dba

    baseline_spl = raw_spl + shift_db
    solarpunk_spl = baseline_spl - tl_db

    sol_a_lin = np.power(10.0, (solarpunk_spl + a_wt) / 10.0)
    sol_total_dba = 10.0 * math.log10(float(np.sum(sol_a_lin)))

    band_mask = (freqs >= 50.0) & (freqs <= 250.0)
    mean_tl_band_db = float(np.mean(tl_db[band_mask]))
    max_tl_band_db = float(np.max(tl_db[band_mask]))

    return {
        "freqs_hz": freqs.tolist(),
        "tl_db": tl_db.tolist(),
        "baseline_spl_db": baseline_spl.tolist(),
        "solarpunk_spl_db": solarpunk_spl.tolist(),
        "resonator_freqs_hz": res_freqs.tolist(),
        "mean_tl_50_250hz_db": mean_tl_band_db,
        "max_tl_50_250hz_db": max_tl_band_db,
        "noise_baseline_dba": cfg.noise_baseline_dba,
        "noise_solarpunk_dba": float(sol_total_dba),
        "noise_reduction_dba": float(cfg.noise_baseline_dba - sol_total_dba),
    }


def run_full_audit(cfg: SolarpunkNodeConfig | None = None) -> Dict[str, Any]:
    """Execute all four coupled physical audits and return unified dictionary."""
    if cfg is None:
        cfg = SolarpunkNodeConfig()

    core = compute_thermodynamic_core(cfg)
    cooling = compute_radiative_sky_cooling(cfg, core["p_it_solarpunk_kw"])
    symbiosis = compute_mof_algae_symbiosis(
        cfg,
        core["p_it_solarpunk_kw"],
        cooling["p_total_solarpunk_kw"],
        cooling["p_total_baseline_kw"],
    )
    acoustics = compute_acoustic_metamaterial_cloak(cfg)

    return {
        "config": asdict(cfg),
        "module1_thermodynamic_core": core,
        "module2_radiative_sky_cooling": cooling,
        "module3_mof_algae_symbiosis": symbiosis,
        "module4_acoustic_metamaterial": acoustics,
    }


def compute_sensitivity_envelope() -> Dict[str, Any]:
    """Evaluate three hardware-readiness & climate boundary tiers (near-term, reference, arid)."""
    tiers = {}

    # Tier 1: Near-term CMOS + MPS + Markov sparse gating only (no analog Boltzmann chip), humid/cloudy (75% RH)
    cfg_t1 = SolarpunkNodeConfig(
        thermo_analog_gain=1.0,
        probabilistic_workload_frac=0.0,
        markov_active_duty=0.38,
        mps_compression_factor=1.85,
        io_memory_floor_frac=0.095,
        pdrc_area_m2=90.0,
        solar_irradiance_wm2=450.0,
        tau_atm_zenith_window=0.68,
        mof_regen_efficiency=0.78,
        pbr_areal_productivity_kg_m2_day=0.115,
    )
    a1 = run_full_audit(cfg_t1)
    tiers["tier1_nearterm_humid"] = {
        "label": "Tier 1: Near-Term CMOS+MPS (Humid 75% RH)",
        "p_it_kw": a1["module1_thermodynamic_core"]["p_it_solarpunk_kw"],
        "compute_reduction_factor": a1["module1_thermodynamic_core"]["compute_reduction_factor"],
        "p_total_kw": a1["module2_radiative_sky_cooling"]["p_total_solarpunk_kw"],
        "q_net_wm2": a1["module2_radiative_sky_cooling"]["q_net_wm2"],
        "pue": a1["module2_radiative_sky_cooling"]["pue_solarpunk"],
        "ere": a1["module3_mof_algae_symbiosis"]["ere_solarpunk"],
        "water_harvest_l_day": a1["module3_mof_algae_symbiosis"]["water_harvested_solarpunk_l_day"],
        "wue_l_per_kwh": a1["module3_mof_algae_symbiosis"]["wue_solarpunk_l_per_kwh"],
        "co2_captured_kg_day": a1["module3_mof_algae_symbiosis"]["co2_captured_kg_day"],
        "noise_dba": a1["module4_acoustic_metamaterial"]["noise_solarpunk_dba"],
    }

    # Tier 2: Reference Hybrid Thermodynamic Node (Clear sky 45% RH)
    a2 = run_full_audit(SolarpunkNodeConfig())
    tiers["tier2_reference_clear"] = {
        "label": "Tier 2: Reference Hybrid Node (Clear 45% RH)",
        "p_it_kw": a2["module1_thermodynamic_core"]["p_it_solarpunk_kw"],
        "compute_reduction_factor": a2["module1_thermodynamic_core"]["compute_reduction_factor"],
        "p_total_kw": a2["module2_radiative_sky_cooling"]["p_total_solarpunk_kw"],
        "q_net_wm2": a2["module2_radiative_sky_cooling"]["q_net_wm2"],
        "pue": a2["module2_radiative_sky_cooling"]["pue_solarpunk"],
        "ere": a2["module3_mof_algae_symbiosis"]["ere_solarpunk"],
        "water_harvest_l_day": a2["module3_mof_algae_symbiosis"]["water_harvested_solarpunk_l_day"],
        "wue_l_per_kwh": a2["module3_mof_algae_symbiosis"]["wue_solarpunk_l_per_kwh"],
        "co2_captured_kg_day": a2["module3_mof_algae_symbiosis"]["co2_captured_kg_day"],
        "noise_dba": a2["module4_acoustic_metamaterial"]["noise_solarpunk_dba"],
    }

    # Tier 3: Arid / Subtropical high-solar envelope (20% RH, elevated desorption energy)
    cfg_t3 = SolarpunkNodeConfig(
        t_amb_k=305.15,
        t_panel_k=311.15,
        solar_irradiance_wm2=1050.0,
        tau_atm_zenith_window=0.92,
        mof_regen_efficiency=0.48,
        pbr_areal_productivity_kg_m2_day=0.165,
    )
    a3 = run_full_audit(cfg_t3)
    tiers["tier3_arid_highsolar"] = {
        "label": "Tier 3: Arid High-Solar Envelope (20% RH)",
        "p_it_kw": a3["module1_thermodynamic_core"]["p_it_solarpunk_kw"],
        "compute_reduction_factor": a3["module1_thermodynamic_core"]["compute_reduction_factor"],
        "p_total_kw": a3["module2_radiative_sky_cooling"]["p_total_solarpunk_kw"],
        "q_net_wm2": a3["module2_radiative_sky_cooling"]["q_net_wm2"],
        "pue": a3["module2_radiative_sky_cooling"]["pue_solarpunk"],
        "ere": a3["module3_mof_algae_symbiosis"]["ere_solarpunk"],
        "water_harvest_l_day": a3["module3_mof_algae_symbiosis"]["water_harvested_solarpunk_l_day"],
        "wue_l_per_kwh": a3["module3_mof_algae_symbiosis"]["wue_solarpunk_l_per_kwh"],
        "co2_captured_kg_day": a3["module3_mof_algae_symbiosis"]["co2_captured_kg_day"],
        "noise_dba": a3["module4_acoustic_metamaterial"]["noise_solarpunk_dba"],
    }

    return tiers
