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

import abc
import math
import cmath
import copy
from fractions import Fraction
from typing import Union, Optional, Generic, TypeVar, Any
from typing import List, Dict, Set, Tuple, Mapping, Iterable, Callable
from typing_extensions import Literal

import numpy as np

from ..utils import EdgeType, VertexType, toggle_edge, vertex_is_zx, toggle_vertex
from ..utils import FloatInt, FractionLike
from ..tensor import tensorfy, tensor_to_matrix
from ..simplify import Simplifier

def cexp(val) -> complex:
    return cmath.exp(1j*math.pi*val)

class Scalar(object):
    def __init__(self) -> None:
        self.power2: int = 0 # Stores power of square root of two
        self.phase: Fraction = Fraction(0) # Stores complex phase of the number
        self.phasenodes: List[FractionLike] = [] # Stores list of legless spiders, by their phases.
        self.floatfactor: complex = 1.0
        self.is_unknown: bool = False # Whether this represents an unknown scalar value
        self.is_zero: bool = False

    def __repr__(self) -> str:
        return "Scalar({})".format(str(self))

    def __str__(self) -> str:
        if self.is_unknown:
            return "UNKNOWN"
        s = "{0.real:.2f}{0.imag:+.2f}i = ".format(self.to_number())
        if self.floatfactor != 1.0:
            s += "{0.real:.2f}{0.imag:+.2f}i".format(self.floatfactor)
        if self.phase:
            s += "exp({}ipi)".format(str(self.phase))
        s += "sqrt(2)^{:d}".format(self.power2)
        for node in self.phasenodes:
            s += "(1+exp({}ipi))".format(str(node))
        return s

    def __complex__(self) -> complex:
        return self.to_number()

    def copy(self) -> 'Scalar':
        s = Scalar()
        s.power2 = self.power2
        s.phase = self.phase
        s.phasenodes = copy.copy(self.phasenodes)
        s.floatfactor = self.floatfactor
        s.is_unknown = self.is_unknown
        s.is_zero = self.is_zero
        return s

    def to_number(self) -> complex:
        val = cexp(self.phase)
        for node in self.phasenodes: # Node should be a Fraction
            val *= 1+cexp(node)
        val *= math.sqrt(2)**self.power2
        return complex(val*self.floatfactor)

    def set_unknown(self) -> None:
        self.is_unknown = True
        self.phasenodes = []

    def add_power(self, n) -> None:
        self.power2 += n
    def add_phase(self, phase: FractionLike) -> None:
        self.phase = (self.phase + phase) % 2
    def add_node(self, node: FractionLike) -> None:
        self.phasenodes.append(node)
        if node == 1: self.is_zero = True
    def add_float(self,f: complex) -> None:
        self.floatfactor *= f

    def mult_with_scalar(self, other: 'Scalar') -> None:
    	self.power2 += other.power2
    	self.phase = (self.phase +other.phase)%2
    	self.phasenodes.extend(other.phasenodes)
    	self.floatfactor *= other.floatfactor
    	if other.is_zero: self.is_zero = True
    	if other.is_unknown: self.is_unknown = True

    def add_spider_pair(self, p1: FractionLike,p2: FractionLike) -> None:
        """Add the scalar corresponding to a connected pair of spiders (p1)-H-(p2)."""
        # These if statements look quite arbitary, but they are just calculations of the scalar
        # of a pair of connected single wire spiders of opposite colours.
        # We make special cases for Clifford phases and pi/4 phases.
        if p2 in (0,1):
            p1,p2 = p2, p1
        if p1 == 0:
            self.add_power(1)
            return
        elif p1 == 1:
            self.add_power(1)
            self.add_phase(p2)
            return
        if p2.denominator == 2:
            p1, p2 = p2, p1
        if p1 == Fraction(1,2):
            self.add_phase(Fraction(1,4))
            self.add_node((p2-Fraction(1,2))%2)
            return
        elif p1 == Fraction(3,2):
            self.add_phase(Fraction(7,4))
            self.add_node((p2-Fraction(3,2))%2)
            return
        if (p1 + p2) % 2 == 0:
            if p1.denominator == 4:
                if p1.numerator in (3,5):
                    self.add_phase(Fraction(1))
                return
            self.add_power(1)
            self.add_float(math.cos(p1))
            return
        # Generic case
        self.add_power(-1)
        self.add_float(1+cexp(p1)+cexp(p2) - cexp(p1+p2))
        return


