"""One exact-candidate, contracts-only documentation dispatcher. It cannot publish, merge or rerun."""
import base64
import hashlib
import json
import os
import time
import urllib.error
import urllib.request

REPO = "pysolvesemi/nodal-fpga"
BRANCH = "closure/fnd-01-evidence"
CONTROL = "ci-control/fnd-01-pr2-fe00d48"
HEAD = "fe00d4861b9dca782fbc05f7965414c1a33f6d30"
TREE = "d1ba20cb819064de8374c6c29809927a55ab89f7"
BASE = "15485fbf1a90c56ecc574d18e389e9c65de86347"
WORKFLOW_ID = 367539769
WORKFLOW_PATH = ".github/workflows/fnd-01-bootstrap.yml"
WORKFLOW_BLOB = "a721884b8daa6fa16f7867988a2273fc02288c96"
LANES = ("contracts",)
ACTIVE = {"queued", "in_progress", "pending", "requested", "waiting"}


def log(kind, **fields):
    record = {"kind": kind, "candidate": HEAD, "tree": TREE, **fields}
    line = json.dumps(record, sort_keys=True)
    with open("dispatch-ledger.jsonl", "a") as stream:
        stream.write(line + "\n")
        stream.flush()
        os.fsync(stream.fileno())
    print(line, flush=True)


def request(path, method="GET", payload=None):
    if not path.startswith("/") or path.startswith("//"):
        raise RuntimeError("unexpected API destination")
    if method != "GET":
        if method != "POST" or path != f"/actions/workflows/{WORKFLOW_ID}/dispatches":
            raise RuntimeError("write is outside the single dispatch allowlist")
        if not isinstance(payload, dict) or payload.get("ref") != BRANCH:
            raise RuntimeError("unexpected candidate ref")
        lane = payload.get("inputs", {}).get("lane")
        if lane not in LANES or payload != {"ref": BRANCH, "inputs": {"lane": lane}}:
            raise RuntimeError("unexpected dispatch payload or full-CI request")
    req = urllib.request.Request("https://api.github.com/repos/" + REPO + path,
        data=None if payload is None else json.dumps(payload).encode(), method=method,
        headers={"Authorization": "Bearer " + os.environ["GH_TOKEN"],
                 "Accept": "application/vnd.github+json", "Content-Type": "application/json",
                 "X-GitHub-Api-Version": "2022-11-28"})
    with urllib.request.urlopen(req, timeout=25) as response:
        if method == "POST":
            if response.status != 204:
                raise RuntimeError("dispatch response was not 204")
            return None
        return json.load(response)


def validate(get=request):
    if get("/git/ref/heads/dev")["object"]["sha"] != BASE:
        raise RuntimeError("target moved")
    if get("/git/ref/heads/" + BRANCH)["object"]["sha"] != HEAD:
        raise RuntimeError("candidate moved")
    if get("/git/commits/" + HEAD)["tree"]["sha"] != TREE:
        raise RuntimeError("candidate tree mismatch")
    pr = get("/pulls/2")
    if not (pr["state"] == "open" and pr["draft"] and pr["head"]["sha"] == HEAD
            and pr["head"]["ref"] == BRANCH and pr["base"]["ref"] == "dev" and pr["base"]["sha"] == BASE):
        raise RuntimeError("PR identity/state mismatch")
    anchor = get("/git/trees/31ad3cf3767020c584066d9d133b606ea91b6826?recursive=1")
    current = get("/git/trees/" + TREE + "?recursive=1")
    if anchor["truncated"] or current["truncated"]:
        raise RuntimeError("source comparison was truncated")
    def implementation(data):
        return {f["path"]: (f["sha"], f["mode"]) for f in data["tree"]
                if f["type"] == "blob" and f["path"] != "README.md" and not f["path"].startswith("docs/")}
    if implementation(anchor) != implementation(current):
        raise RuntimeError("documentation closure changed implementation")
    for run_id in (36226115767, 36226119663, 36226124675):
        run = get("/actions/runs/" + str(run_id))
        if not (run["head_sha"] == "c3e2a789db06c90bc1534f0483b100810b4e7a8b"
                and run["workflow_id"] == WORKFLOW_ID and run["conclusion"] == "success"
                and run["event"] == "workflow_dispatch" and run["run_attempt"] == 1):
            raise RuntimeError("qualified implementation anchor mismatch")
    source = get("/contents/" + WORKFLOW_PATH + "?ref=" + HEAD)
    raw = base64.b64decode(source["content"])
    digest = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
    if source["sha"] != WORKFLOW_BLOB or digest != WORKFLOW_BLOB:
        raise RuntimeError("workflow definition mismatch")
    workflow = get(f"/actions/workflows/{WORKFLOW_ID}")
    if workflow["id"] != WORKFLOW_ID or workflow["path"] != WORKFLOW_PATH or workflow["state"] != "active":
        raise RuntimeError("workflow identity/state mismatch")


