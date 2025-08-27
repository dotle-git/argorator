---
layout: page
title: Echo Mode (Dry Run)
permalink: /docs/features/echo_mode/
---

# Echo Mode (Dry Run)

Added in 0.4.0

Preview what your script would do without executing any commands. Echo mode rewrites each non-comment command line to an `echo "..."` form that prints the exact command line the script would run after variable expansion, while safely neutralizing pipes and operators.

## Why use it?

- Validate variables and positionals resolved by Argorator
- See the final command lines with values interpolated
- Avoid side effects in pipelines, redirects, and destructive operations

## Usage

### Run with echo mode

```bash
argorator run script.sh --echo [script-args]

# Implicit run also works
argorator script.sh --echo [script-args]
```

### Compile to echo-transformed script

```bash
argorator compile script.sh --echo [script-args]
```

This prints the script with Argorator's injected variable definitions plus every executable line rewritten to `echo "..."`.

## Example

Script:

```bash
#!/bin/bash
echo "Building $SERVICE"
docker build -t "$SERVICE:$TAG" .
kubectl apply -f manifests.yaml | tee deploy.log
```

Run in echo mode:

```bash
argorator run build.sh --service api --tag v1 --echo
```

Output (representative):

```bash
echo "echo \"Building $SERVICE\""
echo "docker build -t \"$SERVICE:$TAG\" ."
echo "kubectl apply -f manifests.yaml | tee deploy.log"
```

Note how pipes and operators are quoted inside the echoed string, so no actual pipeline runs.

## Details and behavior

- Shebang is preserved.
- Argorator's injected variable assignments are preserved so variables expand inside echoed lines.
- Non-empty, non-comment lines become `echo "..."` with double quotes; backslashes and quotes are escaped.
- Original script’s own assignments (not injected) are echoed instead of executed.
- Boolean handling and environment/default resolution are identical to normal mode; only command execution changes.

## Tips

- Use `compile --echo` to inspect the exact transformed script.
- Use `run --echo` to preview with your current environment and arguments.
