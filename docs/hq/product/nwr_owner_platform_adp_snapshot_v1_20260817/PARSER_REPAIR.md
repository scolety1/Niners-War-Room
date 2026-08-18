# Parser repair

The existing markdown pipe-table parser remains first. Bold cell text is normalized. If it finds no valid table rows, the fallback accepts split blocks (`WR`, `13`, player, four values) and compact blocks (`WR13`, player, four values).

Values map in order to Consensus, Sleeper, ESPN, and FantasyPros. Dash, em dash, and blank values remain unknown, never zero. Preview reports `MARKDOWN_TABLE` or `PLAIN_TEXT_BLOCK`, safe matches, coverage, and malformed-block warnings without writing state.
