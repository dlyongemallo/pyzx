#!/usr/bin/env python3
"""Simple test for multi-controlled gates - imports only what we need"""

import sys
sys.path.insert(0, '/home/davinci/workspace/pyzx')

from fractions import Fraction

# Import the gates module directly
from pyzx.circuit.gates import (
    U0, RCCX, RC3X, C3X, C3SQRTX, C4X,
    qasm_gate_table
)

print("Testing multi-controlled gates from OpenQASM 2 qelib1.inc...")
print("=" * 70)
print()

# Test 1: Check if gates are in qasm_gate_table
print("1. Checking qasm_gate_table registration:")
gate_names = ['u0', 'rccx', 'rc3x', 'c3x', 'c3sqrtx', 'c4x']
for gate_name in gate_names:
    if gate_name in qasm_gate_table:
        print(f"  ✓ {gate_name} is registered")
    else:
        print(f"  ✗ {gate_name} is NOT registered")
print()

# Test 2: Instantiate gates
print("2. Testing gate instantiation:")
try:
    u0_gate = U0(0, Fraction(1,2))
    print(f"  ✓ U0 gate created: {u0_gate}")
except Exception as e:
    print(f"  ✗ U0 gate failed: {e}")

try:
    rccx_gate = RCCX(0, 1, 2)
    print(f"  ✓ RCCX gate created: {rccx_gate}")
except Exception as e:
    print(f"  ✗ RCCX gate failed: {e}")

try:
    rc3x_gate = RC3X(0, 1, 2, 3)
    print(f"  ✓ RC3X gate created: {rc3x_gate}")
except Exception as e:
    print(f"  ✗ RC3X gate failed: {e}")

try:
    c3x_gate = C3X(0, 1, 2, 3)
    print(f"  ✓ C3X gate created: {c3x_gate}")
except Exception as e:
    print(f"  ✗ C3X gate failed: {e}")

try:
    c3sqrtx_gate = C3SQRTX(0, 1, 2, 3)
    print(f"  ✓ C3SQRTX gate created: {c3sqrtx_gate}")
except Exception as e:
    print(f"  ✗ C3SQRTX gate failed: {e}")

try:
    c4x_gate = C4X(0, 1, 2, 3, 4)
    print(f"  ✓ C4X gate created: {c4x_gate}")
except Exception as e:
    print(f"  ✗ C4X gate failed: {e}")
print()

# Test 3: Test decomposition
print("3. Testing gate decomposition:")
try:
    u0_gate = U0(0, Fraction(1,2))
    basic = u0_gate.to_basic_gates()
    print(f"  ✓ U0 decomposes to {len(basic)} gates (should be 0 for identity)")
except Exception as e:
    print(f"  ✗ U0 decomposition failed: {e}")

try:
    rccx_gate = RCCX(0, 1, 2)
    basic = rccx_gate.to_basic_gates()
    print(f"  ✓ RCCX decomposes to {len(basic)} basic gates")
except Exception as e:
    print(f"  ✗ RCCX decomposition failed: {e}")

try:
    rc3x_gate = RC3X(0, 1, 2, 3)
    basic = rc3x_gate.to_basic_gates()
    print(f"  ✓ RC3X decomposes to {len(basic)} basic gates")
except Exception as e:
    print(f"  ✗ RC3X decomposition failed: {e}")

try:
    c3x_gate = C3X(0, 1, 2, 3)
    basic = c3x_gate.to_basic_gates()
    print(f"  ✓ C3X decomposes to {len(basic)} basic gates")
    print(f"    - T-count: {c3x_gate.tcount()}")
except Exception as e:
    print(f"  ✗ C3X decomposition failed: {e}")

try:
    c3sqrtx_gate = C3SQRTX(0, 1, 2, 3)
    basic = c3sqrtx_gate.to_basic_gates()
    print(f"  ✓ C3SQRTX decomposes to {len(basic)} basic gates")
except Exception as e:
    print(f"  ✗ C3SQRTX decomposition failed: {e}")

try:
    c4x_gate = C4X(0, 1, 2, 3, 4)
    basic = c4x_gate.to_basic_gates()
    print(f"  ✓ C4X decomposes to {len(basic)} basic gates")
    print(f"    - T-count: {c4x_gate.tcount()}")
except Exception as e:
    print(f"  ✗ C4X decomposition failed: {e}")

print()
print("=" * 70)
print("All gate instantiation tests completed! ✓")
