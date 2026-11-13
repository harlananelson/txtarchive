{
  description = "A flake for the txtarchive Python utility";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    # The nixpkgs pin above is from 2025-08 and only has Claude Code 1.0.65.
    # This input stays on nixos-unstable so `claude` can move without moving
    # Python, Pandoc, or Quarto.
    nixpkgs-claude.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, nixpkgs-claude, flake-utils, ... }@inputs:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        # claude-code is unfree. Allow that package only.
        claudePkgs = import nixpkgs-claude {
          inherit system;
          config.allowUnfreePredicate = pkg:
            builtins.elem (nixpkgs-claude.lib.getName pkg) [
              "claude-code"
            ];
        };
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
          # (must match pyproject.toml dependencies)
          propagatedBuildInputs = with pythonPackages; [ requests mammoth python-docx pypandoc beautifulsoup4 pyyaml ];

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
            claudePkgs.claude-code
          ];

          nativeBuildInputs = [ 
            pkgs.python3 # Ensure python interpreter is available
          ];

          shellHook = ''
            # nix-name: give this shell a name when getpwuid has none for the uid.
            # Pure nix shells on iuhlwolfap1122 otherwise prompt "I have no name!".
            # No LD_PRELOAD. The nixpkgs nss_wrapper is linked to a newer glibc than
            # the host, and preloading it breaks host binaries started from the shell.
            if ! id -un >/dev/null 2>&1; then
            _nn_dir="''${TMPDIR:-/tmp}/nix-name-$$"
            mkdir -p "$_nn_dir"
            _nn_name=$(logname 2>/dev/null || printf '%s' "''${USER:-nixuser}")
            printf '%s\n' '#!/bin/sh' "printf '%s\\n' '$_nn_name'" > "$_nn_dir/whoami"
            chmod +x "$_nn_dir/whoami"
            export PATH="$_nn_dir:''${PATH}"
            export USER="$_nn_name"
            export LOGNAME="$_nn_name"
            export PS1="$_nn_name@\h:\w\\$ "
            unset _nn_dir _nn_name
            fi
            export USER=''${USER:-$(whoami)}
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

            if ! command -v claude &> /dev/null; then
                echo "WARNING: claude binary not found!"
            else
                echo "✅ Claude linked: $(claude --version | head -n 1)"
            fi
          '';
        };
      }
    );
}