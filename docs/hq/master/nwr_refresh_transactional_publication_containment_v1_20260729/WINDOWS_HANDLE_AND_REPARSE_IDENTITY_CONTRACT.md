# Windows Handle and Reparse Identity Contract

The safe-root request must use the exact canonical absolute spelling. Device,
extended-length, traversal, alternate-case, short-name, mount/junction, and
other alias forms are rejected.

Every governed ancestor from the volume root through the repository, safe
root, `.staging`, and `generations` is opened with
`FILE_FLAG_OPEN_REPARSE_POINT`. Directory handles record:

- final normalized path from `GetFinalPathNameByHandleW`;
- volume serial and file ID from `GetFileInformationByHandle`;
- directory and reparse attributes.

Governed handles are held without `FILE_SHARE_DELETE`, preventing successful
rename/junction swaps while publication or resolution is active. Identity is
reopened and compared immediately before generation rename and pointer commit.
Any path, volume, file-ID, or reparse change aborts before pointer authority
changes.

Windows commit renames open the source by handle and call
`NtSetInformationFile(FileRenameInformation)` with the already-authenticated
parent handle in `RootDirectory` and a relative target name. Thus the final
operation is bound to the validated parent identity, not a newly resolved path
string.

Authoritative references:

- https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/ntifs/nf-ntifs-ntsetinformationfile
- https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/ntifs/ns-ntifs-_file_rename_information

The 13 controlled Windows mutations all failed before the authoritative
pointer changed.
