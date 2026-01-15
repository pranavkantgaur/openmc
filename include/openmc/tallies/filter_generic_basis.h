#ifndef OPENMC_TALLIES_FILTER_GENERIC_BASIS_H
#define OPENMC_TALLIES_FILTER_GENERIC_BASIS_H

#include <string>
#include <vector>
#include <functional>

#include "openmc/tallies/filter.h"

namespace openmc {

//==============================================================================
//! Gives generic basis function expansion moments of a particle's position.
//!
//! This filter implements functional expansion tallies using a user-defined
//! set of basis functions. This allows for flexibility in choosing basis
//! functions beyond the pre-defined options (Legendre, Zernike, Bezier, etc.)
//!
//! The basis functions are evaluated at the particle position and the tally
//! score is weighted by each basis function value.
//==============================================================================

class GenericBasisFilter : public Filter {
public:
  //----------------------------------------------------------------------------
  // Type definitions
  
  //! Type for 1D basis function: f(x) -> weight
  using BasisFunc1D = std::function<double(double)>;
  
  //! Type for 2D basis function: f(x, y) -> weight
  using BasisFunc2D = std::function<double(double, double)>;
  
  //! Type for 3D basis function: f(x, y, z) -> weight
  using BasisFunc3D = std::function<double(double, double, double)>;

  //----------------------------------------------------------------------------
  // Constructors, destructors

  ~GenericBasisFilter() = default;

  //----------------------------------------------------------------------------
  // Methods

  std::string type_str() const override { return "genericbasis"; }
  FilterType type() const override { return FilterType::GENERIC_BASIS; }

  void from_xml(pugi::xml_node node) override;

  void get_all_bins(const Particle& p, TallyEstimator estimator,
    FilterMatch& match) const override;

  void to_statepoint(hid_t filter_group) const override;

  std::string text_label(int bin) const override;

  //----------------------------------------------------------------------------
  // Accessors

  int dimensionality() const { return dimensionality_; }
  void set_dimensionality(int dim);

  int num_basis_functions() const { return num_basis_; }
  
  const std::vector<std::string>& basis_labels() const { return basis_labels_; }
  void set_basis_labels(const std::vector<std::string>& labels);

  // For pre-defined polynomial bases
  void set_polynomial_basis(const std::string& type, int order);
  
  //----------------------------------------------------------------------------
  // Data members

private:
  //! Dimensionality of the basis (1D, 2D, or 3D)
  int dimensionality_ {1};

  //! Number of basis functions
  int num_basis_ {0};

  //! Type of basis being used (for serialization)
  std::string basis_type_ {"polynomial"};

  //! Order of polynomial basis (if applicable)
  int poly_order_ {0};

  //! Labels for each basis function
  std::vector<std::string> basis_labels_;

  //! Domain bounds for normalization [x_min, x_max, y_min, y_max, z_min, z_max]
  std::vector<double> domain_bounds_;
};

//==============================================================================
//! Polynomial basis filter using orthogonal polynomials
//==============================================================================

class PolynomialBasisFilter : public Filter {
public:
  //----------------------------------------------------------------------------
  // Enum for polynomial types
  
  enum class PolynomialType {
    LEGENDRE,      // Legendre polynomials (orthogonal on [-1,1])
    CHEBYSHEV_1,   // Chebyshev polynomials of the first kind
    CHEBYSHEV_2,   // Chebyshev polynomials of the second kind  
    HERMITE,       // Hermite polynomials (orthogonal on (-inf,inf))
    LAGUERRE       // Laguerre polynomials (orthogonal on [0,inf))
  };

  //----------------------------------------------------------------------------
  // Methods

  std::string type_str() const override { return "polynomialbasis"; }
  FilterType type() const override { return FilterType::POLYNOMIAL_BASIS; }

  void from_xml(pugi::xml_node node) override;

  void get_all_bins(const Particle& p, TallyEstimator estimator,
    FilterMatch& match) const override;

  void to_statepoint(hid_t filter_group) const override;

  std::string text_label(int bin) const override;

  //----------------------------------------------------------------------------
  // Accessors

  int order() const { return order_; }
  void set_order(int order);

  PolynomialType poly_type() const { return poly_type_; }
  void set_poly_type(PolynomialType type);
  void set_poly_type(const std::string& type);

  char axis() const { return axis_; }
  void set_axis(char axis);

  double minimum() const { return min_; }
  double maximum() const { return max_; }
  void set_range(double min, double max);

private:
  //----------------------------------------------------------------------------
  // Data members

  //! Polynomial type
  PolynomialType poly_type_ {PolynomialType::LEGENDRE};

  //! Polynomial order
  int order_ {0};

  //! Axis along which to expand ('x', 'y', or 'z')
  char axis_ {'x'};

  //! Minimum coordinate value
  double min_ {-1.0};

  //! Maximum coordinate value
  double max_ {1.0};
};

} // namespace openmc
#endif // OPENMC_TALLIES_FILTER_GENERIC_BASIS_H
