"""Test Bezier and polynomial basis filters."""

import numpy as np
import pytest
import openmc
from openmc.filter_expansion import BezierFilter, Bezier1DFilter


def test_bezier_filter_creation():
    """Test creation of BezierFilter."""
    f = BezierFilter(order_u=2, order_v=3, x_min=-5.0, x_max=5.0,
                     y_min=-10.0, y_max=10.0)
    assert f.order_u == 2
    assert f.order_v == 3
    assert f.x_min == -5.0
    assert f.x_max == 5.0
    assert f.y_min == -10.0
    assert f.y_max == 10.0
    # Should have (order_u+1) * (order_v+1) = 3 * 4 = 12 bins
    assert f.num_bins == 12


def test_bezier_filter_properties():
    """Test BezierFilter property setters and getters."""
    f = BezierFilter()
    
    # Test order_u
    f.order_u = 3
    assert f.order_u == 3
    
    # Test order_v
    f.order_v = 4
    assert f.order_v == 4
    
    # Test bounds
    f.x_min = -1.0
    f.x_max = 1.0
    f.y_min = -2.0
    f.y_max = 2.0
    assert f.x_min == -1.0
    assert f.x_max == 1.0
    assert f.y_min == -2.0
    assert f.y_max == 2.0


def test_bezier_filter_invalid_order():
    """Test that invalid orders raise errors."""
    with pytest.raises(ValueError):
        f = BezierFilter(order_u=-1)
    
    f = BezierFilter()
    with pytest.raises(ValueError):
        f.order_v = -2


def test_bezier_filter_xml():
    """Test BezierFilter XML export and import."""
    f1 = BezierFilter(order_u=2, order_v=3, x_min=-5.0, x_max=5.0,
                      y_min=-10.0, y_max=10.0, filter_id=1)
    
    # Export to XML
    elem = f1.to_xml_element()
    
    # Import from XML
    f2 = BezierFilter.from_xml_element(elem)
    
    assert f2.id == f1.id
    assert f2.order_u == f1.order_u
    assert f2.order_v == f1.order_v
    assert f2.x_min == f1.x_min
    assert f2.x_max == f1.x_max
    assert f2.y_min == f1.y_min
    assert f2.y_max == f1.y_max


def test_bezier1d_filter_creation():
    """Test creation of Bezier1DFilter."""
    f = Bezier1DFilter(order=3, axis='x', minimum=-5.0, maximum=5.0)
    assert f.order == 3
    assert f.axis == 'x'
    assert f.minimum == -5.0
    assert f.maximum == 5.0
    # Should have (order+1) = 4 bins
    assert f.num_bins == 4


def test_bezier1d_filter_axes():
    """Test Bezier1DFilter with different axes."""
    for axis in ['x', 'y', 'z']:
        f = Bezier1DFilter(order=2, axis=axis, minimum=0.0, maximum=10.0)
        assert f.axis == axis


def test_bezier1d_filter_invalid_axis():
    """Test that invalid axis raises error."""
    with pytest.raises(ValueError):
        f = Bezier1DFilter(order=2, axis='w')


def test_bezier1d_filter_xml():
    """Test Bezier1DFilter XML export and import."""
    f1 = Bezier1DFilter(order=4, axis='z', minimum=-10.0, maximum=10.0,
                        filter_id=2)
    
    # Export to XML
    elem = f1.to_xml_element()
    
    # Import from XML
    f2 = Bezier1DFilter.from_xml_element(elem)
    
    assert f2.id == f1.id
    assert f2.order == f1.order
    assert f2.axis == f1.axis
    assert f2.minimum == f1.minimum
    assert f2.maximum == f1.maximum


def test_bezier_filter_bins():
    """Test that bin labels are generated correctly."""
    f = BezierFilter(order_u=2, order_v=1)
    assert len(f.bins) == 6  # (2+1) * (1+1) = 6
    # Check format of bin labels
    assert all('x' in b for b in f.bins)


def test_bezier1d_filter_bins():
    """Test that bin labels are generated correctly for 1D filter."""
    f = Bezier1DFilter(order=3)
    assert len(f.bins) == 4  # order + 1
    # Check format of bin labels
    assert all('B_' in b for b in f.bins)


def test_bezier_filter_comparison():
    """Test BezierFilter equality and hashing."""
    f1 = BezierFilter(order_u=2, order_v=2, x_min=0.0, x_max=1.0,
                      y_min=0.0, y_max=1.0)
    f2 = BezierFilter(order_u=2, order_v=2, x_min=0.0, x_max=1.0,
                      y_min=0.0, y_max=1.0)
    f3 = BezierFilter(order_u=3, order_v=2, x_min=0.0, x_max=1.0,
                      y_min=0.0, y_max=1.0)
    
    # Same parameters should be equal
    assert f1 == f2
    assert hash(f1) == hash(f2)
    
    # Different parameters should not be equal
    assert f1 != f3
    assert hash(f1) != hash(f3)


def test_bezier_filter_repr():
    """Test BezierFilter string representation."""
    f = BezierFilter(order_u=2, order_v=3, x_min=-5.0, x_max=5.0,
                     y_min=-10.0, y_max=10.0, filter_id=42)
    repr_str = repr(f)
    
    # Check that key information is in the representation
    assert 'BezierFilter' in repr_str
    assert '2' in repr_str  # order_u
    assert '3' in repr_str  # order_v
    assert '42' in repr_str  # filter_id
