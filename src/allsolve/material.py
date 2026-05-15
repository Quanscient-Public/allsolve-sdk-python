# Copyright 2026 Quanscient Oy
# SPDX-License-Identifier: Apache-2.0

from typing import List, Tuple
from typing_extensions import Self
from allsolve.region import Region
from allsolve.util import prevent_deleted
import allsolve_rawapi as rawapi
from .api import get_api, get_auth, check_for_project_api_key


class MaterialProperty:
    """
    MaterialProperty is a base class for managing material properties.
    """

    class PhysicalProperty:
        def __init__(
            self, value: str | float, definition: str, alternative: str
        ) -> None:
            self.value = value
            self.definition = definition
            self.alternative = alternative
            self.is_list = False

        def to_rawapi(self) -> List[rawapi.PhysicalProperty]:
            value = str(self.value)
            return [
                rawapi.PhysicalProperty(
                    definition=self.definition,
                    alternative=self.alternative,
                    value=value,
                )
            ]

    class CoefficientOfThermalExpansion(PhysicalProperty):
        def __init__(self, value: str | float) -> None:
            super().__init__(
                value,
                "coefficientOfThermalExpansion",
                "coefficientOfThermalExpansionIsotropic",
            )

    class CoefficientOfThermalExpansionAnisotropic(PhysicalProperty):
        def __init__(self, value: List[float | str]) -> None:
            # Convert list of floats to format "[1; 2; 3; 4; 5; 6]"
            if len(value) != 6:
                raise ValueError(
                    "Coefficient of thermal expansion must be a list of 6 floats"
                )
            formatted_value = "[" + "; ".join(str(v) for v in value) + "]"
            super().__init__(
                value=formatted_value,
                definition="coefficientOfThermalExpansion",
                alternative="coefficientOfThermalExpansionAnisotropic",
            )

    class Density(PhysicalProperty):
        def __init__(self, value: str | float) -> None:
            super().__init__(
                value=value,
                definition="density",
                alternative="densityGeneric",
            )

    class DynamicViscosity(PhysicalProperty):
        def __init__(self, value: str | float) -> None:
            super().__init__(
                value=value,
                definition="dynamicViscosity",
                alternative="dynamicViscosityIsotropic",
            )

    class DynamicViscosityAnisotropic(PhysicalProperty):
        def __init__(self, value: List[List[float | str]]) -> None:
            if len(value) != 3:
                raise ValueError(
                    "Dynamic viscosity must be a list of 3 lists of 3 floats"
                )
            for row in value:
                if len(row) != 3:
                    raise ValueError(
                        "Dynamic viscosity must be a list of 3 lists of 3 floats"
                    )

            # Format 3x3 matrix to "[11, 12, 14; 12, 13, 15; 14, 15, 16]"
            # Each row becomes comma-separated values, rows separated by semicolons
            formatted_rows = []
            for row in value:
                formatted_row = ", ".join(str(v) for v in row)
                formatted_rows.append(formatted_row)
            formatted_value = "[" + "; ".join(formatted_rows) + "]"

            super().__init__(
                value=formatted_value,
                definition="dynamicViscosity",
                alternative="dynamicViscosityAnisotropic",
            )

    class ElasticityMatrixYoungsModulusPoissonsRatio(PhysicalProperty):

        def __init__(
            self, youngs_modulus: float | str, poissons_ratio: float | str
        ) -> None:
            super().__init__(
                value="",
                definition="",
                alternative="",
            )
            self.youngs_modulus = str(youngs_modulus)
            self.poissons_ratio = str(poissons_ratio)

        def to_rawapi(self) -> List[rawapi.PhysicalProperty]:
            return [
                rawapi.PhysicalProperty(
                    definition="poissonsRatio",
                    alternative="poissonsRatioGeneric",
                    value=self.poissons_ratio,
                ),
                rawapi.PhysicalProperty(
                    definition="youngsModulus",
                    alternative="youngsModulusGeneric",
                    value=self.youngs_modulus,
                ),
                rawapi.PhysicalProperty(
                    definition="elasticityMatrix",
                    alternative="elasticityMatrixYoungsModulusPoissonsRatio",
                ),
            ]

    class ElasticityMatrixPressureShearVelocity(PhysicalProperty):
        def __init__(
            self, pressure_velocity: float | str, shear_velocity: float | str
        ) -> None:
            super().__init__(
                value="",
                definition="",
                alternative="",
            )
            self.pressure_velocity = str(pressure_velocity)
            self.shear_velocity = str(shear_velocity)

        def to_rawapi(self) -> List[rawapi.PhysicalProperty]:
            return [
                rawapi.PhysicalProperty(
                    definition="elasticityMatrix",
                    alternative="elasticityMatrixPressureWaveVelocityShearWaveVelocityDensity",
                ),
                rawapi.PhysicalProperty(
                    definition="pressureWaveVelocity",
                    alternative="pressureWaveVelocityGeneric",
                    value=self.pressure_velocity,
                ),
                rawapi.PhysicalProperty(
                    definition="shearWaveVelocity",
                    alternative="shearWaveVelocityGeneric",
                    value=self.shear_velocity,
                ),
            ]

    class ElasticityMatrix(PhysicalProperty):
        def __init__(self, value: List[List[float | str]]) -> None:
            if len(value) != 6:
                raise ValueError("Elasticity matrix must be a list of 6 floats")
            for row in value:
                if len(row) != 6:
                    raise ValueError("Elasticity matrix must be a list of 6 floats")

            # Format 6x6 matrix to
            # "[11, 12, ..., 16; 21, 22, ..., 26; ...; 61, 62, ..., 66]"
            # Each row becomes comma-separated values, rows separated by semicolons
            formatted_rows = []
            for row in value:
                formatted_row = ", ".join(str(v) for v in row)  # noqa: F841
                formatted_rows.append(formatted_row)
            formatted_value = "[" + "; ".join(formatted_rows) + "]"  # noqa: F841
            super().__init__(
                value=formatted_value,
                definition="elasticityMatrix",
                alternative="elasticityMatrixGeneric",
            )

    class ElectricConductivity(PhysicalProperty):
        def __init__(self, value: str | float) -> None:
            super().__init__(
                value=value,
                definition="electricConductivity",
                alternative="electricConductivityIsotropic",
            )

    class ElectricConductivityAnisotropic(PhysicalProperty):
        def __init__(self, value: List[List[float | str]]) -> None:
            if len(value) != 3:
                raise ValueError(
                    "Electric conductivity must be a list of 3 lists of 3 floats"
                )
            for row in value:
                if len(row) != 3:
                    raise ValueError(
                        "Electric conductivity must be a list of 3 lists of 3 floats"
                    )
            formatted_rows = []
            for row in value:
                formatted_row = ", ".join(str(v) for v in row)
                formatted_rows.append(formatted_row)
            formatted_value = "[" + "; ".join(formatted_rows) + "]"
            super().__init__(
                value=formatted_value,
                definition="electricConductivity",
                alternative="electricConductivityAnisotropic",
            )

    class ElectricPermittivity(PhysicalProperty):
        def __init__(self, value: str | float) -> None:
            super().__init__(
                value=value,
                definition="electricPermittivity",
                alternative="electricPermittivityIsotropic",
            )

    class ElectricPermittivityAnisotropic(PhysicalProperty):
        def __init__(self, value: List[List[float | str]]) -> None:
            if len(value) != 3:
                raise ValueError(
                    "Electric permittivity must be a list of 3 lists of 3 floats"
                )
            for row in value:
                if len(row) != 3:
                    raise ValueError(
                        "Electric permittivity must be a list of 3 lists of 3 floats"
                    )
            formatted_rows = []
            for row in value:
                formatted_row = ", ".join(str(v) for v in row)
                formatted_rows.append(formatted_row)
            formatted_value = "[" + "; ".join(formatted_rows) + "]"
            super().__init__(
                value=formatted_value,
                definition="electricPermittivity",
                alternative="electricPermittivityAnisotropic",
            )

    class HeatCapacity(PhysicalProperty):
        def __init__(self, value: str | float) -> None:
            super().__init__(
                value=value,
                definition="heatCapacity",
                alternative="heatCapacityGeneric",
            )

    class MagneticPermeability(PhysicalProperty):
        def __init__(self, value: str | float) -> None:
            super().__init__(
                value=value,
                definition="magneticPermeability",
                alternative="magneticPermeabilityIsotropic",
            )

    class MagneticPermeabilityAnisotropic(PhysicalProperty):
        def __init__(self, value: List[List[float | str]]) -> None:
            if len(value) != 3:
                raise ValueError(
                    "Magnetic permeability must be a list of 3 lists of 3 floats"
                )
            for row in value:
                if len(row) != 3:
                    raise ValueError(
                        "Magnetic permeability must be a list of 3 lists of 3 floats"
                    )
            formatted_rows = []
            for row in value:
                formatted_row = ", ".join(str(v) for v in row)
                formatted_rows.append(formatted_row)
            formatted_value = "[" + "; ".join(formatted_rows) + "]"
            super().__init__(
                value=formatted_value,
                definition="magneticPermeability",
                alternative="magneticPermeabilityAnisotropic",
            )

    class MassDampingCoefficient(PhysicalProperty):
        def __init__(self, value: str | float) -> None:
            super().__init__(
                value=value,
                definition="massDampingCoefficient",
                alternative="massDampingCoefficientGeneric",
            )

    class PiezoelectricCoupling(PhysicalProperty):
        def __init__(self, value: List[List[float | str]]) -> None:
            if len(value) != 6:
                raise ValueError(
                    "Piezoelectric coupling must be a list of 6 lists of 3 floats"
                )
            for row in value:
                if len(row) != 3:
                    raise ValueError(
                        "Piezoelectric coupling must be a list of 6 lists of 3 floats"
                    )
            formatted_rows = []
            for row in value:
                formatted_row = ", ".join(str(v) for v in row)
                formatted_rows.append(formatted_row)
            formatted_value = "[" + "; ".join(formatted_rows) + "]"
            super().__init__(
                value=formatted_value,
                definition="piezoelectricCoupling",
                alternative="piezoelectricCouplingGeneric",
            )

    class PronySeries(PhysicalProperty):
        def __init__(
            self, poisson_ratio: str, youngs_modulus: str, relaxation_time: str
        ) -> None:
            super().__init__(
                value="",
                definition="",
                alternative="",
            )
            self.poisson_ratio = poisson_ratio
            self.youngs_modulus = youngs_modulus
            self.relaxation_time = relaxation_time

        def to_rawapi(self) -> List[rawapi.PhysicalProperty]:
            return [
                rawapi.PhysicalProperty(
                    definition="pronyPoissonsRatio",
                    alternative="pronyPoissonsRatioGeneric",
                    value=self.poisson_ratio,
                ),
                rawapi.PhysicalProperty(
                    definition="pronyYoungsModulus",
                    alternative="pronyYoungsModulusGeneric",
                    value=self.youngs_modulus,
                ),
                rawapi.PhysicalProperty(
                    definition="pronyRelaxationTime",
                    alternative="pronyRelaxationTimeGeneric",
                    value=self.relaxation_time,
                ),
                rawapi.PhysicalProperty(
                    definition="pronySeries",
                    alternative="pronySeriesYoungsModulusPoissonsRatioRelaxationTime",
                ),
            ]

    class SpeedOfSound(PhysicalProperty):
        def __init__(self, value: str | float) -> None:
            super().__init__(
                value=value,
                definition="speedOfSound",
                alternative="speedOfSoundGeneric",
            )

    class StiffnessDampingCoefficient(PhysicalProperty):
        def __init__(self, value: str | float) -> None:
            super().__init__(
                value=value,
                definition="stiffnessDampingCoefficient",
                alternative="stiffnessDampingCoefficientGeneric",
            )

    class ThermalConductivity(PhysicalProperty):
        def __init__(self, value: str | float) -> None:
            super().__init__(
                value=value,
                definition="thermalConductivity",
                alternative="thermalConductivityIsotropic",
            )

    class ThermalConductivityAnisotropic(PhysicalProperty):
        def __init__(self, value: List[List[float | str]]) -> None:
            if len(value) != 3:
                raise ValueError(
                    "Thermal conductivity must be a list of 3 lists of 3 floats"
                )
            for row in value:
                if len(row) != 3:
                    raise ValueError(
                        "Thermal conductivity must be a list of 3 lists of 3 floats"
                    )
            formatted_rows = []
            for row in value:
                formatted_row = ", ".join(str(v) for v in row)
                formatted_rows.append(formatted_row)
            formatted_value = "[" + "; ".join(formatted_rows) + "]"
            super().__init__(
                value=formatted_value,
                definition="thermalConductivity",
                alternative="thermalConductivityAnisotropic",
            )


