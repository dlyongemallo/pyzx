# PyZX - Python library for quantum circuit rewriting
#        and optimization using the ZX-calculus
# Copyright (C) 2018 - Aleks Kissinger and John van de Wetering

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#    http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import unittest
import random
import sys
import os
if __name__ == '__main__':
    sys.path.append('..')
    sys.path.append('.')
mydir = os.path.dirname(__file__)

try:
    import numpy as np
    from pyzx.tensor import compare_tensors
except ImportError:
    np = None

from pyzx.circuit import Circuit
from fractions import Fraction

@unittest.skipUnless(np, "numpy needs to be installed for this to run")
class TestCircuit(unittest.TestCase):
    def setUp(self):
        c = Circuit(1)
        c.add_gate("YPhase", 0, Fraction(1, 4))
        self.c = c
    def test_to_qasm_and_back(self):
        s = self.c.to_qasm()
        c1 = Circuit.from_qasm(s)
        self.assertEqual(self.c.qubits, c1.qubits)
        self.assertListEqual(self.c.gates,c1.gates)

    def test_load_qasm_from_file(self):
        c1 = Circuit.from_qasm_file(os.path.join(mydir,"ry.qasm"))
        self.assertEqual(c1.qubits, self.c.qubits)
        self.assertListEqual(c1.gates,self.c.gates)

    def test_ry_preserves_graph_semantics(self):
        t = self.c.to_matrix()
        expected_t = np.asarray([[np.cos(np.pi/8), -np.sin(np.pi/8)], [np.sin(np.pi/8), np.cos(np.pi/8)]])
        self.assertTrue(compare_tensors(t, expected_t, False))
