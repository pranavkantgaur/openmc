#ifndef OPENMC_TALLIES_FILTER_BEZIER_H
#define OPENMC_TALLIES_FILTER_BEZIER_H

#include <string>

#include "openmc/tallies/filter.h"

namespace openmc {

//==============================================================================
//! Gives Bezier (Bernstein polynomial) expansion moments of a particle's
//! position in a 2D rectangular domain.
//!
//! This filter implements functional expansion tallies using Bernstein basis
//! polynomials (the basis of Bezier curves/surfaces). These provide an
//! alternative to Zernike polynomials for spatial expansions with better
//! properties near rectangular boundaries.
//==============================================================================

class BezierFilter : public Filter {
public:
  //----------------------------------------------------------------------------
  // Constructors, destructors

  ~BezierFilter() = default;

  //----------------------------------------------------------------------------
  // Methods

  std::string type_str() const override { return "bezier"; }
  FilterType type() const override { return FilterType::BEZIER; }

  void from_xml(pugi::xml_node node) override;

  void get_all_bins(const Particle& p, TallyEstimator estimator,
    FilterMatch& match) const override;

  void to_statepoint(hid_t filter_group) const override;

  std::string text_label(int bin) const override;

  //----------------------------------------------------------------------------
  // Accessors

  int order_u() const { return order_u_; }
  void set_order_u(int order);

  int order_v() const { return order_v_; }
  void set_order_v(int order);

  double x_min() const { return x_min_; }
  void set_x_min(double x) { x_min_ = x; }

  double x_max() const { return x_max_; }
  void set_x_max(double x) { x_max_ = x; }

  double y_min() const { return y_min_; }
  void set_y_min(double y) { y_min_ = y; }

  double y_max() const { return y_max_; }
  void set_y_max(double y) { y_max_ = y; }

  //----------------------------------------------------------------------------
  // Data members

private:
  //! Polynomial degree in x (u) direction
  int order_u_ {0};

  //! Polynomial degree in y (v) direction
  int order_v_ {0};

  //! Minimum x coordinate for the rectangular domain
  double x_min_ {0.0};

  //! Maximum x coordinate for the rectangular domain
  double x_max_ {1.0};

  //! Minimum y coordinate for the rectangular domain
  double y_min_ {0.0};

  //! Maximum y coordinate for the rectangular domain
  double y_max_ {1.0};
};

//==============================================================================
//! 1D Bezier expansion along a single axis (simplified version)
//==============================================================================

class Bezier1DFilter : public Filter {
public:
  //----------------------------------------------------------------------------
  // Methods

  std::string type_str() const override { return "bezier1d"; }
  FilterType type() const override { return FilterType::BEZIER_1D; }

  void from_xml(pugi::xml_node node) override;

  void get_all_bins(const Particle& p, TallyEstimator estimator,
    FilterMatch& match) const override;

  void to_statepoint(hid_t filter_group) const override;

  std::string text_label(int bin) const override;

  //----------------------------------------------------------------------------
  // Accessors

  int order() const { return order_; }
  void set_order(int order);

  char axis() const { return axis_; }
  void set_axis(char axis);

  double minimum() const { return min_; }
  double maximum() const { return max_; }
  void set_range(double min, double max);

private:
  //----------------------------------------------------------------------------
  // Data members

  //! Polynomial degree
  int order_ {0};

  //! Axis along which to expand ('x', 'y', or 'z')
  char axis_ {'x'};

  //! Minimum coordinate value
  double min_ {0.0};

  //! Maximum coordinate value
  double max_ {1.0};
};

} // namespace openmc
#endif // OPENMC_TALLIES_FILTER_BEZIER_H
