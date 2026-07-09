# Route Feed Response Decision Tree V1

## Start

Provider response received.

Do not accept, store, or commit raw route rows. First classify the response and determine whether a future source-admission lane is justified.

## If Provider Says Public Use Allowed

1. Request the exact public license or terms URL.
2. Confirm storage, derived metrics, internal display, model/research use, and redistribution rights.
3. Confirm supported retrieval path and field dictionary.
4. If all core gates are documented, classify `GREEN_PERMISSION_PATH_POSSIBLE`.
5. Open a separate source-admission lane.

## If Provider Says Private Use Allowed Only

1. Capture private/internal use restrictions.
2. Confirm whether NWR may store data and compute derived YPRR/TPRR internally.
3. Confirm whether model research and production rankings are allowed or forbidden.
4. If internal use is allowed but public redistribution is blocked, classify `GREEN_PERMISSION_PATH_POSSIBLE` or `YELLOW_NEEDS_FOLLOWUP` depending on missing evidence.
5. Keep public display and redistribution blocked.

## If Provider Says Paid License Required

1. Classify `CONTRACT_ONLY_PROPRIETARY`.
2. Do not request or accept raw data outside a contract.
3. Escalate to the designated NWR contract/business owner.
4. If contract terms become available, run source-admission review after legal/permission review.

## If Provider Says No Redistribution Allowed

1. Determine whether internal storage and derived metrics are still allowed.
2. If internal research is allowed, raw redistribution remains blocked.
3. If derived metrics cannot be displayed or shared, keep display and downstream use blocked.
4. Classify based on remaining gates: usually `YELLOW_NEEDS_FOLLOWUP` or `GREEN_PERMISSION_PATH_POSSIBLE` for internal-only use.

## If Provider Says No Model/Training Use Allowed

1. Record exact restriction.
2. Determine whether descriptive internal research is allowed.
3. If model/rankings use is prohibited, keep source blocked for production model/rankings use.
4. Classification is usually `YELLOW_NEEDS_FOLLOWUP` or `RED_PERMISSION_BLOCKED` depending on NWR need.

## If Provider Says No API/Export Available

1. Ask whether a supported static file, data room, or scheduled export exists.
2. If only manual page viewing or public UI is available, classify `RED_PERMISSION_BLOCKED`.
3. Do not scrape or build an unofficial export.

## If Provider Says No Response

1. Keep classification `NO_RESPONSE_YET`.
2. Do not infer permission.
3. Send an approved reminder only if outreach owner authorizes it.
4. If repeated non-response, leave source blocked.

## If Provider Sends Raw Data Unexpectedly

1. Do not commit it.
2. Do not inspect beyond what is needed to identify that raw data arrived.
3. Move handling to a designated secure/legal intake path.
4. Record response metadata only.
5. Keep source not admitted.

## Terminal Rule

No response classification admits a source. Every positive path still requires a separate source-admission lane before route counts, YPRR, or TPRR can be used.
