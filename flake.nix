{
  description = "Manages and schedules the training jobs on a cluster of machines";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-22.11";

    utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, ... }@inputs: {
    overlays.dev = (final: prev: {
      pythonPackagesExtensions = prev.pythonPackagesExtensions ++ [
        (python-final: python-prev: {
          libtmux = python-final.callPackage ./nix/pkgs/libtmux {};
        })
      ];
    });
    overlays.default = (final: prev: {
      pythonPackagesExtensions = prev.pythonPackagesExtensions ++ [
        (python-final: python-prev: {
          libtmux = python-final.callPackage ./nix/pkgs/libtmux {};
          traintrack = python-final.callPackage ./nix/pkgs/traintrack {};
        })
      ];

      traintrack = with final.python3Packages; toPythonApplication traintrack;
    });
  } // inputs.utils.lib.eachSystem [
    "x86_64-linux"
  ] (system:
    let pkgs-dev = import nixpkgs {
          inherit system;
          config.allowUnfree = true;
          overlays = [ self.overlays.dev ];
        };

        pkgs = import nixpkgs {
          inherit system;
          config.allowUnfree = true;
          overlays = [ self.overlays.default ];
        };
    in {
      devShells.default = let
        python-env = pkgs-dev.python3.withPackages (pyPkgs: with pyPkgs; [
          loguru
          libtmux
          fastapi
          prompt-toolkit
          uvicorn
          pydantic
          paramiko
          requests
          questionary
          jinja2
          rich
        ]);

        name = "traintrack";
      in pkgs-dev.mkShell {
        inherit name;

        packages = [
          python-env
          pkgs-dev.pre-commit
          pkgs-dev.nodePackages.pyright
        ];

        shellHooks = let pythonIcon = "f3e2"; in ''
          export PS1="$(echo -e '\u${pythonIcon}') {\[$(tput sgr0)\]\[\033[38;5;228m\]\w\[$(tput sgr0)\]\[\033[38;5;15m\]} (${name}) \\$ \[$(tput sgr0)\]"
        '';
      };

      packages.traintrack = pkgs.traintrack;
    });
}
