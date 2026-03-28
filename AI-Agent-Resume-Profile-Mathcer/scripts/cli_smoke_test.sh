#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "[1/3] Running API-level pipeline smoke test..."
python3 - <<'PY'
from agent.matching_agent import HiringMatchingAgent

agent = HiringMatchingAgent(resume_dir='data/resumes')
state = agent.run('data/job_description.txt')

ranked = state.get('ranked_candidates', [])
shortlist = state.get('shortlist', [])
assert len(ranked) >= 3, f"Expected >=3 ranked candidates, got {len(ranked)}"
assert len(shortlist) >= 1, f"Expected >=1 shortlisted candidate, got {len(shortlist)}"
assert ranked[0].get('candidate_id'), "Top ranked candidate_id missing"

print("API smoke test passed")
print("ranked_count=", len(ranked))
print("shortlist_count=", len(shortlist))
print("top_candidate=", ranked[0].get('candidate_id'))
PY

echo "[2/3] Running CLI interaction smoke test..."
CLI_OUTPUT="$(mktemp)"

TOP_IDS="$(python3 - <<'PY'
from agent.matching_agent import HiringMatchingAgent

agent = HiringMatchingAgent(resume_dir='data/resumes')
state = agent.run('data/job_description.txt')
ranked = state.get('ranked_candidates', [])

if not ranked:
		print('')
else:
		top = [c.get('candidate_id', '') for c in ranked[:3] if c.get('candidate_id')]
		print(','.join(top))
PY
)"

PRIMARY_ID="$(echo "$TOP_IDS" | cut -d',' -f1)"
COMPARE_IDS="${TOP_IDS:-$PRIMARY_ID}"

if [[ -z "${PRIMARY_ID}" ]]; then
	echo "Could not determine top candidate ID from dataset"
	rm -f "$CLI_OUTPUT"
	exit 1
fi

printf "run data/job_description.txt\nshow shortlist\nwhy ${PRIMARY_ID}\ncompare ${COMPARE_IDS}\nquestions ${PRIMARY_ID}\nexit\n" | python3 main.py > "$CLI_OUTPUT"

grep -q "Pipeline executed successfully" "$CLI_OUTPUT"
grep -q "Ranked Candidates" "$CLI_OUTPUT"
grep -q "score_breakdown" "$CLI_OUTPUT"
grep -q "comparison" "$CLI_OUTPUT"
grep -q "questions" "$CLI_OUTPUT"

echo "CLI smoke test passed"

echo "[3/3] Cleaning up..."
rm -f "$CLI_OUTPUT"

echo "All smoke tests passed."
