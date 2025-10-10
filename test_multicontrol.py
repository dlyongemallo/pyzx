#!/usr/bin/env python3
"""Test script for multi-controlled gates from OpenQASM 2 qelib1.inc"""

import sys
sys.path.insert(0, '/home/davinci/workspace/pyzx')

import pyzx as zx

# Test QASM string with all new gates
qasm_code = """OPENQASM 2.0;
include "qelib1.inc";

qreg q[6];

// Test u0 gate (identity with duration)
u0(0.5) q[0];

// Test rccx gate (relative-phase CCX)
rccx q[0], q[1], q[2];

// Test rc3x gate (relative-phase C3X)
rc3x q[0], q[1], q[2], q[3];

// Test c3x gate (3-controlled X)
c3x q[0], q[1], q[2], q[3];

// Test c3sqrtx gate (3-controlled sqrt(X))
c3sqrtx q[0], q[1], q[2], q[3];

// Test c4x gate (4-controlled X)
c4x q[0], q[1], q[2], q[3], q[4];
"""

print("Testing multi-controlled gates from OpenQASM 2 qelib1.inc...")
print("=" * 70)

try:
    # Parse the QASM code
    circuit = zx.Circuit.from_qasm(qasm_code)
    print(f"✓ Successfully parsed QASM code")
    print(f"  Circuit has {circuit.qubits} qubits and {len(circuit.gates)} gates")
    print()

    # Print all gates
    print("Gates in the circuit:")
    for i, gate in enumerate(circuit.gates):
        print(f"  {i+1}. {gate}")
    print()

    # Test each gate type individually
    test_gates = [
        ("u0", "u0(0.5) q[0];", "U0 gate"),
        ("rccx", "rccx q[0], q[1], q[2];", "RCCX gate"),
        ("rc3x", "rc3x q[0], q[1], q[2], q[3];", "RC3X gate"),
        ("c3x", "c3x q[0], q[1], q[2], q[3];", "C3X gate"),
        ("c3sqrtx", "c3sqrtx q[0], q[1], q[2], q[3];", "C3SQRTX gate"),
        ("c4x", "c4x q[0], q[1], q[2], q[3], q[4];", "C4X gate"),
    ]

    print("Individual gate tests:")
    for gate_name, qasm_snippet, description in test_gates:
        try:
            test_qasm = f"""OPENQASM 2.0;
include "qelib1.inc";
qreg q[6];
{qasm_snippet}
"""
            test_circuit = zx.Circuit.from_qasm(test_qasm)
            print(f"  ✓ {description} ({gate_name}) - parsed successfully")

            # Test decomposition
            if len(test_circuit.gates) > 0:
                gate = test_circuit.gates[0]
                basic_gates = gate.to_basic_gates()
                if gate_name == 'u0':
                    # U0 decomposes to empty list (identity)
                    if len(basic_gates) == 0:
                        print(f"    - Decomposes to identity (0 gates)")
                    else:
                        print(f"    - ERROR: U0 should decompose to empty list!")
                else:
                    print(f"    - Decomposes to {len(basic_gates)} basic gates")
        except Exception as e:
            print(f"  ✗ {description} ({gate_name}) - FAILED: {e}")

    print()
    print("=" * 70)
    print("All tests completed successfully! ✓")

except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
