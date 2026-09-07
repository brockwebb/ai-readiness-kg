Deliberately empty of servable content: this fixture's server RESETS the connection before a
byte of response (`fixtures/server.py::MODES["resets_connection"]`), so no file here is ever
read. The directory exists because git tracks files, not directories, and the fixture must be
addressable by name.

It models what `www150.statcan.gc.ca` did during the 2026-09-07 cycle: 92 observations across
four targets, every one of them recorded as `dns` because the closed set of `error_class` had
no member for a TCP reset. `scan/errors.py` names it now, and this is the control that keeps
the name honest.
