# Copyright 2026 Quanscient Oy
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations
import json
import os
import sys
import array
import sqlite3
from enum import Enum
from typing import Any, Callable, Iterator, Protocol, TypeVar
import zstandard as zstd
import urllib3

from allsolve import intcomp, varint
import allsolve_rawapi as rawapi
from allsolve.api import get_api, get_auth

_NO_STEP = "nostep"


class _Row:
    rowid: int

    def __init__(self, row: sqlite3.Row):
        self.rowid = row["rowid"]


class InfoRow(_Row):
    __slots__ = (
        "rowid",
        "version",
        "parent_job_id",
    )

    version: int
    parent_job_id: str | None
    """
    The root job id in case of sweep simulations.
    """

    def __init__(self, row: sqlite3.Row):
        super().__init__(row)
        self.version = row["version"]
        self.parent_job_id = row["parent_job_id"]


class _SimulationRow(_Row):
    __slots__ = (
        "rowid",
        "analysis_type",
        "job_id",
        "job_index",
    )

    analysis_type: rawapi.AnalysisType
    job_id: str
    job_index: int

    def __init__(self, row: sqlite3.Row):
        super().__init__(row)
        self.analysis_type = rawapi.AnalysisType(row["analysis_type"])
        self.job_id = row["job_id"]
        self.job_index = row["job_index"]


class _SimulationOverrideValueRow(_Row):
    __slots__ = (
        "rowid",
        "simulation_id",
        "name",
        "value",
    )

    simulation_id: int
    name: str
    value: bytes

    def __init__(self, row: sqlite3.Row):
        super().__init__(row)
        self.simulation_id = row["simulation_id"]
        self.name = row["name"]
        self.value = row["value"]


class SimulationOutput:
    __slots__ = (
        "rowid",
        "analysis_type",
        "job_id",
        "job_index",
        "overrides",
    )

    rowid: int
    analysis_type: rawapi.AnalysisType

    job_id: str
    """
    Sweep step job id or the main job id in case of non-sweep simulations.
    """

    job_index: int
    """
    Sweep step index.
    """

    overrides: dict[str, list[float]]
    """
    Sweep step overrides by variable name.
    """

    def __init__(
        self,
        sim: _SimulationRow,
        overrides_by_sim_id: dict[int, list[_SimulationOverrideValueRow]],
    ):
        self.rowid = sim.rowid
        self.analysis_type = sim.analysis_type
        self.job_id = sim.job_id
        self.job_index = sim.job_index
        self.overrides = {}
        overrides = overrides_by_sim_id.get(self.rowid, [])
        for o in overrides:
            self.overrides[o.name] = _bytes_to_floats(o.value).tolist()


class SimulationStepRow(_Row):
    __slots__ = (
        "rowid",
        "raw_step",
        "step",
    )

    """
    Represents a simulation step:
        - Time step in transient simulations
        - Eigenmode index in eigenvalue simulations
    """

    raw_step: str
    """
    The raw string representation of the step. This is needed to preserve
    the format used in the field output files.
    """

    step: float | None
    """
    The step as a float. None if no step was specified when the value
    was created in the simulation.
    """

    def __init__(self, row: sqlite3.Row):
        super().__init__(row)
        self.raw_step = row["step"]
        self.step = None
        if self.raw_step != _NO_STEP:
            self.step = float(self.raw_step)


class FieldOutputType(Enum):
    """
    Category of a field stored in the simulation output database.

    Each solved simulation writes fields into an SQLite database.
    This enum distinguishes the different kinds of stored data.
    """

    FIELD = 0
    """Primary solved field (e.g. displacement, temperature)."""

    FIELD_STATE = 1
    """Saved state of a field used for restarting or chaining simulations."""

    TRANSIENT_STATE = 2
    """Time-integration state for transient solvers."""

    HPHI_STATE = 3
    """State specific to the H-phi (magnetic scalar potential) formulation."""

    MESH = 4
    """Mesh data associated with the output."""


