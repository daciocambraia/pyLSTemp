# GitHub Upload Checklist

## Before upload

- confirm the repository URL is correct: `https://github.com/daciocambraia/pyLSTemp`
- review `README.md`
- review `pyproject.toml`
- confirm the version number is correct

## After upload

1. check the repository homepage and README rendering
2. open the `Actions` tab and confirm the `CI` workflow runs
3. if you plan to publish on PyPI, add the secret `PYPI_API_TOKEN`
4. create a release tag such as `v0.1.0` when ready to publish

## Local test command

```powershell
$env:PYTHONPATH="C:\Pyland\pyLSTemp\src"
& "C:\Users\dacio\AppData\Local\Programs\Python\Python313\python.exe" -m pytest
```
