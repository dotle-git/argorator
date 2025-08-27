---
title: Iteration Macros
---

Argorator supports comment-based iteration macros that compile into pure Bash loops. They remain valid (and inert) in editors and in raw Bash, but Argorator expands them when running or compiling your script.

### Basic form

Write this in your script:

```bash
# for ITEM in LIST
echo "$ITEM"
# endfor
```

When executed via Argorator, it expands to:

```bash
for ITEM in ${LIST}; do
echo "$ITEM"
done
```

Notes:
- `LIST` is interpreted as a variable; other expressions are used verbatim.
- The loop variable (e.g., `ITEM`) is treated as defined and will not become a CLI argument.
- Indentation is preserved.

### One-line form (no endfor required)

You can omit `# endfor` and have the loop apply only to the next line:

```bash
# for N in NUMS
echo "$N"
echo "done"
```

Expands to:

```bash
for N in ${NUMS}; do
echo "$N"
done
echo "done"
```

### Examples

- Space-separated list via CLI:

```bash
# for F in FILES
cp "$F" /backup
# endfor
```

Run:

```bash
argorator backup.sh --files "a.txt b.txt c.txt"
```

- Glob expression (verbatim):

```bash
# for f in *.log
gzip -9 "$f"
# endfor
``;

- Command substitution (verbatim):

```bash
# for u in "$(jq -r '.urls[]' data.json)"
curl -O "$u"
# endfor
```

### Nested loops

Nesting is supported:

```bash
# for X in XS
  # for Y in YS
  echo "$X,$Y"
  # endfor
# endfor
```

### Compatibility

- Raw Bash: the macro lines are just comments; scripts remain valid.
- Argorator run/compile: macros expand before variable detection and injection.

### Function-call form (multiline bodies as functions)

You can write the body as a function and call it per item:

```bash
process_item() {
  echo "[$1]"
}

# for X in ITEMS -> process_item
echo "after"
```

Expands to:

```bash
for X in ${ITEMS}; do
process_item "$X"
done
echo "after"
```

