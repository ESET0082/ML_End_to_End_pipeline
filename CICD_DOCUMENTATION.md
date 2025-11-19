# CI/CD Pipeline Documentation

## Overview

This CI/CD pipeline automates testing, building, and deployment of the Meter Consumption Prediction ML system.

**Pipeline Stages:**
1. ✅ Code Quality & Linting
2. 🔒 Security Scanning
3. 🧪 Unit Tests
4. 🐳 Docker Image Build
5. 📊 Data Validation
6. 🔗 Integration Tests
7. ⚡ Performance Benchmarks
8. 🚀 Deploy to Staging
9. 🌍 Deploy to Production
10. 📢 Notifications

---

## Pipeline Triggers

### Automatic Triggers
```yaml
# On every push to main or develop
on:
  push:
    branches: [ main, develop ]

# On every pull request
on:
  pull_request:
    branches: [ main, develop ]

# Weekly scheduled run
on:
  schedule:
    - cron: '0 2 * * 0'  # Every Sunday at 2 AM
```

---

## Stage 1: Code Quality & Linting

**Tools Used:**
- **Black**: Code formatting
- **isort**: Import sorting
- **Flake8**: Style guide enforcement
- **Pylint**: Code analysis

**Checks:**
```
✓ Code formatting (Black)
✓ Import ordering (isort)
✓ Style violations (Flake8)
✓ Code quality score (Pylint ≥ 7.0)
```

**Fix Issues Locally:**
```bash
# Format code
black src/

# Sort imports
isort src/

# Check linting
flake8 src/
pylint src/
```

---

## Stage 2: Security Scanning

**Tools Used:**
- **Bandit**: Security issue detection
- **Safety**: Dependency vulnerability scanning

**Checks:**
```
✓ Hardcoded passwords/secrets
✓ SQL injection vulnerabilities
✓ Insecure cryptography
✓ Known CVEs in dependencies
```

**Artifacts Generated:**
- `bandit-report.json` - Security issues
- `safety-report.json` - Dependency vulnerabilities

---

## Stage 3: Unit Tests

**Components Tested:**
- Data ingestion (`src/data/ingestion.py`)
- Feature engineering (`src/data/create_datasets.py`)
- Model training (`src/models/train.py`)
- Model inference (`src/models/inference.py`)
- API endpoints (`src/api/server.py`)

**Coverage Requirements:**
- Minimum 80% code coverage
- All critical paths tested
- Error handling validated

**Run Locally:**
```bash
pytest tests/ -v --cov=src --cov-report=html
```

**Test Database:**
- PostgreSQL 15 (auto-provisioned)
- Isolated test database
- Auto-cleanup after tests

---

## Stage 4: Docker Image Build

**Images Built:**
1. **Airflow** (`docker/airflow/Dockerfile`)
   - DAG orchestration
   - Scheduler & webserver

2. **MLflow** (`docker/mlflow/Dockerfile`)
   - Model tracking server
   - Experiment management

3. **Model API** (`docker/model_api/Dockerfile`)
   - FastAPI server
   - Real-time predictions

**Registry:** GitHub Container Registry (ghcr.io)

**Tagging Strategy:**
```
- Branch: main-latest
- Semver: v1.2.3
- SHA: abc1234567
```

**Build Optimization:**
- Docker layer caching
- Multi-stage builds
- Minimal image sizes

---

## Stage 5: Data Validation

**Validation Rules:**
```
✓ CSV files exist and are readable
✓ Data schema matches expectations
✓ No empty datasets
✓ Data types are correct
✓ Required columns present
```

**Checks:**
- File format validation
- Schema consistency
- Data quality metrics

---

## Stage 6: Integration Tests

**Test Scope:**
- Data pipeline imports
- Training pipeline functionality
- Inference pipeline functionality
- API schema validation
- Cross-component communication

**Example Tests:**
```python
# Data pipeline
from data.create_datasets import load_data, create_features
load_data()  # Should succeed

# Model pipeline
from models.train import train_logistic_regression
train_logistic_regression()  # Should complete

# API schema
from api.server import MeterFeatures
meter = MeterFeatures(...)  # Should validate
```

---

## Stage 7: Performance Benchmarks

**Benchmarks Measured:**
- Model loading time
- Single prediction latency (< 5ms target)
- Feature engineering speed
- API response time (< 100ms target)

**Success Criteria:**
```
✓ Single prediction: < 5ms
✓ Batch predictions (100): < 500ms
✓ Model loading: < 1s
✓ API response: < 100ms
```

---

## Stage 8: Deploy to Staging

**Triggers:**
- Push to `develop` branch

**Actions:**
```
1. ✓ Docker images pushed to registry
2. ✓ Deploy scripts executed
3. ✓ Environment variables configured
4. ✓ Health checks performed
5. ✓ Smoke tests run
```

**Smoke Tests:**
- API endpoints responding
- Database connections healthy
- All services running

**Rollback:**
- Automatic if health checks fail
- Manual rollback available

---

## Stage 9: Deploy to Production

**Triggers:**
- Push to `main` branch
- All tests passed
- Staging deployment successful

