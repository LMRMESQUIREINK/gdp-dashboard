import { expect, test } from 'claude-code/testing'

import { destructiveReason } from './rules'

test('rm -rf is flagged', () => {
  expect(destructiveReason('rm -rf /tmp/scratch')).toContain('rm -rf')
})

test('rm -fr (flags reversed) is flagged', () => {
  expect(destructiveReason('rm -fr build/')).toContain('rm -rf')
})

test('rm --recursive --force is flagged', () => {
  expect(destructiveReason('rm --recursive --force node_modules')).toContain('rm -rf')
})

test('rm with a wildcard is flagged', () => {
  expect(destructiveReason('rm *.log')).toContain('wildcard')
})

test('a plain rm of one named file is not flagged', () => {
  expect(destructiveReason('rm notes.txt')).toBeNull()
})

test('git push --force is flagged', () => {
  expect(destructiveReason('git push --force origin main')).toContain('force-pushes')
})

test('git push -f is flagged', () => {
  expect(destructiveReason('git push -f origin main')).toContain('force-pushes')
})

test('git push --force-with-lease is flagged', () => {
  expect(destructiveReason('git push --force-with-lease origin main')).toContain('force-pushes')
})

test('an ordinary git push is not flagged', () => {
  expect(destructiveReason('git push origin main')).toBeNull()
})

test('git reset --hard is flagged', () => {
  expect(destructiveReason('git reset --hard origin/main')).toContain('reset')
})

test('git reset --soft is not flagged', () => {
  expect(destructiveReason('git reset --soft HEAD~1')).toBeNull()
})

test('git clean -fd is flagged', () => {
  expect(destructiveReason('git clean -fd')).toContain('untracked')
})

test('git branch -D is flagged', () => {
  expect(destructiveReason('git branch -D feature/old')).toContain('branch')
})

test('git branch -d (safe delete) is not flagged', () => {
  expect(destructiveReason('git branch -d feature/merged')).toBeNull()
})

test('git checkout -- . is flagged', () => {
  expect(destructiveReason('git checkout -- .')).toContain('discards uncommitted changes')
})

test('git checkout of a branch is not flagged', () => {
  expect(destructiveReason('git checkout main')).toBeNull()
})

test('git restore --worktree is flagged', () => {
  expect(destructiveReason('git restore --worktree .')).toContain('discards uncommitted changes')
})

test('a benign multi-command line is not flagged', () => {
  expect(destructiveReason('ls -la && cat package.json | grep version')).toBeNull()
})
