# Argorator

Execute or compile shell scripts with CLI-exposed variables.

Usage:

```bash
argorator <script> [--VAR value ...] [ARG1 ARG2 ...]
argorator compile <script> [--VAR value ...] [ARG1 ARG2 ...]
argorator export <script> [--VAR value ...] [ARG1 ARG2 ...]
```

- Undefined variables in the script become required `--VAR` options.
- Variables found only in the environment become optional `--VAR` options with defaults.
- `$1`, `$2`, ... become positional arguments; `$@` or `$*` collect remaining args.
- `compile` prints the modified script; `export` prints `export VAR=...` lines; default runs the script.

Shebang:

```sh
#!/usr/bin/env argorator
# your script follows
```
