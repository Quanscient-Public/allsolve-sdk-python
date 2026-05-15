# Copyright 2026 Quanscient Oy
# SPDX-License-Identifier: Apache-2.0

import abc
import csv
import io
import re
import warnings
from typing import List
from allsolve.api import (
    get_allow_insecure_http,
    get_api,
    get_auth,
    get_http_session,
)
from allsolve.http_transfer import (
    CONNECT_TIMEOUT_S,
    TRANSFER_TIMEOUT_S,
    validate_url_scheme,
)
from allsolve.file import upload_parts
import allsolve_rawapi as rawapi
from allsolve_rawapi.models.cad_gds_unify_layer_discretizations import (
    CadGdsUnifyLayerDiscretizations,
)
from allsolve_rawapi.models.cad_spline_method import CadSplineMethod
from typing_extensions import Self
import pathlib

from .cad_utils import (
    create_distance,
    from_distance,
    create_angle,
    from_angle,
    create_scalar,
    from_scalar,
    create_angular_unit,
)
from .cad_geometry_element import CadGeometryElement
from allsolve.util import prevent_deleted
from .cad_geometry_type import CadGeometryType


class CadFileImport(CadGeometryElement):

    @classmethod
    def _from_rawapi(
        cls, rawapi_element: rawapi.GeometryElement, project_id: str | None = None
    ) -> Self:

        cad_element = rawapi_element.cad_elem
        if cad_element is None:
            raise ValueError("CAD geometry element is not set")
        if cad_element.cad_file is None:
            raise ValueError("CAD file definition is not set")
        if cad_element.cad_file.type != cls._get_rawapi_type():
            raise ValueError(f"CAD file type is not {cls._get_rawapi_type()}")

        cad_file = cad_element.cad_file
        if cad_element.name is None:
            raise ValueError("File name must be set")

        cleanup = False
        if cad_file.parameters is not None:
            cleanup = cad_file.parameters.cleanup

        filepath = cad_file.filename
        if filepath is None:
            filepath = cad_element.name

        cad_object = cls(
            filepath=filepath,
            cleanup=cleanup,
        )

        cls._initialize_from_rawapi(cad_object, rawapi_element, cad_element, project_id)
        return cad_object

    @classmethod
    def _get_rawapi_type(cls) -> rawapi.CadImportType:
        raise NotImplementedError(
            f"{cls.__name__} must implement _get_rawapi_type() method"
        )

    def __init__(
        self,
        filepath: str,
        name: str | None = None,
        cleanup: bool = False,
        enabled: str | bool | None = None,
    ) -> None:
        super().__init__(name=name, enabled=enabled)
        self._filepath: str = filepath
        self._key: str | None = None  # Set internally after file upload
        self._metadata_filename: str | None = None  # Internal use only
        self._metadata_key: str | None = None  # Internal use only
        self._cleanup = cleanup

    def _require_cad_file(self) -> rawapi.CadFileDefinition:
        cad_elem = self._require_cad_elem()
        if cad_elem.cad_file is None:
            raise ValueError("CAD file is not set")
        return cad_elem.cad_file

    @abc.abstractmethod
    def _get_supported_file_suffixes(self) -> list[str]:
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement _get_supported_file_suffixes() method"
        )

    @property
    @prevent_deleted
    def filepath(self) -> str:
        return self._filepath

    @property
    @prevent_deleted
    def cleanup(self) -> bool:
        """Get the cleanup setting."""
        return self._cleanup

    def _initialize_file_attributes(self) -> str:
        if self._filepath is None:
            raise ValueError("File path is not set")

        file_path = pathlib.Path(self._filepath)
        if not file_path.is_file():
            raise FileNotFoundError(f"File not found: {self._filepath}")
        suffix: str = file_path.suffix.lower()
        if suffix not in self._get_supported_file_suffixes():
            raise ValueError(f"Unsupported file type: {suffix}")

        # Set name and file size that are required for uploading the file
        if self._name is None:
            self._name = file_path.name
        self.file_size = file_path.stat().st_size

        return self._filepath

    def _is_file_import(self) -> bool:
        return True

    def _upload(self) -> rawapi.InputFile:
        """
        Upload the geometry file to the project.
        Note: This is called automatically when a geometry is created.
        """
        if self._filepath is None:
            raise ValueError("Geometry file path is not set")
        if self._project_id is None:
            raise ValueError("Project ID is not set")
        if self.id is None:
            raise ValueError("Geometry element ID is not set")

        with get_api() as api:
            url_info = api.get_file_upload_urls(
                authorization=get_auth(), project_id=self._project_id, file_id=self.id
            )

        file = pathlib.Path(self._filepath)
        if not file.is_file():
            raise FileNotFoundError(f"Geometry file not found: {self._filepath}")

        with open(file, "rb") as f:
            completion = upload_parts(f, url_info)

        with get_api() as api:
            response = api.mark_file_uploaded(
                authorization=get_auth(),
                project_id=self._project_id,
                file_id=self.id,
                file_upload_completion=completion,
            )

        return response

    @prevent_deleted
    def download(
        self, output_dir: str = "./", *, overwrite: bool = True
    ) -> pathlib.Path:
        """
        Download the geometry file to a local directory.

        Parameters:
            output_dir: Directory to save the file to. Defaults to the current
                working directory.
            overwrite: If False, raise FileExistsError when the destination file
                already exists. If True (default), replace an existing file.

        Returns:
            The path to the downloaded file.
        """
        if self._project_id is None:
            raise ValueError("Project ID is not set")
        if self.id is None:
            raise ValueError("Geometry element ID is not set")

        with get_api() as api:
            response = api.get_geometry_file_download_url(
                authorization=get_auth(),
                project_id=self._project_id,
                geometry_element_id=self.id,
            )

        url = response.download_url
        if url is None:
            raise ValueError("Failed to get geometry file download URL")

        output_path = pathlib.Path(output_dir)
        if not output_path.exists():
            output_path.mkdir(parents=True, exist_ok=True)

        filename = pathlib.Path(self._filepath).name
        filepath = output_path / filename

        if not overwrite and filepath.exists():
            raise FileExistsError(
                f"File already exists: {filepath}. "
                "Pass overwrite=True to replace it, or choose a different output_dir."
            )

        validate_url_scheme(url, get_allow_insecure_http())
        session = get_http_session()
        with session.get(
            url,
            stream=True,
            timeout=(CONNECT_TIMEOUT_S, TRANSFER_TIMEOUT_S),
        ) as r:
            r.raise_for_status()
            with open(filepath, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

        return filepath

    @prevent_deleted
    def _to_rawapi_cad_element(self) -> rawapi.CadGeometryElement:

        if self._name is None:
            raise ValueError("Name is not set")
        if self.file_size is None:
            raise ValueError("File size is not set")

        import_config = rawapi.CadImportConfig(
            cleanup=self._cleanup,
        )

        file_path = pathlib.Path(self._filepath)
        filename = file_path.name
        cad_file_def = rawapi.CadFileDefinition(
            type=self._get_rawapi_type(),
            filename=filename,
            parameters=import_config,
            size=self.file_size,
        )

        cad_element = rawapi.CadGeometryElement(
            cadFile=cad_file_def,
            name=self._name,
        )

        return cad_element

    def _parse_gds_unit(self, gds_unit_str: str | None) -> tuple[str, str | None]:
        """
        Parse a GDSUnit string to extract value and unit.

        Returns:
            Tuple of (value_string, unit_string) where unit_string can be None.
        """
        if gds_unit_str is None:
            raise ValueError("GDSUnit value cannot be None")

        # Match the pattern: value with optional unit (m, mm, um, nm)
        match = re.match(
            r"^\s*([\-]?(?:0\.|[1-9][0-9]*\.)?[0-9]+(?:[eE][+\-]?[1-9][0-9]*)?)\s*(m|mm|um|nm)?\s*$",
            gds_unit_str.strip(),
        )
        if not match:
            # If it doesn't match, treat the whole string as value
            return (gds_unit_str.strip(), None)

        value = match.group(1)
        unit = match.group(2)
        return (value, unit)

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(filepath={self._filepath}, name={self._name}, cleanup={self._cleanup})"


class CadStepFile(CadFileImport):
    """
    CadStepFile represents a STEP file geometry import.
    """

    def __init__(
        self,
        filepath: str,
        name: str | None = None,
        cleanup: bool = False,
        enabled: str | bool | None = None,
    ) -> None:
        """
        Create a new STEP file geometry import.

        Parameters:
            filepath: Path to a local STEP file. The file will be uploaded automatically.
            name: Optional name for the geometry element
            cleanup: Whether to clean up the imported file.
                Currently not supported yet.
            enabled: Optional enabled state of the geometry element.
                Can be a boolean or a string expression.
                By default, the geometry element is enabled.
        """
        super().__init__(filepath, name, cleanup, enabled)

    @classmethod
    def _get_rawapi_type(cls) -> rawapi.CadImportType:
        return rawapi.CadImportType.STEP

    def _get_supported_file_suffixes(self) -> list[str]:
        return [".step", ".stp"]

    @property
    @prevent_deleted
    def type(self) -> CadGeometryType:
        """Get the type of the geometry element."""
        return CadGeometryType.STEP_FILE


class CadIgesFile(CadFileImport):
    """
    CadIgesFile represents an IGES file geometry import.
    """

    def __init__(
        self,
        filepath: str,
        name: str | None = None,
        cleanup: bool = False,
        enabled: str | bool | None = None,
    ) -> None:
        """
        Create a new IGES file geometry import.

        Parameters:
            filepath: Path to a local IGES file. The file will be uploaded automatically.
            name: Optional name for the geometry element
            cleanup: Whether to clean up the imported file.
                Currently not supported yet.
            enabled: Optional enabled state of the geometry element.
                Can be a boolean or a string expression.
                By default, the geometry element is enabled.
        """
        super().__init__(filepath, name, cleanup, enabled)

    @classmethod
    def _get_rawapi_type(cls) -> rawapi.CadImportType:
        return rawapi.CadImportType.IGES

    def _get_supported_file_suffixes(self) -> list[str]:
        return [".iges", ".igs"]

    @property
    @prevent_deleted
    def type(self) -> CadGeometryType:
        """Get the type of the geometry element."""
        return CadGeometryType.IGES_FILE


class CadSatFile(CadFileImport):
    """
    CadSatFile represents a SAT (ACIS) file geometry import.
    """

    def __init__(
        self,
        filepath: str,
        name: str | None = None,
        cleanup: bool = False,
        enabled: str | bool | None = None,
    ) -> None:
        """
        Create a new SAT file geometry import.

        Parameters:
            filepath: Path to a local SAT file. The file will be uploaded automatically.
            name: Optional name for the geometry element
            cleanup: Whether to clean up the imported file.
                Currently not supported yet.
            enabled: Optional enabled state of the geometry element.
                Can be a boolean or a string expression.
                By default, the geometry element is enabled.
        """
        super().__init__(filepath, name, cleanup, enabled)

    @classmethod
    def _get_rawapi_type(cls) -> rawapi.CadImportType:
        return rawapi.CadImportType.SAT

    def _get_supported_file_suffixes(self) -> list[str]:
        return [".sat"]

    @property
    @prevent_deleted
    def type(self) -> CadGeometryType:
        """Get the type of the geometry element."""
        return CadGeometryType.SAT_FILE


class CadBrepFile(CadFileImport):
    """
    CadBrepFile represents a BREP (OpenCASCADE) file geometry import.
    """

    def __init__(
        self,
        filepath: str,
        name: str | None = None,
        cleanup: bool = False,
        enabled: str | bool | None = None,
    ) -> None:
        """
        Create a new BREP file geometry import.

        Parameters:
            filepath: Path to a local BREP file. The file will be uploaded automatically.
            name: Optional name for the geometry element
            cleanup: Whether to clean up the imported file.
                Currently not supported yet.
            enabled: Optional enabled state of the geometry element.
                Can be a boolean or a string expression.
                By default, the geometry element is enabled.
        """
        super().__init__(filepath, name, cleanup, enabled)

    @classmethod
    def _get_rawapi_type(cls) -> rawapi.CadImportType:
        return rawapi.CadImportType.BREP

    def _get_supported_file_suffixes(self) -> list[str]:
        return [".brep"]

    @property
    @prevent_deleted
    def type(self) -> CadGeometryType:
        """Get the type of the geometry element."""
        return CadGeometryType.BREP_FILE


class CadMshFile(CadFileImport):
    """
    CadMshFile represents a Gmsh MSH file geometry import.
    Only one MSH file can exist in a project and it cannot coexist with other geometry elements.
    """

    def __init__(self, filepath: str) -> None:
        """
        Create a new MSH file geometry import.

        Parameters:
            filepath: Path to a local MSH file. The file will be uploaded automatically.
        """
        super().__init__(filepath=filepath, name=None, cleanup=False, enabled=None)

    @classmethod
    def _get_rawapi_type(cls) -> rawapi.CadImportType:
        return rawapi.CadImportType.MSH

    def _get_supported_file_suffixes(self) -> list[str]:
        return [".msh"]

    @property
    @prevent_deleted
    def type(self) -> CadGeometryType:
        """Get the type of the geometry element."""
        return CadGeometryType.MSH_FILE

    @classmethod
    def _from_rawapi(
        cls, rawapi_element: rawapi.GeometryElement, project_id: str | None = None
    ) -> Self:
        cad_element = rawapi_element.cad_elem
        if cad_element is None:
            raise ValueError("CAD geometry element is not set")
        if cad_element.cad_file is None:
            raise ValueError("CAD file definition is not set")
        if cad_element.cad_file.type != cls._get_rawapi_type():
            raise ValueError(f"CAD file type is not {cls._get_rawapi_type()}")

        cad_file = cad_element.cad_file
        filepath = cad_file.filename
        if filepath is None:
            filepath = cad_element.name
        if filepath is None:
            raise ValueError("File name must be set")

        cad_object = cls(filepath=filepath)
        cls._initialize_from_rawapi(cad_object, rawapi_element, cad_element, project_id)
        return cad_object

    def __str__(self) -> str:
        return f"CadMshFile(filepath={self._filepath})"


class CadNasFile(CadFileImport):
    """
    CadNasFile represents a NASTRAN NAS file geometry import.
    Only one NAS file can exist in a project and it cannot coexist with other geometry elements.
    """

    def __init__(self, filepath: str) -> None:
        """
        Create a new NAS file geometry import.

        Parameters:
            filepath: Path to a local NAS file. The file will be uploaded automatically.
        """
        super().__init__(filepath=filepath, name=None, cleanup=False, enabled=None)

    @classmethod
    def _get_rawapi_type(cls) -> rawapi.CadImportType:
        return rawapi.CadImportType.NAS

    def _get_supported_file_suffixes(self) -> list[str]:
        return [".nas", ".bdf"]

    @property
    @prevent_deleted
    def type(self) -> CadGeometryType:
        """Get the type of the geometry element."""
        return CadGeometryType.NAS_FILE

    @classmethod
    def _from_rawapi(
        cls, rawapi_element: rawapi.GeometryElement, project_id: str | None = None
    ) -> Self:
        cad_element = rawapi_element.cad_elem
        if cad_element is None:
            raise ValueError("CAD geometry element is not set")
        if cad_element.cad_file is None:
            raise ValueError("CAD file definition is not set")
        if cad_element.cad_file.type != cls._get_rawapi_type():
            raise ValueError(f"CAD file type is not {cls._get_rawapi_type()}")

        cad_file = cad_element.cad_file
        filepath = cad_file.filename
        if filepath is None:
            filepath = cad_element.name
        if filepath is None:
            raise ValueError("File name must be set")

        cad_object = cls(filepath=filepath)
        cls._initialize_from_rawapi(cad_object, rawapi_element, cad_element, project_id)
        return cad_object

    def __str__(self) -> str:
        return f"CadNasFile(filepath={self._filepath})"


class CadGdsExtrudeParameters:
    """
    Parameters controlling the GDS boundary curve processing pipeline: layer unification,
    merge tolerance, feature detection thresholds, circle recognition, and spline fitting.
    """

    def __init__(
        self,
        unify_layer_discretizations: CadGdsUnifyLayerDiscretizations | None = None,
        fuzzy_value: float | int | str | None = None,
        feature_angle_threshold: float | int | str | None = None,
        length_ratio_threshold: float | int | str | None = None,
        spline_method: CadSplineMethod | None = None,
        spline_tolerance: float | int | str | None = None,
        circle_max_arc_angle_per_segment: float | int | str | None = None,
        circle_fit_tolerance_fraction: float | int | str | None = None,
        iterative_max_iterations: int | str | None = None,
    ) -> None:
        """
        Create GDS extrude parameters.

        Parameters:
            unify_layer_discretizations: Controls whether boundary curve discretization
                is unified across layers and when that unification happens relative to
                curve smoothing, spline creation, and circle creation. Unification ensures
                that identical shapes on different layers share the same vertex layout,
                improving robustness in meshing and geometry operations.
                Options: OFF, BEFORE, AFTER, BOTH.
            fuzzy_value: Merge tolerance used to merge vertices and edges that are nearly
                touching, eliminate small gaps or overlaps, and determine whether geometry
                is inside, outside, or on a boundary. Can be a number, a string expression.
            feature_angle_threshold: Angle between consecutive polyline segments that
                forces a break in circle or spline creation. Can be a number
                (degrees), a string expression.
            length_ratio_threshold: Length ratio between consecutive polyline segments
                that enforces a break in circle or spline creation.
            spline_method: Defines how splines are generated from polylines.
                POLYLINE preserves the original polyline geometry; curvature information
                is not available but the mesher has more freedom to adjust mesh density.
                ITERATIVE approximates the curve using a 3rd-order Bezier spline to the
                accuracy set by spline_tolerance, enabling curvature-based mesh refinement.
            spline_tolerance: Target accuracy for the iterative spline approximation.
                Can be a number, a string expression.
                Only used when spline_method is ITERATIVE.
            circle_max_arc_angle_per_segment: Maximum arc angle allowed per polyline
                segment when detecting circular arcs. Curves with fewer sample points
                than implied by this angle are not recognized as circular and will be
                fitted as splines instead. Can be a number (degrees), a string expression.
            circle_fit_tolerance_fraction: Controls how closely a fitted circle must match
                the original polyline. After fitting, the circle is accepted only if every
                polyline point lies within radius / circle_fit_tolerance_fraction of the
                arc; otherwise a spline is used instead.
            iterative_max_iterations: Maximum number of iterations for the iterative
                spline fitting method. Only used when spline_method is ITERATIVE.
        """
        self.unify_layer_discretizations = unify_layer_discretizations
        self.fuzzy_value = fuzzy_value
        self.feature_angle_threshold = feature_angle_threshold
        self.length_ratio_threshold = length_ratio_threshold
        self.spline_method = spline_method
        self.spline_tolerance = spline_tolerance
        self.circle_max_arc_angle_per_segment = circle_max_arc_angle_per_segment
        self.circle_fit_tolerance_fraction = circle_fit_tolerance_fraction
        self.iterative_max_iterations = iterative_max_iterations

    @staticmethod
    def _coerce_unify_layer_discretizations(
        value: CadGdsUnifyLayerDiscretizations | None,
    ) -> CadGdsUnifyLayerDiscretizations | None:
        if value is None:
            return None
        if isinstance(value, CadGdsUnifyLayerDiscretizations):
            return value
        raise ValueError("Invalid unify layer discretizations value")

    @staticmethod
    def _coerce_spline_method(
        value: CadSplineMethod | None,
    ) -> CadSplineMethod | None:
        if value is None:
            return None
        if isinstance(value, CadSplineMethod):
            return value
        raise ValueError("Invalid spline method value")

    @staticmethod
    def _create_angle_value(
        value: float | str | tuple[float | str, str],
    ) -> rawapi.CadAngle:
        if isinstance(value, tuple):
            val, unit = value
            return rawapi.CadAngle(
                value=create_scalar(val),
                unit=create_angular_unit(unit),
            )
        return create_angle(value)

    @staticmethod
    def _create_positive_integer(
        value: int | str | None,
    ) -> rawapi.CadPositiveInteger | None:
        if value is None:
            return None
        if isinstance(value, int):
            return rawapi.CadPositiveInteger(expression=str(value))
        if isinstance(value, str):
            return rawapi.CadPositiveInteger(expression=value)
        raise ValueError("Invalid positive integer value")

    @staticmethod
    def _from_positive_integer(
        value: rawapi.CadPositiveInteger | None,
    ) -> int | str | None:
        if value is None:
            return None
        if value.value is not None:
            return value.value
        if value.expression is not None:
            return value.expression
        return None

    def _to_rawapi(
        self, unit: rawapi.CadDistanceUnit
    ) -> rawapi.CadGdsExtrudeParameters:
        return rawapi.CadGdsExtrudeParameters(
            unifyLayerDiscretizations=self._coerce_unify_layer_discretizations(
                self.unify_layer_discretizations
            ),
            fuzzyValue=(
                create_distance(self.fuzzy_value, unit)
                if self.fuzzy_value is not None
                else None
            ),
            featureAngleThreshold=(
                self._create_angle_value(self.feature_angle_threshold)
                if self.feature_angle_threshold is not None
                else None
            ),
            lengthRatioThreshold=(
                create_scalar(self.length_ratio_threshold)
                if self.length_ratio_threshold is not None
                else None
            ),
            splineMethod=self._coerce_spline_method(self.spline_method),
            splineTolerance=(
                create_distance(self.spline_tolerance, unit)
                if self.spline_tolerance is not None
                else None
            ),
            circleMaxArcAnglePerSegment=(
                self._create_angle_value(self.circle_max_arc_angle_per_segment)
                if self.circle_max_arc_angle_per_segment is not None
                else None
            ),
            circleFitToleranceFraction=(
                create_scalar(self.circle_fit_tolerance_fraction)
                if self.circle_fit_tolerance_fraction is not None
                else None
            ),
            iterativeMaxIterations=self._create_positive_integer(
                self.iterative_max_iterations
            ),
        )

    @classmethod
    def _from_rawapi(
        cls,
        rawapi_params: rawapi.CadGdsExtrudeParameters | None,
    ) -> Self | None:
        if rawapi_params is None:
            return None
        return cls(
            unify_layer_discretizations=rawapi_params.unify_layer_discretizations,
            fuzzy_value=(
                from_distance(rawapi_params.fuzzy_value)
                if rawapi_params.fuzzy_value is not None
                else None
            ),
            feature_angle_threshold=(
                from_angle(rawapi_params.feature_angle_threshold)
                if rawapi_params.feature_angle_threshold is not None
                else None
            ),
            length_ratio_threshold=(
                from_scalar(rawapi_params.length_ratio_threshold)
                if rawapi_params.length_ratio_threshold is not None
                else None
            ),
            spline_method=rawapi_params.spline_method,
            spline_tolerance=(
                from_distance(rawapi_params.spline_tolerance)
                if rawapi_params.spline_tolerance is not None
                else None
            ),
            circle_max_arc_angle_per_segment=(
                from_angle(rawapi_params.circle_max_arc_angle_per_segment)
                if rawapi_params.circle_max_arc_angle_per_segment is not None
                else None
            ),
            circle_fit_tolerance_fraction=(
                from_scalar(rawapi_params.circle_fit_tolerance_fraction)
                if rawapi_params.circle_fit_tolerance_fraction is not None
                else None
            ),
            iterative_max_iterations=cls._from_positive_integer(
                rawapi_params.iterative_max_iterations
            ),
        )


_GDS_CSV_COLUMNS = [
    "LayerID",
    "LayerType",
    "Thickness",
    "AbsoluteZ",
    "PreviousLayerIndex",
    "Name",
]

_GDS_CSV_FIELD_ALIASES: dict[str, list[tuple[str, bool]]] = {
    "LayerID": [
        ("layerid", False),
        ("layernumber", False),
        ("id", False),
        ("layer", True),
    ],
    "LayerType": [
        ("layertype", False),
        ("type", True),
    ],
    "Thickness": [
        ("layerthickness", False),
        ("thickness", False),
    ],
    "AbsoluteZ": [
        ("absolutez", False),
        ("startingz", False),
        ("startz", False),
        ("z0", False),
        ("z", True),
    ],
    "PreviousLayerIndex": [
        ("previouslayerindex", False),
        ("prevlayerindex", False),
        ("prevlayer", False),
        ("previouslayer", False),
    ],
    "Name": [
        ("layername", False),
        ("name", False),
    ],
}


def _normalize_header(header: str) -> str:
    return re.sub(r"[^a-z0-9]", "", header.lower())


def _resolve_columns(
    raw_headers: list[str],
) -> dict[str, int | None]:
    """Map each GDS CSV field to its column index using alias matching."""
    normalized = [_normalize_header(h) for h in raw_headers]
    result: dict[str, int | None] = {field: None for field in _GDS_CSV_COLUMNS}

    for field, aliases in _GDS_CSV_FIELD_ALIASES.items():
        for alias, exact_only in aliases:
            for i, norm in enumerate(normalized):
                if norm == alias:
                    result[field] = i
                    break
            if result[field] is not None:
                break

        if result[field] is None:
            for alias, exact_only in aliases:
                if exact_only:
                    continue
                for i, norm in enumerate(normalized):
                    if alias in norm:
                        result[field] = i
                        break
                if result[field] is not None:
                    break

    return result


class CadGdsLayer:

    @staticmethod
    def to_csv_file(
        layers: list["CadGdsLayer"],
        filepath: str | pathlib.Path,
        delimiter: str = ",",
        overwrite: bool = True,
    ) -> None:
        """Write GDS layer definitions to a CSV file.

        Produces the same CSV format used by the GUI for importing/exporting
        GDS2 layer mappings.

        Columns: LayerID, LayerType, Thickness, AbsoluteZ,
        PreviousLayerIndex, Name

        Parameters:
            layers: List of CadGdsLayer instances to write.
            filepath: Output file path.
            delimiter: Column delimiter, ',' (default) or ';'.
            overwrite: If False, raise FileExistsError when the destination
                file already exists. If True (default), replace an existing
                file.

        Raises:
            FileExistsError: If the file already exists and overwrite is
                False.
        """
        path = pathlib.Path(filepath)
        if not overwrite and path.exists():
            raise FileExistsError(
                f"File already exists: {path}. "
                "Pass overwrite=True to replace it, or choose a different path."
            )

        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f, delimiter=delimiter)
            writer.writerow(_GDS_CSV_COLUMNS)
            for layer in layers:
                writer.writerow(
                    [
                        layer.layer,
                        layer.type,
                        layer.thickness if layer.thickness is not None else "",
                        layer.absolute_z0 if layer.absolute_z0 is not None else "",
                        (
                            layer.previous_layer_index
                            if layer.previous_layer_index is not None
                            else ""
                        ),
                        layer.name if layer.name is not None else "",
                    ]
                )

    @classmethod
    def from_csv_file(cls, filepath: str | pathlib.Path) -> list[Self]:
        """Read GDS layer definitions from a CSV file.

        Supports the same CSV format used by the GUI for importing/exporting
        GDS2 layer mappings. Delimiters (comma, semicolon, tab) are
        auto-detected. Rows with missing required fields are skipped
        with a warning.

        Expected columns: LayerID, LayerType, Thickness, AbsoluteZ,
        PreviousLayerIndex, Name

        Parameters:
            filepath: Path to the CSV file.

        Returns:
            List of CadGdsLayer instances, one per valid row.

        Raises:
            FileNotFoundError: If the file does not exist.
        """
        path = pathlib.Path(filepath)
        if not path.is_file():
            raise FileNotFoundError(f"File not found: {filepath}")

        text = path.read_text(encoding="utf-8")

        try:
            dialect = csv.Sniffer().sniff(text[:4096], delimiters=",;\t")
        except csv.Error:
            dialect = csv.excel  # type: ignore[assignment]

        reader = csv.reader(io.StringIO(text), dialect)
        raw_headers = next(reader, None)
        if raw_headers is None:
            return []

        col_map = _resolve_columns(raw_headers)

        layer_id_col = col_map["LayerID"]
        layer_type_col = col_map["LayerType"]
        thickness_col = col_map["Thickness"]
        abs_z_col = col_map["AbsoluteZ"]
        prev_idx_col = col_map["PreviousLayerIndex"]
        name_col = col_map["Name"]

        layers: list[Self] = []
        for row_num, row in enumerate(reader, start=2):

            def _cell(col: int | None) -> str:
                if col is None or col >= len(row):
                    return ""
                return row[col].strip()

            layer_id_str = _cell(layer_id_col)
            layer_type_str = _cell(layer_type_col)
            thickness_str = _cell(thickness_col)
            abs_z_str = _cell(abs_z_col)
            prev_idx_str = _cell(prev_idx_col)
            name_str = _cell(name_col)

            if not thickness_str:
                warnings.warn(
                    f"Row {row_num}: skipped — missing Thickness",
                    stacklevel=2,
                )
                continue

            if not abs_z_str and not prev_idx_str:
                warnings.warn(
                    f"Row {row_num}: skipped — missing both AbsoluteZ "
                    "and PreviousLayerIndex",
                    stacklevel=2,
                )
                continue

            try:
                layer_id = int(layer_id_str)
            except (ValueError, TypeError):
                warnings.warn(
                    f"Row {row_num}: skipped — LayerID is not an integer: "
                    f"{layer_id_str!r}",
                    stacklevel=2,
                )
                continue

            try:
                layer_type = int(layer_type_str)
            except (ValueError, TypeError):
                warnings.warn(
                    f"Row {row_num}: skipped — LayerType is not an integer: "
                    f"{layer_type_str!r}",
                    stacklevel=2,
                )
                continue

            absolute_z0: str | None = abs_z_str if abs_z_str else None

            previous_layer_index: int | None = None
            if prev_idx_str:
                try:
                    previous_layer_index = int(prev_idx_str)
                except (ValueError, TypeError):
                    warnings.warn(
                        f"Row {row_num}: skipped — PreviousLayerIndex is not "
                        f"an integer: {prev_idx_str!r}",
                        stacklevel=2,
                    )
                    continue

            if absolute_z0 is not None and previous_layer_index is not None:
                absolute_z0 = None

            layers.append(
                cls(
                    layer=layer_id,
                    type=layer_type,
                    absolute_z0=absolute_z0,
                    thickness=thickness_str,
                    previous_layer_index=previous_layer_index,
                    name=name_str if name_str else None,
                )
            )

        return layers

    def __init__(
        self,
        layer: int | None,
        type: int | None,
        absolute_z0: str | int | float | None,
        thickness: str | int | float,
        previous_layer_index: int | None = None,
        name: str | None = None,
    ) -> None:
        """GDS layer definition for importing a layer from a GDS2 file.

        Parameters:
        layer: Layer number from the GDS2 file. Together with type, forms
            the layer/datatype identifier.
        type: Datatype number from the GDS2 file. Together with layer, forms
            the layer/datatype identifier.
        absolute_z0: Absolute z0 of the layer.
        thickness: Thickness of the layer.
        previous_layer_index: Optional index of the previous layer in the layers list.
            The layer will be stacked on top of the previous layer.
            If previous_layer_index is set then absolute_z0 must be None.
        name: Optional name for the layer selection.
        """

        if layer is None:
            raise ValueError("Layer must be set")
        if type is None:
            raise ValueError("Type must be set")

        if absolute_z0 is not None and previous_layer_index is not None:
            raise ValueError(
                "Absolute z0 and previous layer index cannot be set at the same time"
            )
        if absolute_z0 is None and previous_layer_index is None:
            raise ValueError("Absolute z0 or previous layer index must be set")
        self.absolute_z0 = str(absolute_z0) if absolute_z0 is not None else None
        self.thickness = str(thickness) if thickness is not None else None
        self.previous_layer_index = previous_layer_index
        self.name = name
        self.layer = layer
        self.type = type

    def _to_rawapi(self, unit: rawapi.CadDistanceUnit) -> rawapi.CadGdsLayer:
        if self.absolute_z0 is None and self.previous_layer_index is None:
            raise ValueError("Absolute z0 or previous layer index must be set")
        if self.thickness is None:
            raise ValueError("Thickness is not set")
        return rawapi.CadGdsLayer(
            layer=self.layer,
            type=self.type,
            absoluteZ0=(
                create_distance(self.absolute_z0, unit)
                if self.absolute_z0 is not None
                else None
            ),
            thickness=create_distance(self.thickness, unit),
            previousLayerIndex=self.previous_layer_index,
            name=self.name,
        )

    @classmethod
    def _from_rawapi(
        cls,
        rawapi_layer: rawapi.CadGdsLayer,
    ) -> Self:
        return cls(
            layer=rawapi_layer.layer,
            type=rawapi_layer.type,
            absolute_z0=(
                str(from_distance(rawapi_layer.absolute_z0))
                if rawapi_layer.absolute_z0 is not None
                else None
            ),
            thickness=str(from_distance(rawapi_layer.thickness)),
            previous_layer_index=rawapi_layer.previous_layer_index,
            name=rawapi_layer.name,
        )


