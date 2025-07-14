build-cluster:
	git ls-files repominder/ scripts/ manage.py send_notifications.py | tar cTf - app-archive.tar --owner=0 --group=0 --mtime=0 --sort=name && \
	docker build -t repominder:k8s -t $$DOCKER_REPO/repominder:k8s .

deploy-cluster: build-cluster
	docker push $$DOCKER_REPO/repominder:k8s && \
	envsubst < kube/secrets.env.yaml | kubectl apply -f - && \
	envsubst < kube/deployment.env.yaml | kubectl apply -f - && \
	kubectl rollout restart deployment repominder

hooks:
	pre-commit run -v --files $$(git ls-files -m)
