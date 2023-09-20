import pyzx as zx
from pyzx.tensor import compare_tensors, find_scalar_correction
from pyzx.circuit import Circuit
from qiskit import quantum_info
from qiskit.circuit import QuantumCircuit
from qiskit.qasm3 import loads



print("qasm2: rz")
qasm2_rz = zx.qasm("""
OPENQASM 2.0;
include "qelib1.inc";
qreg q[1];
rz(0.8*pi) q[0];
""")
t1 = qasm2_rz.to_matrix()
print(t1)
qiskit_rz = QuantumCircuit.from_qasm_str(qasm2_rz.to_qasm())
t2 = quantum_info.Operator(qiskit_rz).data
print(t2)
print(compare_tensors(t1, t2, False))

# print("qasm3: rz")
# qasm3_rz = zx.qasm("""
# OPENQASM 3;
# include "stdgates.inc";
# qreg q[1];
# rz(pi/2) q[0];
# """)
# print(qasm3_rz.to_matrix())
# print(QuantumCircuit.from_qasm_str(qasm3_rz.to_qasm()))
# qiskit_rz = QuantumCircuit.from_qasm_str(qasm3_rz.to_qasm())
# print(quantum_info.Operator(qiskit_rz).data)
# print(qiskit_rz.qasm())

# print("qasm2: crz")
# qasm2_crz = zx.qasm("""
# OPENQASM 2.0;
# include "qelib1.inc";
# qreg q[2];
# crz(pi/2) q[0], q[1];
# """)
# print(qasm2_crz.to_matrix())
# print(QuantumCircuit.from_qasm_str(qasm2_crz.to_qasm()))
# qiskit_swap = QuantumCircuit(2)
# qiskit_swap.swap(0,1)
# qiskit_crz = qiskit_swap & QuantumCircuit.from_qasm_str(qasm2_crz.to_qasm()) & qiskit_swap
# print(quantum_info.Operator(qiskit_crz).data)
# print(qiskit_crz.qasm())

# qasm3 = zx.qasm("""
# OPENQASM 3;
# include "stdgates.inc";
# qubit[3] q0;
# p(pi) q0[0];
# x q0[0];
# // y q0[0];
# z q0[0];
# h q0[0];
# s q0[0];
# sdg q0[0];
# t q0[0];
# tdg q0[0];
# // sx q0[0];
# rx(pi) q0[0];
# ry(pi) q0[0];
# rz(pi) q0[0];
# cx q0[0], q0[1];
# // cy q0[0], q0[1];
# cz q0[0], q0[1];
# // cp(pi) q0[0], q0[1];
# // crx(pi) q0[0], q0[1];
# // cry(pi) q0[0], q0[1];
# crz(pi) q0[0], q0[1];
# ch q0[0], q0[1];
# swap q0[0], q0[1];
# ccx q0[0], q0[1], q0[2];
# // cswap q0[0], q0[1], q0[2];
# // cu(pi, pi, pi, pi) q0[0], q0[1];  // supported gate, but not with pi
# id q0[0];
# """)
# print(QuantumCircuit.from_qasm_str(qasm3.to_qasm()))

# qasm2_wire = zx.qasm("""
# OPENQASM 2.0;
# include "qelib1.inc";
# qreg q0[1];
# creg c0[1];
# measure q0[0] -> c0[0];
# """)
# print(QuantumCircuit.from_qasm_str(qasm2_wire.to_qasm()))
#
# qasm3_wire = zx.qasm("""
# OPENQASM 3;
# include "stdgates.inc";
# bit[1] c0;
# qubit[1] q0;
# c0[0] = measure q0[0];
# """)
# print(QuantumCircuit.from_qasm_str(qasm3_wire.to_qasm()))
#
#
# qasm2_bell_state = zx.qasm("""
# OPENQASM 2.0;
# include "qelib1.inc";
# qreg q0[2];
# creg c0[2];
# h q0[0];
# cx q0[0],q0[1];
# measure q0[0] -> c0[0];
# measure q0[1] -> c0[1];
# """)
# print(QuantumCircuit.from_qasm_str(qasm2_bell_state.to_qasm()))
#
# qasm3_bell_state = zx.qasm("""
# OPENQASM 3;
# include "stdgates.inc";
# bit[2] c0;
# qubit[2] q0;
# h q0[0];
# cx q0[0], q0[1];
# c0[0] = measure q0[0];
# c0[1] = measure q0[1];
# """)
# print(QuantumCircuit.from_qasm_str(qasm3_bell_state.to_qasm()))
#
# qasm2_deutsch = zx.qasm("""
# OPENQASM 2.0;
# include "qelib1.inc";
# qreg q[2];
# creg c[1];
# x q[1];
# barrier q[0],q[1];
# h q[0];
# h q[1];
# barrier q[0],q[1];
# cx q[0],q[1];
# x q[1];
# cx q[0],q[1];
# barrier q[0],q[1];
# h q[0];
# measure q[0] -> c[0];
# """)
# print(QuantumCircuit.from_qasm_str(qasm2_deutsch.to_qasm()))
#
# qasm3_deutsch = zx.qasm("""
# OPENQASM 3;
# include "stdgates.inc";
# bit[1] c;
# qubit[2] q;
# x q[1];
# barrier q[0], q[1];
# h q[0];
# h q[1];
# barrier q[0], q[1];
# cx q[0], q[1];
# x q[1];
# cx q[0], q[1];
# barrier q[0], q[1];
# h q[0];
# c[0] = measure q[0];
# """)
# print(QuantumCircuit.from_qasm_str(qasm2_deutsch.to_qasm()))
#
# qasm2_ghz = zx.qasm("""
# OPENQASM 2.0;
# include "qelib1.inc";
# qreg q0[3];
# creg c0[3];
# h q0[0];
# cx q0[0],q0[1];
# cx q0[0],q0[2];
# measure q0[0] -> c0[0];
# measure q0[1] -> c0[1];
# measure q0[2] -> c0[2];
# """)
# print(QuantumCircuit.from_qasm_str(qasm2_ghz.to_qasm()))
#
# qasm2_ghz = zx.qasm("""
# OPENQASM 3;
# include "stdgates.inc";
# bit[3] c0;
# qubit[3] q0;
# h q0[0];
# cx q0[0], q0[1];
# cx q0[0], q0[2];
# c0[0] = measure q0[0];
# c0[1] = measure q0[1];
# c0[2] = measure q0[2];
# """)
# print(QuantumCircuit.from_qasm_str(qasm2_ghz.to_qasm()))
#
# qasm2_hardy = zx.qasm("""
# OPENQASM 2.0;
# include "qelib1.inc";
# gate unitary q0 { u3(1.9106332362490186,0,pi) q0; }
# qreg q[2];
# creg c[2];
# unitary q[0];
# ch q[0],q[1];
# cx q[1],q[0];
# measure q[0] -> c[0];
# measure q[1] -> c[1];
# """)
# print(QuantumCircuit.from_qasm_str(qasm2_hardy.to_qasm()))

# hardy is broken for qasm3?