class CadGds2File(CadFileImport):
    """
    CadGds2File represents a GDS2 file geometry import.
    """

    def __init__(
        self,
        filepath: str,
        layers: List[CadGdsLayer],
        name: str | None = None,
        cleanup: bool = False,
        enabled: str | bool | None = None,
        extrude_parameters: CadGdsExtrudeParameters | None = None,
        unit: rawapi.CadDistanceUnit = rawapi.CadDistanceUnit.MICROMETER,
    ) -> None:
        """
        Create a new GDS2 file geometry import.

        Parameters:
            filepath: Path to a local GDS2 file. The file will be uploaded automatically.
            layers: List of CadGdsLayers.
            name: Optional name for the geometry element
            cleanup: Whether to clean up the imported file.
                Currently not supported yet.
            enabled: Optional enabled state of the geometry element.
                Can be a boolean or a string expression.
                By default, the geometry element is enabled.
            extrude_parameters: Optional GDS2 extrusion parameters.
            unit: Default distance unit for distance values in layers and extrude_parameters.
                Defaults to CadDistanceUnit.MICROMETER.
        """
        super().__init__(filepath, name, cleanup, enabled)
        self._layers: List[CadGdsLayer] = []
        self._extrude_parameters = extrude_parameters
        self._unit = unit
        self._layers = layers

    @classmethod
    def _get_rawapi_type(cls) -> rawapi.CadImportType:
        return rawapi.CadImportType.GDS2

    def _get_supported_file_suffixes(self) -> list[str]:
        return [".gds2", ".gds"]

    @property
    @prevent_deleted
    def type(self) -> CadGeometryType:
        """Get the type of the geometry element."""
        return CadGeometryType.GDS2_FILE

    @property
    @prevent_deleted
    def layers(self) -> List[CadGdsLayer]:
        """Get the GDS2 import configuration."""
        return self._layers

    @property
    @prevent_deleted
    def extrude_parameters(self) -> CadGdsExtrudeParameters | None:
        """Get the GDS2 extrude parameters."""
        return self._extrude_parameters

    @property
    @prevent_deleted
    def unit(self) -> rawapi.CadDistanceUnit:
        """Get the default distance unit for all GDS numeric values."""
        return self._unit

    @classmethod
    def _from_rawapi(
        cls, rawapi_element: rawapi.GeometryElement, project_id: str | None = None
    ) -> Self:
        cad_element = rawapi_element.cad_elem
        if cad_element is None:
            raise ValueError("CAD geometry element is not set")
        if cad_element.cad_file is None:
            raise ValueError("CAD file definition is not set")
        if cad_element.cad_file.type != cls._get_rawapi_type():
            raise ValueError(f"CAD file type is not {cls._get_rawapi_type()}")

        cad_file = cad_element.cad_file
        if cad_element.name is None:
            raise ValueError("File name must be set")

        cleanup = False
        if cad_file.parameters is not None:
            cleanup = cad_file.parameters.cleanup

        filepath = cad_file.filename
        if filepath is None:
            filepath = cad_element.name

        # Extract GDS2 config from cad_file.parameters
        layers = []
        extrude_parameters = None
        file_unit = rawapi.CadDistanceUnit.MICROMETER
        if (
            cad_file.parameters is not None
            and cad_file.parameters.gds_import_config is not None
        ):
            gds_config = cad_file.parameters.gds_import_config

            if gds_config.z_offset is not None and gds_config.z_offset.unit is not None:
                file_unit = gds_config.z_offset.unit

            for cad_layer in gds_config.layers:
                layers.append(CadGdsLayer._from_rawapi(cad_layer))
            if gds_config.extrude_parameters is not None:
                extrude_parameters = CadGdsExtrudeParameters._from_rawapi(
                    gds_config.extrude_parameters
                )

        if len(layers) == 0:
            raise ValueError("At least one layer is required")

        cad_object = cls(
            filepath=filepath,
            layers=layers,
            cleanup=cleanup,
            extrude_parameters=extrude_parameters,
            unit=file_unit,
        )
        cls._initialize_from_rawapi(cad_object, rawapi_element, cad_element, project_id)
        return cad_object

    @prevent_deleted
    def _to_rawapi_cad_element(self) -> rawapi.CadGeometryElement:
        if self._name is None:
            raise ValueError("Name is not set")
        if self.file_size is None:
            raise ValueError("File size is not set")

        cad_gds_layers = []

        for layer in self._layers:
            cad_gds_layer = layer._to_rawapi(unit=self._unit)
            cad_gds_layers.append(cad_gds_layer)

        cad_gds_config = rawapi.CadGdsImportConfig(
            layers=cad_gds_layers,
            zOffset=create_distance(0, self._unit.value),
            extrudeParameters=(
                self._extrude_parameters._to_rawapi(unit=self._unit)
                if self._extrude_parameters is not None
                else None
            ),
        )

        import_config = rawapi.CadImportConfig(
            cleanup=self._cleanup,
            gdsImportConfig=cad_gds_config,
        )

        cad_file_def = rawapi.CadFileDefinition(
            type=self._get_rawapi_type(),
            filename=self._name,
            parameters=import_config,
            size=self.file_size,
        )

        cad_element = rawapi.CadGeometryElement(
            cadFile=cad_file_def,
            name=self._name,
        )

        return cad_element
