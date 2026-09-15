# Evaluation environment

The frozen benchmark entries were reconciled with PutnamBench commit
`b3e08943b1728842194fe2df693f02c763da4294` before export.

- [evaluation.json](evaluation.json) identifies the model, effort, variant, and benchmark revision.
- [lean-toolchain](lean-toolchain) pins Lean 4.27.0.
- [dependencies.json](dependencies.json) records the Git revisions of Mathlib and its dependencies used by the retained Lean environment.

The Mathlib revision is `a3a10db0e9d66acbebf76c5e6a135066525ac900`.

These pins describe the evaluation environment. The public analysis scripts need only Python and, for plots, the dependency in the root `requirements.txt`. Rechecking the original mathematical artifacts additionally requires the privately retained proofs and the verifier.

The benchmark source and setup documentation are available from the [pinned upstream repository](https://github.com/trishullab/PutnamBench/tree/b3e08943b1728842194fe2df693f02c763da4294).
