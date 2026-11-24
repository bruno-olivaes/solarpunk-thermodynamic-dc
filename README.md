# Symbiotic Low-Entropy Micro-Data Centers (Paper 11)

[![Zenodo DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.24485297.svg)](https://doi.org/10.5281/zenodo.24485297)
[![Paper PDF](https://img.shields.io/badge/Paper-PDF_Manuscript-red.svg)](Paper11_Solarpunk_Thermodynamic_Micro_Data_Centers.pdf)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-green.svg)](https://www.python.org/)
[![Tests: 6/6](https://img.shields.io/badge/pytest-6%2F6_passed-brightgreen.svg)]()

A coupled physical simulation and system-level exergy audit demonstrating how combining **Landauer/Crooks thermodynamic computing**, **Markov-blanket sparse activation (Paper 10)**, **MPS tensor compression (Paper 4)**, **selective $8\text{--}13\ \mu\text{m}$ passive radiative sky cooling**, **MOF-303 atmospheric water harvesting**, **microalgae bio-symbiosis (Paper 9 Pinch)**, and **ventilated Helmholtz--Fano acoustic metamaterials** shrinks a $100\text{ kW}$-equivalent data center while turning waste heat into potable water, oxygen, and carbon sequestration.

---

## Key Verified Audit Results ($100\text{ kW}$-eq Node)

| Physical Subsystem | Hyperscale CMOS Baseline | Symbiotic Low-Entropy Node | Measured Impact |
| :--- | :---: | :---: | :--- |
| **IT Compute Power** | $100.00\text{ kW}$ | **$11.42\text{ kW}$** | **$8.76\times$ reduction** (Markov + MPS + Crooks) |
| **Total Facility Grid Draw** | $142.00\text{ kW}$ | **$11.72\text{ kW}$** | **$12.12\times$ reduction** ($PUE = 1.026$) |
| **Physical Enclosure Volume** | $12.50\text{ m}^3$ | **$1.75\text{ m}^3$** | **$86.0\%$ smaller** (fanless two-phase immersion) |
| **Sky Radiative Flux ($8\text{--}13\ \mu\text{m}$)** | Active chillers | **$+114.12\text{ W/m}^2$** | **$5.14\text{ kW}_{\mathrm{th}}$** passive sink to $3\text{ K}$ space |
| **Water Balance ($WUE$)** | $-6,134.4\text{ L/day}$ ($+1.80$) | **$+115.62\text{ L/day}$ ($-0.411$)** | **Net water generator** via MOF-303 |
| **Bio-Carbon & $\mathrm{O}_2$ Yield** | $0$ | **$32.50\text{ kg CO}_2$ / $23.62\text{ kg O}_2\text{/d}$** | $17.76\text{ kg/day}$ dry *Chlorella* ($ERE = 0.286$) |
| **Exterior Noise at $1\text{ m}$** | $78.5\text{ dBA}$ | **$26.7\text{ dBA}$** | **$63.62\text{ dB}$** $50\text{--}250\text{ Hz}$ metamaterial cloak |

### Three-Tier Hardware & Climate Sensitivity Envelope

| Tier | $P_{\mathrm{IT}}$ [kW] | $q_{\mathrm{net}}$ [$\text{W/m}^2$] | $PUE / ERE$ | Water [L/d] | $WUE$ [L/kWh] |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Tier 1 (Near-Term CMOS+MPS, 75\% RH)** | $31.72$ ($3.15\times$) | $96.97$ | $1.009 / 0.269$ | $+347.95$ | $-0.453$ |
| **Tier 2 (Reference Hybrid, 45\% RH)** | $11.42$ ($8.76\times$) | $114.12$ | $1.026 / 0.286$ | $+115.62$ | $-0.411$ |
| **Tier 3 (Arid Peak Solar, 20\% RH)** | $11.42$ ($8.76\times$) | $138.19$ | $1.026 / 0.286$ | $+77.08$ | $-0.274$ |

---

## Reproducibility

```bash
# Run physical simulation, export JSON audit, and regenerate 4-panel figure
python src/run_simulation.py

# Run complete unit test suite (6/6 tests)
pytest -v
```

---

## License

MIT License.
