# Copyright 2026 Quanscient Oy
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations
import array
from enum import Enum
import math
import os
import shutil
from typing import TYPE_CHECKING, TextIO
from allsolve.api import get_cache_dir, is_setup
from allsolve.simulation.simulation_output_database import (
    _NO_STEP,
    FieldOutputDefinitionRow,
    FieldOutputType,
    SimulationOutput,
    SimulationOutputDatabase,
    SimulationStepRow,
    ValueOutput,
    ValueOutputDefinitionRow,
)
from io import StringIO

if TYPE_CHECKING:
    import pandas as pd

_DB_NOT_INITIALIZED_ERROR = "Database not initialized"


class CsvExportFormat(Enum):
    """
    The format of the CSV file.
    EXPLODED format outputs one row per value.
    Exploded format is slower with large datasets.
    NORMAL format outputs one row per step.
    When multiple values are present per step, the values are output as an array.
    Normal format is faster with large datasets.
    """

    EXPLODED = "exploded"
    NORMAL = "normal"


ValueId = tuple[str, str | None]
"""
Value identifier consists of the name and the specifier.
"""

ValueHeaderOrId = str | ValueId
"""
Value header or value id. Value header is the value name
followed by the specifier in parentheses. If the specifier
is None, the parentheses are not included.
"""


