# Line-ending and canonical-bytes review

The three exact-replay packet paths, builder, and focused tests are narrowly
governed by `.gitattributes` as UTF-8 text with LF endings. Packet writers emit
UTF-8 without BOM, LF only, and a newline at EOF. CSV field order is explicit;
floats use six decimal places. JSON keys are sorted with a newline at EOF.

The builder validates every packet file for BOM, CR bytes, and missing EOF
newline before success. Git-blob and working-tree comparisons therefore use
the same canonical bytes; no checkout conversion waiver is needed.
