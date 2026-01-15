#include "openmc/tallies/filter_bezier.h"

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
// BezierFilter implementation
//==============================================================================

void BezierFilter::from_xml(pugi::xml_node node)
{
  set_order_u(std::stoi(get_node_value(node, "order_u")));
  set_order_v(std::stoi(get_node_value(node, "order_v")));
  x_min_ = std::stod(get_node_value(node, "x_min"));
  x_max_ = std::stod(get_node_value(node, "x_max"));
  y_min_ = std::stod(get_node_value(node, "y_min"));
  y_max_ = std::stod(get_node_value(node, "y_max"));
}

void BezierFilter::set_order_u(int order)
{
  if (order < 0) {
    throw std::invalid_argument {"Bezier order_u must be non-negative."};
  }
  order_u_ = order;
  // Total bins is (order_u + 1) * (order_v + 1)
  n_bins_ = (order_u_ + 1) * (order_v_ + 1);
}

void BezierFilter::set_order_v(int order)
{
  if (order < 0) {
    throw std::invalid_argument {"Bezier order_v must be non-negative."};
  }
  order_v_ = order;
  // Total bins is (order_u + 1) * (order_v + 1)
  n_bins_ = (order_u_ + 1) * (order_v_ + 1);
}

void BezierFilter::get_all_bins(
  const Particle& p, TallyEstimator estimator, FilterMatch& match) const
{
  // Get particle position
  double x = p.r().x;
  double y = p.r().y;

  // Check if particle is within the rectangular domain
  if (x >= x_min_ && x <= x_max_ && y >= y_min_ && y <= y_max_) {
    // Normalize coordinates to [0,1]
    double u = (x - x_min_) / (x_max_ - x_min_);
    double v = (y - y_min_) / (y_max_ - y_min_);

    // Compute Bernstein basis values
    vector<double> bn(n_bins_);
    calc_bernstein_basis_2d(order_u_, order_v_, u, v, bn.data());

    // Add all bins with their weights
    for (int i = 0; i < n_bins_; i++) {
      match.bins_.push_back(i);
      match.weights_.push_back(bn[i]);
    }
  }
}

void BezierFilter::to_statepoint(hid_t filter_group) const
{
  Filter::to_statepoint(filter_group);
  write_dataset(filter_group, "order_u", order_u_);
  write_dataset(filter_group, "order_v", order_v_);
  write_dataset(filter_group, "x_min", x_min_);
  write_dataset(filter_group, "x_max", x_max_);
  write_dataset(filter_group, "y_min", y_min_);
  write_dataset(filter_group, "y_max", y_max_);
}

std::string BezierFilter::text_label(int bin) const
{
  assert(bin >= 0 && bin < n_bins_);
  
  // Decode bin index to (i, j) for Bernstein basis B_{i,order_u} * B_{j,order_v}
  int i = bin / (order_v_ + 1);
  int j = bin % (order_v_ + 1);
  
  return fmt::format("Bezier expansion, B_{},{} x B_{},{}", i, order_u_, j, order_v_);
}

//==============================================================================
// Bezier1DFilter implementation
//==============================================================================

void Bezier1DFilter::from_xml(pugi::xml_node node)
{
  set_order(std::stoi(get_node_value(node, "order")));
  
  auto axis_str = get_node_value(node, "axis");
  if (axis_str.length() > 0) {
    set_axis(axis_str[0]);
  }
  
  double min = std::stod(get_node_value(node, "min"));
  double max = std::stod(get_node_value(node, "max"));
  set_range(min, max);
}

void Bezier1DFilter::set_order(int order)
{
  if (order < 0) {
    throw std::invalid_argument {"Bezier order must be non-negative."};
  }
  order_ = order;
  n_bins_ = order_ + 1;
}

void Bezier1DFilter::set_axis(char axis)
{
  if (axis != 'x' && axis != 'y' && axis != 'z') {
    throw std::invalid_argument {
      "Bezier1D axis must be 'x', 'y', or 'z'"};
  }
  axis_ = axis;
}

