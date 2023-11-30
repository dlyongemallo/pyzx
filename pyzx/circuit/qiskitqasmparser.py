# PyZX - Python library for quantum circuit rewriting
#        and optimisation using the ZX-calculus
# Copyright (C) 2018 - Aleks Kissinger and John van de Wetering

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


import sys
import math
from fractions import Fraction

from . import Circuit
from .gates import qasm_gate_table, ZPhase, XPhase
from .qasmparser import QASMParser

class QiskitQASMParser(QASMParser):
    """Class for parsing QASM source files into circuit descriptions."""
    def qiskitparse(self, s, strict=True):
        lines = s.splitlines()
        r = []
        #strip comments
        for s in lines:
            if s.find("//")!=-1:
                t = s[0:s.find("//")].strip()
            else: t = s.strip()
            if t: r.append(t)

        if r[0].startswith("OPENQASM"):
            r.pop(0)
        elif strict:
            raise TypeError("File does not start with OPENQASM descriptor")

        if r[0].startswith('include "qelib1.inc";'):
            r.pop(0)
        elif strict:
            raise TypeError("File is not importing standard library")

        data = "\n".join(r)
        # Strip the custom command definitions from the normal commands
        while True:
            i = data.find("gate ")
            if i == -1: break
            j = data.find("}", i)
            self.parse_custom_gate(data[i:j+1])
            data = data[:i] + data[j+1:]
        #parse the regular commands
        commands = [s.strip() for s in data.split(";") if s.strip()]
        circuit_list = [] #list of circuits (some qiskit qasm, some pyzx circuits)
        whichpyzx = [] #which indexed circuits in circuit_list are pyzx circuits
        self.gates = [] #current list of gates

        for k in range(len(commands)):
            c = commands[k]
            pc = self.parse_command(c, self.registers)
            if pc is None:
                if self.gates:
                    circ = Circuit(self.qubit_count)
                    circ.gates = self.gates
                    whichpyzx.append(len(circuit_list))
                    circuit_list.append(circ)
                    self.gates = []
                circuit_list.append(c+';')
            else:
                self.gates += pc if isinstance(pc, list) else [pc]
                if k == len(commands) - 1:
                    circ = Circuit(self.qubit_count)
                    circ.gates = self.gates
                    whichpyzx.append(len(circuit_list))
                    circuit_list.append(circ)
                    self.gates = []
        return circuit_list, whichpyzx

    def parse_command(self, c, registers):
        name, rest = c.split(" ", 1)
        if name in ("barrier", "measure"):
            return None
        if name == "y":
            pc0 = super().parse_command("z " + rest, registers)
            pc1 = super().parse_command("x " + rest, registers)
            return [pc0[0], pc1[0]]
        elif name.startswith("ry"):
            return self.parse_command("u3" + name[2:name.find(')')] + ',0,0) ' + rest, registers)
        elif name.startswith("u1"):
            name, rest = c.split("(", 1)
            c = "rz(" + rest
        elif name.startswith("u2") or name.startswith("u3"):
            i = name.find('(')
            j = name.find(')')
            if i == -1 or j == -1: raise TypeError("Invalid specification {}".format(name))
            vals = name[i+1:j]
            args = [s.strip() for s in vals.split(",") if s.strip()]
            phases = []
            for val in args:
                phases.append(self.parse_phase(val, name))
            if name.startswith("u2"):
                rot = [phases[0] + 0.5, 0.5, phases[1] - 0.5]
                pc0 = super().parse_command("rz(" + str(rot[0]) + "*pi) " + rest, registers)
                pc1 = super().parse_command("rx(" + str(rot[1]) + "*pi) " + rest, registers)
                pc2 = super().parse_command("rz(" + str(rot[2]) + "*pi) " + rest, registers)
                return [pc0[0], pc1[0], pc2[0]]
            if name.startswith("u3"):
                rot = [phases[1] + 0.5, phases[0], phases[2] - 0.5]
                pc0 = super().parse_command("rz(" + str(rot[0]) + "*pi) " + rest, registers)
                pc1 = super().parse_command("rx(" + str(rot[1]) + "*pi) " + rest, registers)
                pc2 = super().parse_command("rz(" + str(rot[2]) + "*pi) " + rest, registers)
                return [pc0[0], pc1[0], pc2[0]]
        try:
            pc = super().parse_command(c, registers)
        except TypeError:
            return None
        except:
            print()
            sys.stdout.flush()
            return None
        if c.startswith("qreg") or c.startswith("creg"):
            return None
        else:
            return pc

    def parse_phase(self, val, name=None):
        if val.startswith("pi"):
            val = "1*pi" + val[2:]
        elif val.startswith("-pi"):
            val = "-1*pi" + val[3:]
        try:
            phase = float(val)/math.pi
        except ValueError:
            if val.find('pi') == -1: raise TypeError("Invalid specification {}".format(name))
            val = val.replace('pi', '')
            val = val.replace('*','')
            try:
                phase = float(val)
            except:
                if val.find('/') == -1: raise TypeError("Invalid specification {}".format(name))
                phase = float(val[:val.find('/')]) / float(val[val.find('/') + 1:])
        phase = Fraction(phase).limit_denominator(100000000)
        return float(phase)
