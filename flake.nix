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

          # If the package has dependencies, list them here.
          # For example: propagatedBuildInputs = with pkgs.python3.pkgs; [ requests beautifulsoup4 ];
          propagatedBuildInputs = with pkgs.python3.pkgs; [ ];

          # This tells Nix that the resulting package is in a format that can be tested with `nix build`
          # and makes sure its dependencies are met.
          format = "pyproject"; # or  "setuptools" if using setup.py
        };

        # Problem Solved: Provides a dedicated development shell for *working on* txtarchive itself.
        # This is good practice and completes the "Spoke" pattern.
        devShells.default = pkgs.mkShell {
          name = "txtarchive-dev-shell";
          inputsFrom = [ self.packages.${system}.default ];
          
          # Add any development-only tools here, like linters or test runners.
          nativeBuildInputs = with pkgs.python3.pkgs; [
            pytest
            black
          ];
        };
      });
}