# Packaging

txtarchive is installed from GitHub. It is not published to PyPI.

The version is [semver](https://semver.org). It lives in one place: `__version__` in `txtarchive/_version.py`. `pyproject.toml` and `flake.nix` read that string. The CLI entry point is `txtarchive` (`txtarchive.__main__:main`).

Current version: **0.2.0**.

Updating a project is one version bump in `_version.py`, then a git tag `vX.Y.Z` (for example `v0.2.0`). Downstream pins that tag. Copying the tree into each project is unnecessary.

A breaking CLI change bumps the major version (`1.0.0`, then `2.0.0`).

`setup.py` is retired. It repeated the version and the dependency list. Metadata lives in `pyproject.toml`.

Pin a **tag or a full commit**. A branch moves, so a later install can pick up a breaking CLI change with no version bump.

## Python

```bash
pip install "git+https://github.com/harlananelson/txtarchive@v0.2.0"
```

In another project's `pyproject.toml`:

```toml
dependencies = [
  "txtarchive @ git+https://github.com/harlananelson/txtarchive@v0.2.0",
]
```

A commit pin uses the full SHA in place of `v0.2.0`.

## Nix

`fetchFromGitHub` with `rev` set to the tag. Replace the hash with the one Nix prints on the first build.

```nix
txtarchive = pkgs.python3.pkgs.buildPythonPackage rec {
  pname = "txtarchive";
  version = "0.2.0";
  src = pkgs.fetchFromGitHub {
    owner = "harlananelson";
    repo = "txtarchive";
    rev = "v${version}";
    hash = "sha256-AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=";
  };
  format = "pyproject";
  nativeBuildInputs = [ pkgs.python3.pkgs.setuptools ];
  propagatedBuildInputs = with pkgs.python3.pkgs; [
    requests
    mammoth
    python-docx
    pypandoc
    beautifulsoup4
    pyyaml
  ];
};
```

Or a flake input pinned to the same tag:

```nix
inputs.txtarchive.url = "github:harlananelson/txtarchive/v0.2.0";
```

This repo's `flake.nix` builds the local checkout for development. A consumer pin is a tag or commit.