class Material:
    """
    Material is a class for managing materials in a project.
    """

    @classmethod
    def create(
        cls,
        name: str,
        color: str,
        description: str | None = None,
        properties: List[MaterialProperty.PhysicalProperty] = [],
        target_region: Region | None = None,
        abbreviation: str | None = None,
        orientation: str | Tuple[float | int, float | int, float | int] | None = None,
        enabled: str | None = None,
        project_id: str | None = None,
    ) -> Self:
        """
        Create a new material.

        Parameters:
            name: The name of the material.
            color: The color of the material. Format: "#RRGGBB"
            description: Optional description of the material.
            properties: List of PhysicalProperty objects of the material.
            target_region: The target Region of the material.
            abbreviation: Optional abbreviation of the material.
            orientation: Optional orientation of the material.
                Can be a tuple of 3 floats or a string like "[90; 0; 0]"
            enabled: Optional enabled expression of the material.
                Can be a string expression like "eq(my_variable, 1)"
            project_id: The ID of the project.

        Returns:
            The created Material.
        """
        project_id = check_for_project_api_key(project_id)

        cls._validate_properties(properties)

        orientation = cls._convert_orientation_to_string(orientation)

        properties_rawapi = []
        for property in properties:
            rawapi_properties = property.to_rawapi()
            properties_rawapi.extend(rawapi_properties)

        with get_api() as api:
            material = api.create_material(
                authorization=get_auth(),
                project_id=project_id,
                new_material=rawapi.NewMaterial(
                    name=name,
                    color=color,
                    description=description,
                    properties=properties_rawapi,
                    target=target_region.id if target_region else None,
                    abbreviation=abbreviation,
                    orientation=orientation if orientation else None,
                    enabled=enabled if enabled else None,
                ),
            )
        return cls(project_id, material)

    @classmethod
    def get(cls, material_id: str, project_id: str | None = None) -> Self:
        """
        Get a material by its ID.
        """
        project_id = check_for_project_api_key(project_id)
        with get_api() as api:
            material = api.get_material(
                authorization=get_auth(),
                project_id=project_id,
                material_id=material_id,
            )
        return cls(project_id, material)

    @classmethod
    def get_all(cls, project_id: str | None = None) -> List[Self]:
        """
        Get all materials in a project.
        """
        project_id = check_for_project_api_key(project_id)
        with get_api() as api:
            materials = api.get_materials(
                authorization=get_auth(),
                project_id=project_id,
            )
            return [
                cls(
                    project_id,
                    material,
                )
                for material in materials
            ]

    @classmethod
    def get_all_from_library(cls) -> List[rawapi.Material]:
        """
        Get all library materials.

        Returns:
            List of library rawapi.Material objects.
        """
        with get_api() as api:
            return api.get_shared_materials(
                authorization=get_auth(),
            )

    @classmethod
    def create_from_library(
        cls,
        name: str,
        target_region: Region | None = None,
        enabled: str | None = None,
        project_id: str | None = None,
    ) -> Self:
        """
        Create a new material from a library material by name.

        Parameters:
            name: The name of the library material to copy.
            target_region: The target Region of the material.
            enabled: Optional enabled expression of the material.
                Can be a string expression like "eq(my_variable, 1)"
            project_id: The ID of the project.

        Returns:
            The created Material.

        Raises:
            ValueError: If no library material with the given name is found.
        """
        library_materials = cls.get_all_from_library()
        library_material = next(
            (m for m in library_materials if m.name == name),
            None,
        )
        if library_material is None:
            raise ValueError(f"Library material '{name}' not found")

        return cls.create(
            name=library_material.name,
            color=library_material.color,
            description=library_material.description,
            abbreviation=library_material.abbreviation,
            target_region=target_region,
            properties=[
                MaterialProperty.PhysicalProperty(
                    value=p.value,
                    definition=p.definition,
                    alternative=p.alternative,
                )
                for p in library_material.properties
                if p.value
            ],
            enabled=enabled,
            project_id=project_id,
        )

    @classmethod
    def _convert_orientation_to_string(
        cls, orientation: str | Tuple[float | int, float | int, float | int] | None
    ) -> str | None:
        """Convert the orientation to the string format like "[90; 0; 0]"."""
        if orientation is not None:
            if isinstance(orientation, tuple):
                if len(orientation) != 3:
                    raise ValueError("Orientation must be a tuple of 3 floats")
                orientation = f"[{'; '.join(str(v) for v in orientation)}]"
        return orientation

    @classmethod
    def _validate_properties(
        cls, properties: List[MaterialProperty.PhysicalProperty]
    ) -> None:
        """Validate the properties of the material."""

        # Validate elasticity matrix
        elasticityMatrixCount = 0
        for property in properties:
            if isinstance(property, MaterialProperty.ElasticityMatrix):
                elasticityMatrixCount += 1
            if isinstance(
                property, MaterialProperty.ElasticityMatrixYoungsModulusPoissonsRatio
            ):
                elasticityMatrixCount += 1
            if isinstance(
                property, MaterialProperty.ElasticityMatrixPressureShearVelocity
            ):
                elasticityMatrixCount += 1

        if elasticityMatrixCount > 1:
            raise ValueError("Only one elasticity matrix is allowed")

        # Validate dynamic viscosity
        dynamicViscosityCount = 0
        for property in properties:
            if isinstance(property, MaterialProperty.DynamicViscosity):
                dynamicViscosityCount += 1
            if isinstance(property, MaterialProperty.DynamicViscosityAnisotropic):
                dynamicViscosityCount += 1

        if dynamicViscosityCount > 1:
            raise ValueError("Only one dynamic viscosity is allowed")

        # Validate electric conductivity
        electricConductivityCount = 0
        for property in properties:
            if isinstance(property, MaterialProperty.ElectricConductivity):
                electricConductivityCount += 1
            if isinstance(property, MaterialProperty.ElectricConductivityAnisotropic):
                electricConductivityCount += 1

        if electricConductivityCount > 1:
            raise ValueError("Only one electric conductivity is allowed")

        # Validate electric permittivity
        electricPermittivityCount = 0
        for property in properties:
            if isinstance(property, MaterialProperty.ElectricPermittivity):
                electricPermittivityCount += 1
            if isinstance(property, MaterialProperty.ElectricPermittivityAnisotropic):
                electricPermittivityCount += 1

        if electricPermittivityCount > 1:
            raise ValueError("Only one electric permittivity is allowed")

        # Validate magnetic permeability
        magneticPermeabilityCount = 0
        for property in properties:
            if isinstance(property, MaterialProperty.MagneticPermeability):
                magneticPermeabilityCount += 1
            if isinstance(property, MaterialProperty.MagneticPermeabilityAnisotropic):
                magneticPermeabilityCount += 1

        if magneticPermeabilityCount > 1:
            raise ValueError("Only one magnetic permeability is allowed")

        # Validate thermal conductivity
        thermalConductivityCount = 0
        for property in properties:
            if isinstance(property, MaterialProperty.ThermalConductivity):
                thermalConductivityCount += 1
            if isinstance(property, MaterialProperty.ThermalConductivityAnisotropic):
                thermalConductivityCount += 1

        if thermalConductivityCount > 1:
            raise ValueError("Only one thermal conductivity is allowed")

    def __init__(self, project_id: str, material: rawapi.Material) -> None:
        self._project_id = project_id
        self.material = material
        self._deleted: bool = False
        self._uncommitted_update: rawapi.MaterialUpdate | None = None

    @property
    @prevent_deleted
    def id(self) -> str:
        """
        Get the ID of the material.
        """
        return self.material.id

    @property
    @prevent_deleted
    def name(self) -> str:
        """
        Get the name of the material.
        """
        return self.material.name

    @name.setter
    @prevent_deleted
    def name(self, name: str) -> None:
        """
        Set the name of the material.
        Use save() to commit the change.
        """
        self._current_uncommitted_update().name = name

    @property
    @prevent_deleted
    def description(self) -> str | None:
        """
        Get the description of the material.
        """
        return self.material.description

    @description.setter
    @prevent_deleted
    def description(self, description: str) -> None:
        """
        Set the description of the material.
        Use save() to commit the change.
        """
        self._current_uncommitted_update().description = description

    @property
    @prevent_deleted
    def color(self) -> str:
        """
        Get the color of the material.
        """
        return self.material.color

    @color.setter
    @prevent_deleted
    def color(self, color: str) -> None:
        """
        Set the color of the material.
        Use save() to commit the change.
        """
        self._current_uncommitted_update().color = color

    @property
    @prevent_deleted
    def target(self) -> str | None:
        """
        Get the target of the material.
        """
        return self.material.target

    @target.setter
    @prevent_deleted
    def target(self, target: str) -> None:
        """
        Set the target of the material.
        Use save() to commit the change.
        """
        self._current_uncommitted_update().target = target

    @property
    @prevent_deleted
    def properties(self) -> List[rawapi.PhysicalProperty]:
        """
        Get the properties of the material.
        """
        return self.material.properties

    @properties.setter
    @prevent_deleted
    def properties(self, properties: List[rawapi.PhysicalProperty]) -> None:
        """
        Set the properties of the material.
        Use save() to commit the change.
        """
        # TODO: Mapping to MaterialProperty.PhysicalProperty
        self._current_uncommitted_update().properties = properties

    @property
    @prevent_deleted
    def abbreviation(self) -> str | None:
        """
        Get the abbreviation of the material.
        """
        return self.material.abbreviation

    @abbreviation.setter
    @prevent_deleted
    def abbreviation(self, abbreviation: str) -> None:
        """
        Set the abbreviation of the material.
        Use save() to commit the change.
        """
        self._current_uncommitted_update().abbreviation = abbreviation

    @property
    @prevent_deleted
    def orientation(self) -> str | None:
        """
        Get the orientation of the material.
        """
        return self.material.orientation

    @orientation.setter
    @prevent_deleted
    def orientation(
        self, orientation: str | Tuple[float | int, float | int, float | int] | None
    ) -> None:
        """
        Set the orientation of the material.
        Can be a tuple of 3 floats or a string like "[90; 0; 0]"
        Use save() to commit the change.
        """
        orientation = self._convert_orientation_to_string(orientation)
        self._current_uncommitted_update().orientation = (
            orientation if orientation else None
        )

    @property
    @prevent_deleted
    def enabled(self) -> str | None:
        """
        Get the enabled status of the material.
        """
        return self.material.enabled

    @enabled.setter
    @prevent_deleted
    def enabled(self, enabled: str) -> None:
        """
        Set the enabled status of the material.
        Use save() to commit the change.
        """
        self._current_uncommitted_update().enabled = enabled

    @prevent_deleted
    def delete(self) -> None:
        """
        Delete the material.
        """
        with get_api() as api:
            api.delete_material(
                authorization=get_auth(),
                project_id=self._project_id,
                material_id=self.id,
            )
        self._deleted = True

    @prevent_deleted
    def save(self) -> None:
        """
        Explicitly save the changes to the cloud made by
        setting properties `name`, `description`, `color`, and `properties`.
        """
        if self._uncommitted_update is None:
            return

        project_id = check_for_project_api_key(self._project_id)
        material_update = self._current_uncommitted_update()

        with get_api() as api:
            api.update_material(
                authorization=get_auth(),
                project_id=project_id,
                material_id=self.id,
                material_update=material_update,
            )

            self._uncommitted_update = None

            self.material = api.get_material(
                authorization=get_auth(),
                project_id=self._project_id,
                material_id=self.id,
            )

    @prevent_deleted
    def _current_uncommitted_update(self) -> rawapi.MaterialUpdate:
        """Get the current uncommitted update for the material."""
        if self.material is None:
            raise ValueError("Material is not initialized")
        if self._uncommitted_update is None:
            self._uncommitted_update = rawapi.MaterialUpdate(
                name=self.material.name,
                description=self.material.description,
                color=self.material.color,
                properties=self.material.properties,
                target=self.material.target,
                orientation=(
                    self.material.orientation if self.material.orientation else None
                ),
                enabled=self.material.enabled if self.material.enabled else None,
            )

        return self._uncommitted_update

    def __str__(self) -> str:
        return f"Material(name={self.name}, id={self.id}, color={self.color})"