**Deployment Strategy: Blue-Green**
```
1. ✓ Verify production readiness
2. ✓ Deploy new version (Green)
3. ✓ Run health checks
4. ✓ Gradually shift traffic
5. ✓ Monitor metrics
6. ✓ Rollback if needed
```

**Production Requirements:**
- All unit tests passing (100%)
- Integration tests successful
- Performance benchmarks met
- Security scan clean
- Code quality score ≥ 8.0

**Monitoring Active:**
- Error rates tracked
- Performance metrics logged
- Alerts configured
- Audit trail maintained

---

## Stage 10: Notifications

**Success Notification:**
```
✅ CI/CD Pipeline Successful
- All checks passed
- Docker images built
- Tests: 95/95 passed
- Coverage: 88%
```

**Failure Notification:**
```
❌ CI/CD Pipeline Failed
- Stage: Unit Tests
- Error: Test timeout
- Log: See GitHub Actions
```

**Channels:**
- Slack (if configured)
- GitHub notifications
- Email (optional)
- Team dashboard

---

## GitHub Secrets Required

Add these secrets to GitHub repository settings:

```
SLACK_WEBHOOK_URL          # For Slack notifications
REGISTRY_USERNAME          # Container registry username
REGISTRY_PASSWORD          # Container registry token
DATABASE_URL               # Test database URL
MLFLOW_TRACKING_URI        # MLflow server URL
```

---

## Pipeline Workflow Diagram

```
┌─────────────────┐
│   Push/PR       │
└────────┬────────┘
         │
    ┌────▼────────────────────────┐
    │  CODE QUALITY & LINTING     │ (5 min)
    │  • Black, isort, Flake8     │
    │  • Pylint check             │
    └────────────────────────────┬┘
         │                        │
    ┌────▼────────┐   ┌─────────▼─────────┐
    │   SECURITY  │   │  UNIT TESTS       │ (10 min)
    │   SCANNING  │   │  • Coverage: 80%+ │
    │ • Bandit    │   │  • Pytest         │
    │ • Safety    │   └───────┬───────────┘
    └────────┬────┘           │
             │                │
         ┌───▼────────────────▼──┐
         │  DATA VALIDATION      │ (2 min)
         │  • Schema checks      │
         └──────────┬────────────┘
                    │
              ┌─────▼──────────────┐
              │ BUILD DOCKER       │ (15 min)
              │ • 3 images         │
              │ • Registry push    │
              └────────┬───────────┘
                       │
            ┌──────────▼──────────┐
            │ INTEGRATION TESTS   │ (5 min)
            │ • Pipeline tests    │
            │ • API validation    │
            └────────┬────────────┘
                     │
            ┌────────▼──────────┐
            │ PERFORMANCE       │ (3 min)
            │ BENCHMARKS        │
            └────────┬──────────┘
                     │
          ┌──────────▼──────────────┐
          │  DEPLOY STAGING        │ (5 min)
          │ (if develop branch)    │
          └──────────┬─────────────┘
                     │
          ┌──────────▼──────────────┐
          │ DEPLOY PRODUCTION      │ (10 min)
          │ (if main branch)       │
          └──────────┬─────────────┘
                     │
          ┌──────────▼──────────────┐
          │ NOTIFICATIONS & REPORTS│
          │ • Slack/Email          │
          │ • Test artifacts       │
          └────────────────────────┘
```

**Total Pipeline Duration:** ~50-60 minutes

---

## Local Testing Before Push

**Run these commands locally to avoid CI failures:**

```bash
# Code quality
black src/
isort src/
flake8 src/

# Security
bandit -r src/
safety check

# Tests
pytest tests/ -v --cov=src

# Docker build (optional)
docker build -f docker/airflow/Dockerfile -t airflow:test .
```

---

## Troubleshooting

### Test Failure
1. Check GitHub Actions logs
2. Review error message
3. Run locally: `pytest tests/ -v`
4. Fix and commit
5. Push to trigger pipeline again

### Performance Degradation
1. Check performance benchmark results
2. Profile code locally
3. Optimize critical paths
4. Verify database connections

### Deployment Failure
1. Check staging deployment first
2. Verify all prerequisites passed
3. Check error logs in Actions
4. Manual rollback if needed

---

## Best Practices

✅ **Commit Guidelines:**
- Run local tests before pushing
- Write meaningful commit messages
- Reference issue numbers

✅ **Pull Requests:**
- Create PR for features
- Wait for all checks to pass
- Request code review
- Merge only after approval

✅ **Branching:**
- `main` = Production ready
- `develop` = Staging/testing
- `feature/*` = New features

✅ **Secrets Management:**
- Never commit secrets
- Use GitHub secrets
- Rotate credentials regularly

---

## Monitoring & Maintenance

**Weekly Review:**
- Check pipeline success rate
- Monitor performance trends
- Review security scan results

**Monthly Maintenance:**
- Update dependencies
- Review test coverage
- Optimize pipeline duration

**Quarterly:**
- Full security audit
- Performance baseline
- Process improvement review

