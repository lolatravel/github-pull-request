# github-pull-request

CLI tool to manage GitHub PRs


# Installation

If you don't use `pipsi`, you're missing out.
Here are [installation instructions](https://github.com/mitsuhiko/pipsi#readme).

Simply run:

    $ pipsi install github-pull-request

Otherwise with pip:

    $ pip install github-pull-request

# Setup
You must setup a github access token in order to be able to get or merge pull
requests. To set one up:

  - Got to *GitHub* -> *Settings*
  - Click on *Personal Access Tokens*
  - Click on *Generate new token*
  - Select *repo* access, this should allow both listing and merging
  - Copy the token and use type this into your shell `export GITHUB_ACCESS_TOKEN=[your token]`
  - For best results, put the line above in your `.bashrc` file

# Usage
To use it:

    $ git pr ls   # or 
    $ git pr -h   # for more options

