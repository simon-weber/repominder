let
  pydrive = pkgs: import ./pydrive.nix {inherit pkgs;};
  duplKey = builtins.readFile ../secrets/pydriveprivatekey.pem;
  dbPath = "/opt/repominder/repominder_db.sqlite3";
in let
  genericConf = { config, pkgs, ... }: {
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
    services.journalbeat = {
      enable = true;
      extraConfig = ''
        journalbeat.inputs:
        - paths: ["/var/log/journal"]
          include_matches:
            - "UNIT=acme-www.repominder.com.service"
            - "UNIT=duplicity.service"
            - "_SYSTEMD_UNIT=nginx.service"
            - "_SYSTEMD_UNIT=repominder.service"
            - "_SYSTEMD_UNIT=repominder_notify.service"
            - "_SYSTEMD_UNIT=sshd.service"

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
    services.duplicity = {
      enable = true;
      frequency = "*-*-* 00,12:00:00";
      root = "/tmp/db.backup";
      targetUrl = "pydrive://duply-alpha@repominder.iam.gserviceaccount.com/repominder_backups/db7";
      secretFile = pkgs.writeText "dupl.env" ''
        GOOGLE_DRIVE_ACCOUNT_KEY="${duplKey}"
        '';
      extraFlags = ["--no-encryption"];
    };
    systemd.services.duplicity = {
      path = [ pkgs.bash pkgs.sqlite pkgs.curl ];
      preStart = ''sqlite3 ${dbPath} ".backup /tmp/db.backup"'';
      postStop = ''rm /tmp/db.backup; curl -L -H 'Content-Type: application/json' -d "{\"localtime\": $(date +\"%s\"), \"successful\": $([ "$EXIT_STATUS" == 0 ] && echo "true" || echo "false"), \"message\": \"$EXIT_STATUS\"}" https://script.google.com/macros/s/AKfycbwbk-fT4NGCo9OIeQjzl7MOc4r59q8E4GcCe6JAfQ/exec'';
    };
    systemd.services.repominder = {
      description = "Repominder application";
      after = [ "network-online.target" ];
      wantedBy = [ "network-online.target" ];
      path = [ pkgs.python37 pkgs.bash ];
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
      after = [ "network-online.target" ];
      path = [ pkgs.python37 pkgs.bash ];
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
      users.root.openssh.authorizedKeys.keyFiles = [ ../../.ssh/id_rsa.pub ];
      users.repominder = {
        group = "repominder";
        isSystemUser = true;
      };
      groups.repominder.members = [ "repominder" "nginx" ];
    };

    networking.firewall.allowedTCPPorts = [ 22 80 443 ];

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
      curl
      duplicity
      sqlite
      vim
      (python37.withPackages(ps: with ps; [ virtualenv pip ]))
    ];
  };
  in {
    network.description = "repominder";
    network.enableRollback = true;
    virtualbox = genericConf;
    bvm-lv-1 = genericConf;
  }
