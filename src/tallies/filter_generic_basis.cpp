#include "openmc/tallies/filter_generic_basis.h"

#include <cassert>
#include <cmath>
#include <sstream>
#include <utility> // For pair

#include <fmt/core.h>

#include "openmc/capi.h"
#include "openmc/error.h"
#include "openmc/math_functions.h"
#include "openmc/xml_interface.h"

namespace openmc {

//==============================================================================
// GenericBasisFilter implementation
//==============================================================================

void GenericBasisFilter::from_xml(pugi::xml_node node)
{
  // Read basis type and order
  basis_type_ = get_node_value(node, "basis_type", true);
  
  if (basis_type_ == "polynomial") {
    poly_order_ = std::stoi(get_node_value(node, "order"));
    num_basis_ = poly_order_ + 1;
    
    // Generate labels for polynomial basis
    basis_labels_.clear();
    for (int i = 0; i <= poly_order_; i++) {
      basis_labels_.push_back(fmt::format("P_{}", i));
    }
  }
  
  n_bins_ = num_basis_;
}

void GenericBasisFilter::set_dimensionality(int dim)
{
  if (dim < 1 || dim > 3) {
    throw std::invalid_argument {
      "Generic basis dimensionality must be 1, 2, or 3"};
  }
  dimensionality_ = dim;
}

void GenericBasisFilter::set_basis_labels(
  const std::vector<std::string>& labels)
{
  basis_labels_ = labels;
  num_basis_ = labels.size();
  n_bins_ = num_basis_;
}

void GenericBasisFilter::set_polynomial_basis(
  const std::string& type, int order)
{
  basis_type_ = type;
  poly_order_ = order;
  num_basis_ = order + 1;
  n_bins_ = num_basis_;
  
  // Generate labels
  basis_labels_.clear();
  for (int i = 0; i <= order; i++) {
    basis_labels_.push_back(fmt::format("{}_{}", type, i));
  }
}

void GenericBasisFilter::get_all_bins(
  const Particle& p, TallyEstimator estimator, FilterMatch& match) const
{
  // For now, this is a placeholder that would need user-provided basis functions
  // In a real implementation, this would evaluate the basis functions at particle position
  warning(
    "GenericBasisFilter::get_all_bins is not fully implemented. "
    "Use PolynomialBasisFilter for a working implementation.");
}

void GenericBasisFilter::to_statepoint(hid_t filter_group) const
{
  Filter::to_statepoint(filter_group);
  write_dataset(filter_group, "basis_type", basis_type_);
  write_dataset(filter_group, "dimensionality", dimensionality_);
  write_dataset(filter_group, "num_basis", num_basis_);
  if (basis_type_ == "polynomial") {
    write_dataset(filter_group, "order", poly_order_);
  }
}

std::string GenericBasisFilter::text_label(int bin) const
{
  assert(bin >= 0 && bin < n_bins_);
  if (bin < static_cast<int>(basis_labels_.size())) {
    return fmt::format("Generic basis expansion, {}", basis_labels_[bin]);
  }
  return fmt::format("Generic basis expansion, basis {}", bin);
}

//==============================================================================
// PolynomialBasisFilter implementation
//==============================================================================

void PolynomialBasisFilter::from_xml(pugi::xml_node node)
{
  set_order(std::stoi(get_node_value(node, "order")));
  
  // Read polynomial type
  auto poly_str = get_node_value(node, "polynomial_type", true);
  set_poly_type(poly_str);
  
  // Read axis
  auto axis_str = get_node_value(node, "axis");
  if (axis_str.length() > 0) {
    set_axis(axis_str[0]);
  }
  
  // Read range
  double min = std::stod(get_node_value(node, "min"));
  double max = std::stod(get_node_value(node, "max"));
  set_range(min, max);
}

void PolynomialBasisFilter::set_order(int order)
{
  if (order < 0) {
    throw std::invalid_argument {"Polynomial order must be non-negative."};
  }
  order_ = order;
  n_bins_ = order_ + 1;
}

void PolynomialBasisFilter::set_poly_type(PolynomialType type)
{
  poly_type_ = type;
}

void PolynomialBasisFilter::set_poly_type(const std::string& type)
{
  if (type == "legendre") {
    poly_type_ = PolynomialType::LEGENDRE;
  } else if (type == "chebyshev1" || type == "chebyshev_1") {
    poly_type_ = PolynomialType::CHEBYSHEV_1;
  } else if (type == "chebyshev2" || type == "chebyshev_2") {
    poly_type_ = PolynomialType::CHEBYSHEV_2;
  } else {
    throw std::invalid_argument {
      fmt::format("Unknown polynomial type: {}", type)};
  }
}

void PolynomialBasisFilter::set_axis(char axis)
{
  if (axis != 'x' && axis != 'y' && axis != 'z') {
    throw std::invalid_argument {
      "Polynomial basis axis must be 'x', 'y', or 'z'"};
  }
  axis_ = axis;
}

void PolynomialBasisFilter::set_range(double min, double max)
{
  if (max <= min) {
    throw std::invalid_argument {
      "Maximum value must be greater than minimum value"};
  }
  min_ = min;
  max_ = max;
}

void PolynomialBasisFilter::get_all_bins(
  const Particle& p, TallyEstimator estimator, FilterMatch& match) const
{
  // Get coordinate along the specified axis
  double coord;
  switch (axis_) {
  case 'x':
    coord = p.r().x;
    break;
  case 'y':
    coord = p.r().y;
    break;
  case 'z':
    coord = p.r().z;
    break;
  default:
    return;
  }

  // Check if coordinate is within range
  if (coord >= min_ && coord <= max_) {
    // Normalize coordinate to [-1,1] for orthogonal polynomials
    double x = 2.0 * (coord - min_) / (max_ - min_) - 1.0;

    // Compute polynomial basis values
    vector<double> poly(order_ + 1);
    
    switch (poly_type_) {
    case PolynomialType::LEGENDRE:
      calc_pn_c(order_, x, poly.data());
      break;
    case PolynomialType::CHEBYSHEV_1:
      calc_chebyshev_t(order_, x, poly.data());
      break;
    case PolynomialType::CHEBYSHEV_2:
      calc_chebyshev_u(order_, x, poly.data());
      break;
    default:
      // For now, use Legendre as fallback
      calc_pn_c(order_, x, poly.data());
      break;
    }

    // Add all bins with their weights
    for (int i = 0; i <= order_; i++) {
      match.bins_.push_back(i);
      match.weights_.push_back(poly[i]);
    }
  }
}

void PolynomialBasisFilter::to_statepoint(hid_t filter_group) const
{
  Filter::to_statepoint(filter_group);
  write_dataset(filter_group, "order", order_);
  
  std::string poly_type_str;
  switch (poly_type_) {
  case PolynomialType::LEGENDRE:
    poly_type_str = "legendre";
    break;
  case PolynomialType::CHEBYSHEV_1:
    poly_type_str = "chebyshev_1";
    break;
  case PolynomialType::CHEBYSHEV_2:
    poly_type_str = "chebyshev_2";
    break;
  default:
    poly_type_str = "unknown";
    break;
  }
  write_dataset(filter_group, "polynomial_type", poly_type_str);
  
  std::string axis_str(1, axis_);
  write_dataset(filter_group, "axis", axis_str);
  write_dataset(filter_group, "min", min_);
  write_dataset(filter_group, "max", max_);
}

std::string PolynomialBasisFilter::text_label(int bin) const
{
  std::string poly_name;
  switch (poly_type_) {
  case PolynomialType::LEGENDRE:
    poly_name = "P";
    break;
  case PolynomialType::CHEBYSHEV_1:
    poly_name = "T";
    break;
  case PolynomialType::CHEBYSHEV_2:
    poly_name = "U";
    break;
  default:
    poly_name = "?";
    break;
  }
  
  return fmt::format("Polynomial expansion, {} axis, {}_{}", 
                     axis_, poly_name, bin);
}

} // namespace openmc
