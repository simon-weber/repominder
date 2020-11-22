deploy-prod:
	 ansible-playbook -v -i ansible/production ansible/deploy.yml

deploy-dev:
	 ansible-playbook -v -i ansible/dev ansible/deploy.yml

nix-deploy-prod:
	nixops deploy --include delta-simon-codes -d repominder

nix-deploy-dev:
	nixops deploy --include virtualbox -d repominder

pip-compile:
	pip-compile -r requirements.in && pip-compile -r dev-requirements.in && pip-sync dev-requirements.txt

hooks:
	pre-commit run -v --files $$(git ls-files -m)

# also consider vacuuming the journal:
#    journalctl --vacuum-size=500M
# and cleaning old nix generations:
#    nix-env --list-generations --profile /nix/var/nix/profiles/system
#  then
#    nix-collect-garbage --delete-older-than 123 --dry-run
#  or just
#    nix-collect-garbage --delete-older-than 120d --dry-run
cleanup-prod:
	ansible all -i ansible/production -m shell -a "nix-collect-garbage; docker system prune --force; df -h"
