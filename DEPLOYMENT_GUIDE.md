# Deployment Guide - Meter Consumption Prediction

## Quick Start

### Prerequisites
- GitHub repository with admin access
- Docker & Docker Compose
- GitHub Actions enabled
- Container registry access (ghcr.io)

---

## 1. Initial Setup

### Step 1: Enable GitHub Actions
```bash
# Repository Settings → Actions → Enable
```

### Step 2: Create GitHub Secrets
Navigate to: **Settings → Secrets and variables → Actions**

Add these secrets:
```yaml
SLACK_WEBHOOK_URL:
  Description: Slack webhook for notifications
  Value: https://hooks.slack.com/services/YOUR/WEBHOOK/URL
  (Optional - leave empty to skip Slack notifications)

REGISTRY_USERNAME:
  Description: Container registry username
  Value: your-github-username

REGISTRY_PASSWORD:
  Description: GitHub Container Registry token
  Value: ghp_xxxxxxxxxxxxxxxxxxxx
  (Generate at: https://github.com/settings/tokens)
```

### Step 3: Configure Branches
Ensure branches are protected:
- **main**: Require pull request reviews, status checks
- **develop**: Require status checks

---

## 2. CI/CD Pipeline Workflow

### Automatic Triggers

**On Push to Main:**
```
push → Code Quality → Security → Tests → Build → Deploy to Prod
```

**On Push to Develop:**
```
push → Code Quality → Security → Tests → Build → Deploy to Staging
```

**On Pull Request:**
```
PR → Code Quality → Security → Tests → Build (no deploy)
```

**Weekly Schedule:**
```
Sunday 2 AM → Full pipeline run (regression testing)
```

---

## 3. Local Development Workflow

### Before Committing

```bash
# 1. Run all checks locally
black src/
isort src/
flake8 src/
pylint src/

# 2. Run security scan
bandit -r src/
safety check

# 3. Run tests
pytest tests/ -v --cov=src

# 4. Build Docker image (optional)
docker build -f docker/airflow/Dockerfile -t airflow:test .
```

### Git Workflow

```bash
# 1. Create feature branch
git checkout -b feature/your-feature

# 2. Make changes
# ... edit files ...

# 3. Commit with message
git add .
git commit -m "feat: add new feature"

# 4. Push to GitHub
git push origin feature/your-feature

# 5. Create Pull Request
# → GitHub will run CI/CD checks
# → Wait for all checks to pass
# → Request review

# 6. Merge after approval
# → Merge to develop (for staging)
# → Or merge to main (for production)
```

---

## 4. Monitoring Deployments

### GitHub Actions Dashboard

**View Pipeline Status:**
```
Repository → Actions → Select workflow run
```

**Monitor Stages:**
- ✅ Code Quality (Pass/Fail)
- ✅ Security Scan (Pass/Fail)
- ✅ Unit Tests (Pass/Fail)
- ✅ Docker Build (Pass/Fail)
- ✅ Deployment (Pass/Fail)

### View Logs

```bash
# Download artifacts
Actions → Run → Download artifacts

# View live logs
Actions → Run → Click stage
```

### Test Results

**Coverage Report:**
```
Actions → Run → Artifacts → htmlcov/index.html
```

**Test Details:**
```
Actions → Run → Test Results → See all tests
```

---

## 5. Deployment Strategies

### Staging Deployment (Develop Branch)

**Trigger:** `push to develop`

**Process:**
1. All tests pass
2. Docker images built & pushed
3. Staging environment updated
4. Smoke tests run
5. Ready for manual approval

**Access Staging:**
```
Airflow:  http://staging.example.com:38081
MLflow:   http://staging.example.com:5500
API:      http://staging.example.com:5501
```

### Production Deployment (Main Branch)

**Trigger:** `push to main` (requires all tests pass on develop first)

**Process:**
1. All tests pass
2. Docker images built & pushed
3. Blue-green deployment
4. Health checks
5. Traffic gradually shifted
6. Monitoring active

**Access Production:**
```
Airflow:  http://prod.example.com:38081
MLflow:   http://prod.example.com:5500
API:      http://prod.example.com:5501
```

### Rollback Procedure

**If Production Fails:**

```bash
# 1. Identify previous working version
git log --oneline | head -20

# 2. Create rollback branch
git checkout main
git revert <commit-hash>
git push origin main

# 3. Pipeline automatically deploys rollback
# 4. Monitor status in Actions
```

---

## 6. Pipeline Stages Explained

### Stage 1: Code Quality (5 min)
```
✓ Black: Ensure consistent formatting
✓ isort: Sort imports correctly
✓ Flake8: Check PEP8 compliance
✓ Pylint: Analyze code quality (≥7.0 required)
```

**Fix Issues:**
```bash
black src/
isort src/
pylint src/ --fix
```

### Stage 2: Security (5 min)
```
✓ Bandit: Find hardcoded secrets
✓ Safety: Check for known CVEs
```

**Review Reports:**
```
Actions → Run → Artifacts → security-reports
```

### Stage 3: Unit Tests (10 min)
```
✓ Run all tests in tests/ directory
✓ Generate coverage report
✓ Upload to codecov.io
```

