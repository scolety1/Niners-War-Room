# Packaged NumPy startup diagnosis

The candidate sidecar is a PyInstaller 6.21 `--onefile` executable containing pandas and NumPy. In one-file mode, native libraries are extracted to a runtime temporary directory before loading. The observed warning was consistent with Windows Application Control rejecting one extracted NumPy native module on one attempt; the retry succeeded.

This closure does not add `--runtime-tmpdir`. PyInstaller documents that option as a static build-time path (absolute or relative to the current working directory) and warns to use it only with care. The desktop already has a launcher-governed runtime and per-user installation paths; guessing a static writable/executable directory would introduce a new trust, cleanup, and multi-user risk. An `onedir` sidecar would also change the Tauri external-binary packaging contract and is not a bounded repair.

Disposition: candidate-specific mechanism understood, but no safe bounded root-cause fix is proven. Repeated clean installed launches must determine whether the warning reproduces. If it does, open a packaging lane to evaluate an explicitly provisioned, integrity-checked extraction root or an `onedir` resource contract under application-control policy.
