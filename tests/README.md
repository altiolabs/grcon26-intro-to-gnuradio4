# Maintainer checks

Run these from the repository root with the installed SDK activated and its
compatible compiler selected. Participant build commands are in the workshop
README; these checks automate verification before a workshop.

```bash
bash tests/validate-demos.sh
```

This builds the examples and OOT, runs CTest and the installed-plugin loader
check, compares two finite graph runs byte for byte, and validates tone gains.
Generated artifacts stay under `.work/`. Set `WORKSHOP_BUILD_JOBS` to change
the default of two compile jobs.

For Studio integration checks, start a dedicated backend in another activated
terminal:

```bash
GR4CP_PORT=18080 gr4cp_server
```

Then run the standalone integration check or include it in the full check:

```bash
python3 tests/check-studio.py http://127.0.0.1:18080
bash tests/validate-demos.sh --studio
```

The integration check creates a session, reads four streams, changes the cutoff
and verifies its effect, then deletes its own session. It requires local TCP
access. Set `STUDIO_URL` for the combined check when using a different backend
port. Python checks use only the standard library.
