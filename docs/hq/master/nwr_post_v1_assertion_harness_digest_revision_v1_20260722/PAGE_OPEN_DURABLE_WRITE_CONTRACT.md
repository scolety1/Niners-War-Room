# Page-open durable-write contract

The real Start Here module is rendered against a newly created temporary root.
The harness records sorted directory paths and, for each file, relative POSIX
path, byte size, and SHA-256 before and after render.

Instrumented boundaries include:

- `pathlib`, built-in, and `os` write/open/create/replace/rename/delete calls;
- `shutil` copy, move, and recursive delete;
- refresh receipt writes;
- draft/runtime and Development Lab state writes;
- refresh dispatch and status writes (stubbed so no provider can run);
- launcher backup/recovery/restore writes;
- pandas CSV/JSON/pickle/parquet/Excel exports;
- file-backed SQLite connections.

Any attempted target outside the temporary root fails immediately. Writes within
the root are allowed only so a negative control performs a real durable operation
that the inventory and event recorder can detect. Normal acceptance requires both:

`DURABLE_MUTATION_COUNT = 0`

and exact before/after inventory equality. In-memory Streamlit session state is
permitted and separately proves zero durable mutations.

The six required controls—direct file, receipt, draft runtime, refresh dispatch,
rename/delete, and wrapped file write—are all detected without touching user state.
