# Goal/Loop Method

For any build with several moving parts, or anything running mostly
unsupervised (Claude working while you step away). Distinct from the
screenshot-before-done rule in `CLAUDE.md`, which is for verifying
visual builds by eye — this is the general-purpose version for any kind
of multi-step work, visual or not.

## How it works

1. **Write a Goal document first.** A concrete, checkable description
   of what "done" looks like — specific enough that each line can be
   marked true/false against the finished result. Not "the page should
   look good" but "the hero headline is visible above the fold on
   375px-wide viewports."
2. **Loop:** before marking anything complete, check the work against
   the Goal document, line by line.
3. If something doesn't match, fix it and re-check. Repeat until it
   actually passes — don't stop to ask permission each cycle.
4. Only report done once every line in the Goal document is true.

## Copy-paste starter prompt

```
Before starting, write a Goal document for this build: a checklist of
concrete, checkable statements describing what "done" looks like. Then
build it. Before telling me it's finished, go through the Goal document
line by line against the actual result, fix anything that doesn't pass,
and re-check — repeat until every line passes. Then show me the result
along with the checked-off Goal document.
```

## Example Goal document shape

- [ ] Page loads with no console errors
- [ ] Headline and subhead match the approved copy exactly
- [ ] Layout holds at 375px, 768px, and 1440px widths
- [ ] Primary CTA button uses the brand colour from design-rules.md
- [ ] Form submits and shows a visible success state
- [ ] All copy is free of placeholder/lorem ipsum text
