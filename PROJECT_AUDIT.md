# Nova Infrastructure Project Audit

## Executive Summary
Comprehensive audit of nova-infra project to identify file purposes, dependencies, and consolidation opportunities.

## Key Questions to Answer
1. **File Purpose**: What does each file do? Is it necessary?
2. **Dependency Tracking**: What depends on each file? Can we create a dependency graph?
3. **Tool Integration**: Are there orphaned tools? How can we "attach" everything to the project?
4. **Consolidation**: Can we simplify and reduce file count?
5. **Structure**: Is everything organized optimally?

## File Inventory Analysis

### Root Level Files (14 files)
- `.gitignore` - **NEEDED**: Git ignore patterns
- `.pre-commit-config.yaml` - **NEEDED**: Pre-commit hooks for quality
- `Makefile` - **NEEDED**: Root orchestration
- `README.md` - **NEEDED**: Project documentation
- `Dockerfile.ci` - **NEEDED**: CI/CD container definition
- `docker-compose.ci.yml` - **NEEDED**: CI container orchestration
- `.claude/settings.local.json` - **QUESTIONABLE**: Claude AI settings (multiple copies)
- `PROJECT.md` - **REDUNDANT?**: Overlaps with README
- `BACKLOG_COMPLETED.md` - **QUESTIONABLE**: Could be in issues/wiki

### GitHub Workflows (7 files)
**All NEEDED but CONSOLIDATABLE**:
- `ci.yml` - General CI pipeline
- `complete-setup.yml` - Full setup workflow
- `ecr-push.yml` - ECR image push
- `terraform-deploy.yml` - Terraform deployment
- `terraform-validate.yml` - Terraform validation
- `terraform.yml` - Terraform operations
- `build-deploy.yml` - **MISSING**: Referenced but not found

**Issue**: Too many overlapping workflows. Could consolidate to 2-3 files.

### Terraform Infrastructure (19 files)
**Structure**: Well-organized with modules
- `terraform/` root files - **NEEDED**: Main configuration
- `terraform/modules/` - **NEEDED**: Modular components (eks, ecr, networking)
- `terraform/bootstrap/` - **NEEDED**: Backend initialization
- `terraform/.terraform/` - **GENERATED**: Should be gitignored

### Application (24 files)
**Structure**: Flask backend + React frontend
- `apps/tf-visualizer/` - Main application
- Multiple docker-compose files - **CONSOLIDATABLE**: dev, local, default
- Frontend build artifacts - **SHOULD BE GITIGNORED**
- Test files - **NEEDED**: Good coverage

### Helm Charts (7 files)
**Structure**: Standard Helm layout
- All files **NEEDED** and properly minimal
- Good separation of concerns

### Scripts (3 files)
- `install-terraform-tools.sh` - **NEEDED**: Tool installation
- `setup.sh` - **NEEDED**: Environment setup
- `validate.sh` - **NEEDED**: Validation script

## Dependency Analysis

### Direct Dependencies (Can Track)
```
Makefile (root)
├── apps/tf-visualizer/Makefile
├── terraform/Makefile
└── scripts/*.sh

GitHub Actions
├── Dockerfile.ci
├── docker-compose.ci.yml
├── terraform/*
├── helm/*
└── apps/tf-visualizer/*

Application
├── backend/*.py → requirements.txt
├── frontend/*.tsx → package.json
└── tests/*.py → pytest
```

