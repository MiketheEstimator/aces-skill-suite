---
name: SKILL_CODE_BASH_GENERAL
description: "Command-line automation artifacts with proper environment shebangs and permissions. Use when producing .sh files for system automation, CI/CD pipelines, build scripts, cron jobs, or deployment scripts. Triggers: 'bash script', 'shell script', '.sh file', 'automate with bash', 'cron job', 'deployment script', 'CI script'."
---

# SKILL_CODE_BASH_GENERAL — Bash/Shell Script Skill

## Quick Reference

| Task | Section |
|------|---------|
| Script template | [Script Template](#script-template) |
| Safety flags | [Safety Flags](#safety-flags) |
| Argument parsing | [Argument Parsing](#argument-parsing) |
| Logging & output | [Logging & Output](#logging--output) |
| Common patterns | [Common Patterns](#common-patterns) |
| Permissions & deployment | [Permissions & Deployment](#permissions--deployment) |
| Linting & validation | [Linting & Validation](#linting--validation) |
| QA loop | [Validation & QA](#validation--qa) |

---

## Script Template

### Standard Production Script

```bash
#!/usr/bin/env bash
# =============================================================================
# script_name.sh — Brief description of what this script does.
#
# Usage:
#   ./script_name.sh [OPTIONS] <argument>
#
# Options:
#   -h, --help      Show this help message
#   -v, --verbose   Enable verbose output
#   -n, --dry-run   Preview actions without making changes
#
# Examples:
#   ./script_name.sh --input ./data --output ./results
#   ./script_name.sh --dry-run --verbose
#
# Requirements:
#   - bash >= 4.0
#   - curl, jq (see Dependencies section)
# =============================================================================

set -euo pipefail
IFS=$'\n\t'

# =============================================================================
# CONSTANTS
# =============================================================================
readonly SCRIPT_NAME="$(basename "${BASH_SOURCE[0]}")"
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly LOG_FILE="${SCRIPT_DIR}/logs/${SCRIPT_NAME%.sh}.log"
readonly TIMESTAMP="$(date +%Y%m%d_%H%M%S)"

# =============================================================================
# DEFAULTS
# =============================================================================
VERBOSE=false
DRY_RUN=false
INPUT_DIR=""
OUTPUT_DIR="${SCRIPT_DIR}/output"

# =============================================================================
# LOGGING
# =============================================================================
mkdir -p "$(dirname "${LOG_FILE}")"

log_info()    { echo "[$(date +%H:%M:%S)] [INFO]  $*" | tee -a "${LOG_FILE}"; }
log_debug()   { ${VERBOSE} && echo "[$(date +%H:%M:%S)] [DEBUG] $*" | tee -a "${LOG_FILE}" || true; }
log_warn()    { echo "[$(date +%H:%M:%S)] [WARN]  $*" | tee -a "${LOG_FILE}" >&2; }
log_error()   { echo "[$(date +%H:%M:%S)] [ERROR] $*" | tee -a "${LOG_FILE}" >&2; }
log_success() { echo "[$(date +%H:%M:%S)] [OK]    $*" | tee -a "${LOG_FILE}"; }

# =============================================================================
# USAGE
# =============================================================================
usage() {
  grep '^#' "${BASH_SOURCE[0]}" | grep -v '#!/' | sed 's/^# \?//'
  exit 0
}

# =============================================================================
# ARGUMENT PARSING
# =============================================================================
parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      -h|--help)     usage ;;
      -v|--verbose)  VERBOSE=true; shift ;;
      -n|--dry-run)  DRY_RUN=true; shift ;;
      --input)       INPUT_DIR="$2"; shift 2 ;;
      --output)      OUTPUT_DIR="$2"; shift 2 ;;
      --)            shift; break ;;
      -*)            log_error "Unknown option: $1"; exit 1 ;;
      *)             break ;;
    esac
  done
}

# =============================================================================
# VALIDATION
# =============================================================================
validate() {
  local errors=0

  if [[ -z "${INPUT_DIR}" ]]; then
    log_error "--input is required"
    (( errors++ ))
  elif [[ ! -d "${INPUT_DIR}" ]]; then
    log_error "Input directory not found: ${INPUT_DIR}"
    (( errors++ ))
  fi

  if (( errors > 0 )); then
    log_error "Validation failed. Run with --help for usage."
    exit 1
  fi

  mkdir -p "${OUTPUT_DIR}"
}

# =============================================================================
# CORE LOGIC
# =============================================================================
process() {
  local input_dir="$1"
  local output_dir="$2"
  local count=0

  log_info "Processing files in: ${input_dir}"

  while IFS= read -r -d '' file; do
    log_debug "Processing: ${file}"

    if ${DRY_RUN}; then
      log_info "[DRY-RUN] Would process: ${file}"
    else
      # TODO: implement processing
      (( count++ ))
    fi

  done < <(find "${input_dir}" -type f -name "*.txt" -print0)

  log_success "Processed ${count} files → ${output_dir}"
  return 0
}

# =============================================================================
# CLEANUP
# =============================================================================
cleanup() {
  local exit_code=$?
  log_debug "Cleanup on exit (code: ${exit_code})"
  # Remove temp files, release locks, etc.
  exit "${exit_code}"
}
trap cleanup EXIT
trap 'log_error "Script interrupted"; exit 130' INT TERM

# =============================================================================
# MAIN
# =============================================================================
main() {
  parse_args "$@"
  log_info "=== ${SCRIPT_NAME} started (${TIMESTAMP}) ==="
  ${DRY_RUN} && log_warn "DRY-RUN mode enabled — no changes will be made"

  validate
  process "${INPUT_DIR}" "${OUTPUT_DIR}"

  log_info "=== ${SCRIPT_NAME} completed ==="
}

main "$@"
```

---

## Safety Flags

```bash
# Always include at the top of every script
set -euo pipefail

# What each flag does:
# -e   Exit immediately if any command returns non-zero
# -u   Treat unset variables as errors (prevents silent bugs)
# -o pipefail   Pipeline fails if ANY command in it fails
#               (without this: false | true exits 0)

# Additional: safer word splitting and globbing
IFS=$'\n\t'    # split on newlines and tabs only, not spaces
```

### When to Temporarily Disable

```bash
# Check if command succeeds without exiting on failure
set +e
command_that_might_fail
exit_code=$?
set -e

# Or use conditional
if command_that_might_fail; then
  echo "Succeeded"
else
  echo "Failed with $?"
fi

# Check if variable is set without -u crashing
if [[ -z "${OPTIONAL_VAR:-}" ]]; then
  echo "Not set"
fi
```

---

## Argument Parsing

### Simple Positional Arguments

```bash
#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "Usage: $0 <source> <destination>"
  exit 1
fi

SOURCE="$1"
DEST="$2"
```

### getopts (POSIX — short flags only)

```bash
VERBOSE=false
OUTPUT=""

while getopts ":vo:" opt; do
  case ${opt} in
    v) VERBOSE=true ;;
    o) OUTPUT="${OPTARG}" ;;
    :) echo "Option -${OPTARG} requires an argument"; exit 1 ;;
    \?) echo "Unknown option: -${OPTARG}"; exit 1 ;;
  esac
done

shift $(( OPTIND - 1 ))
# Remaining positional args now in "$@"
```

### Long Flags Pattern (bash, no getopt)

```bash
while [[ $# -gt 0 ]]; do
  case "$1" in
    --file)    FILE="$2";    shift 2 ;;
    --verbose) VERBOSE=true; shift   ;;
    --dry-run) DRY_RUN=true; shift   ;;
    --)        shift; break          ;;
    -*)        echo "Unknown: $1"; exit 1 ;;
    *)         POSITIONAL+=("$1"); shift ;;
  esac
done
```

---

## Logging & Output

```bash
# Colour codes (terminal output only)
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'   # No Colour

# Check if terminal supports colour before using
if [[ -t 1 ]]; then
  log_ok()   { echo -e "${GREEN}[OK]${NC}    $*"; }
  log_fail() { echo -e "${RED}[FAIL]${NC}  $*" >&2; }
  log_warn() { echo -e "${YELLOW}[WARN]${NC}  $*" >&2; }
else
  # No colour for pipes/files
  log_ok()   { echo "[OK]    $*"; }
  log_fail() { echo "[FAIL]  $*" >&2; }
  log_warn() { echo "[WARN]  $*" >&2; }
fi

# Redirect all output to log file AND terminal
exec > >(tee -a "${LOG_FILE}") 2>&1
```

---

## Common Patterns

### Safe File Operations

```bash
# Check before acting
[[ -f "$file" ]] || { log_error "File not found: $file"; exit 1; }
[[ -d "$dir"  ]] || mkdir -p "$dir"
[[ -r "$file" ]] || { log_error "File not readable: $file"; exit 1; }

# Atomic write via temp file
tmp="$(mktemp)"
generate_content > "$tmp"
mv "$tmp" "${OUTPUT_FILE}"    # atomic on same filesystem

# Secure temp directory
tmpdir="$(mktemp -d)"
trap 'rm -rf "${tmpdir}"' EXIT
```

### Loop Patterns

```bash
# Safe file loop (handles spaces in filenames)
while IFS= read -r -d '' file; do
  echo "Processing: $file"
done < <(find . -name "*.log" -print0)

# Loop over array
declare -a FILES=("file1.txt" "file2.txt" "file3.txt")
for file in "${FILES[@]}"; do
  echo "$file"
done

# Loop with index
for i in "${!FILES[@]}"; do
  echo "$i: ${FILES[$i]}"
done
```

### Checking Dependencies

```bash
check_dependencies() {
  local deps=("$@")
  local missing=()

  for dep in "${deps[@]}"; do
    if ! command -v "$dep" &>/dev/null; then
      missing+=("$dep")
    fi
  done

  if [[ ${#missing[@]} -gt 0 ]]; then
    log_error "Missing required tools: ${missing[*]}"
    log_error "Install with: sudo apt install ${missing[*]}"
    exit 1
  fi
}

# Usage
check_dependencies curl jq python3 git
```

### Retry Logic

```bash
retry() {
  local max_attempts="$1"
  local delay="$2"
  shift 2
  local attempt=1

  while (( attempt <= max_attempts )); do
    if "$@"; then
      return 0
    fi
    log_warn "Attempt ${attempt}/${max_attempts} failed. Retrying in ${delay}s..."
    sleep "$delay"
    (( attempt++ ))
  done

  log_error "All ${max_attempts} attempts failed: $*"
  return 1
}

# Usage
retry 3 5 curl -fsSL "https://api.example.com/data" -o output.json
```

### Lock File (prevent concurrent runs)

```bash
LOCK_FILE="/tmp/${SCRIPT_NAME}.lock"

acquire_lock() {
  if [[ -f "${LOCK_FILE}" ]]; then
    local pid
    pid="$(cat "${LOCK_FILE}")"
    if kill -0 "$pid" 2>/dev/null; then
      log_error "Script already running (PID ${pid}). Exiting."
      exit 1
    fi
    log_warn "Stale lock file found. Removing."
    rm -f "${LOCK_FILE}"
  fi
  echo $$ > "${LOCK_FILE}"
  trap 'rm -f "${LOCK_FILE}"' EXIT
}

acquire_lock
```

---

## Permissions & Deployment

```bash
# Make executable
chmod +x script.sh

# Set in one step (create and make executable)
install -m 755 script.sh /usr/local/bin/script

# Verify shebang resolves correctly
head -1 script.sh            # should show: #!/usr/bin/env bash
which bash                   # verify bash location

# Test as different user
sudo -u deploy ./script.sh

# Check script syntax without running
bash -n script.sh            # syntax check only

# Trace execution (debug)
bash -x script.sh            # print each command before executing
```

---

## Linting & Validation

```bash
# Install shellcheck (static analyser)
sudo apt install shellcheck      # Linux
brew install shellcheck          # macOS
scoop install shellcheck         # Windows

# Lint script
shellcheck script.sh

# Lint with severity filter
shellcheck --severity=warning script.sh

# Lint all scripts in project
find . -name "*.sh" -exec shellcheck {} +

# shfmt — formatter
go install mvdan.cc/sh/v3/cmd/shfmt@latest
# or: brew install shfmt

shfmt -i 2 -ci script.sh        # format with 2-space indent
shfmt -w script.sh               # write in place
shfmt -d script.sh               # diff mode
```

---

## Validation & QA

```bash
# Syntax check
bash -n script.sh
# Pass: no output

# Shellcheck
shellcheck script.sh
# Pass: no output

# Format check
shfmt -d script.sh
# Pass: no diff output

# Smoke test
./script.sh --help

# Dry-run test
./script.sh --dry-run --verbose --input ./test_data
```

### QA Checklist

- [ ] Shebang is `#!/usr/bin/env bash`
- [ ] `set -euo pipefail` present immediately after shebang
- [ ] Script has usage/help text
- [ ] All variables quoted: `"${VAR}"` not `$VAR`
- [ ] `readonly` used for constants
- [ ] `trap` handles cleanup on EXIT, INT, TERM
- [ ] All dependencies checked with `command -v`
- [ ] No hardcoded paths (use `SCRIPT_DIR` relative references)
- [ ] Temp files cleaned up
- [ ] `shellcheck` passes with zero warnings
- [ ] Script runs successfully with `--dry-run`
- [ ] Script executable: `chmod +x script.sh`

### QA Loop

1. Write script
2. `bash -n script.sh` — syntax check
3. `shellcheck script.sh` — fix all warnings
4. `shfmt -d script.sh` — format
5. `./script.sh --help` — smoke test
6. `./script.sh --dry-run` — dry run
7. Full run with test data
8. **Do not deploy until shellcheck passes and dry-run succeeds**

---

## Common Issues & Fixes

| Issue | Cause | Fix |
|-------|-------|-----|
| `unbound variable` | `-u` flag + unset var | Use `${VAR:-default}` or check before use |
| `command not found` in cron | PATH not set | Add `PATH=/usr/local/bin:/usr/bin:/bin` at top |
| Works interactively, fails in CI | Different shell or environment | Test with `env -i bash script.sh` |
| Spaces in filename break loop | Word splitting | Use `find ... -print0` + `read -r -d ''` |
| Pipe fails silently | Missing `-o pipefail` | Add `set -o pipefail` |
| `[` vs `[[` confusion | `[` is POSIX, `[[` is bash | Always use `[[` in bash scripts |
| Script not executable | Missing `+x` bit | `chmod +x script.sh` |

---

## Dependencies

```bash
# Static analysis (required for QA)
sudo apt install shellcheck

# Formatter
brew install shfmt           # macOS
# or download binary: https://github.com/mvdan/sh/releases

# Common external tools scripts may call
sudo apt install curl jq bc parallel
```
