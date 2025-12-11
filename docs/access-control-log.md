# Access control implementation log

- Added a server-side `app_settings` table to persist the optional login switch and hashed passcodes.
- Introduced `/auth/status`, `/auth/settings/login`, and `/auth/login` endpoints to read, toggle, and authenticate against the passcode.
- Wrapped document and schema endpoints with conditional authentication that only enforces a token after the switch is enabled.
- Wired the Next.js UI with an "Access control" card so admins can enter the passcode twice, enable/disable the lock, and handle login prompts.
- Updated documentation (README, comprehensive guide, operations manual) to explain the default-off behavior, how to enable, and how to recover if locked out.
- Left UI hooks to surface 401 responses as a cue to re-authenticate while keeping uploads and listings disabled until unlocked.
