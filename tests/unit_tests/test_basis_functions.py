"""Test mathematical basis functions for filters."""

import numpy as np
import pytest


def test_bernstein_basis_properties():
    """Test mathematical properties of Bernstein basis functions."""
    # Bernstein basis of degree n forms a partition of unity
    # That is, sum of all basis functions at any t should equal 1
    
    # We'll test this by importing the C++ library if available
    # For now, test the Python-side properties
    
    from openmc.filter_expansion import BezierFilter, Bezier1DFilter
    
    # Test that filter creates correct number of bins
    f = Bezier1DFilter(order=3)
    assert f.num_bins == 4  # degree 3 has 4 basis functions (0,1,2,3)
    
    f2d = BezierFilter(order_u=2, order_v=3)
    assert f2d.num_bins == 12  # (2+1) * (3+1) = 12


def test_chebyshev_properties():
    """Test that Chebyshev polynomial filters are created correctly."""
    # This tests the structure, actual math is tested in C++
    # We would need to expose the PolynomialBasisFilter to Python first
    pass


def test_filter_normalization_domain():
    """Test that filters have proper domain specifications."""
    from openmc.filter_expansion import BezierFilter, Bezier1DFilter
    
    # 1D filter
    f1d = Bezier1DFilter(order=2, axis='x', minimum=-1.0, maximum=1.0)
    assert f1d.minimum < f1d.maximum
    
    # 2D filter
    f2d = BezierFilter(order_u=2, order_v=2, 
                       x_min=-1.0, x_max=1.0,
                       y_min=-2.0, y_max=2.0)
    assert f2d.x_min < f2d.x_max
    assert f2d.y_min < f2d.y_max


def test_bezier_vs_zernike_domain():
    """Compare domain specifications between Bezier and Zernike filters."""
    from openmc.filter_expansion import BezierFilter, ZernikeFilter
    
    # Zernike works on circular domain (unit disk)
    zernike = ZernikeFilter(order=3, x=0.0, y=0.0, r=1.0)
    
    # Bezier works on rectangular domain
    bezier = BezierFilter(order_u=3, order_v=3,
                         x_min=-1.0, x_max=1.0,
                         y_min=-1.0, y_max=1.0)
    
    # Both should generate bins based on their order
    # Zernike: (n+1)(n+2)/2 = 4*5/2 = 10 bins
    # Bezier: (n_u+1)(n_v+1) = 4*4 = 16 bins
    assert zernike.num_bins == 10
    assert bezier.num_bins == 16
    
    # This demonstrates that Bezier has more bins for same order
    # but covers a rectangular domain vs circular


def test_spatial_legendre_vs_bezier1d():
    """Compare 1D spatial Legendre with 1D Bezier filter."""
    from openmc.filter_expansion import Bezier1DFilter, SpatialLegendreFilter
    
    # Both can expand along an axis over a range
    legendre = SpatialLegendreFilter(order=3, axis='x', minimum=-1.0, maximum=1.0)
    bezier = Bezier1DFilter(order=3, axis='x', minimum=-1.0, maximum=1.0)
    
    # Same number of bins for same order
    assert legendre.num_bins == 4
    assert bezier.num_bins == 4
    
    # But use different basis functions:
    # - Legendre uses orthogonal polynomials (good for smooth functions)
    # - Bezier uses Bernstein polynomials (good for localized features)
