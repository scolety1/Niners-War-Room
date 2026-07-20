# Desktop launcher Stop ownership hotfix report

Starting HQ `d294634d0008c8062f3dd8890fa00e967a18f715` and tree `6d46025b917e0c1e32de872aa2714db3fd6ede49` were verified after fetch/prune with no remote advance. Implementation commit `d8286da34eab8bedf5d2f3f3b0176d29a696ed66` changes only the Windows launcher and two launcher test files.

The canonical failure reproduced under isolated state: ownership was `RUNNING`; Stop created `stop.request`; at 5.869 seconds the ownership file disappeared while listener PID 16472 remained; Stop timed out; status returned `health_status: HEALTHY` and `process_ownership: NONE`. The captured tree was revalidated and removed without targeting unrelated processes.

The hotfix makes ownership durable across `RUNNING`, `STOP_REQUESTED`, `STOPPING`, `RECOVERY_REQUIRED`, and `STOPPED`; records full identity evidence; preserves conflicts; tracks browser descendants; writes an atomic final receipt; and deletes ownership only after complete verified absence. Focused review passed 84 tests, full Hermetic passed 2,724 tests, and LocalData returned the required exit 4 marker.
