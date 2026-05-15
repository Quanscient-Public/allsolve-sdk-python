# Copyright 2026 Quanscient Oy
# SPDX-License-Identifier: Apache-2.0

from typing import List, Tuple
import allsolve_rawapi as rawapi
import re
import pathlib
from allsolve_rawapi import GeometryUnit


class GDSUnit:
    """
    GDSUnit describes a unit in GDS2 file.
    """

    @classmethod
    def _validate(cls, value: str | None) -> None:
        """
        Validate a GDS unit string.

        Args:
            value: The string to validate.

        Raises:
            ValueError: If the value does not match the required pattern.
        """
        if value is None:
            return
        if not re.match(
            r"^\s*([\-]?(?:0\.|[1-9][0-9]*\.)?[0-9]+(?:[eE][+\-]?[1-9][0-9]*)?)\s*(m|mm|um|nm)?$",
            value,
        ):
            raise ValueError(f"Invalid GDSUnit value: '{value}'")

    def __init__(self, value: str | None) -> None:
        self._validate(value)
        self._value = value

    @property
    def value(self) -> str | None:
        """Get the value of the GDS unit."""
        return self._value

    @value.setter
    def value(self, value: str | None) -> None:
        """Set the value of the GDS unit."""
        self._validate(value)
        self._value = value


class GDSAbsoluteLayer:
    """
    GDSAbsoluteLayer describes a layer in GDS2 file with thickness and absolute z0.
    """

    def __init__(
        self,
        name: str,
        thickness: str | int | float,
        absolute_z0: str | int | float,
        disabled: bool = False,
    ) -> None:
        self.name = name
        self.thickness = GDSUnit(str(thickness))
        self.absolute_z0 = GDSUnit(str(absolute_z0))
        self.disabled = disabled

    @property
    def name(self) -> str:
        """Get the name of the layer."""
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        """Set the name of the layer."""
        self._name = value

    @property
    def absolute_z0(self) -> GDSUnit:
        """Get the absolute z0 of the layer."""
        return self._absolute_z0

    @absolute_z0.setter
    def absolute_z0(self, value: GDSUnit) -> None:
        """Set the absolute z0 of the layer."""
        self._absolute_z0 = value

    @property
    def disabled(self) -> bool:
        """Get the disabled state of the layer."""
        return self._disabled

    @disabled.setter
    def disabled(self, value: bool) -> None:
        """Set the disabled state of the layer."""
        self._disabled = value


class GDSStackedLayer:
    """
    GDSStackedLayer describes a layer in GDS2 file with thickness.
    Z0 is calculated from previous layers.
    """

    def __init__(
        self,
        name: str,
        thickness: str | int | float,
        disabled: bool = False,
    ) -> None:
        self.name = name
        self.thickness = GDSUnit(str(thickness))
        self.disabled = disabled

    @property
    def name(self) -> str:
        """Get the name of the layer."""
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        """Set the name of the layer."""
        self._name = value

    @property
    def thickness(self) -> GDSUnit:
        """Get the thickness of the layer."""
        return self._thickness

    @thickness.setter
    def thickness(self, value: GDSUnit) -> None:
        """Set the thickness of the layer."""
        self._thickness = value

    @property
    def disabled(self) -> bool:
        """Get the disabled state of the layer."""
        return self._disabled

    @disabled.setter
    def disabled(self, value: bool) -> None:
        """Set the disabled state of the layer."""
        self._disabled = value


class GDS2ImportConfig:
    """
    GDS2ImportConfig holds parameters for importing a geometry from a GDS2 file.
    Configuration requires an unit and layers defined in absolute or/and stacked order.
    Each layer should have thickness and a name as defined in the GDS2 file.
    Absolute layers should have also absolute z0.
    """

    class GDSLayer:
        def __init__(
            self,
            name: str,
            thickness: GDSUnit,
            disabled: bool = False,
            id: int | None = None,
            previous_layer_id: int | None = None,
            absolute_z0: GDSUnit | None = None,
        ) -> None:
            self.name = name
            if id is not None and id < 0:
                raise ValueError("Layer id must be non-negative")
            if thickness.value is None:
                raise ValueError("Thickness is required")
            self.id = id
            self.disabled = disabled
            self.previous_layer_id = previous_layer_id
            self.absolute_z0 = absolute_z0
            self.thickness = thickness

        def _to_rawapi(self) -> rawapi.GDSLayer:
            if self.thickness.value is None:
                raise ValueError("Thickness is required")
            result: rawapi.GDSLayer = rawapi.GDSLayer(
                name=self.name,
                disabled=self.disabled,
                thickness=self.thickness.value,
            )
            if self.id is not None:
                result.id = self.id
            if self.previous_layer_id is not None:
                result.previous_layer_id = self.previous_layer_id
            if self.absolute_z0 is not None:
                result.absolute_z0 = self.absolute_z0.value
            return result

    def __init__(
        self,
        unit: GeometryUnit,
        absolute_layers: (
            List[GDSAbsoluteLayer | Tuple[str, str | int | float, str | int | float]]
            | None
        ) = None,
        stacked_layers: (
            List[GDSStackedLayer | Tuple[str, str | int | float]] | None
        ) = None,
        included_top_level_cells: List[str] | None = None,
        z_offset: GDSUnit | None = None,
    ) -> None:
        self._unit = unit
        self.layers: List[GDS2ImportConfig.GDSLayer] = []

        if absolute_layers:
            for absolute_layer in absolute_layers:
                if isinstance(absolute_layer, tuple):
                    name, thickness, absolute_z0 = absolute_layer
                    absolute_layer = GDSAbsoluteLayer(name, thickness, absolute_z0)
                self.layers.append(
                    GDS2ImportConfig.GDSLayer(
                        name=absolute_layer.name,
                        thickness=absolute_layer.thickness,
                        absolute_z0=absolute_layer.absolute_z0,
                        disabled=absolute_layer.disabled,
                    )
                )
        if stacked_layers:
            id = 0
            previous_layer_id = None
            for stacked_layer in stacked_layers:
                if isinstance(stacked_layer, tuple):
                    name, thickness = stacked_layer
                    stacked_layer = GDSStackedLayer(name, thickness)
                self.layers.append(
                    GDS2ImportConfig.GDSLayer(
                        name=stacked_layer.name,
                        thickness=stacked_layer.thickness,
                        disabled=stacked_layer.disabled,
                        id=id,
                        previous_layer_id=previous_layer_id,
                    )
                )
                previous_layer_id = id
                id += 1

        if len(self.layers) == 0:
            raise ValueError("At least one layer is required")

        self.included_top_level_cells = included_top_level_cells or []
        self.z_offset = z_offset

    @property
    def unit(self) -> GeometryUnit:
        """Get the unit of the GDSImportConfig."""
        return self._unit

    def _to_rawapi(self) -> rawapi.GDSImportConfig:
        result: rawapi.GDSImportConfig = rawapi.GDSImportConfig(
            layers=[layer._to_rawapi() for layer in self.layers],
        )
        if self.included_top_level_cells:
            result.included_top_level_cells = self.included_top_level_cells
        if self.z_offset is not None and self.z_offset.value is not None:
            result.z_offset = self.z_offset.value
        return result


