install:
	pip install -r backend/requirements.txt
	cd frontend && pnpm install

dev:
	uvicorn backend.main:app --reload --port 8000 &
	cd frontend && pnpm dev

reset:
	rm -f data/jobradar.db
	make dev
