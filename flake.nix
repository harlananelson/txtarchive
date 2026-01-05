{
  description = "A flake for the txtarchive Python utility";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils, ... }@inputs:
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
          
          # Native inputs = tools needed to build
          nativeBuildInputs = with pythonPackages; [ setuptools wheel build ];
          
          # Propagated inputs = python libraries needed at runtime
          propagatedBuildInputs = with pythonPackages; [ requests mammoth python-docx pypandoc ];

          # CORRECTIVE ACTION: Ensure pandoc binary is visible to the python app
          makeWrapperArgs = [ "--prefix PATH : ${pkgs.pandoc}/bin" ];

          doCheck = false;
          pythonImportsCheck = [ "txtarchive" ];
        };

        devShells.default = pkgs.mkShell {
          packages = [
            pkgs.git
            pkgs.quarto
            pkgs.pandoc # CRITICAL: Added pandoc binary so pypandoc works
            pkgs.uv     # CRITICAL: Use standalone Rust binary
          ];

          nativeBuildInputs = [ 
            pkgs.python3 # Ensure python interpreter is available
          ];

          shellHook = ''
            export UV_LINK_MODE=copy

            if [ ! -d ".venv" ]; then
              echo "Creating Python virtual environment with uv in ./.venv..."
              uv venv .venv
            fi
            source .venv/bin/activate
            
            echo "Installing dependencies and txtarchive in editable mode..."
            uv pip install -e ".[dev]"
            
            # Verification step
            if ! command -v pandoc &> /dev/null; then
                echo "WARNING: pandoc binary not found!"
            else
                echo "✅ Pandoc linked: $(pandoc --version | head -n 1)"
            fi
          '';
        };
      }
    );
}