### Orphaned/Questionable Files
1. **Multiple .claude/settings.local.json** - 4 copies across dirs
2. **apps/hello-world/** - Old directory referenced in Makefile
3. **PROJECT.md vs README.md** - Redundant documentation
4. **BACKLOG_COMPLETED.md** - Better in GitHub issues

## Tool Integration Strategy

### Current Tools & Integration Status
| Tool | Purpose | Integration | Tracked? |
|------|---------|------------|----------|
| Terraform | Infrastructure | Makefile, GH Actions | ✅ |
| Docker | Containerization | Makefile, compose files | ✅ |
| Helm | K8s deployment | GH Actions | ✅ |
| pytest | Testing | Makefile | ✅ |
| mypy | Type checking | Makefile | ✅ |
| ruff | Python linting | Makefile | ✅ |
| ESLint | JS linting | package.json | ✅ |
| pre-commit | Git hooks | .pre-commit-config.yaml | ✅ |
| tflint | Terraform lint | scripts/install | ⚠️ Partial |
| tfsec | Terraform security | scripts/install | ⚠️ Partial |

### Integration Improvements
1. **Add tflint/tfsec to Makefile targets**
2. **Create dependency graph generator** (Python script using AST)
3. **Add tool manifest file** listing all tools and versions
4. **Use pre-commit for ALL validations**

## Consolidation Opportunities

### 1. GitHub Actions (7→3 files)
```yaml
# Consolidate to:
- ci.yml          # All CI/CD including build, test, deploy
- terraform.yml   # All Terraform operations
- release.yml     # Release management
```

### 2. Docker Compose (3→1 file)
```yaml
# Single file with profiles:
docker-compose.yml
  profiles:
    - dev
    - local
    - ci
```

### 3. Documentation (3→1 file)
```markdown
# Merge into README.md:
- PROJECT.md content
- Move BACKLOG_COMPLETED.md to GitHub wiki/issues
```

### 4. Claude Settings (4→1 file)
Keep only root `.claude/settings.local.json`

### 5. Makefiles
Current structure is good but could add:
- Dependency graph generation target
- Tool version checking target
- Full project audit target

## Dependency Graph Generation

### Proposed Solution
Create `scripts/generate-deps.py`:
```python
# Analyzes:
# - Python imports → call graph
# - JS/TS imports → dependency tree
# - Makefile targets → execution flow
# - Terraform modules → resource graph
# - Docker layers → build dependencies

# Outputs:
# - GraphViz DOT file
# - Mermaid diagram
# - JSON dependency manifest
```

## Action Plan

### Priority 1: Clean Up
- [ ] Remove `apps/hello-world/` references
- [ ] Gitignore frontend build artifacts
- [ ] Consolidate .claude settings
- [ ] Merge PROJECT.md into README.md

### Priority 2: Consolidate
- [ ] Reduce GitHub Actions to 3 files
- [ ] Single docker-compose with profiles
- [ ] Move BACKLOG_COMPLETED to wiki

### Priority 3: Enhance Integration
- [ ] Add dependency graph generator
- [ ] Create tools.json manifest
- [ ] Add Makefile targets for all tools
- [ ] Enhance pre-commit hooks

### Priority 4: Documentation
- [ ] Create architecture diagram
- [ ] Document all Make targets
- [ ] Add tool usage guide

## Answers to Your Questions

### 1. Can every file be attached to the project?
**YES** - Through proper dependency tracking and tooling:
- Make targets for all operations
- Pre-commit hooks for validation
- CI/CD for automated checks
- Dependency graphs for visualization

### 2. Are there independent tools?
**NO** - In a well-integrated project:
- All tools should be invoked via Make/scripts
- All validation in pre-commit
- All deployment in CI/CD
- Nothing should be "floating"

### 3. Can we simplify?
**YES** - Significant consolidation possible:
- 7 GitHub Actions → 3 files
- 3 docker-compose → 1 file
- 4 .claude settings → 1 file
- 2 documentation files → 1 file

### 4. Is Helm minimal?
**YES** - Current Helm setup is properly minimal

### 5. Missing dependency tracking?
**YES** - No current way to visualize:
- Python call graphs
- JS import trees
- Terraform resource dependencies
- Make target flows

## Conclusion

The project is well-structured but has accumulation of redundant files and missing integration points. With the proposed consolidation and dependency tracking, we can reduce file count by ~30% and achieve 100% tool integration.