def inventory():
    result = []
    for page in range(1, 21):
        data = request(f"/actions/runs?head_sha={HEAD}&per_page=100&page={page}")
        result.extend(data["workflow_runs"])
        if len(result) >= data["total_count"]:
            return result
    raise RuntimeError("run inventory exceeded bound")


def existing(runs, lane):
    if lane not in LANES:
        raise RuntimeError("unexpected lane")
    same_workflow = [r for r in runs if r["head_sha"] == HEAD and r["workflow_id"] == WORKFLOW_ID]
    allowed_titles = {f"FND-01 {name} / {HEAD}" for name in LANES}
    if any(r["event"] == "workflow_dispatch" and r["display_title"] not in allowed_titles
           for r in same_workflow):
        raise RuntimeError("unrecognized qualification context; inspect before dispatch")
    if any(r["event"] != "workflow_dispatch" and (r["status"] in ACTIVE or r.get("conclusion") == "success")
           for r in same_workflow):
        raise RuntimeError("retain and inspect existing automatic qualification before dispatch")
    matches = [r for r in same_workflow if r["event"] == "workflow_dispatch"
               and r["display_title"] == f"FND-01 {lane} / {HEAD}"]
    if len(matches) > 1:
        raise RuntimeError("multiple matching runs require reconciliation")
    if not matches:
        return None
    run = matches[0]
    if run["head_branch"] != BRANCH:
        raise RuntimeError("unexpected existing run ref")
    if run["status"] in ACTIVE or (run["status"] == "completed" and run["conclusion"] == "success"):
        return run
    raise RuntimeError("existing unsuccessful run requires diagnosed repair, not blind redispatch")


def observe(lane):
    for _ in range(30):
        try:
            run = existing(inventory(), lane)
        except RuntimeError as exc:
            if str(exc) != "unrecognized qualification context; inspect before dispatch":
                raise
            # GitHub may expose a registered workflow title before rendering run-name.
            # Wait only after one POST; never infer inputs or send another request.
            log("awaiting_run_title", lane=lane)
            time.sleep(2)
            continue
        if run is not None:
            return run
        time.sleep(2)
    raise RuntimeError("dispatch outcome unresolved; do not repeat POST without reconciliation")


def main():
    if (os.environ.get("GITHUB_REPOSITORY") != REPO
        or os.environ.get("GITHUB_REF") != "refs/heads/" + CONTROL
        or os.environ.get("GITHUB_EVENT_NAME") != "push"):
        raise RuntimeError("unexpected controller execution context")
    log("controller_start", controller=os.environ.get("GITHUB_SHA"), workflow_id=WORKFLOW_ID)
    validate()
    before = inventory()
    for lane in LANES:
        current = existing(before, lane)
        log("pre_inventory", lane=lane, workflow_id=WORKFLOW_ID,
            existing_run=None if current is None else current["id"])
    for lane in LANES:
        validate()
        current = existing(inventory(), lane)
        if current:
            log("retained", lane=lane, run_id=current["id"], status=current["status"])
            continue
        payload = {"ref": BRANCH, "inputs": {"lane": lane}}
        log("intent", workflow_id=WORKFLOW_ID, lane=lane, payload=payload)
        try:
            request(f"/actions/workflows/{WORKFLOW_ID}/dispatches", "POST", payload)
            log("accepted", lane=lane)
        except urllib.error.HTTPError as exc:
            log("http_error", lane=lane, status=exc.code, detail=exc.read(2000).decode(errors="replace"))
            # A failed response does not authorize repeating a possibly delivered POST.
            raise
        except Exception as exc:
            log("uncertain_response", lane=lane, error=type(exc).__name__)
            observed = observe(lane)
            log("reconciled", lane=lane, run_id=observed["id"])
            raise RuntimeError("uncertain POST reconciled; inspect before continuing") from exc
        observed = observe(lane)
        log("observed", lane=lane, run_id=observed["id"], event=observed["event"],
            head=observed["head_sha"], branch=observed["head_branch"])
    log("dispatch_complete", qualification=False)


if __name__ == "__main__":
    main()
