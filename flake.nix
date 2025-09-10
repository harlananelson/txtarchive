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
      in
      {
        # Problem Solved: This exposes the packaged application so other flakes can use it.
        # `buildPythonApplication` is the standard Nix function for building a Python project
        # that has a setup.py or pyproject.toml and provides command-line entry points.
        packages.default = pkgs.python3.pkgs.buildPythonApplication {
          pname = "txtarchive";
          version = "0.1.0"; # Or pull from a version file

          # The `src` is the directory containing the flake itself.
          src = self;

          
          format = "pyproject";

          # Add all the build dependencies needed for pyproject builds
          nativeBuildInputs = with pkgs.python3.pkgs; [ 
            setuptools 
            wheel 
            build
            pip  # Sometimes needed for pyproject builds
          ];
          

          # Add any runtime dependencies your package needs
          propagatedBuildInputs = with pkgs.python3.pkgs; [ 
            requests
            # Add your package dependencies here if any
          ];

          
          # Skip tests for now - you can enable later when you have tests
          doCheck = false;
          
          # Optional: specify Python version compatibility
          pythonImportsCheck = [ "txtarchive" ];
        };

        # Problem Solved: Provides a dedicated development shell for *working on* txtarchive itself.
        # This is good practice and completes the "Spoke" pattern.
        devShells.default = pkgs.mkShell {
          name = "txtarchive-dev-shell";
          # sage The inputsFrom attribute is unnecessary here because the devShells.default already includes the tools explicitly listed in nativeBuildInputs.
          inputsFrom = [ self.packages.${system}.default ];
          
          # Add any development-only tools here, like linters or test runners.
          nativeBuildInputs = with pkgs.python3.pkgs; [
            setuptools
            wheel
            build
            #pip   pip is not required for building a pyproject.toml-based package. The build tool handles the build process.
            pytest
            black
            #requests removed by sage as it is not needed in devShells
            # Add other dev tools as needed
          ];
          # This hook runs every time you enter the shell
          shellHook = ''
            # Create a virtual environment directory if it doesn't exist
            if [ ! -d ".venv" ]; then
              echo "Creating Python virtual environment in ./.venv..."
              python -m venv .venv
            fi

            # Activate the virtual environment
            source .venv/bin/activate

            echo "Installing txtarchive in editable mode into the venv..."
            # Use a newer pip if available and install the project
            pip install --upgrade pip
            pip install -e .

            echo "Nix shell is ready. Python environment is in ./.venv"
          '';

        };
      });
}