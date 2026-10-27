# Testing expectations

## Tests for behavior changes
Every bug fix and feature ships with a test that fails without the change.

## Test isolation
Tests must not call the network or depend on execution order. Mock external services.
