ecr_login:
	@$(shell aws ecr get-login --registry-ids 423681189101 --region us-east-1)