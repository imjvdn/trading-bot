# Hedge Fund Simulator Release Checklist

## Pre-Release Checks

### Code Quality
- [ ] Run all tests: `python run_tests.py`
- [ ] Run linters: `python run_tests.py --lint-only`
- [ ] Run security checks: `python run_tests.py --security-only`
- [ ] Fix all warnings and errors
- [ ] Update CHANGELOG.md with release notes
- [ ] Update version in pyproject.toml
- [ ] Verify all dependencies are up to date

### Documentation
- [ ] Update README.md with latest features and usage
- [ ] Ensure all public APIs are documented
- [ ] Verify example code in documentation works
- [ ] Update any references to version numbers

### Testing
- [ ] Run integration tests: `python -m pytest tests/integration/ -v`
- [ ] Run performance tests if applicable
- [ ] Test installation in a clean virtual environment
- [ ] Verify all examples work as expected

## Release Process

### Local Testing
1. Create a clean virtual environment
2. Install the package in development mode: `pip install -e .[dev]`
3. Run verification script: `python scripts/verify_installation.py`
4. Verify CLI commands work: `hedgefund-simulator --help`

### Creating the Release
1. Create release branch: `git checkout -b release/vX.Y.Z`
2. Update version in pyproject.toml
3. Update CHANGELOG.md with release date
4. Commit changes: `git commit -am "Prepare for vX.Y.Z release"`
5. Create tag: `git tag -a vX.Y.Z -m "Version X.Y.Z"`
6. Push changes and tags: `git push origin release/vX.Y.Z --tags`

### Package and Publish
1. Build the package: `python -m build`
2. Verify the built package: `twine check dist/*`
3. Upload to TestPyPI: `twine upload --repository testpypi dist/*`
4. Test installation from TestPyPI:
   ```bash
   pip install -i https://test.pypi.org/simple/ hedgefund-simulator==X.Y.Z
   python -c "import hedgefund_simulator; print(hedgefund_simulator.__version__)"
   ```
5. Upload to PyPI: `twine upload dist/*`

### Post-Release
1. Merge release branch into main: `git checkout main && git merge --no-ff release/vX.Y.Z`
2. Push changes: `git push origin main`
3. Create a GitHub release with release notes
4. Close the milestone if using GitHub project management
5. Announce the release to relevant channels

## Verification
- [ ] Verify package installs correctly from PyPI
- [ ] Verify documentation is up to date
- [ ] Verify all tests pass with the released version
- [ ] Update any dependent projects if necessary

## Post-Release Tasks
- [ ] Create a new development version in pyproject.toml
- [ ] Update CHANGELOG.md with [Unreleased] section
- [ ] Create a new milestone for the next release
- [ ] Close any completed issues in the release

## Emergency Rollback Plan
If a critical issue is found after release:
1. Yank the broken version: `twine yank hedgefund-simulator X.Y.Z -r pypi`
2. Create a hotfix branch from the previous version
3. Fix the critical issue
4. Follow the release process for a patch version
5. Document the issue and resolution in the CHANGELOG.md
