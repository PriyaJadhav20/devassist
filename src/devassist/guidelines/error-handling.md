# Error handling

## Exceptions swallow bare except error handling
Catch the narrowest exception you can handle. A bare except or an empty handler hides bugs; log and re-raise what you cannot recover from.

## Mutable default arguments
Use None as the default and create lists or dicts inside the function so calls do not share state.

## Validate input at boundaries
Validate and normalize external input once, at the edge of the system, and fail with a clear error message.
