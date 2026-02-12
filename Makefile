.PHONY: deploy-prod deploy-backend deploy-sync

NS ?= analytics-dashboard

deploy-prod: deploy-configs deploy-backend deploy-sync

deploy-configs:
	kubectl -n $(NS) apply -f deploy/prod/

deploy-backend:
	kubectl -n $(NS) apply -f deploy/backend.yaml
	kubectl -n $(NS) rollout status deployment/backend --timeout=300s

deploy-sync:
	kubectl -n $(NS) apply -f deploy/sync.yaml
	kubectl -n $(NS) rollout status deployment/sync --timeout=300s
