{
  virtualbox =
    { config, pkgs, ... }:
    { deployment.targetEnv = "virtualbox";
      deployment.virtualbox.memorySize = 1024; # megabytes
      deployment.virtualbox.vcpu = 2; # number of cpus
      deployment.virtualbox.headless = true;
    };
  delta-simon-codes =
    { config, lib, pkgs, ... }:
    { deployment.targetHost = "delta.simon.codes";
      networking.hostName = "delta.simon.codes";
      services.openssh = {
        passwordAuthentication = false;
        challengeResponseAuthentication = false;
        extraConfig = "AllowUsers root";
      };

      # from generated configuration.nix
      boot.loader.grub.device = "/dev/vda";
      boot.loader.grub.enable = true;
      boot.loader.grub.version = 2;
      services.openssh.enable = true;
      services.openssh.permitRootLogin = "prohibit-password";
      system.stateVersion = "18.09";

      # from generated hardware-configuration.nix
      boot.initrd.availableKernelModules = [ "ata_piix" "uhci_hcd" "virtio_pci" "sr_mod" "virtio_blk" ];
      boot.kernelModules = [ ];
      boot.extraModulePackages = [ ];

      fileSystems."/" =
        { device = "/dev/disk/by-uuid/cd3d8aa2-8626-4d28-be4a-322935cd60a5";
          fsType = "ext4";
        };

      swapDevices =
        [ { device = "/dev/disk/by-uuid/cd94282c-8684-4a91-bfde-b6110e27b2fd"; }
        ];

      nix.maxJobs = lib.mkDefault 1;
      virtualisation.hypervGuest.enable = false;
    };
}
