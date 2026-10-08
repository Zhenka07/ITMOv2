.PHONY: run build build-linux setup docker-build docker-up docker-down docker-logs vet

run:
	go run main.go

build:
	go build -o bot_app main.go

build-linux:
	CGO_ENABLED=1 GOOS=linux go build -ldflags="-w -s" -o bot_app main.go

setup:
	cp .env.example .env
	@echo "Setup complete! Please add your TELEGRAM_API_KEY to the .env file."

docker-build:
	docker compose build

docker-up:
	docker compose up -d

docker-down:
	docker compose down

docker-logs:
	docker compose logs -f

vet:
	go vet ./...