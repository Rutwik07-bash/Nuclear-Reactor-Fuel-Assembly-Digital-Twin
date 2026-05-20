import openmc
import numpy as np
import os

# ==============================================================================
# --- 1. MATERIAL DEFINITIONS (FOR THE DOUBLE FAILURE SCENARIO) ---
# ==============================================================================

# FAILURE #1: Manufacturing error - No burnable poisons are added.
fuel_material = openmc.Material(name='UO2 Fuel (No Poisons)')
fuel_material.add_element('U', 1.0, enrichment=4.95)
fuel_material.add_element('O', 2.0)
fuel_material.set_density('g/cm3', 10.5)

zircaloy = openmc.Material(name='Zircaloy-4')
zircaloy.add_element('Zr', 0.98)
zircaloy.set_density('g/cm3', 6.55)

# FAILURE #2: Flooding accident - Pure, unborated water.
water = openmc.Material(name='Pure Light Water')
water.add_nuclide('H1', 2)
water.add_element('O', 1)
water.add_s_alpha_beta('c_H_in_H2O')
water.set_density('g/cm3', 1.0)  # Using pure water density

materials = openmc.Materials([fuel_material, zircaloy, water])

# ==============================================================================
# --- 2. GEOMETRY AND SETTINGS (MAXIMUM FIDELITY) ---
# ==============================================================================

# Using the standard 19x19 geometry
fuel_pellet_radius = 0.365
fuel_cladding_radius = 0.425
pin_pitch_19 = 1.127

# --- Standard Geometry Definitions (Fuel Pin, Guide Tube, Lattice) ---
fuel_surface = openmc.ZCylinder(r=fuel_pellet_radius)
cladding_surface = openmc.ZCylinder(r=fuel_cladding_radius)
fuel_region = -fuel_surface
cladding_region = +fuel_surface & -cladding_surface
moderator_region_fuel = +cladding_surface
fuel_cell = openmc.Cell(name='Fuel Pin', fill=fuel_material, region=fuel_region)
cladding_cell = openmc.Cell(name='Fuel Cladding', fill=zircaloy, region=cladding_region)
moderator_cell_fuel = openmc.Cell(name='Moderator (Fuel)', fill=water, region=moderator_region_fuel)
fuel_pin_universe = openmc.Universe(cells=[fuel_cell, cladding_cell, moderator_cell_fuel])

guide_tube_surface = openmc.ZCylinder(r=fuel_cladding_radius)
guide_tube_cell = openmc.Cell(name='Guide Tube', fill=water, region=-guide_tube_surface)
moderator_cell_gt = openmc.Cell(name='Moderator (GT)', fill=water, region=+guide_tube_surface)
guide_tube_universe = openmc.Universe(cells=[guide_tube_cell, moderator_cell_gt])

assembly_universes = np.full((19, 19), fuel_pin_universe, dtype=object)
guide_tube_map = [
    (3,3), (3,6), (3,9), (3,12), (3,15), (5,5), (5,13), (6,3), (6,9), (6,15),
    (8,8), (8,10), (9,3), (9,6), (9,9), (9,12), (9,15), (10,8), (10,10),
    (12,3), (12,9), (12,15), (13,5), (13,13), (15,3), (15,6), (15,9), (15,12), (15,15)
]
for i, j in guide_tube_map:
    assembly_universes[i, j] = guide_tube_universe

assembly_lattice = openmc.RectLattice()
assembly_lattice.pitch = (pin_pitch_19, pin_pitch_19)
assembly_lattice.lower_left = (-19 * pin_pitch_19 / 2.0, -19 * pin_pitch_19 / 2.0)
assembly_lattice.universes = assembly_universes

assembly_boundary = 19 * pin_pitch_19 / 2.0
min_x = openmc.XPlane(-assembly_boundary, boundary_type='reflective')
max_x = openmc.XPlane(assembly_boundary, boundary_type='reflective')
min_y = openmc.YPlane(-assembly_boundary, boundary_type='reflective')
max_y = openmc.YPlane(assembly_boundary, boundary_type='reflective')

main_cell = openmc.Cell(name='19x19 Fuel Assembly', fill=assembly_lattice, region=+min_x & -max_x & +min_y & -max_y)
root_universe = openmc.Universe(cells=[main_cell])
geometry = openmc.Geometry(root_universe)

# --- HIGH-FIDELITY SETTINGS FOR THE FINAL RUN ---
settings = openmc.Settings()
settings.batches = 200       # Increased batches for higher precision
settings.inactive = 40
settings.particles = 100000  # Set to 100,000 particles for maximum fidelity

bounds = [-assembly_boundary, -assembly_boundary, -1, assembly_boundary, assembly_boundary, 1]
uniform_dist = openmc.stats.Box(bounds[:3], bounds[3:])
settings.source = openmc.IndependentSource(space=uniform_dist)

# ==============================================================================
# --- 3. RUN THE SIMULATION AND PRINT RESULTS ---
# ==============================================================================
print("--- Starting Maximum-Fidelity Double Contingency Simulation ---")
print("--- 100,000 Particles ---")
print("Scenario: Unpoisoned Fuel Assembly Flooded with Pure Water")

# Define the model with all components
model = openmc.Model(geometry=geometry, materials=materials, settings=settings)

# Run the simulation, showing output in the terminal
model.run()

# --- Process and print the final k-effective ---
sp_path = f'statepoint.{settings.batches}.h5'
if os.path.exists(sp_path):
    sp = openmc.StatePoint(sp_path)
    k_final = sp.k_combined
    print("\n--- FINAL SIMULATION RESULTS ---")
    print(f"Combined k-effective = {k_final}")
    sp.close()
else:
    print(f"\nError: Statepoint file '{sp_path}' not found.")
