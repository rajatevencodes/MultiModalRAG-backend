# Makefile - ADD THIS
.PHONY: server worker redis eval-collect eval-run 

# Development servers
server:
	./start_server.sh

worker:
	./start_worker.sh

redis:
	./start_redis.sh

# Stop services
stop:
	./stop.sh

# Evaluation tasks
eval-collect:
	python3 evaluation/scripts/ragas_data_collection.py

eval-run:
	python3 evaluation/scripts/ragas_run_evaluation.py


