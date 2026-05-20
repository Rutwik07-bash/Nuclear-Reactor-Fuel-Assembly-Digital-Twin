import openmc
import numpy as np

# ==============================================================================
# --- 1. MATERIAL DEFINITIONS ---
# ==============================================================================
# We define the basic materials to color-code the plot.
fuel_material = openmc.Material(name='UO2 Fuel')
fuel_material.add_element('U', 1.0, enrichment=4.95)
fuel_material.add_element('O', 2.0)
fuel_material.set_density('g/cm3', 10.5)

zircaloy = openmc.Material(name='Zircaloy-4')
zircaloy.add_element('Zr', 0.98)
zircaloy.set_density('g/cm3', 6.55)

water = openmc.Material(name='Light Water')
water.add_nuclide('H1', 2)
water.add_element('O', 1)
water.add_s_alpha_beta('c_H_in_H2O')
water.set_density('g/cm3', 1.0)

materials = openmc.Materials([fuel_material, zircaloy, water])

# ==============================================================================
# --- 2. GEOMETRY DEFINITIONS ---
# ==============================================================================
# This uses the same 19x19 geometry from our simulations.
fuel_pellet_radius = 0.365
fuel_cladding_radius = 0.425
pin_pitch_19 = 1.127

# --- Fuel Pin Universe ---
fuel_surface = openmc.ZCylinder(r=fuel_pellet_radius)
cladding_surface = openmc.ZCylinder(r=fuel_cladding_radius)
fuel_cell = openmc.Cell(name='Fuel Pin', fill=fuel_material, region=-fuel_surface)
cladding_cell = openmc.Cell(name='Fuel Cladding', fill=zircaloy, region=+fuel_surface & -cladding_surface)
moderator_cell_fuel = openmc.Cell(name='Moderator (Fuel)', fill=water, region=+cladding_surface)
fuel_pin_universe = openmc.Universe(cells=[fuel_cell, cladding_cell, moderator_cell_fuel])

# --- Guide Tube Universe ---
guide_tube_surface = openmc.ZCylinder(r=fuel_cladding_radius)
guide_tube_cell = openmc.Cell(name='Guide Tube', fill=water, region=-guide_tube_surface)
moderator_cell_gt = openmc.Cell(name='Moderator (GT)', fill=water, region=+guide_tube_surface)
guide_tube_universe = openmc.Universe(cells=[guide_tube_cell, moderator_cell_gt])

# --- 19x19 Lattice ---
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

# ==============================================================================
# --- 3. PLOTTING COMMANDS ---
# ==============================================================================
# Create a plot object
plot = openmc.Plot()
plot.filename = 'assembly_visualization'
plot.width = (assembly_boundary * 2, assembly_boundary * 2)
plot.pixels = (800, 800)  # Set resolution for a high-quality image
plot.color_by = 'material'

# Define colors for each material
plot.colors = {
    fuel_material: 'yellow',
    zircaloy: 'dimgray',
    water: 'skyblue'
}

# Create a plots.xml file and export the model
plots = openmc.Plots([plot])
plots.export_to_xml()
model = openmc.Model(geometry=geometry, materials=materials)
model.export_to_xml()

# Run the plotter
openmc.plot_geometry()

print("Plot created successfully.")
