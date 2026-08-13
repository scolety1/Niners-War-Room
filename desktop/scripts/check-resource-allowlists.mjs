import assert from "node:assert/strict";
import { existsSync, readFileSync, readdirSync, statSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const desktopRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const forbiddenResourceTrees = ["sample_data", "templates", "data_packs", "assets/branding"];
const ownerMarkers = ["Michael Colety", "Spencer Colety", "las-vegas-enginerds"];

const allowlists = {
  dynasty: [
    "config/nwr_future_pick_context_v1.csv",
    "docs/draft_day_exports/final_board_v1_20260622/app_props/mock_draft/mock_pick_context.csv",
    "docs/hq/master/nwr_model_v4_2026_rookie_board_review_v1_20260730/2026_ROOKIE_IDENTITY_BLOCKERS.csv",
    "docs/hq/master/nwr_model_v4_2026_rookie_board_review_v1_20260730/MODEL_V4_2026_ROOKIE_BOARD_REVIEW.csv",
    "docs/hq/master/nwr_outcome_columns_v3_rc1_v1_20260729/MANIFEST.json",
    "docs/hq/master/nwr_outcome_columns_v3_rc1_v1_20260729/OUTCOME_V3_INTEGRATION_PACK.csv",
    "docs/hq/model/current_board_deterministic_rebuild_with_recovery_inputs_v1_20260708/rebuilt_full_player_board_value_review_rows.csv",
    "docs/hq/model/nwr_unified_research_preview_v1_20260808/MANIFEST.json",
    "docs/hq/model/nwr_unified_research_preview_v1_20260808/ROOKIE_VETERAN_NEIGHBORHOODS.csv",
    "docs/hq/model/nwr_unified_research_preview_v1_20260808/UNIFIED_DYNASTY_RESEARCH_PREVIEW.csv",
  ],
  redraft: [
    "docs/hq/model/nwr_redraft_2026_rookie_projection_candidate_v1_20260809/BLOCKED_2026_ROOKIES.csv",
    "docs/hq/model/nwr_redraft_2026_rookie_projection_candidate_v1_20260809/GOVERNED_COMBINED_608_PROJECTION_SNAPSHOT.csv",
    "docs/hq/model/nwr_redraft_2026_rookie_projection_candidate_v1_20260809/NWR_DATA_GOVERNANCE.json",
  ],
};

function normalize(value) {
  return String(value).replaceAll("\\", "/").replace(/^\.\//, "").replace(/\/$/, "");
}

function containsTree(value, tree) {
  return `/${normalize(value)}/`.includes(`/${tree}/`);
}

function readJson(relativePath) {
  return JSON.parse(readFileSync(path.join(desktopRoot, relativePath), "utf8"));
}

function expectedResourceMap(mode) {
  return Object.fromEntries(
    allowlists[mode].map((destination) => [`../../../../${destination}`, destination]),
  );
}

function sortedEntries(value) {
  return Object.entries(value ?? {}).sort(([left], [right]) => left.localeCompare(right));
}

function assertNoOwnerMarkers(file, label) {
  if (statSync(file).size > 256 * 1024 * 1024) {
    return;
  }
  const body = readFileSync(file);
  for (const marker of ownerMarkers) {
    assert(
      !body.includes(Buffer.from(marker, "utf8")),
      `${label} contains owner marker ${JSON.stringify(marker)}: ${file}`,
    );
  }
}

for (const mode of Object.keys(allowlists)) {
  const base = readJson(`apps/${mode}/src-tauri/tauri.conf.json`);
  const windows = readJson(`apps/${mode}/src-tauri/tauri.windows.conf.json`);
  const iconPrefix = `../../../../assets/branding/nwr_${mode}_desktop_icon`;
  assert.deepEqual(
    base.bundle?.icon,
    [`${iconPrefix}.ico`, `${iconPrefix}.png`],
    `${mode} application icons must remain in bundle.icon`,
  );
  assert.equal(
    base.bundle?.windows?.nsis?.installerIcon,
    `${iconPrefix}.ico`,
    `${mode} NSIS installer icon must remain configured`,
  );
  assert.deepEqual(
    sortedEntries(base.bundle?.resources),
    [],
    `${mode} base config must not bundle broad resource trees`,
  );
  const resources = windows.bundle?.resources ?? {};
  assert.deepEqual(
    sortedEntries(resources),
    sortedEntries(expectedResourceMap(mode)),
    `${mode} Windows resources must match the exact runtime allowlist`,
  );
  for (const [source, destination] of Object.entries(resources)) {
    assert(
      forbiddenResourceTrees.every(
        (tree) => !containsTree(source, tree) && !containsTree(destination, tree),
      ),
      `${mode} resource map contains a forbidden tree: ${source} -> ${destination}`,
    );
    const tauriRoot = path.join(desktopRoot, "apps", mode, "src-tauri");
    const sourcePath = path.resolve(tauriRoot, source);
    const repositoryRoot = path.resolve(tauriRoot, "../../../..");
    assert(sourcePath.startsWith(`${repositoryRoot}${path.sep}`), `${source} escapes the repository`);
    assert(statSync(sourcePath).isFile(), `${mode} resource is not an exact file: ${source}`);
    assertNoOwnerMarkers(sourcePath, `${mode} allowlisted resource`);
  }
  const otherMode = mode === "dynasty" ? "redraft" : "dynasty";
  assert(
    allowlists[otherMode].every(
      (destination) => !Object.values(resources).includes(destination),
    ),
    `${mode} resource map contains ${otherMode}-only evidence`,
  );
}

function walk(root, directory = root) {
  const files = [];
  for (const entry of readdirSync(directory, { withFileTypes: true })) {
    const absolute = path.join(directory, entry.name);
    const relative = normalize(path.relative(root, absolute));
    if (entry.isDirectory()) {
      assert(
        forbiddenResourceTrees.every((tree) => !containsTree(relative, tree)),
        `packaged resources contain forbidden tree: ${relative}`,
      );
      files.push(...walk(root, absolute));
    } else if (entry.isFile()) {
      files.push(absolute);
    }
  }
  return files;
}

const inspectIndex = process.argv.indexOf("--inspect-dir");
if (inspectIndex >= 0) {
  const inspectDir = process.argv[inspectIndex + 1];
  const modeIndex = process.argv.indexOf("--mode");
  const mode = modeIndex >= 0 ? process.argv[modeIndex + 1] : undefined;
  assert(inspectDir, "--inspect-dir requires a packaged resource directory");
  assert(mode && mode in allowlists, "--mode must be dynasty or redraft");
  const root = path.resolve(inspectDir);
  assert(existsSync(root) && statSync(root).isDirectory(), `${root} is not a directory`);
  for (const relative of allowlists[mode]) {
    const packagedFile = path.join(root, relative);
    assert(
      existsSync(packagedFile) && statSync(packagedFile).isFile(),
      `packaged ${mode} resource missing: ${relative}`,
    );
  }
  for (const relative of allowlists[mode === "dynasty" ? "redraft" : "dynasty"]) {
    assert(!existsSync(path.join(root, relative)), `packaged ${mode} resources contain cross-mode file: ${relative}`);
  }
  for (const file of walk(root)) {
    assertNoOwnerMarkers(file, `packaged ${mode} resource`);
  }
}

console.log("NWR Desktop resource allowlists are exact and privacy-bounded.");
