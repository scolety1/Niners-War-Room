# Temporal Availability Contract

- Outer unit: NFL draft class; no random player/player-season split.
- Training and normalization: classes strictly earlier than the untouched outer class.
- Feature cutoff: college seasons strictly before draft class.
- Y1 maturity: classes through 2025; Y2 through 2024; Y3 through 2023.
- 2026 class and all 2026 NFL outcomes: prohibited.
- Model form: fixed ridge/logistic regularization; explicit missingness indicators; no outer-fold selection.
- Same-class teammates remain together in the held-out class.