class SimulationOutputData:
    NO_STEP = _NO_STEP

    __slots__ = (
        "_project_id",
        "_simulation_id",
        "_cache_dir",
        "_database",
        "_simulations_sorted",
        "_simulations_by_overrides",
        "_steps_sorted",
        "_step_index_by_label",
        "_step_index_by_step",
        "_value_defs_sorted",
        "_value_defs_by_header",
        "_value_defs_by_id",
        "_values_by_sim_id_and_step_id_and_definition_id",
    )

    _project_id: str
    _simulation_id: str
    _cache_dir: str
    _database: SimulationOutputDatabase | None

    _simulations_sorted: list[SimulationOutput] | None
    _simulations_by_overrides: (
        dict[str, dict[float | list[float], SimulationOutput]] | None
    )

    _steps_sorted: list[SimulationStepRow] | None
    _step_index_by_label: dict[str, int] | None
    _step_index_by_step: dict[float | None, int] | None

    _value_defs_sorted: list[ValueOutputDefinitionRow] | None
    _value_defs_by_header: dict[str, ValueOutputDefinitionRow] | None
    _value_defs_by_id: dict[ValueId, ValueOutputDefinitionRow] | None
    _values_by_sim_id_and_step_id_and_definition_id: (
        dict[int, dict[int, dict[int, ValueOutput]]] | None
    )

    def __init__(
        self,
        project_id: str,
        simulation_id: str,
        cache_dir: str | None = None,
        db: SimulationOutputDatabase | None = None,
    ):
        self._project_id = project_id
        self._simulation_id = simulation_id
        self._clear_cache_props()

        if cache_dir is None:
            if not is_setup():
                raise ValueError("Allsolve is not setup")
            base_dir = get_cache_dir()
            if base_dir is None:
                raise ValueError("Cache directory not set")
            self._cache_dir = os.path.join(
                base_dir,
                project_id,
                simulation_id,
            )
        else:
            self._cache_dir = cache_dir

        if db is None and os.path.exists(self._cache_dir):
            self._database = SimulationOutputDatabase(
                self._project_id,
                self._simulation_id,
                self._cache_dir,
            )
        else:
            self._database = db

    def _clear_cache_props(self) -> None:
        self._simulations_sorted = None
        self._simulations_by_overrides = None

        self._steps_sorted = None
        self._step_index_by_label = None
        self._step_index_by_step = None

        self._value_defs_sorted = None
        self._value_defs_by_header = None
        self._value_defs_by_id = None
        self._values_by_sim_id_and_step_id_and_definition_id = None

    @property
    def project_id(self) -> str | None:
        return self._project_id

    @property
    def simulation_id(self) -> str | None:
        return self._simulation_id

    @property
    def _db(self) -> SimulationOutputDatabase:
        if self._database is None:
            raise ValueError(_DB_NOT_INITIALIZED_ERROR)
        return self._database

    def refresh(self) -> None:
        """
        Download the simulation output data.
        Data is stored in the cache directory.
        """
        self._create_cache_dir()
        self._clear_cache_props()
        if not self._database:
            self._database = SimulationOutputDatabase(
                self._project_id,
                self._simulation_id,
                self._cache_dir,
            )
        self._database.refresh()

    def clean_cache(self) -> None:
        """
        Clean the local output data cache directory for this simulation.
        To use output data again, you need to call refresh to download the data again.
        """
        self._clear_cache_props()
        if os.path.exists(self._cache_dir):
            shutil.rmtree(self._cache_dir)

    def to_dataframe(
        self,
        *,
        include_overrides: bool = True,
    ) -> pd.DataFrame:
        """
        Return all sweep steps as a tidy pandas DataFrame.

        Each row represents one array element at a particular sweep step and
        simulation step.  Columns are ``Sweep step``, ``Step``,
        ``Array index``, any sweep-variable overrides (when
        *include_overrides* is ``True``), and one column per value output.

        Scalar value outputs (array length 1) are broadcast to every array
        index within the same step, matching :meth:`to_csv` with
        ``CsvExportFormat.EXPLODED``.

        Requires ``pandas``. Install the pandas library, or install the SDK
        with DataFrame support: ``pip install allsolve[dataframe]``
        """
        self._check_pandas()

        if self._database is None:
            raise ValueError(_DB_NOT_INITIALIZED_ERROR)

        return self._build_tidy_dataframe(
            self._get_simulations_sorted(),
            include_overrides=include_overrides,
        )

    def sweep_step_to_dataframe(
        self,
        sweep_index: int,
        *,
        include_overrides: bool = True,
    ) -> pd.DataFrame:
        """
        Return a single sweep step as a tidy pandas DataFrame.

        The returned frame has the same column schema as :meth:`to_dataframe`
        but only contains rows for the requested *sweep_index*.

        Requires ``pandas``. Install the pandas library, or install the SDK
        with DataFrame support: ``pip install allsolve[dataframe]``

        Raises:
            ValueError: If ``sweep_index`` is out of range.
        """
        self._check_pandas()

        if self._database is None:
            raise ValueError(_DB_NOT_INITIALIZED_ERROR)

        sims_sorted = self._get_simulations_sorted()
        if sweep_index < -len(sims_sorted) or sweep_index >= len(sims_sorted):
            raise ValueError(f"Sweep index {sweep_index} out of range")

        if sweep_index < 0:
            sweep_index = len(sims_sorted) + sweep_index

        return self._build_tidy_dataframe(
            [sims_sorted[sweep_index]],
            include_overrides=include_overrides,
        )

    def to_dict(
        self,
        sweep_index: int = 0,
        include_overrides: bool = False,
    ) -> dict[str, dict[str, list[float]]]:
        """
        Returns the value output data of a single sweep step as a dictionary.

        Args:
            sweep_index: The sweep step index.
            include_overrides: If True, variable override values for the sweep step
                are included as additional entries in each step's dictionary.
        """
        if self._database is None:
            raise ValueError(_DB_NOT_INITIALIZED_ERROR)

        all_values: dict[str, dict[str, list[float]]] = {}

        sims_sorted = self._get_simulations_sorted()
        if sweep_index < -len(sims_sorted) or sweep_index >= len(sims_sorted):
            return {}
        simulation_id = sims_sorted[sweep_index].rowid

        steps_sorted = self._get_steps_sorted()
        for step in steps_sorted:
            all_values[step.raw_step] = (
                self._get_sweep_and_step_values_grouped_by_header(
                    simulation_id=simulation_id,
                    step_id=step.rowid,
                )
            )

        if include_overrides:
            overrides = sims_sorted[sweep_index].overrides
            for step_values in all_values.values():
                for name, values in overrides.items():
                    if name not in step_values:
                        step_values[name] = values

        return all_values

    def to_csv_file(
        self,
        filename: str,
        delimiter: str = ",",
        csv_format: CsvExportFormat = CsvExportFormat.EXPLODED,
        include_overrides: bool = False,
    ):
        """
        Write simulation output as CSV to ``filename``.

        The file must not already exist.

        Args:
            filename: Path of the CSV file to create.
            delimiter: Field delimiter for the CSV output.
            csv_format: Row layout; see ``CsvExportFormat``.
            include_overrides: If True, variable override values for each sweep step
                are included as additional columns.

        Raises:
            ValueError: If ``filename`` already exists.
        """
        if self._database is None:
            raise ValueError(_DB_NOT_INITIALIZED_ERROR)

        if os.path.exists(filename):
            raise ValueError(f"File {filename} already exists")

        with open(filename, "w") as f:
            self._to_csv_stream(
                output=f,
                delimiter=delimiter,
                csv_format=csv_format,
                include_overrides=include_overrides,
            )

    def to_csv(
        self,
        delimiter: str = ",",
        csv_format: CsvExportFormat = CsvExportFormat.EXPLODED,
        include_overrides: bool = False,
    ) -> str:
        """
        Return simulation output as a CSV string.

        Args:
            delimiter: Field delimiter for the CSV output.
            csv_format: Row layout; see ``CsvExportFormat``.
            include_overrides: If True, variable override values for each sweep step
                are included as additional columns.

        Returns:
            The full CSV document as a single string.
        """
        if self._database is None:
            raise ValueError(_DB_NOT_INITIALIZED_ERROR)

        buf = StringIO()
        self._to_csv_stream(
            output=buf,
            delimiter=delimiter,
            csv_format=csv_format,
            include_overrides=include_overrides,
        )
        return buf.getvalue()

    def to_csv_stream(
        self,
        delimiter: str = ",",
        stream: TextIO | None = None,
        csv_format: CsvExportFormat = CsvExportFormat.EXPLODED,
        include_overrides: bool = False,
    ) -> StringIO | None:
        """
        Write CSV data to a stream.

        Args:
            delimiter: The delimiter to use in the CSV output.
            stream: Optional stream to write to.
            include_overrides: If True, variable override values for each sweep step
                are included as additional columns in the CSV output.

        Returns:
            None if stream was provided, StringIO if no stream was provided.

        Examples:
            # Get a StringIO
            csv_stream = data.to_csv_stream()

            # Stream directly to a file
            with open("output.csv", "w") as f:
                data.to_csv_stream(stream=f)
        """
        if self._database is None:
            raise ValueError(_DB_NOT_INITIALIZED_ERROR)

        if stream is None:
            # Backward compatible: create and return StringIO
            output = StringIO()
            self._to_csv_stream(
                output=output,
                delimiter=delimiter,
                csv_format=csv_format,
                include_overrides=include_overrides,
            )
            output.seek(0)  # Reset cursor to the beginning
            return output
        else:
            # User provided stream: write directly and return None
            self._to_csv_stream(
                output=stream,
                delimiter=delimiter,
                csv_format=csv_format,
                include_overrides=include_overrides,
            )
            return None

    def get_value_headers(self) -> list[str]:
        """
        Returns header strings of all value outputs. The header equals the name of the
        value output plus the specifier if it was provided. The specifier is included
        after the name in parentheses.

        Examples:
          - Name "Resistance" and no specifier    --> "Resistance"
          - Name "Impedance" and specifier "real" --> "Impedance (real)"
        """
        if self._database is None:
            raise ValueError(_DB_NOT_INITIALIZED_ERROR)

        return list(self._get_value_defs_by_header().keys())

    def get_value_ids(self) -> list[ValueId]:
        """
        Returns the identifier tuples of all value outputs. An identifier tuple consists
        of the name and the specifier.

        Examples:
          - Name "Resistance" and no specifier    --> ("Resistance", None)
          - Name "Impedance" and specifier "real" --> ("Impedance", "real")
        """
        if self._database is None:
            raise ValueError(_DB_NOT_INITIALIZED_ERROR)

        return list(self._get_value_defs_by_id().keys())

    def get_sweep_step_overrides(self) -> list[dict[str, list[float]]]:
        """
        Returns the variable overrides for each sweep step. The returned list
        can be used to find the sweep index based on a variable's value.

        The following example finds the index of the sweep step where
        "my_variable" had the value 42:

        ```python
        overrides = data.get_sweep_step_overrides()
        sweep_index = -1
        for i, step_overrides in enumerate(overrides):
            if step_overrides["my_variable"][0] == 42:
                sweep_index = i
                break
        ```

        The found sweep index can then be passed into various methods of this
        class to get the data of that sweep step.

        For simple key-value pairs, use the `get_sweep_index` method.
        """
        if self._database is None:
            raise ValueError(_DB_NOT_INITIALIZED_ERROR)

        return [s.overrides for s in self._get_simulations_sorted()]

    def get_sweep_index(self, variable_name: str, value: float | list[float]) -> int:
        """
        Finds the sweep index based on a variable name and a value.

        If multiple sweep steps have the same variable name and value,
        the first one found is returned.

        Examples:
        ```python
        # Get the sweep index for the variable "my_variable" with the value 42
        sweep_index = data.get_sweep_index("my_variable", 42)

        # Get the sweep index for the variable "my_variable" with the value [1.0, 2.0]
        sweep_index = data.get_sweep_index("my_variable", [1.0, 2.0])
        ```

        If you meed more fine-grained control, use the `get_sweep_step_overrides` method.
        """
        if self._database is None:
            raise ValueError(_DB_NOT_INITIALIZED_ERROR)

        if isinstance(value, list) and len(value) == 1:
            value = value[0]

        simulations_by_overrides = self._simulations_by_overrides
        if simulations_by_overrides is None:
            simulations_by_overrides = self._get_simulations_by_overrides()

        val_dict = simulations_by_overrides.get(variable_name)
        if val_dict is not None:
            sim = val_dict.get(value)
            if sim is not None:
                return sim.job_index

        raise ValueError(f"Sweep step {variable_name} == {value} not found")

    def get_sweep_count(self) -> int:
        """
        Returns the total number of sweep steps.
        """
        if self._database is None:
            raise ValueError(_DB_NOT_INITIALIZED_ERROR)

        return len(self._db.simulations_by_row_id)

    def get_step_count(self, sweep_index: int | None = None) -> int:
        """
        Returns the total number of steps. This function returns the number of
        time steps in transient simulations and the number of eigenmodes in
        eigenvalue simulations. This is not to be confused with sweep steps.
        Each sweep step can have multiple steps.

        If no value is passed in, the total number of steps is returned. Note
        that each sweep step can have different set of steps. All steps are not
        necessarily present in all sweep steps.

        If a sweep index is passed in, the number of steps in that sweep step
        is returned.
        """
        if self._database is None:
            raise ValueError(_DB_NOT_INITIALIZED_ERROR)

        if sweep_index is None:
            return len(self._get_steps_sorted())

        # Combine steps collected from fields and values
        # TODO: this is really slow if this method is called frequently.
        field_steps = {
            field.step.raw_step
            for field in self._db.fields
            if field.definition.type == FieldOutputType.FIELD
            and field.simulation.job_index == sweep_index
        }
        value_steps = {
            value.step.raw_step
            for value in self._db.values
            if value.simulation.job_index == sweep_index
        }

        return len(field_steps | value_steps)

    def get_step_labels(self) -> list[str]:
        """
        Returns the labels of all steps. A label is the string representation of
        a step. A step here means the time step in a transient simulation or the
        eigenmode index in an eigenvalue simulation. This is not to be confused with
        sweep steps. Each sweep step can have multiple steps.

        The label can either be a stringified numeric value or the special string
        `SimulationOutputData.NO_STEP`. `NO_STEP` is used as the step label when
        data is saved without specifying a step.
        """
        if self._database is None:
            raise ValueError(_DB_NOT_INITIALIZED_ERROR)

        return [step.raw_step for step in self._get_steps_sorted()]

    def get_step_label(self, step_index: int) -> str:
        """
        Returns the `step_index`th value of the `get_step_labels` list.
        """
        if self._database is None:
            raise ValueError(_DB_NOT_INITIALIZED_ERROR)

        sorted_steps = self._steps_sorted
        if sorted_steps is None:
            sorted_steps = self._get_steps_sorted()

        if step_index < -len(sorted_steps) or step_index >= len(sorted_steps):
            raise ValueError(f"Step index {step_index} out of range")

        return sorted_steps[step_index].raw_step

    def get_step_index(self, step_label: str | float | int | None) -> int:
        """
        Finds the step index based on a label or a numeric value. A step here
        means the time step in a transient simulation or the eigenmode index
        in an eigenvalue simulation. This is not to be confused with
        sweep steps. Each sweep step can have multiple steps.

        Examples:
        ```python
        # Get the step index for the step label "0.2"
        step_index = data.get_step_index("0.2")

        # Get the step index for the step whose numeric value is 1.0
        step_index = data.get_step_index(1.0)

        # Get the the step index for data that was saved without specifying a step
        step_index = data.get_step_index(SimulationOutputData.NO_STEP)
        ```

        NOTE: It's always better find using a float value than the string string
        label. If you use the string representation of a float value, it needs to
        be __exactly__ the same as the one stored in the database. There's no
        guarantee that the string representation was produced using `str(float_value)`.
        """
        if self._database is None:
            raise ValueError(_DB_NOT_INITIALIZED_ERROR)

        if isinstance(step_label, str):
            step_index_by_label = self._step_index_by_label
            if step_index_by_label is None:
                step_index_by_label = self._get_step_index_by_label()
            index = step_index_by_label.get(step_label)
            if index is not None:
                return index
        else:
            step_index_by_step = self._step_index_by_step
            if step_index_by_step is None:
                step_index_by_step = self._get_step_index_by_step()
            index = step_index_by_step.get(step_label)
            if index is not None:
                return index

        raise ValueError(f"Step label {step_label} not found")

    def get_array_index_count_at(
        self,
        sweep_index: int,
        step_index: int,
        value_header: ValueHeaderOrId,
    ) -> int:
        """
        Equivalent to `len(get_values_at(sweep_index, step_index, value_header))`.
        """
        # Hot path: don't use the prevent_uninitialized decorator.
        if self._database is None:
            raise ValueError(_DB_NOT_INITIALIZED_ERROR)

        values = self._get_values_at(sweep_index, step_index, value_header)
        if values is None:
            return 0

        return len(values)

    def get_value_at(
        self,
        sweep_index: int,
        step_index: int,
        value_header: ValueHeaderOrId,
        array_index: int | None = None,
    ) -> float | None:
        """
        Equivalent to `get_values_at(sweep_index, step_index, value_header)[array_index]`.
        """
        # Hot path: don't use the prevent_uninitialized decorator.
        if self._database is None:
            raise ValueError(_DB_NOT_INITIALIZED_ERROR)

        values = self._get_values_at(sweep_index, step_index, value_header)
        if values is None:
            return None
        if array_index is None:
            array_index = 0
        if array_index >= len(values):
            return None
        return values[array_index]

    def get_values_at(
        self,
        sweep_index: int,
        step_index: int,
        value_header: ValueHeaderOrId,
    ) -> list[float] | None:
        """
        Returns the value output data of the value identified by `value_header` at the
        given sweep index and step index. See the `get_sweep_index` and `get_step_index`
        methods for more information on how to determine the sweep index and step index.

        The `value_header` can either be:

          - A string representing the value header. For example, "Impedance (real)" where
            "Impedance" is the name and "real" is the specifier. If there's no specifier,
            the header is just the value output's name, so in this case "Impedance".

          - A tuple consisting of the name and the specifier. For example, ("Impedance", "real")
            where "Impedance" is the name and "real" is the specifier. If there's no specifier,
            the tuple still needs to contain two elements: the name and `None`. For example
            ("Impedance", None). But in case there's no specifier, you can just pass in the
            name as a string since it matches the header format.

        Examples:
        ```python
        sweep_index = data.get_sweep_index("my_variable", 42)
        step_index = data.get_step_index(0.1)

        # Get the resistance at the given sweep index and step index.
        values = data.get_values_at(sweep_index, step_index, "Resistance")

        # Get the real part of the impedance at the given sweep index and step index.
        values = data.get_values_at(sweep_index, step_index, ("Impedance", "real"))

        # Get the real part of the impedance using a header string
        values = data.get_values_at(sweep_index, step_index, "Impedance (real)")
        ```
        """
        # Hot path: don't use the prevent_uninitialized decorator.
        if self._database is None:
            raise ValueError(_DB_NOT_INITIALIZED_ERROR)

        values = self._get_values_at(sweep_index, step_index, value_header)
        if values is None:
            return None

        return values.tolist()

    def get_filenames_for_output_field(
        self,
        field_name: str,
        sweep_index: int = 0,
        step_index: int | None = None,
    ) -> list[str]:
        if self._database is None:
            raise ValueError(_DB_NOT_INITIALIZED_ERROR)

        return self._get_field_filenames(
            field_name,
            FieldOutputType.FIELD,
            sweep_index,
            step_index,
        )

    def get_filenames_for_mesh(
        self,
        field_name: str,
        sweep_index: int = 0,
        step_index: int | None = None,
    ) -> list[str]:
        if self._database is None:
            raise ValueError(_DB_NOT_INITIALIZED_ERROR)

        return self._get_field_filenames(
            field_name,
            FieldOutputType.MESH,
            sweep_index,
            step_index,
        )

    def _get_field_filenames(
        self,
        field_name: str,
        field_type: FieldOutputType,
        sweep_index: int = 0,
        step_index: int | None = None,
    ) -> list[str]:
        if step_index is None:
            step_label = SimulationOutputData.NO_STEP
        else:
            step_label = self.get_step_label(step_index)

        for field in self._db.fields:
            if (
                SimulationOutputData._get_header_for_field_def(field.definition)
                == field_name
                and field.definition.type == field_type
                and field.simulation.job_index == sweep_index
                and field.step.raw_step == step_label
            ):
                return field.get_file_names()

        return []

    def get_simulation_job_id(
        self,
        sweep_index: int = 0,
        step_index: int | None = None,  # deprecated
    ) -> str:
        if self._database is None:
            raise ValueError(_DB_NOT_INITIALIZED_ERROR)

        sims_sorted = self._get_simulations_sorted()
        return sims_sorted[sweep_index].job_id

    def _get_values_at(
        self,
        sweep_index: int,
        step_index: int,
        value_header: ValueHeaderOrId,
    ) -> array.array[float] | None:
        sims_sorted = self._simulations_sorted
        if sims_sorted is None:
            sims_sorted = self._get_simulations_sorted()
        sim = sims_sorted[sweep_index]

        steps_sorted = self._steps_sorted
        if steps_sorted is None:
            steps_sorted = self._get_steps_sorted()
        step = steps_sorted[step_index]

        if isinstance(value_header, str):
            value_defs_by_header = self._value_defs_by_header
            if value_defs_by_header is None:
                value_defs_by_header = self._get_value_defs_by_header()
            value_def = value_defs_by_header.get(value_header)
            if value_def is None:
                return None
        else:
            value_defs_by_id = self._value_defs_by_id
            if value_defs_by_id is None:
                value_defs_by_id = self._get_value_defs_by_id()
            value_def = value_defs_by_id.get(value_header)
            if value_def is None:
                return None

        values_dict = self._values_by_sim_id_and_step_id_and_definition_id
        if values_dict is None:
            values_dict = self._get_values_by_sim_id_and_step_id_and_definition_id()

        sim_dict = values_dict.get(sim.rowid)
        if sim_dict is None:
            return None

        step_dict = sim_dict.get(step.rowid)
        if step_dict is None:
            return None

        value = step_dict.get(value_def.rowid)
        if value is None:
            return None

        return self._db.get_value_data(value)

    def _get_simulations_sorted(self) -> list[SimulationOutput]:
        if self._simulations_sorted is not None:
            return self._simulations_sorted

        sims = self._db.simulations_by_row_id
        self._simulations_sorted = sorted(sims.values(), key=lambda x: x.job_index)

        return self._simulations_sorted

    def _get_simulations_by_overrides(
        self,
    ) -> dict[str, dict[float | list[float], SimulationOutput]]:
        if self._simulations_by_overrides is not None:
            return self._simulations_by_overrides

        sims_sorted = self._get_simulations_sorted()
        self._simulations_by_overrides = {}
        for sim in sims_sorted:
            for key, value in sim.overrides.items():
                val: float | list[float] = value
                if len(value) == 1:
                    val = value[0]
                val_dict = self._simulations_by_overrides.setdefault(key, {})
                if val not in val_dict:
                    val_dict[val] = sim

        return self._simulations_by_overrides

    def _get_value_defs_sorted(self) -> list[ValueOutputDefinitionRow]:
        if self._value_defs_sorted is not None:
            return self._value_defs_sorted

        value_defs = self._db.value_defs_by_row_id
        self._value_defs_sorted = sorted(value_defs.values(), key=lambda x: x.rowid)

        return self._value_defs_sorted

    def _get_value_defs_by_header(
        self,
    ) -> dict[str, ValueOutputDefinitionRow]:
        """
        Get value definitions by header. The headers are in the order returned by
        `_get_value_defs_sorted`. Since python guarantees dictionary iteration order,
        you get the headers in the sorted order when you iterate over the dictionary.
        """
        if self._value_defs_by_header is not None:
            return self._value_defs_by_header

        value_defs_sorted = self._get_value_defs_sorted()
        self._value_defs_by_header = {
            SimulationOutputData._get_header_for_value_def(value_def): value_def
            for value_def in value_defs_sorted
        }

        return self._value_defs_by_header

    def _get_value_defs_by_id(
        self,
    ) -> dict[ValueId, ValueOutputDefinitionRow]:
        """
        Get value definitions by id. The ids are in the order returned by
        `_get_value_defs_sorted`. Since python guarantees dictionary iteration order,
        you get the ids in the sorted order when you iterate over the dictionary.
        """
        if self._value_defs_by_id is not None:
            return self._value_defs_by_id

        value_defs_sorted = self._get_value_defs_sorted()
        self._value_defs_by_id = {
            (value_def.name, value_def.specifier): value_def
            for value_def in value_defs_sorted
        }

        return self._value_defs_by_id

    def _get_values_by_sim_id_and_step_id_and_definition_id(
        self,
    ) -> dict[int, dict[int, dict[int, ValueOutput]]]:
        if self._values_by_sim_id_and_step_id_and_definition_id is not None:
            return self._values_by_sim_id_and_step_id_and_definition_id

        self._values_by_sim_id_and_step_id_and_definition_id = {}
        values_dict = self._values_by_sim_id_and_step_id_and_definition_id
        for value in self._db.values:
            sim_dict = values_dict.setdefault(value.simulation.rowid, {})
            step_dict = sim_dict.setdefault(value.step.rowid, {})
            step_dict[value.definition.rowid] = value

        return values_dict

    def _get_steps_sorted(self) -> list[SimulationStepRow]:
        if self._steps_sorted is not None:
            return self._steps_sorted

        steps = self._db.steps_by_row_id

        nostep_step: SimulationStepRow | None = None
        numbered_steps: list[SimulationStepRow] = []

        for step in steps.values():
            if step.raw_step == _NO_STEP:
                nostep_step = step
            else:
                numbered_steps.append(step)

        numbered_steps_sorted = sorted(
            numbered_steps, key=lambda s: -math.inf if s.step is None else s.step
        )

        # Combine: NO_STEP step first (if exists), then sorted numbered steps
        if nostep_step:
            self._steps_sorted = [nostep_step] + numbered_steps_sorted
        else:
            self._steps_sorted = numbered_steps_sorted

        return self._steps_sorted

    def _get_step_index_by_label(self) -> dict[str, int]:
        if self._step_index_by_label is not None:
            return self._step_index_by_label

        steps_sorted = self._get_steps_sorted()
        self._step_index_by_label = {
            step.raw_step: index for index, step in enumerate(steps_sorted)
        }

        return self._step_index_by_label

    def _get_step_index_by_step(self) -> dict[float | None, int]:
        if self._step_index_by_step is not None:
            return self._step_index_by_step
        steps_sorted = self._get_steps_sorted()
        self._step_index_by_step = {
            step.step: index for index, step in enumerate(steps_sorted)
        }

        return self._step_index_by_step

    def _to_csv_stream(
        self,
        output: TextIO,
        delimiter: str = ",",
        csv_format: CsvExportFormat = CsvExportFormat.EXPLODED,
        include_overrides: bool = False,
    ) -> None:
        db = self._db
        is_exploded = csv_format == CsvExportFormat.EXPLODED

        value_defs_sorted = self._get_value_defs_sorted()
        value_defs_by_header = self._get_value_defs_by_header()
        value_headers = list(value_defs_by_header.keys())
        num_value_cols = len(value_defs_sorted)
        value_def_rowids = [vd.rowid for vd in value_defs_sorted]

        # --- header row -----------------------------------------------
        headers: list[str] = ["Sweep step", "Step"]
        if is_exploded:
            headers.append("Array index")

        sims_sorted = self._get_simulations_sorted()
        override_names: list[str] = []
        if include_overrides:
            override_names = (
                [
                    name
                    for name in sims_sorted[0].overrides.keys()
                    if name not in value_defs_by_header
                ]
                if sims_sorted
                else []
            )
            headers.extend(override_names)

        headers.extend(value_headers)
        output.write(delimiter.join(headers))
        output.write("\n")

        # --- prepare lookup structures --------------------------------
        _empty_cells = [""] * num_value_cols
        values_dict = self._get_values_by_sim_id_and_step_id_and_definition_id()
        steps_sorted = self._get_steps_sorted()

        _FLUSH_SIZE = 64 * 1024
        _write = output.write
        buf: list[str] = []
        buf_len = 0

        _str = str
        _get_value_data = db.get_value_data
        _len = len
        _range = range
        _append = buf.append

        for sim in sims_sorted:
            sim_rowid = sim.rowid
            sim_index_str = _str(sim.job_index)
            sim_dict = values_dict.get(sim_rowid)

            override_prefix = ""
            if include_overrides and override_names:
                override_parts: list[str] = []
                for name in override_names:
                    vals = sim.overrides.get(name, [])
                    if _len(vals) == 1:
                        override_parts.append(_str(vals[0]))
                    else:
                        override_parts.append(_str(vals))
                override_prefix = delimiter + delimiter.join(override_parts)

            for step in steps_sorted:
                step_dict = sim_dict.get(step.rowid) if sim_dict is not None else None

                step_label = step.raw_step

                if not is_exploded:
                    row_prefix = (
                        sim_index_str + delimiter + step_label + override_prefix
                    )

                    if step_dict is None:
                        line = row_prefix + delimiter + delimiter.join(_empty_cells)
                    else:
                        value_cells: list[str] = []
                        _vc_append = value_cells.append
                        for def_rowid in value_def_rowids:
                            value_output = step_dict.get(def_rowid)
                            if value_output is None:
                                _vc_append("")
                            else:
                                data = _get_value_data(value_output)
                                data_len = _len(data)
                                if data_len == 0:
                                    _vc_append("")
                                elif data_len == 1:
                                    _vc_append(_str(data[0]))
                                else:
                                    _vc_append(
                                        '"['
                                        + ",".join(
                                            _str(data[i]) for i in _range(data_len)
                                        )
                                        + ']"'
                                    )
                        line = row_prefix + delimiter + delimiter.join(value_cells)

                    _append(line)
                    buf_len += _len(line)

                else:
                    if step_dict is None:
                        continue

                    row_prefix = sim_index_str + delimiter + step_label + delimiter

                    # Collect array.array objects and pre-convert scalars
                    data_arrays: list[array.array[float] | None] = [
                        None
                    ] * num_value_cols
                    scalar_strs: list[str | None] = [None] * num_value_cols
                    data_lens: list[int] = [0] * num_value_cols
                    max_value_count = 0

                    for col_idx in _range(num_value_cols):
                        value_output = step_dict.get(value_def_rowids[col_idx])
                        if value_output is not None:
                            arr = _get_value_data(value_output)
                            data_arrays[col_idx] = arr
                            arr_len = _len(arr)
                            data_lens[col_idx] = arr_len
                            if arr_len == 1:
                                scalar_strs[col_idx] = _str(arr[0])
                            if arr_len > max_value_count:
                                max_value_count = arr_len

                    for array_index in _range(max_value_count):
                        value_cells = []
                        _vc_append = value_cells.append
                        for col_idx in _range(num_value_cols):
                            col_arr: array.array[float] | None = data_arrays[col_idx]
                            if col_arr is None:
                                _vc_append("")
                            else:
                                arr_len = data_lens[col_idx]
                                if array_index < arr_len:
                                    _vc_append(_str(col_arr[array_index]))
                                elif arr_len == 1:
                                    _vc_append(scalar_strs[col_idx])  # type: ignore[arg-type]
                                else:
                                    _vc_append("")

                        line = (
                            row_prefix
                            + _str(array_index)
                            + override_prefix
                            + delimiter
                            + delimiter.join(value_cells)
                        )
                        _append(line)
                        buf_len += _len(line)

                if buf_len >= _FLUSH_SIZE:
                    _write("\n".join(buf))
                    _write("\n")
                    buf.clear()
                    buf_len = 0

        if buf:
            _write("\n".join(buf))
            _write("\n")

    def _get_sweep_and_step_values_grouped_by_header(
        self,
        simulation_id: int,
        step_id: int,
    ) -> dict[str, list[float]]:
        values_dict = self._values_by_sim_id_and_step_id_and_definition_id
        if values_dict is None:
            values_dict = self._get_values_by_sim_id_and_step_id_and_definition_id()

        sim_dict = values_dict.get(simulation_id)
        if sim_dict is None:
            return {}

        step_dict = sim_dict.get(step_id)
        if step_dict is None:
            return {}

        value_defs_by_header = self._value_defs_by_header
        if value_defs_by_header is None:
            value_defs_by_header = self._get_value_defs_by_header()

        values_by_header: dict[str, list[float]] = {}
        for header, value_def in value_defs_by_header.items():
            value = step_dict.get(value_def.rowid)
            if value is not None:
                values_by_header[header] = self._db.get_value_data(value).tolist()

        return values_by_header

    def _create_cache_dir(self):
        if not os.path.exists(self._cache_dir):
            os.makedirs(self._cache_dir, mode=0o700, exist_ok=True)

    @staticmethod
    def _get_header_for_value_def(value_def: ValueOutputDefinitionRow) -> str:
        if value_def.specifier is not None:
            return f"{value_def.name} ({value_def.specifier})"
        return value_def.name

    @staticmethod
    def _get_header_for_field_def(field_def: FieldOutputDefinitionRow) -> str:
        if field_def.specifier is not None:
            return f"{field_def.name} ({field_def.specifier})"
        return field_def.name

    @staticmethod
    def _check_pandas() -> None:
        try:
            import pandas as _pd  # noqa: F401

            del _pd
        except ImportError:
            raise ImportError(
                "pandas is required for DataFrame support. "
                "Install the pandas library, or install the SDK with "
                "DataFrame support: pip install allsolve[dataframe]"
            ) from None

    def _build_tidy_dataframe(
        self,
        sims: list[SimulationOutput],
        *,
        include_overrides: bool,
    ) -> pd.DataFrame:
        import pandas as pd

        db = self._db
        value_defs_sorted = self._get_value_defs_sorted()
        value_defs_by_header = self._get_value_defs_by_header()
        value_headers = list(value_defs_by_header.keys())
        num_value_cols = len(value_defs_sorted)
        value_def_rowids = [vd.rowid for vd in value_defs_sorted]
        steps_sorted = self._get_steps_sorted()
        values_dict = self._get_values_by_sim_id_and_step_id_and_definition_id()

        _get_value_data = db.get_value_data
        _len = len

        override_names: list[str] = []
        if include_overrides and sims:
            override_names = [
                name
                for name in sims[0].overrides.keys()
                if name not in value_defs_by_header
            ]

        col_sweep: list[int] = []
        col_step: list[object] = []
        col_array_idx: list[int] = []
        col_overrides: dict[str, list[object]] = {n: [] for n in override_names}
        col_values: dict[str, list[object]] = {h: [] for h in value_headers}

        for sim in sims:
            override_scalars: dict[str, object] = {}
            if include_overrides:
                for name in override_names:
                    vals = sim.overrides.get(name, [])
                    override_scalars[name] = vals[0] if _len(vals) == 1 else str(vals)

            sim_dict = values_dict.get(sim.rowid)

            for step in steps_sorted:
                step_dict = sim_dict.get(step.rowid) if sim_dict is not None else None
                if step_dict is None:
                    continue

                data_arrays: list[array.array[float] | None] = [None] * num_value_cols
                data_lens: list[int] = [0] * num_value_cols
                max_count = 0

                for col_idx in range(num_value_cols):
                    value_output = step_dict.get(value_def_rowids[col_idx])
                    if value_output is not None:
                        arr = _get_value_data(value_output)
                        data_arrays[col_idx] = arr
                        arr_len = _len(arr)
                        data_lens[col_idx] = arr_len
                        if arr_len > max_count:
                            max_count = arr_len

                step_val: object = step.raw_step

                for array_index in range(max_count):
                    col_sweep.append(sim.job_index)
                    col_step.append(step_val)
                    col_array_idx.append(array_index)

                    for name in override_names:
                        col_overrides[name].append(override_scalars[name])

                    for col_idx in range(num_value_cols):
                        header = value_headers[col_idx]
                        col_arr = data_arrays[col_idx]
                        if col_arr is None:
                            col_values[header].append(None)
                        else:
                            arr_len = data_lens[col_idx]
                            if array_index < arr_len:
                                col_values[header].append(col_arr[array_index])
                            elif arr_len == 1:
                                col_values[header].append(col_arr[0])
                            else:
                                col_values[header].append(None)

        data: dict[str, list[object]] = {
            "Sweep step": col_sweep,  # type: ignore[dict-item]
            "Step": col_step,  # type: ignore[dict-item]
            "Array index": col_array_idx,  # type: ignore[dict-item]
        }
        data.update(col_overrides)
        data.update(col_values)

        return pd.DataFrame(data)
