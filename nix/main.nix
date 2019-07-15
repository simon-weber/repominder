# filebeat stuff from https://github.com/danbst/nixos-vs-mainstream/blob/07d67dfabcfbd7b92e228e6e8d6cd1745c27a965/spring-music/nixos/nixops_vm.nix
let
  pydrive = pkgs: import ./pydrive.nix {inherit pkgs;};
  duplKey = builtins.readFile ../secrets/pydriveprivatekey.pem;
  filebeatModule = { lib, config, pkgs, ...}:
    let cfg = config.services.filebeat;
        realConfig = ''
            path.data: /var/lib/filebeat
            path.logs: /var/logs/filebeat

            filebeat.inputs:
            - type: log
              enabled: true
              paths:
                - "${config.services.nginx.stateDir}/logs/*.log"
            - type: log
              enabled: true
              paths:
                - "/var/log/repominder/*.log"

            output:
              elasticsearch:
                hosts: ["https://cloud.humio.com:443/api/v1/ingest/elastic-bulk"]
                username: anything
                password: ${builtins.readFile ../secrets/humiocloud.password}
                compression_level: 5
                bulk_max_size: 200
                worker: 1
        '';
  in with lib; {
      options.services.filebeat = {
         enable = mkOption {};
      };
      config = mkIf cfg.enable {
          environment.etc."filebeat.yml".text = realConfig;
        systemd.services.filebeat = {
            wantedBy = [ "multi-user.target" ];
            after = [ "network.target" ];
            serviceConfig.ExecStart =
              "${pkgs.filebeat7}/bin/filebeat -c ${pkgs.writeText "filebeat.yml" realConfig}";
        };
    };
  };
in let
  genericConf = { config, pkgs, ... }: {
    imports = [
        filebeatModule
    ];
    services.nginx = {
      enable = true;
      recommendedGzipSettings = true;
      recommendedOptimisation = true;
      recommendedProxySettings = true;
      # recommendedTlsSettings = true;
      upstreams.gunicorn = {
        servers = {
          "127.0.0.1:8000" = {};
        };
        # extraConfig = "fail_timeout=0";
      };
      virtualHosts."www.repominder.com" = {
        # enableACME = true;
        # forceSSL = true;
        locations."/" = {
          root = "/opt/repominder/assets";
          tryFiles = "$uri @proxy_to_app";
        };
        locations."@proxy_to_app" = {
  		proxyPass = "http://gunicorn";
        };
      };
      # reject requests with bad host headers
      appendHttpConfig = ''
        server {
          server_name _;
          listen 80 default_server;
          listen 443 default_server;
          return 444;
        }
      '';
    };
    # TODO not everything is needed
    services.journalbeat = {
      enable = true;
      extraConfig = ''
        output:
         elasticsearch:
           hosts: ["https://cloud.humio.com:443/api/v1/ingest/elastic-bulk"]
           username: anything
           password: ${builtins.readFile ../secrets/humiocloud.password}
           compression_level: 5
           bulk_max_size: 200
           worker: 1
           template.enabled: false
      '';
    };
    services.logrotate = {
      enable = true;
      config = ''
        /var/log/repominder/*.log
        {
          daily
          maxsize 10M
          rotate 3
          compress
          missingok
          notifempty
          nocreate
        }'';
    };
    services.filebeat = {
      enable = true;
    };
    services.duplicity = {
      enable = true;
      root = "/opt/repominder/repominder_db.sqlite3";
      targetUrl = "pydrive://duply-alpha@repominder.iam.gserviceaccount.com/repominder_backups/db6";
      secretFile = pkgs.writeText "dupl.env" ''
        GOOGLE_DRIVE_ACCOUNT_KEY=${duplKey}
        '';
      extraFlags = ["--no-encryption"];
    };
    systemd.services.repominder = {
      description = "Repominder application";
      after = [ "network.target" ];
      path = [ pkgs.python27 pkgs.bash ];
      environment = {
        PYTHONHASHSEED = "random";
      };
      serviceConfig = {
        WorkingDirectory = "/opt/repominder/code";
        ExecStart = "/opt/repominder/venv/exec gunicorn --worker-class gevent repominder.wsgi -b '127.0.0.1:8000'";
        Restart = "always";
        User = "repominder";
        Group = "repominder";
      };
    };
    systemd.services.repominder_notify = {
      description = "Repominder weekly notifications";
      startAt = "weekly";
      after = [ "network.target" ];
      path = [ pkgs.python27 pkgs.bash ];
      environment = {
        DJANGO_SETTINGS_MODULE = "repominder.settings";
        PYTHONHASHSEED = "random";
      };
      serviceConfig = {
        WorkingDirectory = "/opt/repominder/code";
        ExecStart = "/opt/repominder/venv/exec python send_notifications.py";
        User = "repominder";
        Group = "repominder";
      };
    };
    
    users = {
      users.root.openssh.authorizedKeys.keyFiles = [ ../nix_rsa.pub ];
      users.repominder = {
        group = "repominder";
        isSystemUser = true;
      };
      groups.repominder.members = [ "repominder" "nginx" ];
    };

    networking.firewall.allowedTCPPorts = [ 22 80 ];

    nixpkgs.config = {
      allowUnfree = true;
    };
    nixpkgs.overlays = [ (self: super: {
       duplicity = super.duplicity.overrideAttrs (oldAttrs: { 
         propagatedBuildInputs = oldAttrs.propagatedBuildInputs ++ [ (pydrive pkgs).packages.PyDrive ];
         doCheck = false;
         doInstallCheck = false;
       });
     }
    )];

    environment.systemPackages = with pkgs; [
      vim
      (python27.withPackages(ps: with ps; [ virtualenv pip ]))
    ];
  };
  in {
    network.description = "repominder";
    virtualbox = genericConf;
    bvm-lv-1 = genericConf;
  }
