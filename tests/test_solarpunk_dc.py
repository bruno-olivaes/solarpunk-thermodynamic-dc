"""Unit and integration tests for Paper 11 Solarpunk Thermodynamic Micro-Data Center."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from solarpunk_dc_engine import (
    SolarpunkNodeConfig,
    compute_thermodynamic_core,
    compute_radiative_sky_cooling,
    compute_mof_algae_symbiosis,
    compute_acoustic_metamaterial_cloak,
    run_full_audit,
    compute_sensitivity_envelope,
)


def test_thermodynamic_core_compression():
    cfg = SolarpunkNodeConfig()
    core = compute_thermodynamic_core(cfg)
    assert core["compute_reduction_factor"] > 8.0
    assert core["volume_reduction_pct"] > 80.0
    assert 1e-21 < core["e_landauer_j_per_bit"] < 5e-21


def test_radiative_sky_cooling_pue():
    cfg = SolarpunkNodeConfig()
    core = compute_thermodynamic_core(cfg)
    cooling = compute_radiative_sky_cooling(cfg, core["p_it_solarpunk_kw"])
    assert cooling["q_net_wm2"] > 80.0
    assert cooling["passive_headroom_kw"] > 0.0
    assert cooling["pue_solarpunk"] < 1.04


def test_mof_water_harvest_and_algae_symbiosis():
    cfg = SolarpunkNodeConfig()
    core = compute_thermodynamic_core(cfg)
    cooling = compute_radiative_sky_cooling(cfg, core["p_it_solarpunk_kw"])
    sym = compute_mof_algae_symbiosis(
        cfg,
        core["p_it_solarpunk_kw"],
        cooling["p_total_solarpunk_kw"],
        cooling["p_total_baseline_kw"],
    )
    assert sym["wue_solarpunk_l_per_kwh"] < 0.0
    assert sym["water_harvested_solarpunk_l_day"] > 100.0
    assert sym["net_potable_water_export_l_day"] > 95.0
    assert abs(sym["energy_balance_residual_kw"]) < 1e-6
    assert sym["ere_solarpunk"] < 0.35
    assert sym["co2_captured_kg_day"] > 25.0


def test_acoustic_metamaterial_suppression():
    cfg = SolarpunkNodeConfig()
    ac = compute_acoustic_metamaterial_cloak(cfg)
    assert ac["mean_tl_50_250hz_db"] > 38.0
    assert ac["noise_solarpunk_dba"] < 35.0
    assert ac["noise_flanking_limited_dba"] < 35.0
    assert ac["noise_reduction_dba"] > 40.0


def test_end_to_end_audit_and_artifacts():
    audit = run_full_audit()
    assert set(audit.keys()) == {
        "config",
        "module1_thermodynamic_core",
        "module2_radiative_sky_cooling",
        "module3_mof_algae_symbiosis",
        "module4_acoustic_metamaterial",
    }
    json_path = ROOT / "results" / "solarpunk_dc_audit.json"
    fig_path = ROOT / "figures" / "fig1_solarpunk_thermodynamic_dc_audit.png"
    assert json_path.exists()
    assert fig_path.exists()
    loaded = json.loads(json_path.read_text(encoding="utf-8"))
    assert loaded["module2_radiative_sky_cooling"]["pue_solarpunk"] < 1.04


def test_sensitivity_envelope_tiers():
    tiers = compute_sensitivity_envelope()
    assert set(tiers.keys()) == {
        "tier1_nearterm_humid",
        "tier2_reference_clear",
        "tier3_arid_highsolar",
    }
    assert tiers["tier1_nearterm_humid"]["compute_reduction_factor"] > 3.0
    assert tiers["tier1_nearterm_humid"]["wue_l_per_kwh"] < 0.0
    assert tiers["tier2_reference_clear"]["compute_reduction_factor"] > 8.0
    assert tiers["tier3_arid_highsolar"]["water_harvest_l_day"] > 70.0
    assert tiers["tier3_arid_highsolar"]["q_net_wm2"] > 100.0
