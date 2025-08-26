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

## Examples

### Example 1: Required vs optional variables

Create `greet.sh`:

```sh
#!/usr/bin/env argorator

echo "Hello, $NAME!"
echo "City: $CITY"
```

- Without environment variables set, both `$NAME` and `$CITY` are required and must be passed as `--NAME` and `--CITY`.
- If an environment variable exists, it becomes an optional `--VAR` with that default.

Run with env-provided default for `CITY`:

```bash
export CITY=Zurich
argorator greet.sh --NAME Alice
# -> Hello, Alice!
# -> City: Zurich
```

Pass both explicitly:

```bash
argorator greet.sh --NAME Bob --CITY Tokyo
# -> Hello, Bob!
# -> City: Tokyo
```

If you omit a required variable, Argorator will prompt/fail indicating the missing `--VAR`.

### Example 2: Positional arguments (`$1`, `$2`, `$@`)

Create `sum.sh` using positional arguments:

```sh
#!/usr/bin/env argorator

echo "$(($1 + $2))"
```

Invoke with numbers as positional args:

```bash
argorator sum.sh 2 3
# -> 5
```

Create `process.sh` collecting remaining args via `$@`:

```sh
#!/usr/bin/env argorator

echo "Mode: $MODE"
for f in "$@"; do
  echo "Processing $f"
done
```

Run with one option and many files:

```bash
argorator process.sh --MODE fast a.txt b.txt c.txt
# -> Mode: fast
# -> Processing a.txt
# -> Processing b.txt
# -> Processing c.txt
```

### Example 3: Compile a script (show substituted result)

`compile` prints the modified script after applying `--VAR` values and argument handling.

```bash
argorator compile greet.sh --NAME Alice --CITY Zurich
# (prints the compiled shell script to stdout)
```

You can redirect to a file:

```bash
argorator compile greet.sh --NAME Alice --CITY Zurich > greet.compiled.sh
```

### Example 4: Export variables for later use

`export` prints `export VAR=...` lines for the variables Argorator detects.

```bash
argorator export greet.sh --NAME Alice --CITY Zurich
# export NAME=Alice
# export CITY=Zurich
```

This is handy to prime your environment:

```bash
source <(argorator export greet.sh --NAME Alice --CITY Zurich)
```

### Example 5: Shebang + direct execution

Make your script executable and run it directly; Argorator will be invoked via the shebang.

```bash
chmod +x greet.sh
./greet.sh --NAME Dana --CITY Berlin
```

Tips:
- Use `$@` in your scripts to forward all remaining CLI arguments.
- Combine environment defaults with CLI overrides as needed.
