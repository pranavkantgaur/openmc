"""Test Bezier filter in a simple pin cell geometry."""

import openmc
from openmc.filter_expansion import BezierFilter, Bezier1DFilter
from tests.testing_harness import PyAPITestHarness


def test_bezier_filter():
    """Test Bezier filter with a simple pin cell geometry."""
    
    # Create materials
    uo2 = openmc.Material(name='UO2')
    uo2.add_nuclide('U235', 0.03)
    uo2.add_nuclide('U238', 0.97)
    uo2.add_nuclide('O16', 2.0)
    uo2.set_density('g/cm3', 10.0)
    
    water = openmc.Material(name='Water')
    water.add_nuclide('H1', 2.0)
    water.add_nuclide('O16', 1.0)
    water.set_density('g/cm3', 1.0)
    water.add_s_alpha_beta('c_H_in_H2O')
    
    # Create geometry
    fuel_radius = 0.39
    clad_inner_radius = 0.40
    clad_outer_radius = 0.46
    pitch = 1.26
    
    fuel_or = openmc.ZCylinder(r=fuel_radius)
    clad_ir = openmc.ZCylinder(r=clad_inner_radius)
    clad_or = openmc.ZCylinder(r=clad_outer_radius)
    
    left = openmc.XPlane(-pitch/2, boundary_type='reflective')
    right = openmc.XPlane(pitch/2, boundary_type='reflective')
    front = openmc.YPlane(-pitch/2, boundary_type='reflective')
    back = openmc.YPlane(pitch/2, boundary_type='reflective')
    bottom = openmc.ZPlane(-10, boundary_type='reflective')
    top = openmc.ZPlane(10, boundary_type='reflective')
    
    fuel_region = -fuel_or & +bottom & -top
    gap_region = +fuel_or & -clad_ir & +bottom & -top
    clad_region = +clad_ir & -clad_or & +bottom & -top
    water_region = +clad_or & +left & -right & +front & -back & +bottom & -top
    
    fuel = openmc.Cell(fill=uo2, region=fuel_region)
    gap = openmc.Cell(fill=None, region=gap_region)
    clad = openmc.Cell(fill=water, region=clad_region)
    moderator = openmc.Cell(fill=water, region=water_region)
    
    root = openmc.Universe(cells=[fuel, gap, clad, moderator])
    geometry = openmc.Geometry(root)
    
    # Create settings
    settings = openmc.Settings()
    settings.batches = 10
    settings.inactive = 5
    settings.particles = 1000
    settings.source = openmc.IndependentSource(space=openmc.stats.Point())
    
    # Create tallies with Bezier filters
    tallies = openmc.Tallies()
    
    # 2D Bezier filter in xy plane
    bezier_2d_filter = BezierFilter(
        order_u=2, order_v=2, 
        x_min=-pitch/2, x_max=pitch/2,
        y_min=-pitch/2, y_max=pitch/2
    )
    tally_2d = openmc.Tally(name='bezier-2d')
    tally_2d.filters = [bezier_2d_filter]
    tally_2d.scores = ['flux']
    tally_2d.estimator = 'tracklength'
    tallies.append(tally_2d)
    
    # 1D Bezier filter along x-axis
    bezier_1d_filter = Bezier1DFilter(
        order=3, axis='x',
        minimum=-pitch/2, maximum=pitch/2
    )
    tally_1d = openmc.Tally(name='bezier-1d-x')
    tally_1d.filters = [bezier_1d_filter]
    tally_1d.scores = ['flux']
    tally_1d.estimator = 'tracklength'
    tallies.append(tally_1d)
    
    # 1D Bezier filter along z-axis
    bezier_z_filter = Bezier1DFilter(
        order=2, axis='z',
        minimum=-10.0, maximum=10.0
    )
    tally_z = openmc.Tally(name='bezier-1d-z')
    tally_z.filters = [bezier_z_filter]
    tally_z.scores = ['flux', 'fission']
    tally_z.estimator = 'tracklength'
    tallies.append(tally_z)
    
    # Create model
    model = openmc.Model(geometry, openmc.Materials([uo2, water]), settings, tallies)
    
    # Run test
    harness = PyAPITestHarness('statepoint.10.h5', model)
    harness.main()
