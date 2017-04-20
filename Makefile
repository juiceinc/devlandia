.PHONY: ecr_login

ecr_login:
	@$(shell aws ecr get-login --registry-ids 976661725066)