void Bezier1DFilter::set_range(double min, double max)
{
  if (max <= min) {
    throw std::invalid_argument {
      "Maximum value must be greater than minimum value"};
  }
  min_ = min;
  max_ = max;
}

void Bezier1DFilter::get_all_bins(
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
    return; // Should never happen
  }

  // Check if coordinate is within range
  if (coord >= min_ && coord <= max_) {
    // Normalize coordinate to [0,1]
    double t = (coord - min_) / (max_ - min_);

    // Compute Bernstein basis values
    vector<double> bn(order_ + 1);
    calc_bernstein_basis(order_, t, bn.data());

    // Add all bins with their weights
    for (int i = 0; i <= order_; i++) {
      match.bins_.push_back(i);
      match.weights_.push_back(bn[i]);
    }
  }
}

void Bezier1DFilter::to_statepoint(hid_t filter_group) const
{
  Filter::to_statepoint(filter_group);
  write_dataset(filter_group, "order", order_);
  std::string axis_str(1, axis_);
  write_dataset(filter_group, "axis", axis_str);
  write_dataset(filter_group, "min", min_);
  write_dataset(filter_group, "max", max_);
}

std::string Bezier1DFilter::text_label(int bin) const
{
  return fmt::format("Bezier expansion, {} axis, B_{},{}", 
                     axis_, bin, order_);
}

//==============================================================================
// C-API functions
//==============================================================================

std::pair<int, BezierFilter*> check_bezier_filter(int32_t index)
{
  // Make sure this is a valid index to an allocated filter.
  int err = verify_filter(index);
  if (err) {
    return {err, nullptr};
  }

  // Get a pointer to the filter and downcast.
  const auto& filt_base = model::tally_filters[index].get();
  auto* filt = dynamic_cast<BezierFilter*>(filt_base);

  // Check the filter type.
  if (!filt) {
    set_errmsg("Not a Bezier filter.");
    err = OPENMC_E_INVALID_TYPE;
  }
  return {err, filt};
}

extern "C" int openmc_bezier_filter_get_orders(
  int32_t index, int* order_u, int* order_v)
{
  // Check the filter.
  auto check_result = check_bezier_filter(index);
  auto err = check_result.first;
  auto filt = check_result.second;
  if (err)
    return err;

  // Output the orders.
  *order_u = filt->order_u();
  *order_v = filt->order_v();
  return 0;
}

extern "C" int openmc_bezier_filter_get_params(int32_t index, double* x_min,
  double* x_max, double* y_min, double* y_max)
{
  // Check the filter.
  auto check_result = check_bezier_filter(index);
  auto err = check_result.first;
  auto filt = check_result.second;
  if (err)
    return err;

  // Output the params.
  *x_min = filt->x_min();
  *x_max = filt->x_max();
  *y_min = filt->y_min();
  *y_max = filt->y_max();
  return 0;
}

extern "C" int openmc_bezier_filter_set_orders(
  int32_t index, int order_u, int order_v)
{
  // Check the filter.
  auto check_result = check_bezier_filter(index);
  auto err = check_result.first;
  auto filt = check_result.second;
  if (err)
    return err;

  // Update the filter.
  filt->set_order_u(order_u);
  filt->set_order_v(order_v);
  return 0;
}

extern "C" int openmc_bezier_filter_set_params(int32_t index,
  const double* x_min, const double* x_max, const double* y_min,
  const double* y_max)
{
  // Check the filter.
  auto check_result = check_bezier_filter(index);
  auto err = check_result.first;
  auto filt = check_result.second;
  if (err)
    return err;

  // Update the filter.
  if (x_min)
    filt->set_x_min(*x_min);
  if (x_max)
    filt->set_x_max(*x_max);
  if (y_min)
    filt->set_y_min(*y_min);
  if (y_max)
    filt->set_y_max(*y_max);
  return 0;
}

} // namespace openmc
