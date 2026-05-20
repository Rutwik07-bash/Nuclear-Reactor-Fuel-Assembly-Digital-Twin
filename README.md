AI-Driven Criticality Safety Management System for SMR Fuel Assemblies
MSc Dissertation Project | University of Manchester | Nuclear Science & Technology | 2025
Distinction Grade

All model parameters are derived from publicly available Generic Design Assessment (GDA) data. No proprietary or commercially sensitive information is included in this repository.


Overview
This repository contains the Python source code for an AI-driven workflow developed to automate the design and safety validation of a Small Modular Reactor (SMR) fuel assembly. The project demonstrates how Bayesian Optimisation, coupled with high-fidelity Monte Carlo neutronics simulation (OpenMC), can intelligently identify optimal burnable poison configurations that satisfy international criticality safety requirements.
The core safety requirement is to ensure inherent subcriticality (keff ≤ 0.95) during non-operational states such as transport and storage — a standard set by the IAEA and adopted by the UK's Office for Nuclear Regulation (ONR).
The project was developed as an industry-linked MSc dissertation, supervised by Dr Jordan Hall and Aileen Buchanan at Capgemini, Manchester.

Key Results
Poison StrategyGd ConcentrationB ConcentrationFinal keffGd-Only0.1212 wt%0.0000 wt%0.95000 ± 0.00031B-Only0.0000 wt%2.8553 wt%0.95002 ± 0.00049Hybrid (Final)0.1000 wt%0.4188 wt%0.95013 ± 0.00033
The hybrid configuration was identified as the optimal engineering solution — using less Gadolinium than the Gd-only case while avoiding the high Boron concentrations required by the B-only approach.
Double Contingency Principle validation: Under a worst-case double-failure scenario (no poisons + pure water flooding), keff = 1.498 — confirming that two independent failures are required to cause criticality, fully compliant with international safety standards.

Repository Structure
nuclear-reactor-digital-twin/
│
├── Model_Geometry.py          # OpenMC 19x19 SMR fuel assembly geometry and 2D visualisation
├── optimize_Gdtarget.py       # Bayesian optimisation — Gadolinium-only campaign
├── optimize_borontarget.py    # Bayesian optimisation — Boron-only campaign
├── optimize_hybrid_2.py       # Bayesian optimisation — Hybrid (Gd + B) campaign
├── Pitch_Parameter.py         # AI-driven pin pitch sensitivity study
├── DCP.py                     # Double Contingency Principle validation simulation
└── README.md

Technical Stack
ToolPurposeOpenMCMonte Carlo neutron transport simulationscikit-optimizeBayesian Optimisation (Gaussian Process)Python 3Scripting, automation, and workflow integrationNumPyNumerical computation

Fuel Assembly Model
The computational model represents a 19×19 PWR-style SMR fuel assembly, based on publicly available Generic Design Assessment (GDA) data:
ParameterValueFuel materialUO₂ (4.95% ²³⁵U enrichment)CladdingZircaloy-4ModeratorLight water (0.7 g/cm³)Fuel pellet radius0.365 cmCladding outer radius0.425 cmPin pitch1.127 cmAssembly layout336 fuel pins + 25 guide tubesBoundary conditionsReflective (infinite lattice approximation)

How It Works
The AI-driven workflow operates as a closed loop:

The Bayesian Optimiser proposes a burnable poison configuration (Gd and/or B concentration)
OpenMC runs a Monte Carlo neutron transport simulation for that configuration
The objective function evaluates how close keff is to the 0.95 safety target: (keff - 0.95)²
The optimiser updates its internal probabilistic model and proposes the next configuration
This loop repeats for 56 iterations, converging on the optimal solution

This approach is significantly more efficient than manual parameter sweeps, requiring far fewer simulations to find the global optimum in a complex, multi-dimensional design space.

Running the Code
Prerequisites
bashpip install openmc scikit-optimize numpy

Note: OpenMC requires nuclear data libraries. See the OpenMC installation guide for full setup instructions.

Run geometry visualisation
bashpython Model_Geometry.py
Run optimisation campaigns
bashpython optimize_Gdtarget.py       # Gd-only
python optimize_borontarget.py    # B-only
python optimize_hybrid_2.py       # Hybrid
Run sensitivity study
bashpython Pitch_Parameter.py
Run Double Contingency Principle validation
bashpython DCP.py

Background & Framework
This project was developed as part of a broader Criticality Safety Management System (CSMS) framework, aligned with the INCOSE Systems Engineering Lifecycle. The CSMS provides a structured, auditable pathway from computational design to regulatory safety documentation using the Claim-Argument-Evidence (CAE) structure required by UK nuclear regulators (ONR).
The framework covers the full nuclear facility lifecycle — from conceptual design and optimisation through to operational monitoring and decommissioning — demonstrating how AI can be responsibly integrated into safety-critical nuclear engineering workflows.
The abstract was selected for presentation at the International Youth Nuclear Congress (IYNC), France, and the research was presented as a talk at the Early Career Researcher (ECR) Conference, Manchester, May 2026.

Author
Rutwik Pandirkar
MSc Nuclear Science & Technology — University of Manchester
MSc Physics — University of Mumbai
📧 pandirkarrutwik@gmail.com
🔗 github.com/Rutwik07-bash