**Run Locally:**
```bash
pytest tests/ -v --cov=src --cov-report=html
open htmlcov/index.html
```

### Stage 4: Build Images (15 min)
```
✓ Build 3 Docker images (Airflow, MLflow, API)
✓ Run security scan on images
✓ Push to GitHub Container Registry
```

**Images Created:**
```
ghcr.io/org/repo-airflow:latest
ghcr.io/org/repo-mlflow:latest
ghcr.io/org/repo-api:latest
```

### Stage 5: Data Validation (2 min)
```
✓ Verify data files exist
✓ Check schema validity
✓ Validate data types
```

### Stage 6: Integration Tests (5 min)
```
✓ Test data pipeline
✓ Test training pipeline
✓ Test inference pipeline
✓ Test API schema
```

### Stage 7: Performance (3 min)
```
✓ Model loading: < 1s
✓ Single prediction: < 5ms
✓ Batch prediction: < 500ms
✓ API response: < 100ms
```

### Stage 8: Deploy Staging (5 min)
```
✓ Update staging environment
✓ Run smoke tests
✓ Health checks pass
```

### Stage 9: Deploy Production (10 min)
```
✓ Blue-green deployment
✓ Health checks
✓ Traffic shift
✓ Monitoring enabled
```

### Stage 10: Notifications (1 min)
```
✓ Send Slack message
✓ Upload test artifacts
✓ Create GitHub deployment
```

---

## 7. Troubleshooting

### Test Failure

**Symptoms:** Red X on GitHub

**Solution:**
```bash
# 1. Check error in GitHub Actions log
# 2. Reproduce locally
pytest tests/ -v

# 3. Fix issue
# ... edit files ...

# 4. Commit & push
git add .
git commit -m "fix: resolve test failure"
git push origin feature/name
```

### Build Failure

**Symptoms:** Docker build fails

**Solution:**
```bash
# 1. Build locally
docker build -f docker/airflow/Dockerfile .

# 2. Fix Dockerfile issues
# 3. Test again
# 4. Commit & push
```

### Deployment Failure

**Symptoms:** Staging/Production deployment fails

**Solution:**
```bash
# 1. Check logs in Actions
# 2. Verify environment variables
# 3. Check database connectivity
# 4. Rollback if needed
git revert <commit-hash>
git push origin main
```

### Performance Failure

**Symptoms:** Benchmarks fail

**Solution:**
```bash
# 1. Profile locally
pytest tests/test_performance.py -v

# 2. Optimize code
# ... optimize critical paths ...

# 3. Verify improvements locally
# 4. Commit & push
```

---

## 8. Best Practices

### ✅ Do's

- ✓ Create feature branches for all changes
- ✓ Write tests for new code
- ✓ Run local checks before pushing
- ✓ Write clear commit messages
- ✓ Request code review before merge
- ✓ Keep commits focused and small
- ✓ Monitor CI/CD pipeline status

### ❌ Don'ts

- ✗ Commit directly to main/develop
- ✗ Push without running tests locally
- ✗ Ignore failing pipeline
- ✗ Force push to protected branches
- ✗ Commit secrets or credentials
- ✗ Mix multiple features in one PR
- ✗ Merge without approval

---

## 9. Monitoring in Production

### Metrics to Track

```
✓ Pipeline success rate (target: 99%)
✓ Test coverage (target: 80%+)
✓ Deployment frequency (weekly)
✓ Lead time (< 30 min from commit to deploy)
✓ MTTR: Mean Time to Recovery (< 10 min)
```

### Alerts

```
❌ Pipeline fails → Immediate notification
❌ Tests fail → Block merge
❌ Security issues → Manual review required
⚠️  Coverage drops → Warning
```

---

## 10. Advanced Configuration

### Custom Environment Variables

**Add to GitHub Secrets:**
```
AIRFLOW_ENV=production
MLFLOW_URL=https://mlflow.prod.example.com
DATABASE_URL=postgresql://...
```

**Use in Workflow:**
```yaml
env:
  AIRFLOW_ENV: ${{ secrets.AIRFLOW_ENV }}
  MLFLOW_URL: ${{ secrets.MLFLOW_URL }}
```

### Conditional Deployments

**Deploy only on main:**
```yaml
if: github.ref == 'refs/heads/main'
```

**Deploy only for specific tags:**
```yaml
if: startsWith(github.ref, 'refs/tags/v')
```

### Matrix Builds

**Test multiple Python versions:**
```yaml
strategy:
  matrix:
    python-version: [3.8, 3.9, '3.10']
```

---

## 11. Maintenance Schedule

### Weekly
- Review pipeline logs
- Check test coverage trends
- Update dependencies (if needed)

### Monthly
- Security audit
- Performance review
- Optimize slow tests

### Quarterly
- Full system assessment
- Update CI/CD best practices
- Team training

---

## Support & Resources

- GitHub Actions Docs: https://docs.github.com/en/actions
- Docker Docs: https://docs.docker.com
- Pytest Docs: https://docs.pytest.org
- Security Best Practices: https://owasp.org/Top10

