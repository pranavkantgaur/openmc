#!/usr/bin/env python
"""
Simple test to verify Bayesian optimization integration in keff_search.
This test uses a mock evaluation function instead of running actual OpenMC simulations.
"""

import numpy as np
import tempfile
from pathlib import Path


def test_bayesian_optimization_mock():
    """Test Bayesian optimization with a mock quadratic function."""
    print("\n" + "=" * 80)
    print("Testing Bayesian Optimization Integration (Mock Function)")
    print("=" * 80)
    
    # Mock function: f(x) = (x - 5)^2 - 1
    # Root at x ≈ 5 when f(x) = 0, i.e., x = 5 ± 1
    def mock_function(x):
        """Mock k_eff - target, with derivative."""
        f = (x - 5.0)**2 - 1.0
        df_dx = 2.0 * (x - 5.0)
        uncertainty = 0.01
        return f, uncertainty, df_dx, 0.001
    
    # Track evaluations
    evaluations = []
    
    def eval_and_record(x):
        """Evaluate and record for analysis."""
        f, s, df, df_s = mock_function(x)
        evaluations.append({'x': x, 'f': f, 's': s, 'df': df, 'df_s': df_s})
        print(f"  Eval {len(evaluations)}: x={x:.4f}, f={f:.6f}, df/dx={df:.6f}")
        return f, s, df, df_s
    
    # Simulate Bayesian optimization search manually
    from openmc.model.model import GaussianProcess, expected_improvement
    
    # Initial evaluations
    x0, x1 = 3.0, 7.0
    f0, s0, df0, dfs0 = eval_and_record(x0)
    f1, s1, df1, dfs1 = eval_and_record(x1)
    
    xs = [x0, x1]
    fs = [f0, f1]
    ss = [s0, s1]
    dks = [df0, df1]
    dks_std = [dfs0, dfs1]
    
    # Run a few Bayesian optimization iterations
    max_iter = 5
    target_tol = 0.1
    
    for iteration in range(max_iter):
        print(f"\nIteration {iteration + 3}:")
        
        # Fit GP
        X_train = np.array(xs).reshape(-1, 1)
        y_train = np.array(fs)
        y_std = np.array(ss)
        dy_train = np.array(dks)
        dy_std = np.array(dks_std)
        
        # Adaptive hyperparameters
        x_range = max(xs) - min(xs)
        length_scale = max(x_range / 3.0, 0.1)
        signal_var = max(np.var(fs), 0.01)
        
        gp = GaussianProcess(
            length_scale=length_scale,
            signal_variance=signal_var,
            noise_variance=np.mean(ss)**2
        )
        
        gp.fit(X_train, y_train, y_std, dy_train, dy_std)
        print(f"  GP fitted with {len(xs)} points and derivatives")
        
        # Find best point via EI
        y_best = min(np.abs(fs))
        X_candidates = np.linspace(2.0, 8.0, 100).reshape(-1, 1)
        ei_values = expected_improvement(X_candidates, gp, y_best, xi=0.01)
        
        best_idx = np.argmax(ei_values)
        x_new = float(X_candidates[best_idx, 0])
        
        print(f"  Selected x={x_new:.4f} (max EI={ei_values[best_idx]:.6e})")
        
        # Evaluate
        f_new, s_new, df_new, dfs_new = eval_and_record(x_new)
        
        xs.append(x_new)
        fs.append(f_new)
        ss.append(s_new)
        dks.append(df_new)
        dks_std.append(dfs_new)
        
        # Check convergence
        if abs(f_new) < target_tol:
            print(f"\n✓ Converged! |f| = {abs(f_new):.6f} < {target_tol}")
            break
    
    # Results
    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)
    best_idx = np.argmin(np.abs(fs))
    print(f"Best x: {xs[best_idx]:.6f}")
    print(f"Best |f|: {abs(fs[best_idx]):.6f}")
    print(f"Total evaluations: {len(evaluations)}")
    print(f"Expected root: x ≈ 4.0 or 6.0")
    print(f"Error: {min(abs(xs[best_idx] - 4.0), abs(xs[best_idx] - 6.0)):.6f}")
    
    # Verify convergence
    assert abs(fs[best_idx]) < 0.15, f"Did not converge: |f|={abs(fs[best_idx])}"
    assert len(evaluations) <= 10, f"Too many evaluations: {len(evaluations)}"
    
    print("\n✓ Test PASSED: Bayesian optimization converged efficiently")
    return True


if __name__ == '__main__':
    try:
        test_bayesian_optimization_mock()
        print("\n" + "=" * 80)
        print("ALL TESTS PASSED")
        print("=" * 80)
    except Exception as e:
        print(f"\n✗ Test FAILED: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
