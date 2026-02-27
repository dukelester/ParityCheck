# envguard CLI

Environment drift detection for ParityCheck.

## Installation

```bash
pip install envguard
```

Or from source:

```bash
cd cli && pip install -e .s
```

## Quick Start

```bash
envguard collect --env=dev
envguard collect --env=prod
envguard compare --env=prod
envguard report --api-key=YOUR_KEY --env=dev
```

## Commands

### collect

Gather metadata from the current environment.

```bash
envguard collect [--env=dev] [--output=FILE] [--include-secrets]
```

### compare

Compare two cached reports.

```bash
envguard compare [--env=prod] [--baseline=dev]
```

### report

Upload report to ParityCheck SaaS.

```bash
envguard report --api-key=KEY [--env=dev] [--output=FILE]
```

### schedule

Configure scheduled drift checks.

```bash
envguard schedule [--interval=daily] [--notify] [--api-key=KEY]
```

### history

List cached reports.

```bash
envguard history [--env=NAME]
```

## Full Documentation

See [../docs/README.md](../docs/README.md) for the complete CLI reference.
