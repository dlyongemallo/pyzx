from qiskit import QuantumCircuit
import pyzx
from pyzx.circuit.qiskitqasmparser import QiskitQASMParser

qc = QuantumCircuit(2)
qc.y(0)
qc.cx(1,0)
p = QiskitQASMParser()
p.qiskitparse(qc.decompose().qasm())

