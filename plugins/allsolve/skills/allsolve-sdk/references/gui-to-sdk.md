# Allsolve GUI name to SDK class map

**Contents:** [Concepts that are not one class](#concepts-that-are-not-one-class) · [Physics, interactions and outputs](#physics-interactions-and-outputs)

This reference maps the names in the Allsolve web app to SDK classes. Use it to turn a GUI-based spec or tutorial into SDK calls.

## Concepts that are not one class

| GUI term | SDK |
|---|---|
| Floating electrode | `Interaction.ElectrostaticsLump` with `electrostatics_lump_actuation_mode=ElectrostaticsLumpActuationMode.CHARGE`, `electrostatics_lump_charge="0"`. Read the voltage as `<namespace>.V` |
| Initial field state (from another simulation) | `FieldInitialization(type=FieldInitializationType.FIELDSTATE, ...)` and an `Output.FieldState` on the source |
| Post-processing simulation | `FieldInitializationType.POSTPROCESSING` (experimental) |
| Static / Steady state | `create_simulation_static` (`AnalysisType.STATIC`) |
| Generalized alpha | `TimestepAlgorithm.GEN_ALPHA` |
| Boundary intersection (region operation) | Not in the SDK. Use `RegionOperation.INTERSECTION` of two `BOUNDARY` regions, or `INTERSECTION` of two volume regions with a surface target |
| 2D axisymmetric project | Not available from the SDK (see [mesh](mesh.md#2d-axisymmetric)) |
| PML layers | `project.pml_num_layers` |
| "From material properties" (an interaction parameter that reads the material) | The parameter expression `par.<name>()`, for example `par.Mub(f)` and `par.Mus(f)` for viscous damping. See [physics-and-interactions](physics-and-interactions.md#interaction-parameters-from-material-properties) |

## Physics, interactions and outputs

Generated from the SDK classes and the web app's English labels. Labels such as "Constraint" repeat across physics, so match the physics column too. Two classes share the label "Acoustic structure": `AcousticWavesAcousticStructure` (with solid mechanics) and `AcousticWavesAcousticStructureForElasticWaves` (with elastic waves). The GUI label "Value output" is `Output.ValueOutput`.

| GUI label | Physics | SDK class | definition_id |
|---|---|---|---|
| Acoustic waves | Acoustic waves | `Physics.AcousticWaves` | `acousticWaves` |
| Current flow | Current flow | `Physics.CurrentFlow` | `currentFlow` |
| Elastic waves | Elastic waves | `Physics.ElasticWaves` | `elasticWaves` |
| Electromagnetic waves | Electromagnetic waves | `Physics.ElectromagneticWaves` | `electromagneticWaves` |
| Electrostatics | Electrostatics | `Physics.Electrostatics` | `electrostatics` |
| Heat fluid | Heat fluid | `Physics.HeatFluid` | `heatFluid` |
| Heat solid | Heat solid | `Physics.HeatTransfer` | `heatTransfer` |
| Laminar flow | Laminar flow | `Physics.LaminarFlow` | `laminarFlow` |
| Magnetism A | Magnetism A | `Physics.MagnetismA` | `magnetismA` |
| Magnetism H | Magnetism H | `Physics.MagnetismH` | `magnetismH` |
| Magnetism φ | Magnetism φ | `Physics.MagnetismPhi` | `magnetismPhi` |
| Mesh deformation | Mesh deformation | `Physics.MeshDeformation` | `meshDeformation` |
| Solid mechanics | Solid mechanics | `Physics.SolidMechanics` | `solidMechanics` |
| Absorbing boundary | Acoustic waves | `Interaction.AcousticWavesAbsorbingBoundary` | `acousticWavesAbsorbingBoundary` |
| Acoustic damping | Acoustic waves | `Interaction.AcousticWavesAcousticDamping` | `acousticWavesAcousticDamping` |
| Acoustic structure | Acoustic waves | `Interaction.AcousticWavesAcousticStructure` | `acousticStructure` |
| Acoustic structure | Acoustic waves | `Interaction.AcousticWavesAcousticStructureForElasticWaves` | `acousticStructureForElasticWaves` |
| Constraint | Acoustic waves | `Interaction.AcousticWavesConstraint` | `acousticWavesConstraint` |
| Continuity | Acoustic waves | `Interaction.AcousticWavesContinuity` | `acousticWavesContinuity` |
| Initial value | Acoustic waves | `Interaction.AcousticWavesInitialValue` | `acousticWavesInitialValue` |
| Normal acceleration | Acoustic waves | `Interaction.AcousticWavesNormalAcceleration` | `acousticWavesNormalAcceleration` |
| Perfectly matched layer | Acoustic waves | `Interaction.AcousticWavesPml` | `acousticWavesPml` |
| Periodicity | Acoustic waves | `Interaction.AcousticWavesPeriodicity` | `acousticWavesPeriodicity` |
| Constraint | Current flow | `Interaction.CurrentFlowConstraint` | `currentFlowConstraint` |
| Current density source | Current flow | `Interaction.CurrentFlowCurrentDensity` | `currentDensity` |
| Initial value | Current flow | `Interaction.CurrentFlowInitialValue` | `currentFlowInitialValue` |
| Lump V/I | Current flow | `Interaction.CurrentFlowLump` | `currentFlowLump` |
| Lump V/I cut | Current flow | `Interaction.CurrentFlowLumpVICut` | `currentFlowLumpVICut` |
| Periodicity | Current flow | `Interaction.CurrentFlowPeriodicity` | `currentFlowPeriodicity` |
| Absorbing boundary | Elastic waves | `Interaction.ElasticWavesAbsorbingBoundary` | `elasticWavesAbsorbingBoundary` |
| Clamp | Elastic waves | `Interaction.ElasticWavesClamp` | `elasticWavesClamp` |
| Constraint | Elastic waves | `Interaction.ElasticWavesConstraint` | `elasticWavesConstraint` |
| Continuity | Elastic waves | `Interaction.ElasticWavesContinuity` | `elasticWavesContinuity` |
| Electric force | Elastic waves | `Interaction.ElasticWavesElectricForce` | `elasticWavesElectricForce` |
| Initial value | Elastic waves | `Interaction.ElasticWavesInitialValue` | `elasticWavesInitialValue` |
| Load | Elastic waves | `Interaction.ElasticWavesLoad` | `elasticWavesLoad` |
| Lump U/F | Elastic waves | `Interaction.ElasticWavesLump` | `elasticWavesLump` |
| Perfectly matched layer | Elastic waves | `Interaction.ElasticWavesPml` | `elasticWavesPml` |
| Periodicity | Elastic waves | `Interaction.ElasticWavesPeriodicity` | `elasticWavesPeriodicity` |
| Piezoelectricity | Elastic waves | `Interaction.ElasticWavesPiezoelectricity` | `elasticWavesPiezoelectricity` |
| Pressure | Elastic waves | `Interaction.ElasticWavesPressure` | `elasticWavesPressure` |
| Proportional damping | Elastic waves | `Interaction.ElasticWavesProportionalDamping` | `elasticWavesProportionalDamping` |
| Symmetry | Elastic waves | `Interaction.ElasticWavesSymmetry` | `elasticWavesSymmetry` |
| Thermal expansion | Elastic waves | `Interaction.ElasticWavesThermalExpansion` | `elasticWavesThermalExpansion` |
| Viscoelasticity | Elastic waves | `Interaction.ElasticWavesViscoelasticity` | `viscoelasticity` |
| Viscous damping | Elastic waves | `Interaction.ElasticWavesViscousDamping` | `elasticWavesViscousDamping` |
| Absorbing boundary | Electromagnetic waves | `Interaction.ElectromagneticWavesAbsorbingBoundary` | `electromagneticWavesAbsorbingBoundary` |
| Boundary admittance | Electromagnetic waves | `Interaction.ElectromagneticWavesBoundaryAdmittance` | `electromagneticWavesBoundaryAdmittance` |
| Boundary current density | Electromagnetic waves | `Interaction.ElectromagneticWavesBoundaryCurrentDensity` | `electromagneticWavesBoundaryCurrentDensity` |
| Constraint | Electromagnetic waves | `Interaction.ElectromagneticWavesConstraint` | `electromagneticWavesConstraint` |
| Dielectric loss | Electromagnetic waves | `Interaction.ElectromagneticWavesDielectricLoss` | `electromagneticWavesDielectricLoss` |
| Eigenmode port | Electromagnetic waves | `Interaction.ElectromagneticWavesEigenmodePort` | `electromagneticWavesEigenmodePort` |
| Initial value | Electromagnetic waves | `Interaction.ElectromagneticWavesInitialValue` | `electromagneticWavesInitialValue` |
| Lump V/I | Electromagnetic waves | `Interaction.ElectromagneticWavesLumpVI` | `electromagneticWavesLumpVI` |
| Perfect conductor | Electromagnetic waves | `Interaction.ElectromagneticWavesPerfectConductor` | `electromagneticWavesPerfectConductor` |
| Perfectly matched layer | Electromagnetic waves | `Interaction.ElectromagneticWavesPml` | `electromagneticWavesPml` |
| Periodicity | Electromagnetic waves | `Interaction.ElectromagneticWavesPeriodicity` | `electromagneticWavesPeriodicity` |
| Rectangular port | Electromagnetic waves | `Interaction.ElectromagneticWavesRectangularPort` | `electromagneticWavesRectangularPort` |
| Constraint | Electrostatics | `Interaction.ElectrostaticsConstraint` | `electrostaticsConstraint` |
| Initial value | Electrostatics | `Interaction.ElectrostaticsInitialValue` | `electrostaticsInitialValue` |
| Large displacement | Electrostatics | `Interaction.ElectrostaticsLargeDisplacement` | `electrostaticsLargeDisplacement` |
| Lump V/Q | Electrostatics | `Interaction.ElectrostaticsLump` | `electrostaticsLump` |
| Periodicity | Electrostatics | `Interaction.ElectrostaticsPeriodicity` | `electrostaticsPeriodicity` |
| Piezoelectricity | Electrostatics | `Interaction.ElectrostaticsPiezoelectricity` | `piezoelectricity` |
| Piezoelectricity | Electrostatics | `Interaction.ElectrostaticsElasticWavesPiezoelectricity` | `elasticWavesPiezoelectricity` |
| Constraint | Heat fluid | `Interaction.HeatFluidConstraint` | `heatFluidConstraint` |
| Heat source | Heat fluid | `Interaction.HeatFluidHeatSource` | `heatFluidHeatSource` |
| Initial value | Heat fluid | `Interaction.HeatFluidInitialValue` | `heatFluidInitialValue` |
| Periodicity | Heat fluid | `Interaction.HeatFluidPeriodicity` | `heatFluidPeriodicity` |
| Constraint | Heat solid | `Interaction.HeatTransferTemperatureConstraint` | `temperatureConstraint` |
| Convection | Heat solid | `Interaction.HeatTransferConvection` | `heatTransferConvection` |
| Heat source | Heat solid | `Interaction.HeatTransferHeatSource` | `heatSource` |
| Initial value | Heat solid | `Interaction.HeatTransferInitialValue` | `heatTransferInitialValue` |
| Joule heating | Heat solid | `Interaction.HeatTransferJouleHeating` | `jouleHeating` |
| Lump T/Φ | Heat solid | `Interaction.HeatTransferLumpTPhi` | `heatTransferLumpTPhi` |
| Periodicity | Heat solid | `Interaction.HeatTransferPeriodicity` | `heatTransferPeriodicity` |
| Fluid structure | Laminar flow | `Interaction.LaminarFlowFluidStructure` | `laminarFlowFluidStructure` |
| Force | Laminar flow | `Interaction.LaminarFlowForce` | `laminarFlowForce` |
| Initial pressure | Laminar flow | `Interaction.LaminarFlowPressureInitialValue` | `laminarFlowPressureInitialValue` |
| Initial velocity | Laminar flow | `Interaction.LaminarFlowVelocityInitialValue` | `laminarFlowVelocityInitialValue` |
| Large displacement | Laminar flow | `Interaction.LaminarFlowLargeDisplacement` | `laminarFlowLargeDisplacement` |
| Linear | Laminar flow | `Interaction.LaminarFlowLinear` | `laminarFlowLinear` |
| Lump P/M | Laminar flow | `Interaction.LaminarFlowLumpPM` | `laminarFlowLumpPM` |
| Lump V/Fv | Laminar flow | `Interaction.LaminarFlowLumpVFv` | `laminarFlowLumpVFv` |
| Pressure constraint | Laminar flow | `Interaction.LaminarFlowPressureConstraint` | `laminarFlowPressureConstraint` |
| Pressure periodicity | Laminar flow | `Interaction.LaminarFlowPressurePeriodicity` | `laminarFlowPressurePeriodicity` |
| Pressure symmetry | Laminar flow | `Interaction.LaminarFlowPressureSymmetry` | `laminarFlowPressureSymmetry` |
| Thermal fluid | Laminar flow | `Interaction.LaminarFlowThermalFluid` | `laminarFlowThermalFluid` |
| Velocity constraint | Laminar flow | `Interaction.LaminarFlowVelocityConstraint` | `laminarFlowVelocityConstraint` |
| Velocity periodicity | Laminar flow | `Interaction.LaminarFlowVelocityPeriodicity` | `laminarFlowVelocityPeriodicity` |
| Velocity symmetry | Laminar flow | `Interaction.LaminarFlowVelocitySymmetry` | `laminarFlowVelocitySymmetry` |
| A-v coupling | Magnetism A | `Interaction.MagnetismAElectromagneticCoupling` | `electromagneticCoupling` |
| Initial value | Magnetism A | `Interaction.MagnetismAInitialValue` | `magnetismAInitialValue` |
| Magnetic wall | Magnetism A | `Interaction.MagnetismAMagneticWall` | `magneticWall` |
| Periodicity | Magnetism A | `Interaction.MagnetismAPeriodicity` | `magnetismAPeriodicity` |
| Remanence | Magnetism A | `Interaction.MagnetismABackgroundField` | `magnetismABackgroundField` |
| Constraint | Magnetism H | `Interaction.MagnetismHConstraint` | `magnetismHConstraint` |
| Electrical insulator | Magnetism H | `Interaction.MagnetismHElectricalInsulator` | `magnetismHElectricalInsulator` |
| H-φ coupling | Magnetism H | `Interaction.MagnetismHHPhiCoupling` | `hPhiCoupling` |
| Initial value | Magnetism H | `Interaction.MagnetismHInitialValue` | `magnetismHInitialValue` |
| Periodicity | Magnetism H | `Interaction.MagnetismHPeriodicity` | `magnetismHPeriodicity` |
| Constraint | Magnetism φ | `Interaction.MagnetismPhiConstraint` | `magnetismPhiConstraint` |
| Continuity | Magnetism φ | `Interaction.MagnetismPhiContinuity` | `magnetismPhiContinuity` |
| External field | Magnetism φ | `Interaction.MagnetismPhiExternalField` | `magnetismPhiExternalField` |
| Initial value | Magnetism φ | `Interaction.MagnetismPhiInitialValue` | `magnetismPhiInitialValue` |
| Lump I/V cut | Magnetism φ | `Interaction.MagnetismPhiLumpIV` | `magnetismPhiLumpIV` |
| Lump φ/Φ | Magnetism φ | `Interaction.MagnetismPhiLumpPhiPhiB` | `magnetismPhiLumpPhiPhiB` |
| Periodicity | Magnetism φ | `Interaction.MagnetismPhiPeriodicity` | `magnetismPhiPeriodicity` |
| Remanence | Magnetism φ | `Interaction.MagnetismPhiBackgroundField` | `magnetismPhiBackgroundField` |
| Clamp | Mesh deformation | `Interaction.MeshDeformationClamp` | `meshDeformationClamp` |
| Constraint | Mesh deformation | `Interaction.MeshDeformationConstraint` | `meshDeformationConstraint` |
| Initial value | Mesh deformation | `Interaction.MeshDeformationInitialValue` | `meshDeformationInitialValue` |
| Periodicity | Mesh deformation | `Interaction.MeshDeformationPeriodicity` | `meshDeformationPeriodicity` |
| Symmetry | Mesh deformation | `Interaction.MeshDeformationSymmetry` | `meshDeformationSymmetry` |
| Clamp | Solid mechanics | `Interaction.SolidMechanicsClamp` | `clamp` |
| Constraint | Solid mechanics | `Interaction.SolidMechanicsConstraint` | `solidMechanicsConstraint` |
| Contact | Solid mechanics | `Interaction.SolidMechanicsContact` | `solidMechanicsContact` |
| Electric force | Solid mechanics | `Interaction.SolidMechanicsElectricForce` | `solidMechanicsElectricForce` |
| Geometric nonlinearity | Solid mechanics | `Interaction.SolidMechanicsGeometricNonlinearity` | `solidMechanicsGeometricNonlinearity` |
| Initial value | Solid mechanics | `Interaction.SolidMechanicsInitialValue` | `solidMechanicsInitialValue` |
| Large displacement | Solid mechanics | `Interaction.SolidMechanicsLargeDisplacement` | `solidMechanicsLargeDisplacement` |
| Load | Solid mechanics | `Interaction.SolidMechanicsLoad` | `load` |
| Lump U/F | Solid mechanics | `Interaction.SolidMechanicsLump` | `solidMechanicsLump` |
| Magnetic force | Solid mechanics | `Interaction.SolidMechanicsMagneticForce` | `solidMechanicsMagneticForce` |
| Periodicity | Solid mechanics | `Interaction.SolidMechanicsPeriodicity` | `solidMechanicsPeriodicity` |
| Piezoelectricity | Solid mechanics | `Interaction.SolidMechanicsPiezoelectricity` | `piezoelectricity` |
| Pressure | Solid mechanics | `Interaction.SolidMechanicsPressure` | `solidMechanicsPressure` |
| Prestress | Solid mechanics | `Interaction.SolidMechanicsPrestress` | `solidMechanicsPrestress` |
| Proportional damping | Solid mechanics | `Interaction.SolidMechanicsProportionalDamping` | `solidMechanicsProportionalDamping` |
| Symmetry | Solid mechanics | `Interaction.SolidMechanicsSymmetry` | `solidMechanicsSymmetry` |
| Thermal expansion | Solid mechanics | `Interaction.SolidMechanicsThermalExpansion` | `thermalExpansion` |
| Viscohyperelasticity | Solid mechanics | `Interaction.SolidMechanicsViscohyperelasticity` | `solidMechanicsViscohyperelasticity` |
| Acoustic extrapolation | (any / output) | `Output.AcousticWavesAcousticExtrapolation` | `acousticWavesAcousticExtrapolation` |
| Acoustic radiation pattern | (any / output) | `Output.AcousticWavesRadiationPattern` | `acousticWavesRadiationPattern` |
| EM radiation pattern | (any / output) | `Output.ElectromagneticWavesRadiationPattern` | `electromagneticWavesRadiationPattern` |
| Eigenfrequencies | (any / output) | `Output.Eigenfrequencies` | `eigenfrequencies` |
| Eigenvalues | (any / output) | `Output.Eigenvalues` | `eigenvalues` |
| Field output | (any / output) | `Output.FieldOnlyOutput` | `fieldOnlyOutput` |
| Field output | (any / output) | `Output.FieldOutput` | `fieldOutput` |
| Field state | (any / output) | `Output.FieldState` | `fieldState` |
| Final H-φ state | (any / output) | `Output.FinalHPhiState` | `finalHPhiState` |
| Magnetic force | (any / output) | `Output.MagneticForce` | `magneticForce` |
| Q-factors | (any / output) | `Output.QFactors` | `qFactors` |
| S-parameters | (any / output) | `Output.SParameters` | `sParameters` |
| Transient state | (any / output) | `Output.TransientState` | `transientState` |
| Value output | (any / output) | `Output.ValueOutput` | `discreteOutput` |
