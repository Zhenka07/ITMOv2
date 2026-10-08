package config

import (
	"fmt"
	"os"
	"strconv"
	"time"
)

type Config struct {
	TelegramAPIKey string
	TelegramHost   string
	SQLitePath     string
	BatchSize      int
	PollTimeout    time.Duration
}

func LoadConfig() (*Config, error) {
	key := os.Getenv("TELEGRAM_API_KEY")
	if key == "" {
		return nil, fmt.Errorf("TELEGRAM_API_KEY environment variable is not set")
	}

	config := &Config{
		TelegramAPIKey: key,
		TelegramHost:   getEnv("TELEGRAM_HOST", "api.telegram.org"),
		SQLitePath:     getEnv("SQLITE_PATH", "user_data/sqlite/storage.db"),
		BatchSize:      getEnvInt("BATCH_SIZE", 100),
		PollTimeout:    getEnvAsDuration("POLL_TIMEOUT", 1*time.Second),
	}

	return config, nil
}

func getEnv(key, defaultStr string) string {
	key, exists := os.LookupEnv(key)
	if exists && key != "" {
		return key
	}
	return defaultStr
}

func getEnvInt(key string, defaultVal int) int {
	valStr := getEnv(key, "")
	if valStr == "" {
		return defaultVal
	}

	valInt, err := strconv.Atoi(valStr)
	if err != nil {
		return defaultVal
	}
	return valInt
}

func getEnvAsDuration(key string, defaultVal time.Duration) time.Duration {
	valueStr := getEnv(key, "")
	if valueStr == "" {
		return defaultVal
	}
	value, err := time.ParseDuration(valueStr)
	if err != nil {
		return defaultVal
	}
	return value
}
