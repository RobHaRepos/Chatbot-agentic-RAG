# Security exceptions and rationale

This repository intentionally excludes certain torch-native vulnerability findings from Snyk scans for the reasons described below.

## Ignored issues (Snyk)

I have added a `.snyk` ignore policy that suppresses specific Torch CVEs reported by Snyk. The reasons:

- Torch is a runtime, heavy, native/compiled dependency (binary wheels). Many of the flagged issues are native memory issues that are:
  - hard for Snyk to map to a pip-upgrade patch, and
  - not exploitable in our CI/static-testing environment because torch is used for optional runtime ML workloads and not executed in CI jobs that run untrusted input.

- I prefer to keep Snyk focused on the application dependencies (frameworks, libraries) rather than runtime ML binaries.