class DocstringMeta(abc.ABCMeta):
    """Metaclass that allows docstring 'inheritance'."""

    def __new__(mcls, classname, bases, cls_dict):
        cls = abc.ABCMeta.__new__(mcls, classname, bases, cls_dict)
        mro = cls.__mro__[1:]
        for name, member in cls_dict.items():
            if not getattr(member, '__doc__'):
                for base in mro:
                    try:
                        member.__doc__ = getattr(base, name).__doc__
                        break
                    except AttributeError:
                        pass
        return cls

def pack_indices(lst: List[FloatInt]) -> Mapping[FloatInt,int]:
    d: Dict[FloatInt,int] = dict()
    if len(lst) == 0: return d
    list.sort(lst)
    i: int = 0
    x: Optional[FloatInt] = None
    for j in range(len(lst)):
        y = lst[j]
        if y != x:
            x = y
            d[y] = i
            i += 1
    return d

VT = TypeVar('VT') # The type that is used for representing vertices (e.g. an integer)
ET = TypeVar('ET') # The type used for representing edges (e.g. a pair of integers)

class BaseGraph(Generic[VT, ET], metaclass=DocstringMeta):
    """Base class for letting graph backends interact with PyZX.
    For a backend to work with PyZX, there should be a class that implements
    all the methods of this class. For implementations of this class see 
    :class:`~graph.graph_s.GraphS` or :class `~graph.graph_ig.GraphIG`."""

    backend: str = 'None'

    def __init__(self) -> None:
        self.scalar: Scalar = Scalar()
        self.inputs: List[VT] = []
        self.outputs: List[VT] = []
        #Data necessary for phase tracking for phase teleportation
        self.track_phases: bool = False
        self.phase_index : Dict[VT,int] = dict() # {vertex:index tracking its phase for phase teleportation}
        self.phase_master: Optional[Simplifier] = None
        self.phase_mult: Dict[int,Literal[1,-1]] = dict()
        self.max_phase_index: int = -1

        # merge_vdata(v0,v1) is an optional, custom function for merging
        # vdata of v1 into v0 during spider fusion etc.
        self.merge_vdata: Optional[Callable[[VT,VT], None]] = None

    def __str__(self) -> str:
        return "Graph({} vertices, {} edges)".format(
                str(self.num_vertices()),str(self.num_edges()))

    def __repr__(self) -> str:
        return str(self)

    def stats(self) -> str:
        s = str(self) + "\n"
        degrees: Dict[int,int] = {}
        for v in self.vertices():
            d = self.vertex_degree(v)
            if d in degrees: degrees[d] += 1
            else: degrees[d] = 1
        s += "degree distribution: \n"
        for d, n in sorted(degrees.items(),key=lambda x: x[0]):
            s += "{:d}: {:d}\n".format(d,n)
        return s

    def copy(self, adjoint:bool=False, backend:Optional[str]=None) -> 'BaseGraph':
        """Create a copy of the graph. If ``adjoint`` is set, 
        the adjoint of the graph will be returned (inputs and outputs flipped, phases reversed).
        When ``backend`` is set, a copy of the graph with the given backend is produced. 
        By default the copy will have the same backend.

        `Note`: The copy will have consecutive vertex indices, even if the original
        graph did not.
        """
        from .graph import Graph # imported here to prevent circularity
        if (backend is None):
            backend = type(self).backend
        g = Graph(backend = backend)
        g.track_phases = self.track_phases
        g.scalar = self.scalar.copy()
        g.merge_vdata = self.merge_vdata
        mult:int = 1
        if adjoint: mult = -1

        #g.add_vertices(self.num_vertices())
        ty = self.types()
        ph = self.phases()
        qs = self.qubits()
        rs = self.rows()
        maxr = self.depth()
        vtab = dict()
        for v in self.vertices():
            i = g.add_vertex(ty[v],phase=mult*ph[v])
            if v in qs: g.set_qubit(i,qs[v])
            if v in rs: 
                if adjoint: g.set_row(i, maxr-rs[v])
                else: g.set_row(i, rs[v])
            vtab[v] = i
            for k in self.vdata_keys(v):
                g.set_vdata(i, k, self.vdata(v, k))

        for i in self.inputs:
            if adjoint: g.outputs.append(vtab[i])
            else: g.inputs.append(vtab[i])
        for o in self.outputs:
            if adjoint: g.inputs.append(vtab[o])
            else: g.outputs.append(vtab[o])
        
        etab = {e:g.edge(vtab[self.edge_s(e)],vtab[self.edge_t(e)]) for e in self.edges()}
        g.add_edges(etab.values())
        for e,f in etab.items():
            g.set_edge_type(f, self.edge_type(e))
        return g
    def adjoint(self) -> 'BaseGraph':
        """Returns a new graph equal to the adjoint of this graph."""
        return self.copy(adjoint=True)

    def map_qubits(self, qubit_map:Mapping[int,Tuple[float,float]]) -> None:
        for v in self.vertices():
            q = self.qubit(v)
            r = self.row(v)
            q0 = min(max(0,math.floor(q)), len(qubit_map)-1)
            offset = q - q0
            coord = qubit_map[q0]
            qf = 3*(coord[0]+offset)+(0.6 * coord[1])
            rf = 3*r+(0.6 * coord[1])
            self.set_qubit(v, qf)
            self.set_row(v, rf)


    def replace_subgraph(self, left_row: FloatInt, right_row: FloatInt, replace: 'BaseGraph') -> None:
        """Deletes the subgraph of all nodes with rank strictly between ``left_row``
        and ``right_row`` and replaces it with the graph ``replace``.
        The amount of nodes on the left row should match the amount of inputs of 
        the replacement graph and the same for the right row and the outputs.
        The graphs are glued together based on the qubit index of the vertices."""
        qleft = [v for v in self.vertices() if self.row(v)==left_row]
        qright= [v for v in self.vertices() if self.row(v)==right_row]
        if len(qleft) != len(replace.inputs):
            raise TypeError("Inputs do not match glueing vertices")
        if len(qright) != len(replace.outputs):
            raise TypeError("Outputs do not match glueing vertices")
        if set(self.qubit(v) for v in qleft) != set(replace.qubit(v) for v in replace.inputs):
            raise TypeError("Input qubit indices do not match")
        if set(self.qubit(v) for v in qright)!= set(replace.qubit(v) for v in replace.outputs):
            raise TypeError("Output qubit indices do not match")
        
        self.remove_vertices([v for v in self.vertices() if (left_row < self.row(v) and self.row(v) < right_row)])
        self.remove_edges([self.edge(s,t) for s in qleft for t in qright if self.connected(s,t)])
        rdepth = replace.depth() -1
        for v in (v for v in self.vertices() if self.row(v)>=right_row):
            self.set_row(v, self.row(v)+rdepth)

        vtab = {}
        for v in replace.vertices():
            if v in replace.inputs or v in replace.outputs: continue
            vtab[v] = self.add_vertex(replace.type(v),replace.qubit(v),
                                replace.row(v)+left_row,replace.phase(v))
        for v in replace.inputs:
            vtab[v] = [i for i in qleft if self.qubit(i) == replace.qubit(v)][0]

        for v in replace.outputs:
            vtab[v] = [i for i in qright if self.qubit(i) == replace.qubit(v)][0]

        etab = {e:self.edge(vtab[replace.edge_s(e)],vtab[replace.edge_t(e)]) for e in replace.edges()}
        self.add_edges(etab.values())
        for e,f in etab.items():
            self.set_edge_type(f, replace.edge_type(e))

    def compose(self, other: 'BaseGraph') -> None:
        """Inserts a graph after this one. The amount of qubits of the graphs must match.
        Also available by the operator `graph1 + graph2`"""
        if self.qubit_count() != other.qubit_count():
            raise TypeError("Circuits work on different qubit amounts")
        self.normalise()
        other = other.copy()
        other.normalise()
        self.scalar.mult_with_scalar(other.scalar)
        for o in self.outputs:
            q = self.qubit(o)
            e = list(self.incident_edges(o))[0]
            if self.edge_type(e) == EdgeType.HADAMARD:
                i = [v for v in other.inputs if other.qubit(v)==q][0]
                e = list(other.incident_edges(i))[0]
                other.set_edge_type(e, toggle_edge(other.edge_type(e)))
        d = self.depth()
        self.replace_subgraph(d-1,d,other)

    def tensor(self, other: 'BaseGraph') -> 'BaseGraph':
        """Take the tensor product of two graphs. Places the second graph below the first one.
        Can also be called using the operator `graph1 @ graph2`"""
        g = self.copy()
        ts = other.types()
        qs = other.qubits()
        height = max(qs.values()) + 1
        rs = other.rows()
        phases = other.phases()
        vertex_map = dict()
        for v in other.vertices():
            w = g.add_vertex(ts[v],qs[v]+height,rs[v],phases[v])
            vertex_map[v] = w
        for e in other.edges():
            s,t = other.edge_st(e)
            g.add_edge((vertex_map[s],vertex_map[t]),other.edge_type(e))
        for v in other.inputs:
            g.inputs.append(vertex_map[v])
        for v in other.outputs:
            g.outputs.append(vertex_map[v])
        return g


    def __iadd__(self, other: 'BaseGraph') -> 'BaseGraph':
        self.compose(other)
        return self

    def __add__(self, other: 'BaseGraph') -> 'BaseGraph':
        g = self.copy()
        g += other
        return g

    def __matmul__(self, other: 'BaseGraph') -> 'BaseGraph':
        return self.tensor(other)

    def apply_state(self, state: str) -> None:
        """Inserts a state into the inputs of the graph. ``state`` should be
        a string with every character representing an input state for each qubit.
        The possible types of states are on of '0', '1', '+', '-' for the respective
        kets. If '/' is specified this input is skipped."""
        if len(state) > len(self.inputs): raise TypeError("Too many input states specified")
        inputs = self.inputs.copy()
        self.inputs = []
        for i,s in enumerate(state):
            v = inputs[i]
            if s == '/': 
                self.inputs.append(v)
                continue
            if s in ('0', '1'):
                self.scalar.add_power(-1)
                self.set_type(v, VertexType.X)
                if s == '1':
                    self.set_phase(v, Fraction(1))
            elif s in ('+', '-'):
                self.scalar.add_power(-1)
                self.set_type(v, VertexType.Z)
                if s == '-':
                    self.set_phase(v, Fraction(1))
            else:
                raise TypeError("Unknown input state " + s)

    def apply_effect(self, effect: str) -> None:
        """Inserts an effect into the outputs of the graph. ``effect`` should be
        a string with every character representing an output effect for each qubit.
        The possible types of effects are one of '0', '1', '+', '-' for the respective
        kets. If '/' is specified this output is skipped."""
        if len(effect) > len(self.outputs): raise TypeError("Too many output effects specified")
        outputs = self.outputs.copy()
        self.outputs = []
        for i,s in enumerate(effect):
            v = outputs[i]
            if s == '/': 
                self.outputs.append(v)
                continue
            if s in ('0', '1'):
                self.scalar.add_power(-1)
                self.set_type(v, VertexType.X)
                if s == '1':
                    self.set_phase(v, Fraction(1))
            elif s in ('+', '-'):
                self.scalar.add_power(-1)
                self.set_type(v, VertexType.Z)
                if s == '-':
                    self.set_phase(v, Fraction(1))
            else:
                raise TypeError("Unknown output effect " + s)

    def to_tensor(self, preserve_scalar:bool=True) -> np.ndarray:
        """Returns a representation of the graph as a tensor using :func:`~pyzx.tensor.tensorfy`"""
        return tensorfy(self, preserve_scalar)
    def to_matrix(self,preserve_scalar:bool=True) -> np.ndarray:
        """Returns a representation of the graph as a matrix using :func:`~pyzx.tensor.tensorfy`"""
        return tensor_to_matrix(tensorfy(self, preserve_scalar), len(self.inputs), len(self.outputs))


    def is_id(self) -> bool:
        for e in self.edges():
            s,t = self.edge_st(e)
            if s in self.inputs and t in self.outputs:
                if self.inputs.index(s) != self.outputs.index(t):
                    return False
            elif t in self.inputs and s in self.outputs:
                if self.inputs.index(t) != self.outputs.index(s):
                    return False
            else:
                return False
        return True

    def vindex(self) -> VT:
        """The index given to the next vertex added to the graph. It should always
        be equal to ``max(g.vertices()) + 1``."""
        raise NotImplementedError("Not implemented on backend " + type(self).backend)

    def depth(self) -> FloatInt:
        """Returns the value of the highest row number given to a vertex.
        This is -1 when no rows have been set."""
        raise NotImplementedError("Not implemented on backend " + type(self).backend)

    def pack_circuit_rows(self) -> None:
        """Compresses the rows of the graph so that every index is used."""
        rows = [self.row(v) for v in self.vertices()]
        new_rows = pack_indices(rows)
        for v in self.vertices():
            self.set_row(v, new_rows[self.row(v)])

    def qubit_count(self) -> int:
        """Returns the number of inputs of the graph"""
        return len(self.inputs)

    def auto_detect_inputs(self) -> Tuple[List[VT],List[VT]]:
        if self.inputs or self.outputs: return self.inputs, self.outputs
        minrow: FloatInt = 100000
        maxrow: FloatInt = -100000
        nodes = {}
        ty = self.types()
        for v in self.vertices():
            if ty[v] == VertexType.BOUNDARY:
                r = self.row(v)
                nodes[v] = r
                if r < minrow:
                    minrow = r
                if r > maxrow:
                    maxrow = r

        for v,r in nodes.items():
            if r == minrow:
                self.inputs.append(v)
            if r == maxrow:
                self.outputs.append(v)
        self.inputs.sort(key=self.qubit)
        self.outputs.sort(key=self.qubit)
        return self.inputs, self.outputs


    def normalise(self) -> None:
        """Puts every node connecting to an input/output at the correct qubit index and row."""
        if not self.inputs:
            self.auto_detect_inputs()
        max_r = self.depth() - 1
        if max_r <= 2: 
            for o in self.outputs:
                self.set_row(o,4)
            max_r = self.depth() -1
        claimed = []
        for q,i in enumerate(sorted(self.inputs, key=self.qubit)):
            self.set_row(i,0)
            self.set_qubit(i,q)
            #q = self.qubit(i)
            n = list(self.neighbours(i))[0]
            if self.type(n) in (VertexType.Z, VertexType.X):
                claimed.append(n)
                self.set_row(n,1)
                self.set_qubit(n, q)
            else: #directly connected to output
                e = self.edge(i, n)
                t = self.edge_type(e)
                self.remove_edge(e)
                v = self.add_vertex(VertexType.Z,q,1)
                self.add_edge(self.edge(i,v),toggle_edge(t))
                self.add_edge(self.edge(v,n),EdgeType.HADAMARD)
                claimed.append(v)
        for q, o in enumerate(sorted(self.outputs,key=self.qubit)):
            #q = self.qubit(o)
            self.set_row(o,max_r+1)
            self.set_qubit(o,q)
            n = list(self.neighbours(o))[0]
            if n not in claimed:
                self.set_row(n,max_r)
                self.set_qubit(n, q)
            else:
                e = self.edge(o, n)
                t = self.edge_type(e)
                self.remove_edge(e)
                v = self.add_vertex(VertexType.Z,q,max_r)
                self.add_edge(self.edge(o,v),toggle_edge(t))
                self.add_edge(self.edge(v,n),EdgeType.HADAMARD)

        self.pack_circuit_rows()

    def add_vertices(self, amount: int) -> List[VT]:
        """Add the given amount of vertices, and return the indices of the
        new vertices added to the graph, namely: range(g.vindex() - amount, g.vindex())"""
        raise NotImplementedError("Not implemented on backend " + type(self).backend)

    def add_vertex(self, ty:VertexType.Type=VertexType.BOUNDARY, qubit:FloatInt=-1, row:FloatInt=-1, phase:Optional[FractionLike]=None) -> VT:
        """Add a single vertex to the graph and return its index.
        The optional parameters allow you to respectively set
        the type, qubit index, row index and phase of the vertex."""
        v = self.add_vertices(1)[0]
        self.set_type(v, ty)
        if phase is None:
            if ty == VertexType.H_BOX: phase = 1
            else: phase = 0
        if qubit!=-1: self.set_qubit(v, qubit)
        if row!=-1: self.set_row(v, row)
        if phase: 
            self.set_phase(v, phase)
        if self.track_phases:
            self.max_phase_index += 1
            self.phase_index[v] = self.max_phase_index
            self.phase_mult[self.max_phase_index] = 1
        return v

    def add_edges(self, edges: Iterable[ET], edgetype:EdgeType.Type=EdgeType.SIMPLE) -> None:
        """Adds a list of edges to the graph."""
        raise NotImplementedError("Not implemented on backend " + type(self).backend)

    def add_edge(self, edge: ET, edgetype:EdgeType.Type=EdgeType.SIMPLE) -> None:
        """Adds a single edge of the given type"""
        self.add_edges([edge], edgetype)

    def add_edge_table(self, etab:Mapping[ET,List[int]]) -> None:
        """Takes a dictionary mapping (source,target) --> (#edges, #h-edges) specifying that
        #edges regular edges must be added between source and target and $h-edges Hadamard edges.
        The method selectively adds or removes edges to produce that ZX diagram which would 
        result from adding (#edges, #h-edges), and then removing all parallel edges using Hopf/spider laws."""
        add: Dict[EdgeType.Type,List] = {EdgeType.SIMPLE: [], EdgeType.HADAMARD: []} # list of edges and h-edges to add
        new_type: Optional[EdgeType.Type]
        remove: List = []   # list of edges to remove
        for e,(n1,n2) in etab.items():
            v1,v2 = self.edge_st(e)
            conn_type = self.edge_type(e)
            if conn_type == EdgeType.SIMPLE: n1 += 1 #and add to the relevant edge count
            elif conn_type == EdgeType.HADAMARD: n2 += 1

            t1 = self.type(v1)
            t2 = self.type(v2)
            if t1 == t2 and vertex_is_zx(t1) and vertex_is_zx(t2): #types are ZX & equal,
                n1 = bool(n1)           #so normal edges fuse
                pairs, n2 = divmod(n2,2)#while hadamard edges go modulo 2
                self.scalar.add_power(-2*pairs)
                if n1 != 0 and n2 != 0:  #reduction rule for when both edges appear
                    new_type = EdgeType.SIMPLE
                    self.add_to_phase(v1, 1)
                    self.scalar.add_power(-1)
                elif n1 != 0: new_type = EdgeType.SIMPLE
                elif n2 != 0: new_type = EdgeType.HADAMARD
                else: new_type = None
            elif t1 != t2 and vertex_is_zx(t1) and vertex_is_zx(t2): #types are ZX & different
                pairs, n1 = divmod(n1,2)#so normal edges go modulo 2
                n2 = bool(n2)           #while hadamard edges fuse
                self.scalar.add_power(-2*pairs)
                if n1 != 0 and n2 != 0:  #reduction rule for when both edges appear
                    new_type = EdgeType.HADAMARD
                    self.add_to_phase(v1, 1)
                    self.scalar.add_power(-1)
                elif n1 != 0: new_type = EdgeType.SIMPLE
                elif n2 != 0: new_type = EdgeType.HADAMARD
                else: new_type = None
            elif ((t1 == VertexType.Z and t2 == VertexType.H_BOX) or 
                  (t1 == VertexType.H_BOX and t2 == VertexType.Z)):
                # Z & H-box
                n1 = bool(n1)
                if n1 + n2 > 1:
                    raise ValueError("Unhandled parallel edges between nodes of type (%s,%s)" % (t1,t2))
                else:
                    if n1 == 1: new_type = EdgeType.SIMPLE
                    elif n2 == 1: new_type = EdgeType.HADAMARD
                    else: new_type = None
            else:
                if n1 + n2 > 1:
                    raise ValueError("Unhandled parallel edges between nodes of type (%s,%s)" % (t1,t2))
                else:
                    if n1 == 1: new_type = EdgeType.SIMPLE
                    elif n2 == 1: new_type = EdgeType.HADAMARD
                    else: new_type = None


            if new_type: # They should be connected, so update the graph
                if not conn_type: #new edge added
                    add[new_type].append((v1,v2))
                elif conn_type != new_type: #type of edge has changed
                    self.set_edge_type(self.edge(v1,v2), new_type)
            elif conn_type: #They were connected, but not anymore, so update the graph
                remove.append(self.edge(v1,v2))

        self.remove_edges(remove)
        self.add_edges(add[EdgeType.SIMPLE],EdgeType.SIMPLE)
        self.add_edges(add[EdgeType.HADAMARD],EdgeType.HADAMARD)

    def set_phase_master(self, m: Simplifier) -> None:
        """Points towards an instance of the class :class:`simplify.Simplifier`.
        Used for phase teleportation."""
        self.phase_master = m

    def update_phase_index(self, old:VT, new:VT) -> None:
        """When a phase is moved from a vertex to another vertex,
        we need to tell the phase_teleportation algorithm that this has happened.
        This function does that. Used in some of the rules in `simplify`."""
        if not self.track_phases: return
        i = self.phase_index[old]
        self.phase_index[old] = self.phase_index[new]
        self.phase_index[new] = i

    def fuse_phases(self, p1: VT, p2: VT) -> None:
        if p1 not in self.phase_index or p2 not in self.phase_index: 
            return
        if self.phase_master is not None: 
            self.phase_master.fuse_phases(self.phase_index[p1],self.phase_index[p2])
        self.phase_index[p2] = self.phase_index[p1]

    def phase_negate(self, v: VT) -> None:
        if v not in self.phase_index: return
        index = self.phase_index[v]
        mult = self.phase_mult[index]
        if mult == 1: self.phase_mult[index] = -1
        else: self.phase_mult[index] = 1
        #self.phase_mult[index] = -1*mult 

    def vertex_from_phase_index(self, i: int) -> VT:
        return list(self.phase_index.keys())[list(self.phase_index.values()).index(i)]


    def remove_vertices(self, vertices: List[VT]) -> None:
        """Removes the list of vertices from the graph."""
        raise NotImplementedError("Not implemented on backend " + type(self).backend)

    def remove_vertex(self, vertex: VT) -> None:
        """Removes the given vertex from the graph."""
        self.remove_vertices([vertex])

    def remove_isolated_vertices(self) -> None:
        """Deletes all vertices and vertex pairs that are not connected to any other vertex."""
        rem: List[VT] = []
        for v in self.vertices():
            d = self.vertex_degree(v)
            if d == 0:
                rem.append(v)
                self.scalar.add_node(self.phase(v))
            if d == 1: # It has a unique neighbour
                if v in rem: continue # Already taken care of
                if self.type(v) == VertexType.BOUNDARY: continue # Ignore in/outputs
                w = list(self.neighbours(v))[0]
                if len(list(self.neighbours(w))) > 1: continue # But this neighbour has other neighbours
                if self.type(w) == VertexType.BOUNDARY: continue # It's a state/effect
                # At this point w and v are only connected to each other
                rem.append(v)
                rem.append(w)
                et = self.edge_type(self.edge(v,w))
                if self.type(v) == self.type(w):
                    if et == EdgeType.SIMPLE:
                        self.scalar.add_node(self.phase(v)+self.phase(w))
                    else:
                        self.scalar.add_spider_pair(self.phase(v), self.phase(w))
                else:
                    if et == EdgeType.SIMPLE:
                        self.scalar.add_spider_pair(self.phase(v), self.phase(w))
                    else:
                        self.scalar.add_node(self.phase(v)+self.phase(w))
        self.remove_vertices(rem)

    def remove_edges(self, edges: List[ET]) -> None:
        """Removes the list of edges from the graph."""
        raise NotImplementedError("Not implemented on backend " + type(self).backend)

    def remove_edge(self, edge: ET) -> None:
        """Removes the given edge from the graph."""
        self.remove_edges([edge])

    def num_vertices(self) -> int:
        """Returns the amount of vertices in the graph."""
        raise NotImplementedError("Not implemented on backend " + type(self).backend)

    def num_edges(self) -> int:
        """Returns the amount of edges in the graph"""
        raise NotImplementedError("Not implemented on backend " + type(self).backend)

    def vertices(self) -> Iterable[VT]:
        """Iterator over all the vertices."""
        raise NotImplementedError("Not implemented on backend " + type(self).backend)

    def edges(self) -> Iterable[ET]:
        """Iterator that returns all the edges. Output type depends on implementation in backend."""
        raise NotImplementedError("Not implemented on backend " + type(self).backend)

    def vertex_set(self) -> Set[VT]:
        """Returns the vertices of the graph as a Python set. 
        Should be overloaded if the backend supplies a cheaper version than this."""
        return set(self.vertices())

    def edge_set(self) -> Set[ET]:
        """Returns the edges of the graph as a Python set. 
        Should be overloaded if the backend supplies a cheaper version than this."""
        return set(self.edges())

    def edge(self, s:VT, t:VT) -> ET:
        """Returns the edge object with the given source/target."""
        raise NotImplementedError("Not implemented on backend " + type(self).backend)

    def edge_st(self, edge: ET) -> Tuple[VT, VT]:
        """Returns a tuple of source/target of the given edge."""
        raise NotImplementedError("Not implemented on backend " + type(self).backend)
    def edge_s(self, edge: ET) -> VT:
        """Returns the source of the given edge."""
        return self.edge_st(edge)[0]
    def edge_t(self, edge: ET) -> VT:
        """Returns the target of the given edge."""
        return self.edge_st(edge)[1]

    def neighbours(self, vertex: VT) -> Iterable[VT]:
        """Returns all neighbouring vertices of the given vertex."""
        raise NotImplementedError("Not implemented on backend " + type(self).backend)

    def vertex_degree(self, vertex: VT) -> int:
        """Returns the degree of the given vertex."""
        raise NotImplementedError("Not implemented on backend " + type(self).backend)

    def incident_edges(self, vertex: VT) -> Iterable[ET]:
        """Returns all neighbouring edges of the given vertex."""
        raise NotImplementedError("Not implemented on backend " + type(self).backend)

    def connected(self,v1: VT,v2: VT) -> bool:
        """Returns whether vertices v1 and v2 share an edge."""
        raise NotImplementedError("Not implemented on backend " + type(self).backend)

    def edge_type(self, e: ET) -> EdgeType.Type:
        """Returns the type of the given edge:
        EdgeType.SIMPLE_ if it is regular, EdgeType.HADAMARD_ if it is a Hadamard edge,
        0 if the edge is not in the graph."""
        raise NotImplementedError("Not implemented on backend " + type(self).backend)
    def set_edge_type(self, e: ET, t: EdgeType.Type) -> None:
        """Sets the type of the given edge."""
        raise NotImplementedError("Not implemented on backend " + type(self).backend)

    def type(self, vertex: VT) -> VertexType.Type:
        """Returns the type of the given vertex:
        VertexType.BOUNDARY if it is a boundary, VertexType.Z if it is a Z node,
        VertexType.X if it is a X node, VertexType.H_BOX if it is an H-box."""
        raise NotImplementedError("Not implemented on backend " + type(self).backend)
    def types(self) -> Mapping[VT, VertexType.Type]:
        """Returns a mapping of vertices to their types."""
        raise NotImplementedError("Not implemented on backend " + type(self).backend)
    def set_type(self, vertex: VT, t: VertexType.Type) -> None:
        """Sets the type of the given vertex to t."""
        raise NotImplementedError("Not implemented on backend" + type(self).backend)
    
    def phase(self, vertex: VT) -> FractionLike:
        """Returns the phase value of the given vertex."""
        raise NotImplementedError("Not implemented on backend" + type(self).backend)
    def phases(self) -> Mapping[VT, FractionLike]:
        """Returns a mapping of vertices to their phase values."""
        raise NotImplementedError("Not implemented on backend" + type(self).backend)
    def set_phase(self, vertex: VT, phase: FractionLike) -> None:
        """Sets the phase of the vertex to the given value."""
        raise NotImplementedError("Not implemented on backend" + type(self).backend)
    def add_to_phase(self, vertex: VT, phase: FractionLike) -> None:
        """Add the given phase to the phase value of the given vertex."""
        self.set_phase(vertex,self.phase(vertex)+phase)

    def qubit(self, vertex: VT) -> FloatInt:
        """Returns the qubit index associated to the vertex. 
        If no index has been set, returns -1."""
        raise NotImplementedError("Not implemented on backend" + type(self).backend)
    def qubits(self) -> Mapping[VT,FloatInt]:
        """Returns a mapping of vertices to their qubit index."""
        raise NotImplementedError("Not implemented on backend" + type(self).backend)
    def set_qubit(self, vertex: VT, q: FloatInt) -> None:
        """Sets the qubit index associated to the vertex."""
        raise NotImplementedError("Not implemented on backend" + type(self).backend)

    def row(self, vertex: VT) -> FloatInt:
        """Returns the row that the vertex is positioned at. 
        If no row has been set, returns -1."""
        raise NotImplementedError("Not implemented on backend" + type(self).backend)
    def rows(self) -> Mapping[VT, FloatInt]:
        """Returns a mapping of vertices to their row index."""
        raise NotImplementedError("Not implemented on backend" + type(self).backend)
    def set_row(self, vertex: VT, r: FloatInt) -> None:
        """Sets the row the vertex should be positioned at."""
        raise NotImplementedError("Not implemented on backend" + type(self).backend)

    def set_position(self, vertex: VT, q: FloatInt, r: FloatInt):
        """Set both the qubit index and row index of the vertex."""
        self.set_qubit(vertex, q)
        self.set_row(vertex, r)

    def vdata_keys(self, vertex: VT) -> Iterable[str]:
        """Returns an iterable of the vertex data key names.
        Used e.g. in making a copy of the graph in a backend-independent way."""
        raise NotImplementedError("Not implemented on backend" + type(self).backend)
    def vdata(self, vertex: VT, key: str, default: Any=0) -> Any:
        """Returns the data value of the given vertex associated to the key.
        If this key has no value associated with it, it returns the default value."""
        raise NotImplementedError("Not implemented on backend" + type(self).backend)
    def set_vdata(self, vertex: VT, key: str, val: Any) -> None:
        """Sets the vertex data associated to key to val."""
        raise NotImplementedError("Not implemented on backend" + type(self).backend)
