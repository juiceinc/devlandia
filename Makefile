.PHONY: ecr_login

ecr_login_test:
	@$(shell aws ecr get-login --registry-ids 423681189101)