class GeometryElement:
    """
    GeometryElement is a base class for importing a geometry to a project.
    """

    class ImportGeometry:
        """ImportGeometry is a base class for importing a geometry to a project from a file."""

        def __init__(
            self,
            filepath: str,
            expected_type: rawapi.GeometryFileType,
            config: dict | GDS2ImportConfig | None = None,
        ) -> None:
            file: pathlib.Path = pathlib.Path(filepath)
            if not file.is_file():
                raise FileNotFoundError(f"Geometry file not found: {filepath}")

            self._filepath: str = filepath
            self._file_type: rawapi.GeometryFileType = self.get_file_type(file)
            if self._file_type != expected_type:
                raise ValueError(
                    f"Wrong file type: {self._file_type} expected {expected_type}"
                )
            self._file_name: str = file.name
            self._file_size: int = file.stat().st_size
            self._config: dict | GDS2ImportConfig | None = config

        @property
        def filepath(self) -> str:
            return self._filepath

        @property
        def file_type(self) -> rawapi.GeometryFileType:
            return self._file_type

        @property
        def file_name(self) -> str:
            return self._file_name

        @property
        def file_size(self) -> int:
            return self._file_size

        @property
        def config(self) -> dict | GDS2ImportConfig | None:
            return self._config

        @staticmethod
        def get_file_type(filepath: pathlib.Path) -> rawapi.GeometryFileType:
            suffix: str = filepath.suffix.lower()
            if suffix == ".step" or suffix == ".stp":
                return rawapi.GeometryFileType.STEP
            elif suffix == ".iges" or suffix == ".igs":
                return rawapi.GeometryFileType.IGES
            elif suffix == ".brep":
                return rawapi.GeometryFileType.BREP
            elif suffix == ".sat":
                return rawapi.GeometryFileType.SAT
            elif suffix == ".msh":
                return rawapi.GeometryFileType.MSH
            elif suffix == ".nas":
                return rawapi.GeometryFileType.NAS
            elif suffix == ".gds2" or suffix == ".gds":
                return rawapi.GeometryFileType.GDS2
            else:
                raise ValueError(f"Unsupported file type: {suffix}")

        def __str__(self) -> str:
            return f"{self.__class__.__name__}(filepath={self._filepath}, config={self._config})"

    class ImportStep(ImportGeometry):
        """ImportStep is a class for importing a STEP file to a project."""

        def __init__(self, filepath: str, config=None) -> None:
            super().__init__(filepath, rawapi.GeometryFileType.STEP, config)

    class ImportIges(ImportGeometry):
        """ImportIges is a class for importing an IGES file to a project."""

        def __init__(self, filepath: str, config=None) -> None:
            super().__init__(filepath, rawapi.GeometryFileType.IGES, config)

    class ImportBrep(ImportGeometry):
        """ImportBrep is a class for importing a BREP file to a project."""

        def __init__(self, filepath: str, config=None) -> None:
            super().__init__(filepath, rawapi.GeometryFileType.BREP, config)

    class ImportSat(ImportGeometry):
        """ImportSat is a class for importing a SAT file to a project."""

        def __init__(self, filepath: str, config=None) -> None:
            super().__init__(filepath, rawapi.GeometryFileType.SAT, config)

    class ImportMsh(ImportGeometry):
        """ImportMsh is a class for importing a MSH file to a project."""

        def __init__(self, filepath: str, config=None) -> None:
            super().__init__(filepath, rawapi.GeometryFileType.MSH, config)

    class ImportNas(ImportGeometry):
        """ImportNas is a class for importing a NAS file to a project."""

        def __init__(self, filepath: str, config=None) -> None:
            super().__init__(filepath, rawapi.GeometryFileType.NAS, config)

    class ImportGds2(ImportGeometry):
        """ImportGds2 is a class for importing a GDS2 file to a project."""

        def __init__(self, filepath: str, config: GDS2ImportConfig) -> None:
            super().__init__(filepath, rawapi.GeometryFileType.GDS2, config)
