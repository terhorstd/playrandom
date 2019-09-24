
# Release Process

   The current release is configured in `config.yaml`. This is the version that
   will be built.


## Test Release

   To create a test release and upload it to the pypi test server run

    $ snakemake

   Install test version via

    $ pip install --index-url https://test.pypi.org/simple playrandom


## Full Release

   For a full release run

    $ snakemake release

   If you only want to create the package run

    $ snakemake package
