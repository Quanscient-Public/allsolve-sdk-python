# Introduction

This demo uses the Quanscient Allsolve SDK to simulate AC loss in a twisted
high-temperature superconducting (HTS) wire with the H-φ formulation.

It follows the step-by-step tutorial:

https://allsolve.quanscient.com/documentation/learn-by-doing/step-by-step-tutorials/tutorial-twisted-superconductor-acloss

The example creates the full project via the SDK (geometry, regions, materials,
physics, mesh, and transient simulation). A custom simulation script section (scripts/formulations.py)
replaces the default Magnetism H formulation with Newton linearization for the
YBCO power law, matching the tutorial and reference simulation script.

# Prerequisites

Follow [Installation](../README.md#installation) and [Running](../README.md#running)
in the parent example README to set up Python, install the Allsolve SDK,
and configure credentials.

# Running

From the `examples/` directory:

```
(venv) $ python twisted_superconductor_acloss/twisted_superconductor_acloss.py
```
