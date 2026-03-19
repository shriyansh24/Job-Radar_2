# Chunk 6: Fixture Tests + Contract Tests + CLI Completion
> **Depends on:** Chunk 5 (full pipeline working, all adapters registered)
> **Produces:** Real ATS response fixtures, parser contract tests, CLI quarantine/health commands, updated project status
> **Spec sections:** 8.4-8.6, 9.1-9.3

---

### Task 26: Capture Real Fixtures

> **Workday Fixture Note:** Workday XHR fixtures require a browser session to capture because Workday's `/wday/cxs/` endpoint uses session cookies and CSRF tokens that are set by their JavaScript. You cannot simply `httpx.get()` the endpoint. Instead, use Nodriver or a manual browser session:
> 1. Navigate to the Workday career page in a browser
> 2. Open DevTools Network tab, filter by XHR
> 3. Find the POST to `/wday/cxs/{tenant}/{section}/jobs`
> 4. Copy the response JSON and save as `tests/fixtures/workday/microsoft_xhr.json`
>
> Alternatively, use the WorkdayScraper itself to make the authenticated request and dump the response.

- [ ] **Step 1: Capture Greenhouse fixture**

```bash
cd D:/jobradar-v2/backend
python -c "
import httpx, json, asyncio
async def fetch():
    async with httpx.AsyncClient() as c:
        r = await c.get('https://boards-api.greenhouse.io/v1/boards/huggingface/jobs')
        with open('tests/fixtures/greenhouse/huggingface_board.json', 'w') as f:
            json.dump(r.json(), f, indent=2)
        print(f'Saved {len(r.json().get(\"jobs\", []))} jobs')
asyncio.run(fetch())
"
```

- [ ] **Step 2: Capture Lever fixture**

```bash
python -c "
import httpx, json, asyncio
async def fetch():
    async with httpx.AsyncClient() as c:
        r = await c.get('https://api.lever.co/v0/postings/stripe?mode=json')
        with open('tests/fixtures/lever/stripe_postings.json', 'w') as f:
            json.dump(r.json(), f, indent=2)
        print(f'Saved {len(r.json())} postings')
asyncio.run(fetch())
"
```

- [ ] **Step 3: Capture Ashby fixture**

Fetch from `https://jobs.ashbyhq.com/api/non-user-graphql` with Ramp's org slug.

- [ ] **Step 4: Capture Workday fixture**

Use a browser-based approach (see note above) to capture the XHR response from Microsoft's Workday career page. Save as `tests/fixtures/workday/microsoft_xhr.json`.

- [ ] **Step 5: Save expected outputs alongside each fixture**

For each fixture, run the parser and save the expected output as `expected_jobs.json`.

- [ ] **Step 6: Commit fixtures**

```bash
git add tests/fixtures/
git commit -m "test: add real ATS response fixtures for parser testing"
```

---

### Task 27: Write Parser Contract Tests

**Files:**
- Create: `backend/tests/contracts/test_greenhouse_contract.py`
- Create: `backend/tests/contracts/test_lever_contract.py`
- Create: `backend/tests/contracts/test_workday_contract.py`

- [ ] **Step 1: Write contract tests**

Each contract test:
- Loads a fixture
- Runs the parser
- Asserts every ScrapedJob has: title, company_name, source, source_url
- Asserts no invalid enums
- Asserts salary_min <= salary_max when both present
- Asserts no malformed URLs

- [ ] **Step 2: Run contract tests**

```bash
python -m pytest tests/contracts/ -v
```

- [ ] **Step 3: Commit**

```bash
git commit -m "test: add parser contract tests for ATS scrapers"
```

---

### Task 28: Complete CLI Quarantine and Health Commands

**Files:**
- Modify: `backend/app/scraping/ops.py`

- [ ] **Step 1: Add quarantine commands**

```python
@quarantine_app.command("list")
def quarantine_list():
    """Show all quarantined targets with failure reasons."""

@quarantine_app.command("review")
def quarantine_review(target_id: str):
    """Show last 5 attempts and failure traces for a target."""

@quarantine_app.command("release")
def quarantine_release(target_id: str, force_tier: int = typer.Option(None)):
    """Un-quarantine and reset failure count."""
```

- [ ] **Step 2: Add health and test commands**

```python
@app.command("health")
def health_cmd():
    """Show per-source success rates and circuit breaker states."""

@app.command("test-fetch")
def test_fetch(url: str, tier: int = typer.Option(None), dry_run: bool = False):
    """Test-scrape a single URL through the full pipeline."""
```

- [ ] **Step 3: Commit**

```bash
git commit -m "feat: complete CLI with quarantine, health, and test commands"
```

---

### Task 29: Update PROJECT_STATUS.md

- [ ] **Step 1: Update project status doc**

Mark completed:
- Scraper ecosystem installed and integrated
- 1,473 H1B career pages imported and classified
- Tier router with escalation
- Browser pool with concurrency governance
- Scoring-based scheduler
- CLI ops tool
- Fixture-based parser tests

Update "What To Do Next" to reflect remaining work:
- Fix slow page switching
- Port remaining v1 features
- Wire frontend scraper controls
- End-to-end live testing

- [ ] **Step 2: Commit**

```bash
git commit -m "docs: update project status after scraper platform build"
```

---

## Chunk Status
- [ ] All tasks completed
- [ ] All tests passing
- [ ] Greenhouse, Lever, Ashby fixtures captured
- [ ] Workday fixture captured (browser-based)
- [ ] Contract tests passing for all ATS parsers
- [ ] CLI quarantine commands working
- [ ] CLI health and test-fetch commands working
- [ ] PROJECT_STATUS.md updated

### Notes / Issues Encountered
_Record any deviations from the plan, issues hit, or decisions made during implementation._

| Date | Note |
|------|------|
| | |
