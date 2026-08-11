# Numeric Sort Root Cause

The artifact and market join already contained numeric values. The owner-facing display builder converted display cells, including DP Value and probability fields, to text before handing the frame to Streamlit. The data grid therefore performed lexicographic header sorting: values such as `98`, `978`, and `9716` were ordered by characters.

The repair separates raw/display responsibilities. Numeric display columns are parsed with `pandas.to_numeric`, blanks remain `NaN`, percent signs are removed only for numeric presentation, and Streamlit `NumberColumn` configuration supplies the visible formatting. Missing numeric values remain missing and sort last in the explicit server-side helper. No ranking, score, market value, or Outcome probability was changed.

The exact regression fixture descends as `9716, 9626, 9184, 9141, 978, 98, 96, 91`. The actual browser grid descends from `10208, 9716, 9626, 9184, 9141, 9076, 8991, 8991` and ascends from the numeric low end.
