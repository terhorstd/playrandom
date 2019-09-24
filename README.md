
# playrandom

   This tool is a command-line interface to `mplayer` that uses directories as
   playlists. Media files are played in random order until all files are
   played, then successively the least recent files are released to enable a
   loop in random order.

# Install

   The fastest way to install playrandom is to use your systems tools:

    pip install playrandom


## Requirements

   All python required packages are listed in `environment.yaml`. In case you
   installed playrandom via a package management system like pip, anaconda,
   miniconda, ... all dependencies should already be installed automatically.
   The only "external" dependency is [mplayer](http://www.mplayerhq.hu), which
   is usually installable by your systems package manager (apt, yum, ...).


# Getting Started

   After installation run `playrandom --help` to get a first overview of
   command line options and usage.


# Developing playrandom

   Contributions are very welcome! Write issues for feature requests or
   directly file a pull-request with your contribution and/or contact me
   directly!


## Tests

   This project uses the [PyTest framework](https://docs.pytest.org/en/latest/)
   with tests defined in the [tests/](tests/) sudirectory. It is added into the
   setuptools config, so that it can be run with

    python setup.py test

   This automatically tests a temporarily packaged version.

   Alternatively you can run `pytest` manually with all it [glory
   details](https://docs.pytest.org/en/latest/usage.html).


## Releases

   The release workflow is mostly automated and is in the [release/](release/)
   folder.


