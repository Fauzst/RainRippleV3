# Logs

The pipeline log of the rainrs-server application.

```
logs/
  rainrs.log          rotating log file (5 MB per file, 5 backups)
```

## What is logged

`src/rainrs_server/logging_setup.py` configures a single rotating file
handler for the `rainrs_server` logger. The format is

```
%(asctime)s %(levelname)-8s %(name)s: %(message)s
```

with an ISO 8601 timestamp in the local timezone, for example:

```
2026-10-22T04:02:23-0700 INFO  rainrs_server.process.rungge: derived 1 master key and 3 slave key(s) for image 1
```

Recorded events are metadata only:

- which capture is being processed, and its file name;
- how many ripples were found;
- the outcome of a capture (`processed`, `no_features`, `error`);
- the error message of a failed capture;
- which capture was moved or deleted;
- how many master and slave keys were derived for a capture;
- the detector weights that were loaded.

## What is never logged

- captured images or image content;
- derived ripple features (positions, radii, confidences);
- generated key material (master or slave keys).

Feature values and keys are printed by
`src/rainrs_server/process/dev.py` instead. That development printing
writes to stdout only, is disabled unless `RAINRS_DEV_PRINT=1` or
`--print` is given, and is never written to this log.

## Log level

The level is taken from `RAINRS_LOG_LEVEL` (`DEBUG`, `INFO`, `WARNING`,
`ERROR`, `CRITICAL`); the default is `INFO`. A console handler is not
attached, so the CLI output stays machine readable.

## Rotation and version control

The handler rotates at 5 MB and keeps 5 backups
(`rainrs.log.1` … `rainrs.log.5`). The log files are excluded from
version control by the repository `.gitignore`.
