# Protected and Frozen Path Validation

The sole allowed write prefix is:

`docs/hq/master/rookie_registry_batch_836e_metadata_proof_preparation_v1_20260711/`

Verified starting HQ is `b6d16e64d4c182f4a9a5cce558a4b389d0d48bc1`. The final changed-path scan must show only files under the allowed prefix. The app, runtime, ranking, formula, source-registry, rookie-registry, plugin-governance, protected, and frozen paths are outside the write set.

The normalized baseline hashes are:

- mapping contract: `19bb737de35f476ad39bff50d41f25e5ec6ef3b88dacd48d23b47917960fa264`;
- queue contract: `e6c5d46f114afb4edc59b007e3422c0e543e1a3403be6708e93b610d67c30075`;
- canonical queue: `9ef64f1a3a06dc96a968da37bc53e825de656b0545e177c6d9c899485db6971f`.

All controlling packet manifest entries validated before packet creation. Final frozen-artifact and canonical-queue byte scans are required to reproduce the same hashes and show no tracked changes outside the packet.
