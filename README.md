# Autoharmonize
## CS 262 Final Project
### Ari Troper, Liam McInroy, & Max Snyder

# Setup and scripts

All scripts mentioned in this document should be ran in the main directory
(i.e. where you currently are, i.e. [autoharmonize/](./)).

## Module installation

First, you should (preferably) setup a `virtualenv`. This isn't required,
but best practice.

Anyways, once that is configured, then use

```bash
source install.sh
```

to install a local version of the modules in the project; this is just the

```bash
pip install -e ./
```

command.

## Configuring IP

To get the IP address of the host, run

```bash
ipconfig getifaddr en0
```

## Running

To run autoharmonize, execute 

```bash
python -m synfony.main \
    [--machines HOST0:PORT0 HOST1:PORT1 ... HOSTN:PORTN]
    [[--idx i] | [--multiprocess]]
```

- You may omit providing the `machines` field, it will default to
`localhost:10000 localhost:20000 localhost30000`.

- If you are start separate clients, then provide the `idx` flag with `i`
determining the machine's identifier.

- If you use `localhost` addresses, then you can pass the `multiprocess` flag
to start all of the machines on one computer (useful for testing).

If one port doesn't work, try another!

## Linting

To lint the source code, run

```bash
source lint.sh
```

## Testing

To run the tests, run

```bash
source runtest.sh
```

## Documentation

There is some documentation in the [Engineering notebook](notebook.md).
Otherwise, you can view code-level documentation (in `man`), run

```bash
source docs.sh
```

or on [`localhost:1234/synfony`](http://localhost:1234/synfony), run

```bash
souce docshtml.sh
```
