{
  description = "NeuroSpeller development environment";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs {
          inherit system;
          config.allowUnfree = true;
        };

        python = pkgs.python311;

        pythonEnv = python.withPackages (ps: with ps; [
          numpy
          pygame
          scikit-learn
          mne
          pandas
          matplotlib
          # brainaccess is not in nixpkgs - install manually or via pip
        ]);

      in {
        devShells.default = pkgs.mkShell {
          buildInputs = [
            pythonEnv
            pkgs.SDL2
            pkgs.SDL2_image
            pkgs.SDL2_mixer
            pkgs.SDL2_ttf
          ];

          shellHook = ''
            export SDL_VIDEODRIVER=''${SDL_VIDEODRIVER:-x11}
            export LD_LIBRARY_PATH=${pkgs.SDL2}/lib:$LD_LIBRARY_PATH
            echo "NeuroSpeller env ready. Run: python main.py"
          '';
        };
      });
}
