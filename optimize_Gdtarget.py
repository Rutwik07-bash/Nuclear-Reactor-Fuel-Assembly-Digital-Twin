import openmc
import numpy as np
from skopt import gp_minimize
from skopt.space import Real

def simulate_keff(params):
    """
    This function takes a list of parameters from the optimizer,
    runs a full OpenMC simulation, and returns the objective value.
    """
    gadolinium_conc, boron_conc = params

    print(f"--- Running simulation with Gd={gadolinium_conc*100:.4f} wt%, B={boron_conc*100:.4f} wt% ---")

    fuel = openmc.Material(name='UO2 Fuel')
    total_poison = gadolinium_conc + boron_conc
    if total_poison >= 1.0:
        return 1.0e6
    fuel.add_element('U', 1.0 - total_poison, enrichment=4.95)
    fuel.add_element('O', 2.0)
    fuel.add_element('Gd', gadolinium_conc)
    fuel.add_element('B', boron_conc)
    fuel.set_density('g/cm3', 10.5)
    zircaloy = openmc.Material(name='Zircaloy-4')
    zircaloy.add_element('Zr', 0.98)
    zircaloy.set_density('g/cm3', 6.55)
    water = openmc.Material(name='Light Water')
    water.add_nuclide('H1', 2)
    water.add_element('O', 1)
    water.add_s_alpha_beta('c_H_in_H2O')
    water.set_density('g/cm3', 0.7)
    materials = openmc.Materials([fuel, zircaloy, water])
    materials.export_to_xml()

    fuel_pellet_radius = 0.73 / 2.0
    fuel_cladding_radius = 0.85 / 2.0
    pin_pitch_19 = 1.127
    fuel_surface = openmc.ZCylinder(r=fuel_pellet_radius)
    cladding_surface = openmc.ZCylinder(r=fuel_cladding_radius)
    fuel_region = -fuel_surface
    cladding_region = +fuel_surface & -cladding_surface
    moderator_region_fuel = +cladding_surface
    fuel_cell = openmc.Cell(name='Fuel Pin', fill=fuel, region=fuel_region)
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
    geometry.export_to_xml()

    settings = openmc.Settings()
    settings.batches = 100
    settings.inactive = 20
    settings.particles = 10000
    bounds = [-assembly_boundary, -assembly_boundary, -1, assembly_boundary, assembly_boundary, 1]
    uniform_dist = openmc.stats.Box(bounds[:3], bounds[3:])
    settings.source = openmc.IndependentSource(space=uniform_dist)
    settings.export_to_xml()

    openmc.run(output=False, cwd='.') 
    sp = openmc.StatePoint(f'statepoint.{settings.batches}.h5')
    keff_from_simulation = sp.keff.n
    sp.close()
    
    objective_value = (keff_from_simulation - 0.95)**2
    
    print(f"Result: k_eff = {keff_from_simulation:.5f}, Objective = {objective_value:.8f}")
    return objective_value

search_space = [
    Real(0.0, 0.03, name='gadolinium_conc'),
    Real(0.0, 1e-9, name='boron_conc')
]

result = gp_minimize(
    func=simulate_keff,
    dimensions=search_space,
    n_calls=50,
    random_state=123
)

print("\n--- Optimization Finished ---")
print(f"Best parameters found: Gd={result.x[0]*100:.4f} wt%, B={result.x[1]*100:.4f} wt%")
print(f"Best objective value (closest to 0): {result.fun:.8f}")

best_keff = np.sqrt(result.fun) + 0.95 if result.fun >= 0 else 0.95 - np.sqrt(abs(result.fun))
print(f"This corresponds to a k_eff of approximately: {best_keff:.5f}")