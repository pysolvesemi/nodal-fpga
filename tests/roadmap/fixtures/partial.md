# Independently authored partial-progress example

Future consumers DB-99 and RTL-99 appear in prose, never in Depends on.

- [ ] FND-01 — Independent bootstrap
  Depends on: none.
  - [ ] FND-01.a Nested implementation
    - [x] FND-01.a.1 First accepted leaf
    - [ ] FND-01.a.2 Remaining leaf
  - [x] FND-01.b A separately complete task
  - [x] FND-01.f Independent review
    - [x] FND-01.f.1 Reviewed own result
  - [ ] FND-01.g Remaining bounded measurement
  - [ ] FND-01.e Final closure
    - [ ] FND-01.e.1 Final evidence

- [ ] FND-02 — Contracts
  Depends on: FND-01.
  Future consumers include FND-08; that reference is not a dependency.
  - [ ] FND-02.a Describe the contracts
  - [ ] FND-02.e Final closure

- [ ] FND-08 — Foundation gate
  Depends on: FND-02.
  - [ ] FND-08.a Replay evidence
  - [ ] FND-08.e Final closure
