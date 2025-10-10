OPENQASM 2.0;
include "qelib1.inc";

// Test multi-controlled gates from OpenQASM 2 qelib1.inc
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
