import openmc
import numpy as np
import os
from skopt import gp_minimize
from skopt.space import Real

# ==============================================================================
# --- 1. MATERIAL DEFINITION (Using the FINAL Optimized Hybrid Design) ---
# ==============================================================================

# This uses the final Gd and B concentrations from the successful AI run.
fuel_material = openmc.Material(name='Optimized Hybrid Fuel')
# All components must use the same percent type. Using Atom Percent ('ao').
fuel_material.add_element('U', 1.0, enrichment=4.95, percent_type='ao')
fuel_material.add_element('O', 2.0, percent_type='ao')
fuel_material.add_element('Gd', 0.001000, 'ao')  # Corrected to Atom Percent
fuel_material.add_element('B', 0.004188, 'ao')   # Corrected to Atom Percent
fuel_material.set_density('g/cm3', 10.5)

zircaloy = openmc.Material(name='Zircaloy-4')
zircaloy.add_element('Zr', 0.98)
zircaloy.set_density('g/cm3', 6.55)

water = openmc.Material(name='Light Water')
water.add_nuclide('H1', 2)
water.add_element('O', 1)
water.add_s_alpha_beta('c_H_in_H2O')
water.set_density('g/cm3', 0.7)  # Using operational density

materials = openmc.Materials([fuel_material, zircaloy, water])

# ==============================================================================
# --- 2. OBJECTIVE FUNCTION (for the AI Optimizer) ---
# ==============================================================================

def objective_function(params):
    """
    This function takes a set of parameters from the AI optimizer,
    runs an OpenMC simulation, and returns an objective value to be minimized.
    """
    pitch = params[0]
    print(f"\n--- Running simulation for pin pitch = {pitch:.4f} cm ---")

    # --- SIMULATION SETTINGS ---
    settings = openmc.Settings()
    settings.batches = 100
    settings.inactive = 20
    settings.particles = 10000

    # --- GEOMETRY (This is redefined for each call) ---
    fuel_pellet_radius = 0.365
    fuel_cladding_radius = 0.425

    fuel_pin_universe = openmc.Universe()
    fuel_surface = openmc.ZCylinder(r=fuel_pellet_radius)
    cladding_surface = openmc.ZCylinder(r=fuel_cladding_radius)
    fuel_cell = openmc.Cell(fill=fuel_material, region=-fuel_surface)
    cladding_cell = openmc.Cell(fill=zircaloy, region=+fuel_surface & -cladding_surface)
    moderator_cell_fuel = openmc.Cell(fill=water, region=+cladding_surface)
    fuel_pin_universe.add_cells([fuel_cell, cladding_cell, moderator_cell_fuel])

    guide_tube_universe = openmc.Universe()
    guide_tube_surface = openmc.ZCylinder(r=fuel_cladding_radius)
    guide_tube_cell = openmc.Cell(fill=water, region=-guide_tube_surface)
    moderator_cell_gt = openmc.Cell(fill=water, region=+guide_tube_surface)
    guide_tube_universe.add_cells([guide_tube_cell, moderator_cell_gt])

    assembly_universes = np.full((19, 19), fuel_pin_universe, dtype=object)
    guide_tube_map = [
        (3,3), (3,6), (3,9), (3,12), (3,15), (5,5), (5,13), (6,3), (6,9), (6,15),
        (8,8), (8,10), (9,3), (9,6), (9,9), (9,12), (9,15), (10,8), (10,10),
        (12,3), (12,9), (12,15), (13,5), (13,13), (15,3), (15,6), (15,9), (15,12), (15,15)
    ]
    for i, j in guide_tube_map:
        assembly_universes[i, j] = guide_tube_universe

    assembly_lattice = openmc.RectLattice()
    assembly_lattice.pitch = (pitch, pitch)
    assembly_lattice.lower_left = (-19 * pitch / 2.0, -19 * pitch / 2.0)
    assembly_lattice.universes = assembly_universes

    assembly_boundary = 19 * pitch / 2.0
    min_x = openmc.XPlane(-assembly_boundary, boundary_type='reflective')
    max_x = openmc.XPlane(assembly_boundary, boundary_type='reflective')
    min_y = openmc.YPlane(-assembly_boundary, boundary_type='reflective')
    max_y = openmc.YPlane(assembly_boundary, boundary_type='reflective')

    main_cell = openmc.Cell(fill=assembly_lattice, region=+min_x & -max_x & +min_y & -max_y)
    root_universe = openmc.Universe(cells=[main_cell])
    geometry = openmc.Geometry(root_universe)

    bounds = [-assembly_boundary, -assembly_boundary, -1, assembly_boundary, assembly_boundary, 1]
    uniform_dist = openmc.stats.Box(bounds[:3], bounds[3:])
    settings.source = openmc.IndependentSource(space=uniform_dist)

    # --- Run the simulation ---
    model = openmc.Model(geometry=geometry, materials=materials, settings=settings)
    model.run(output=False)

    # --- Process result and return objective value ---
    sp_path = f'statepoint.{settings.batches}.h5'
    k_eff = 0.0
    if os.path.exists(sp_path):
        sp = openmc.StatePoint(sp_path)
        k_final = sp.keff  # Updated to use the recommended 'keff' property
        k_eff = k_final.n
        print(f"Result: k-effective = {k_final}")
        sp.close()
    else:
        print(f"Error: Statepoint file not found for pitch {pitch:.4f} cm.")
        return 1.0  # Return a high objective value on error

    objective = (k_eff - 0.95) ** 2
    print(f"Objective = {objective}")
    return objective

# ==============================================================================
# --- 3. AI OPTIMIZATION SETUP AND EXECUTION ---
# ==============================================================================

# Define the search space for the pin pitch
space = [Real(1.08, 1.26, name='pin_pitch')]

print("--- Starting AI-Driven Pin Pitch Optimization ---")

# Run the Bayesian optimization
result = gp_minimize(
    objective_function,  # The function to minimize
    space,               # The bounds on the parameters
    n_calls=10,          # The number of simulations to run
    random_state=0       # For reproducibility
)

# ==============================================================================
# --- 4. PRINT FINAL RESULTS ---
# ==============================================================================
best_pitch = result.x[0]
best_objective = result.fun

print("\n--- AI Optimization Complete ---")
print("==========================================")
print(f"Best pin pitch found: {best_pitch:.4f} cm")
print(f"Lowest objective value: {best_objective:.6f}")
print(f"This corresponds to a k-effective of approximately: {np.sqrt(best_objective) + 0.95:.5f}")
print("==========================================")
