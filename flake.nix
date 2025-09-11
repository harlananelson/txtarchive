{
  description = "A flake for the txtarchive Python utility";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        # Define the python version to be used throughout the flake
        pythonPackages = pkgs.python3.pkgs;
      in
      {
        packages.default = pythonPackages.buildPythonApplication {
          pname = "txtarchive";
          version = "0.1.0";

          src = self;
          format = "pyproject";

          nativeBuildInputs = with pythonPackages; [
            setuptools
            wheel
            build
            # pip is not strictly necessary here as `build` handles it, but can be kept for compatibility
          ];

          propagatedBuildInputs = with pythonPackages; [
            requests
          ];

          doCheck = false;
          pythonImportsCheck = [ "txtarchive" ];
        };

        devShells.default = pkgs.mkShell {
          name = "txtarchive-dev-shell";

          # CHANGE 1: `inputsFrom` is removed. It's redundant because the shellHook
          # installs the package and its dependencies into the venv anyway.
          # The build tools are already explicitly listed below.

          # Add development tools here.
          nativeBuildInputs = with pythonPackages; [
            uv # Modern and fast venv/package manager
            # CHANGE 2: Corrected package references and removed duplicates.
            # Use `pytest` directly, not `python3.pkgs.pytest`.
            pytest
            black
            # Build dependencies needed for `pip install -e .`
            setuptools
            wheel
            build
          ];

          # This hook runs every time you enter the shell
          shellHook = ''
            # Create/re-use a virtual environment
            if [ ! -d ".venv" ]; then
              echo "Creating Python virtual environment with uv in ./.venv..."
              uv venv .venv --seed
            fi

            # Activate the virtual environment
            source .venv/bin/activate

            echo "Installing dependencies and txtarchive in editable mode..."
            # CHANGE 3: Use `uv pip` for consistency and install from pyproject.toml
            uv pip install -e ".[dev]" # Assumes you have a [project.optional-dependencies] dev group

            echo "✅ Nix shell is ready. Python virtual environment is active."
          '';
        };
      });
}