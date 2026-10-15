# Fences do not introduce status or dependencies

```markdown
- [x] EXAMPLE-01 Never becomes a node
  Depends on: UNKNOWN-99.
  - [ ] EXAMPLE-01.a Must not cause parent inconsistency
```

~~~~markdown
- [~] BAD-01 Not a real checkbox
```markdown
- [x] FND-01 A fake duplicate inside the other delimiter
```
~~~~~

````markdown
- [x] LONG-01 Ignored
```
- [x] LONG-02 A shorter closing candidate cannot close four backticks
~~~~
- [x] LONG-03 A mismatched delimiter cannot close backticks
````not-a-closing-fence
- [x] LONG-04 A closing candidate with trailing text is still content
`````

- [ ] FND-01 — Actual status
  Depends on: none.
  - [ ] FND-01.a Implementation
    ```markdown
    - [x] FND-01 Nested example does not duplicate the real root
    ```
  - [ ] FND-01.e Final closure
