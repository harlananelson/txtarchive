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
        pythonPackages = pkgs.python3.pkgs;
      in
      {
        packages.default = pythonPackages.buildPythonApplication {
          pname = "txtarchive";
          version = "0.1.0";
          src = self;
          format = "pyproject";
          nativeBuildInputs = with pythonPackages; [ setuptools wheel build ];
          propagatedBuildInputs = with pythonPackages; [ requests ];
          doCheck = false;
          pythonImportsCheck = [ "txtarchive" ];
        };

        devShells.default = pkgs.mkShell {
          name = "txtarchive-dev-shell";

          nativeBuildInputs = with pythonPackages; [
            uv
            pytest
            black
            setuptools
            wheel
            build
          ];

          shellHook = ''
            # To silence the hardlink warning, uncomment the next line
            # export UV_LINK_MODE=copy
            
            if [ ! -d ".venv" ]; then
              echo "Creating Python virtual environment with uv in ./.venv..."
              uv venv .venv --seed
            fi

            source .venv/bin/activate

            echo "Installing dependencies and txtarchive in editable mode..."
            # This command will now work because of the change to pyproject.toml
            uv pip install -e ".[dev]"

            echo "✅ Nix shell is ready. Python virtual environment is active."
          '';
        };
      });
}