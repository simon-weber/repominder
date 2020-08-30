let
  duplKey = builtins.readFile ../secrets/pydriveprivatekey.pem;
  opsgridToken = builtins.readFile ../secrets/opsgrid_token.txt;
  dbPath = "/opt/repominder/repominder_db.sqlite3";
  logUnitYaml = lib: builtins.toJSON (lib.lists.flatten (builtins.map (x: [ "UNIT=${x}" "_SYSTEMD_UNIT=${x}" ]) [
    "acme-www.repominder.com.service"
    "duplicity.service"
    "docker.service"
    "docker-repominder.service"
    "docker-repominder_notify.service"
    "docker-repominder_cleanup.service"
    "nginx.service"
    "sshd.service"
  ]));
in let
  genericConf = { config, pkgs, lib, ... }: {

    virtualisation.docker = {
      enable = true;
      logDriver = "journald";
    };
    docker-containers.repominder = {
      image = "repominder:latest";
      ports = [ "127.0.0.1:8000:8000" ];
      volumes = [ "/opt/repominder:/opt/repominder" ];
    };

    docker-containers.repominder_notify = {
      image = "repominder:latest";
      volumes = [ "/opt/repominder:/opt/repominder" ];
      entrypoint = "python";
      cmd = [ "send_notifications.py" ];
    };
    systemd.services.docker-repominder_notify = {
      startAt = "weekly";
      wantedBy = pkgs.lib.mkForce [];
      serviceConfig = {
        Restart = pkgs.lib.mkForce "no";
      };
    };
    docker-containers.repominder_cleanup = {
      image = "repominder:latest";
      volumes = [ "/opt/repominder:/opt/repominder" ];
      entrypoint = "python";
      cmd = [ "manage.py" "clearsessions" ];
    };
    systemd.services.docker-repominder_cleanup = {
      startAt = "*-*-* 07:30:00";  # early mornings eastern
      wantedBy = pkgs.lib.mkForce [];
      serviceConfig = {
        Restart = pkgs.lib.mkForce "no";
        # TODO figure out how to merge these automatically
        # https://github.com/NixOS/nixpkgs/issues/76620
        ExecStopPost = pkgs.lib.mkForce [ "-${pkgs.docker}/bin/docker rm -f %n" "${pkgs.sqlite}/bin/sqlite3 ${dbPath} 'VACUUM;'" ];
      };
    };

    services.nginx = {
      enable = true;
      recommendedGzipSettings = true;
      recommendedOptimisation = true;
      recommendedProxySettings = true;
      recommendedTlsSettings = true;
      upstreams.gunicorn = {
        servers = {
          "127.0.0.1:8000" = {};
        };
      };
      virtualHosts."www.repominder.com" = {
        enableACME = true;
        forceSSL = true;
        locations."/assets/" = {
          alias = "/opt/repominder/assets/";
        };
        locations."/" = {
          proxyPass = "http://gunicorn";
        };
      };
      # reject requests with bad host headers
      virtualHosts."_" = {
        onlySSL = true;
        default = true;
        sslCertificate = ./fake-cert.pem;
        sslCertificateKey = ./fake-key.pem;
        extraConfig = "return 444;";
      };
      appendHttpConfig = ''
        error_log stderr;
        access_log syslog:server=unix:/dev/log combined;
      '';
    };

    # TODO log collection seems to be working only sometimes, eg not for notifications
    services.journalbeat = {
      enable = true;
      extraConfig = ''
        journalbeat.inputs:
        - paths: ["/var/log/journal"]
          include_matches: ${(logUnitYaml lib)}
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

    services.telegraf = {
      enable = true;
    };
    systemd.services.telegraf = {
      environment = {
        OPSGRID_INGEST_TOKEN = opsgridToken;
      };
      serviceConfig = {
        ExecStart = pkgs.lib.mkForce ''${pkgs.telegraf}/bin/telegraf -config "${./telegraf.conf}"'';
      };
    };


    services.duplicity = {
      enable = true;
      frequency = "*-*-* 00,12:00:00";
      root = "/tmp/db.backup";
      targetUrl = "pydrive://duply-alpha@repominder.iam.gserviceaccount.com/repominder_backups/db8";
      secretFile = pkgs.writeText "dupl.env" ''
        GOOGLE_DRIVE_ACCOUNT_KEY="${duplKey}"
        '';
      # https://bugs.launchpad.net/duplicity/+bug/667885
      extraFlags = ["--no-encryption" "--allow-source-mismatch"];
    };
    systemd.services.duplicity = {
      path = [ pkgs.bash pkgs.sqlite pkgs.curl ];
      preStart = ''sqlite3 ${dbPath} ".backup /tmp/db.backup"'';
      postStop = ''rm /tmp/db.backup; curl -L -H 'Content-Type: application/json' -d "{\"localtime\": $(date +\"%s\"), \"successful\": $([ "$EXIT_STATUS" == 0 ] && echo "true" || echo "false"), \"message\": \"$EXIT_STATUS\"}" https://script.google.com/macros/s/AKfycbwbk-fT4NGCo9OIeQjzl7MOc4r59q8E4GcCe6JAfQ/exec'';

      # max 5 retries waiting 30s to work around db locking
      serviceConfig = {
        Restart = "on-failure";
        RestartSec = 30;
      };
      unitConfig = {
        StartLimitIntervalSec = 200;
        StartLimitBurst = 5;
      };
    };

    users = {
      users.root.extraGroups = [ "docker" ];
      users.root.openssh.authorizedKeys.keyFiles = [ ../../.ssh/id_rsa.pub ];
      users.repominder = {
        group = "repominder";
        isSystemUser = true;
        uid = 497;
      };
      groups.repominder = {
        members = [ "repominder" "nginx" ];
        gid = 499;
      };
    };

    networking.firewall.allowedTCPPorts = [ 22 80 443 ];

    security.acme.acceptTerms = true;
    security.acme.email = "domains@simonmweber.com";

    nixpkgs.config = {
      allowUnfree = true;
    };
    nixpkgs.overlays = [ (self: super: {
       duplicity = super.duplicity.overrideAttrs (oldAttrs: { 
         doCheck = false;
         doInstallCheck = false;
       });
     }
    )];

    environment.systemPackages = with pkgs; [
      curl
      duplicity
      sqlite
      vim
      python3  # for ansible
      htop
      iotop
      sysstat
    ];
  };
  in {
    network.description = "repominder";
    network.enableRollback = true;
    delta-simon-codes = genericConf;
  }