class FieldOutputDefinitionRow(_Row):
    __slots__ = (
        "rowid",
        "type",
        "name",
        "specifier",
        "file_name_format",
        "file_name_prefix",
        "ranks",
    )

    type: FieldOutputType
    """
    The type of the field.
    """

    name: str
    """
    The user specified name for the field output.
    """

    specifier: str | None
    """
    An optional specifier added by the user or by the code generator. For example,
    some field outputs produce both real and imaginary parts, even though the user
    has just specified a single output. In this case the `name` of both fields will
    be the user specified name, but the `specifier` will be `"real"` or `"imaginary"`.

    Users can also give any specifier they want in modified or custom scripts.
    """

    file_name_format: str
    """
    A format string to produce the file names of field outputs. The format string
    will have placeholders `{step}` and `{rank}`. To get the file name, use the raw
    string step SimulationStepRow._step to replace `{step}` and the rank integer
    to replace `{rank}`.
    """

    file_name_prefix: str
    """
    The prefix part of `file_name_format`. Only contains the name and optionally
    the specifier in a filename friendly format.
    """

    ranks: list[int]
    """
    The ranks that produced this field output.
    """

    def __init__(self, row: sqlite3.Row):
        super().__init__(row)
        self.type = FieldOutputType(row["type"])
        self.name = row["name"]
        self.specifier = row["specifier"]
        self.file_name_format = row["file_name_format"]
        self.file_name_prefix = row["file_name_prefix"]
        self.ranks = varint.decode(row["ranks"])


class ValueOutputDefinitionRow(_Row):
    __slots__ = (
        "rowid",
        "name",
        "specifier",
    )

    name: str
    """
    The user specified name for the value output.
    """

    specifier: str | None
    """
    An optional specifier added by the user or by the code generator. For example,
    some value outputs produce both real and imaginary parts, even though the user
    has just specified a single output. In this case the `name` of both values will
    be the user specified name, but the `specifier` will be `"real"` or `"imaginary"`.
    """

    def __init__(self, row: sqlite3.Row):
        super().__init__(row)
        self.name = row["name"]
        self.specifier = row["specifier"]


class ValueOutput:
    __slots__ = (
        "simulation",
        "step",
        "definition",
        "value_db_id",
        "value_blob_id",
        "value_offset",
        "value_length",
        "data",
    )

    simulation: SimulationOutput
    step: SimulationStepRow
    definition: ValueOutputDefinitionRow
    value_db_id: int
    value_blob_id: int
    value_offset: int
    value_length: int
    data: array.array[float] | None

    def __init__(
        self,
        simulation: SimulationOutput,
        step: SimulationStepRow,
        definition: ValueOutputDefinitionRow,
        value_db_id: int,
        value_blob_id: int,
        value_offset: int,
        value_length: int,
        data: array.array[float] | None,
    ):
        self.simulation = simulation
        self.step = step
        self.definition = definition
        self.value_db_id = value_db_id
        self.value_blob_id = value_blob_id
        self.value_offset = value_offset
        self.value_length = value_length
        self.data = data


class FieldOutput:
    __slots__ = (
        "simulation",
        "step",
        "definition",
        "uploaded",
    )

    simulation: SimulationOutput
    step: SimulationStepRow
    definition: FieldOutputDefinitionRow
    uploaded: bool

    def __init__(
        self,
        simulation: SimulationOutput,
        step: SimulationStepRow,
        definition: FieldOutputDefinitionRow,
        uploaded: bool,
    ):
        self.simulation = simulation
        self.step = step
        self.definition = definition
        self.uploaded = uploaded

    def get_file_names(self) -> list[str]:
        return [
            self.definition.file_name_format.replace(
                "{step}", self.step.raw_step
            ).replace("{rank}", str(rank))
            for rank in self.definition.ranks
        ]


class BlobDatabase:
    __slots__ = (
        "might_need_refresh",
        "data",
        "offsets",
    )

    might_need_refresh: bool
    data: array.array[float]
    """
    All the data of the blob database. To get the data of the blob with id `blob_id`,
    use `db.data[db.offsets[blob_id - 1] : db.offsets[blob_id]])]`.
    """
    offsets: array.array[int]

    def __init__(self, file_path: str):
        self.might_need_refresh = False

        db = sqlite3.connect(file_path)
        db.row_factory = sqlite3.Row

        # Read the whole blob database into `self.data`. Store the offset of each
        # blob in `self.offsets`.
        try:
            blobs = [
                _bytes_to_floats(row[0])
                for row in db.execute("SELECT blob FROM blob ORDER BY rowid")
            ]

            self.offsets = array.array("l", [0] * (len(blobs) + 1))
            total_size = 0
            for i, blob in enumerate(blobs):
                self.offsets[i] = total_size
                total_size += len(blob)
            self.offsets[len(blobs)] = total_size

            self.data = array.array("d", [0.0] * total_size)
            for i, blob in enumerate(blobs):
                self.data[self.offsets[i] : self.offsets[i] + len(blob)] = blob
        finally:
            db.close()


