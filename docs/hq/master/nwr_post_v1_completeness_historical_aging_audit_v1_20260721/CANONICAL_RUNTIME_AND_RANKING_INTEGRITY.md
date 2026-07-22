# Canonical runtime and ranking integrity

Starting remote HQ was 532215c1b1a8896d5a838b827535c13dd655199d with tree
bca7ca6ecc1111ead8289a77650f481516d283fd. The stable checkout at
C:/NWR/Niners-War-Room-V1 was clean, exact, and zero ahead or behind.

The Desktop shortcut target is Windows PowerShell with the canonical
NWR Desktop Commands.ps1 start command, stable working directory, persistent
LocalAppData root, app-mode browser contract, and port 8520. Launcher status
reported HEALTHY and VERIFIED_RUNNING. Its app_commit field is a hard-coded
accepted RC1 compatibility floor; it is not current HEAD. Git independently
proved the actual stable commit and tree.

The exact rankings loader resolved:
- source: local_exports/model_v4/current_value/latest/full_player_board_value_review_rows.csv
- rows: 240
- SHA-256: 263cc8aa050c4670bf5ed22701d7b04801d143480c5630b98e00dd08d2968ce4
- errors: none
- top five: Puka Nacua; Jaxon Smith-Njigba; Bijan Robinson; Jonathan Taylor; Jahmyr Gibbs

The rendered candidate showed Full dynasty rows: 240 at 1440px and 320px with
one Dynasty Rankings H1, no exception, and no root overflow. Formula, score,
rank, source admission, player identity, recommendation, and board files were
unchanged.
