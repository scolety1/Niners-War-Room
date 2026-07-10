import fs from "node:fs/promises";
import path from "node:path";
import { Workbook } from "file:///C:/Users/codex-agent/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs";

const packetDir = path.resolve(process.argv[2] ?? ".");
const names = (await fs.readdir(packetDir))
  .filter((name) => name.toLowerCase().endsWith(".csv"))
  .sort();

if (names.length === 0) {
  throw new Error(`No CSV files found in ${packetDir}`);
}

const results = [];
for (const name of names) {
  const csvText = await fs.readFile(path.join(packetDir, name), "utf8");
  if (!csvText.includes("\n")) {
    throw new Error(`CSV has no header/data boundary: ${name}`);
  }
  const workbook = await Workbook.fromCSV(csvText, { sheetName: "Data" });
  const sheet = workbook.worksheets.getItem("Data");
  const usedRange = sheet.getUsedRange(true);
  if (!usedRange) {
    throw new Error(`Artifact Tool produced no used range: ${name}`);
  }
  const sheetInspection = await workbook.inspect({ kind: "sheet", include: "id,name" });
  results.push({ file: name, status: "PASS", bytes: Buffer.byteLength(csvText, "utf8"), sheetInspection });
}

process.stdout.write(`${JSON.stringify({ engine: "@oai/artifact-tool", csvFilesParsed: results.length, results }, null, 2)}\n`);
