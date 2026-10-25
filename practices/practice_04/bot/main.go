package main

import (
	"context"
	"log"
	"os"
	"os/signal"
	"syscall"

	tgEvent "github.com/Zhenka07/TelegramBot/client/events/telegram"
	tgClient "github.com/Zhenka07/TelegramBot/client/telegram"
	"github.com/Zhenka07/TelegramBot/config"
	eConsumer "github.com/Zhenka07/TelegramBot/consumer/event_consumer"
	bdStorage "github.com/Zhenka07/TelegramBot/storage/sqlite"

	"github.com/joho/godotenv"
)

func main() {
	if err := godotenv.Load(); err != nil {
		log.Println("Note: .env file not found, using system environment variables")
	}

	cfg, err := config.LoadConfig()
	if err != nil {
		log.Fatalf("Error in config: %v", err)
	}

	log.Print("service starting...")

	tgClient := tgClient.New(cfg.TelegramHost, cfg.TelegramAPIKey)

	st, err := bdStorage.New(cfg.SQLitePath)
	if err != nil {
		log.Fatalf("can't start database: %v", err)
	}
	defer func() {
		if err := st.Close(); err != nil {
			log.Printf("error closing database: %v", err)
		}
	}()

	if err := st.Init(context.Background()); err != nil {
		log.Fatalf("can't init database: %v", err)
	}

	processor, fetcher := tgEvent.New(tgClient, st)
	consumer := eConsumer.New(processor, fetcher, cfg.BatchSize)

	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()

	log.Print("service started")

	if err := consumer.Start(ctx); err != nil {
		log.Fatalf("service stopped with error: %v", err)
	}

	log.Print("service stopped gracefully")
}
