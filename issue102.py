import pyzx as zx
import numpy as np
from pyzx.circuit import Circuit
from pyzx.tensor import compare_tensors, find_scalar_correction
from qiskit import QuantumCircuit, Aer, transpile, quantum_info
# from qiskit.providers.aer.library import save_unitary

# qc=QuantumCircuit(2)
# qc.crz(0.5*np.pi,1,0)

qc=QuantumCircuit(4)
qc.ccx(2,1,0)
qc.ccz(0,1,2)
qc.h(1)
qc.ccx(1,2,3)
qc.t(1)
qc.ccz(0,1,2)
qc.h(1)
qc.t(0)
qc.ccz(2,1,0)
qc.s(1)
qc.ccx(2,1,0)
qc.crz(0.2*np.pi,0,1)
qc.rz(0.8*np.pi,1)
qc.cry(0.4*np.pi,2,1)
qc.crx(0.02*np.pi,2,0)

simulator = Aer.get_backend('unitary_simulator')
qc1 = transpile(qc, simulator)
# qc1 = transpile(qc)
# qc1.save_unitary()
# print(qc1)
mat1 = quantum_info.Operator(qc1).data
# result = simulator.run(qc1).result()
# mat1 = np.asarray(result.get_unitary(qc1))
# print(*mat1.tolist(), "", sep="\n")

c=Circuit.from_qasm(qc1.qasm())
print(qc1.qasm())
g1 = c.to_graph()
zx.simplify.full_reduce(g1)
g1 = zx.extract_circuit(g1).to_basic_gates()
qasm = g1.to_qasm()
print(qasm)

# n=g1.qubits
# qc2=QuantumCircuit(n)
# for g in g1.gates:
#     print(g)
#     if g.name == 'SWAP':
#         qc2.swap(g.control,g.target)
#     if g.name == 'HAD':
#         qc2.h(g.target)
#     if g.name == 'ZPhase':
#         qc2.p(g.phase*np.pi,g.target)
#     if g.name == 'CZ':
#         qc2.cz(g.control, g.target)
#     if g.name == 'CNOT':
#         qc2.cx(g.control, g.target)
#     if g.name == 'S':
#         qc2.p(g.phase*np.pi, g.target)
#     if g.name == 'T':
#         qc2.p(g.phase*np.pi, g.target)
#     if g.name == 'XPhase':
#         qc2.rx(g.phase*np.pi, g.target)
#     if g.name == 'CCZ':
#         qc2.ccz(g.ctrl1,g.ctrl2,g.target)
#     if g.name=='CHAD':
#         qc2.ch(g.control,g.target)
#     if g.name == 'CRZ':
#         qc2.crz(g.control,g.target,g.phase)
#     if g.name=='Tof':
#         qc2.ccx(g.ctrl1,g.ctrl2,g.target)

# qc2.save_unitary()
qc2 = QuantumCircuit().from_qasm_str(qasm)
# print(qc2.qasm())
mat2 = quantum_info.Operator(qc2).data
# result = simulator.run(qc2).result()
# mat2 = np.asarray(result.get_unitary(qc2))
# print(*mat2.tolist(), "", sep="\n")

print(compare_tensors(mat1, mat2, False))
print(find_scalar_correction(mat1, mat2))