class DatabaseDownloadResponse(Protocol):
    status: int
    headers: urllib3.HTTPHeaderDict

    def stream(self) -> Iterator[bytes]: ...
    def json(self) -> Any: ...
    def release_conn(self) -> None: ...


class SimulationOutputDatabase:
    __slots__ = (
        "_project_id",
        "_simulation_id",
        "_working_dir",
        "_etags",
        "_blob_dbs",
        "_info",
        "_simulations_by_row_id",
        "_steps_by_row_id",
        "_field_defs_by_row_id",
        "_value_defs_by_row_id",
        "_fields",
        "_values",
        "_request_database",
        "_zstd_decompressor",
    )

    _project_id: str
    _simulation_id: str
    _working_dir: str
    _etags: dict[str, str]
    _blob_dbs: dict[int, BlobDatabase]
    _info: InfoRow | None
    _simulations_by_row_id: dict[int, SimulationOutput]
    _steps_by_row_id: dict[int, SimulationStepRow]
    _field_defs_by_row_id: dict[int, FieldOutputDefinitionRow]
    _value_defs_by_row_id: dict[int, ValueOutputDefinitionRow]
    _fields: list[FieldOutput]
    _values: list[ValueOutput]
    _request_database: Callable[
        ["SimulationOutputDatabase", int | None, str | None], DatabaseDownloadResponse
    ]
    _zstd_decompressor: zstd.ZstdDecompressor

    def __init__(
        self,
        project_id: str,
        simulation_id: str,
        working_dir: str,
    ):
        self._project_id = project_id
        self._simulation_id = simulation_id
        self._working_dir = working_dir
        self._etags = {}
        self._blob_dbs = {}
        self._info = None
        self._simulations_by_row_id = {}
        self._steps_by_row_id = {}
        self._field_defs_by_row_id = {}
        self._value_defs_by_row_id = {}
        self._fields = []
        self._values = []
        self._zstd_decompressor = zstd.ZstdDecompressor()
        self._request_database = _request_database
        if not os.path.exists(self._working_dir):
            os.makedirs(self._working_dir, exist_ok=True)
        self._read_metadata()
        self._init_database()
        self._init_blob_dbs()

    @property
    def project_id(self) -> str:
        return self._project_id

    @property
    def simulation_id(self) -> str:
        return self._simulation_id

    @property
    def working_dir(self) -> str:
        return self._working_dir

    @property
    def info(self) -> InfoRow | None:
        return self._info

    @property
    def simulations_by_row_id(self) -> dict[int, SimulationOutput]:
        return self._simulations_by_row_id

    @property
    def steps_by_row_id(self) -> dict[int, SimulationStepRow]:
        return self._steps_by_row_id

    @property
    def field_defs_by_row_id(self) -> dict[int, FieldOutputDefinitionRow]:
        return self._field_defs_by_row_id

    @property
    def value_defs_by_row_id(self) -> dict[int, ValueOutputDefinitionRow]:
        return self._value_defs_by_row_id

    @property
    def values(self) -> list[ValueOutput]:
        return self._values

    @property
    def fields(self) -> list[FieldOutput]:
        return self._fields

    def get_value_data(self, value: ValueOutput) -> array.array[float]:
        """
        Get data for a value output.
        """

        if value.value_db_id == 0 and value.data is not None:
            # If the value db id is 0, the data is stored in the value hash
            # and has already been hydrated to `value.data`.
            return value.data

        if value.value_db_id not in self._blob_dbs:
            self._download_database(value.value_db_id)
            db = BlobDatabase(self._get_file_path(value.value_db_id))
            self._blob_dbs[value.value_db_id] = db

        db = self._blob_dbs[value.value_db_id]
        if db.might_need_refresh:
            did_download = self._download_database(value.value_db_id)
            if did_download:
                db = BlobDatabase(self._get_file_path(value.value_db_id))
                self._blob_dbs[value.value_db_id] = db
            else:
                # The database is up to date.
                db.might_need_refresh = False

        offset = db.offsets[value.value_blob_id - 1] + value.value_offset
        return db.data[offset : offset + value.value_length]

    def refresh(self):
        did_download = self._download_database()

        if did_download or self._info is None:
            for db in self._blob_dbs.values():
                db.might_need_refresh = True
            self._init_database()

    def _init_database(self):
        if not os.path.exists(self._get_file_path()):
            return

        db = self._connect_to_database()
        try:
            self._info = self._get_info(db)
            self._simulations_by_row_id = self._get_simulations(db)
            self._steps_by_row_id = self._get_steps(db)
            self._field_defs_by_row_id = self._get_field_defs(db)
            self._value_defs_by_row_id = self._get_value_defs(db)
            self._fields = self._get_fields(db)
            self._values = self._get_values(db)
        finally:
            db.close()

    def _init_blob_dbs(self):
        for blob_db_file_name in self._etags.keys():
            blob_db_id = self._get_blob_db_id_from_filename(blob_db_file_name)
            if blob_db_id is None:
                continue
            db_path = self._get_file_path(blob_db_id)
            if not os.path.exists(db_path):
                continue
            self._blob_dbs[blob_db_id] = BlobDatabase(db_path)

    def _get_metadata_file_path(self) -> str:
        return os.path.join(self._working_dir, "metadata.json")

    def _get_blob_db_id_from_filename(self, filename: str) -> int | None:
        if filename == "output.db":
            return None
        return int(filename.split("-blobs-")[1].split(".db")[0])

    def _read_metadata(self):
        if not os.path.exists(self._get_metadata_file_path()):
            return
        with open(self._get_metadata_file_path(), "r") as f:
            meta = json.load(f)
            self._etags = meta["etags"]

    def _write_metadata(self):
        with open(self._get_metadata_file_path(), "w") as f:
            json.dump({"etags": self._etags}, f)

    def _download_database(
        self,
        blob_db_id: int | None = None,
    ) -> bool:
        file_name = self._get_filename(blob_db_id)
        res = self._request_database(self, blob_db_id, self._etags.get(file_name))

        try:
            if res.status == 304:
                # Database is up to date
                return False
            if res.status != 200:
                body = res.json()
                raise rawapi.ApiException(status=res.status, body=body)

            etag = res.headers.get("ETag")
            if etag is None:
                raise rawapi.ApiException(status=200, reason="No ETag found")

            with open(self._get_file_path(blob_db_id), "wb") as f:
                for chunk in res.stream():
                    f.write(chunk)

            self._etags[file_name] = etag
            self._write_metadata()
        finally:
            res.release_conn()

        return True

    def _get_file_path(self, blob_db_id: int | None = None) -> str:
        return os.path.join(self._working_dir, self._get_filename(blob_db_id))

    def _get_filename(self, blob_db_id: int | None = None) -> str:
        if blob_db_id is None:
            return "output.db"
        return f"output-blobs-{blob_db_id}.db"

    def _connect_to_database(self) -> sqlite3.Connection:
        db = sqlite3.connect(self._get_file_path())
        db.row_factory = sqlite3.Row
        return db

    def _get_info(self, db: sqlite3.Connection) -> InfoRow | None:
        infos = _select(
            db, "SELECT rowid, version, parent_job_id FROM info", [], InfoRow
        )
        return next(iter(infos.values()), None)

    def _get_simulations(self, db: sqlite3.Connection) -> dict[int, SimulationOutput]:
        sims_by_id = _select(
            db,
            "SELECT rowid, * FROM simulation ORDER BY rowid",
            [],
            _SimulationRow,
        )

        overrides_by_id = _select(
            db,
            "SELECT rowid, * FROM simulation_override_value ORDER BY rowid",
            [],
            _SimulationOverrideValueRow,
        )

        overrides_by_sim_id: dict[int, list[_SimulationOverrideValueRow]] = {}
        for o in overrides_by_id.values():
            overrides_by_sim_id.setdefault(o.simulation_id, []).append(o)

        sim_outputs: dict[int, SimulationOutput] = {}
        for sim in sims_by_id.values():
            sim_outputs[sim.rowid] = SimulationOutput(sim, overrides_by_sim_id)

        return sim_outputs

    def _get_steps(self, db: sqlite3.Connection) -> dict[int, SimulationStepRow]:
        return _select(
            db,
            "SELECT rowid, * FROM simulation_step ORDER BY rowid",
            [],
            SimulationStepRow,
        )

    def _get_field_defs(
        self, db: sqlite3.Connection
    ) -> dict[int, FieldOutputDefinitionRow]:
        return _select(
            db,
            "SELECT rowid, * FROM field_output_definition ORDER BY rowid",
            [],
            FieldOutputDefinitionRow,
        )

    def _get_value_defs(
        self, db: sqlite3.Connection
    ) -> dict[int, ValueOutputDefinitionRow]:
        return _select(
            db,
            "SELECT rowid, * FROM value_output_definition ORDER BY rowid",
            [],
            ValueOutputDefinitionRow,
        )

    def _get_fields(self, db: sqlite3.Connection) -> list[FieldOutput]:
        assert self._info is not None
        version = self._info.version
        fields: list[FieldOutput] = []

        for row in db.execute("SELECT rowid, * FROM field_output ORDER BY rowid"):
            definition_id = row["definition_id"]
            simulation_id = row["simulation_id"]
            step_ids = (
                [row["step_id"]]
                if version == 1
                else intcomp.decode(row["step_ids"], self._zstd_decompressor)
            )
            uploaded = (
                [row["uploaded"] == 1]
                if version == 1
                else [
                    f == 1
                    for f in intcomp.decode(
                        row["uploaded_flags"], self._zstd_decompressor
                    )
                ]
            )
            for i, step_id in enumerate(step_ids):
                fields.append(
                    FieldOutput(
                        self._simulations_by_row_id[simulation_id],
                        self._steps_by_row_id[step_id],
                        self._field_defs_by_row_id[definition_id],
                        uploaded[i],
                    )
                )

        return fields

    def _get_values(self, db: sqlite3.Connection) -> list[ValueOutput]:
        assert self._info is not None
        version = self._info.version
        values: list[ValueOutput] = []

        for row in db.execute("SELECT rowid, * FROM value_output ORDER BY rowid"):
            definition_id = row["definition_id"]
            simulation_id = row["simulation_id"]
            value_db_id = row["value_db_id"]
            value_blob_id = row["value_blob_id"]
            value_hash = row["value_hash"]
            if len(value_hash) < 16:
                # Trailing zeros have been removed from the value hash. Add them back.
                value_hash = value_hash.ljust(16, b"\x00")
            step_ids = (
                [row["step_id"]]
                if version == 1
                else intcomp.decode(row["step_ids"], self._zstd_decompressor)
            )
            value_lengths = (
                [row["num_values"]]
                if version == 1
                else intcomp.decode(row["value_shapes"], self._zstd_decompressor)
            )
            value_hash_data: array.array[float] | None = None
            if value_db_id == 0:
                value_hash_data = _bytes_to_floats(value_hash)

            value_offset = 0
            for i, step_id in enumerate(step_ids):
                value_length = value_lengths[i]
                values.append(
                    ValueOutput(
                        self._simulations_by_row_id[simulation_id],
                        self._steps_by_row_id[step_id],
                        self._value_defs_by_row_id[definition_id],
                        value_db_id,
                        value_blob_id,
                        value_offset,
                        value_length,
                        # The data is stored in the value hash if the value db id is 0.
                        (
                            value_hash_data[value_offset : value_offset + value_length]
                            if value_hash_data is not None
                            else None
                        ),
                    )
                )
                value_offset += value_length

        return values


_RowT = TypeVar("_RowT", bound=_Row)


def _select(
    db: sqlite3.Connection | None,
    sql: str,
    parameters: list[Any],
    row_class: type[_RowT],
) -> dict[int, _RowT]:
    if db is None:
        raise ValueError("Database not connected")
    cur = db.execute(sql, parameters)
    rows: dict[int, _RowT] = {}
    for r in cur:
        row = row_class(r)
        rows[row.rowid] = row
    cur.close()
    return rows


def _bytes_to_floats(data: bytes) -> array.array[float]:
    floats = array.array("d")
    floats.frombytes(data)
    # The data is guaranteed to be little endian, but the machine running
    # this code might be big endian.
    if sys.byteorder != "little":
        floats.byteswap()
    return floats


def _request_database(
    db: SimulationOutputDatabase,
    blob_db_id: int | None = None,
    previous_etag: str | None = None,
) -> DatabaseDownloadResponse:
    with get_api() as api:
        return api.get_simulation_output_data_without_preload_content(
            authorization=get_auth(),
            project_id=db._project_id,
            simulation_id=db._simulation_id,
            blob_db_id=blob_db_id,
            if_none_match=previous_etag,
        )
