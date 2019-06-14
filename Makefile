deploy-prod:
	 ansible-playbook -v -i ansible/production ansible/deploy.yml

deploy-dev:
	 ansible-playbook -v -i ansible/dev ansible/deploy.yml

nix-deploy-prod:
	nixops deploy --include bvm-lv-1 -d repominder

nix-deploy-dev:
	nixops deploy --include virtualbox -d repominder
