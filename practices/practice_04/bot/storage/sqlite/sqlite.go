package sqllite

import (
	"context"
	"database/sql"
	"fmt"
	"os"
	"path/filepath"

	"github.com/Zhenka07/TelegramBot/storage"
	_ "github.com/mattn/go-sqlite3"
)

type Storage struct {
	db *sql.DB
}

func New(path string) (*Storage, error) {
	if dir := filepath.Dir(path); dir != "" && dir != "." {
		if err := os.MkdirAll(dir, 0755); err != nil {
			return nil, fmt.Errorf("can't create database directory %w", err)
		}
	}

	db, err := sql.Open("sqlite3", path)
	if err != nil {
		return nil, fmt.Errorf("can't open database %w", err)
	}
	if err := db.Ping(); err != nil {
		return nil, fmt.Errorf("can't connect to database %w", err)
	}
	return &Storage{db: db}, nil
}

func (s *Storage) Close() error {
	if s.db != nil {
		return s.db.Close()
	}
	return nil
}

func (s *Storage) Save(ctx context.Context, p *storage.Page) error {
	query := `INSERT INTO pages (url, user_name) VALUES (?, ?)`
	_, err := s.db.ExecContext(ctx, query, p.URL, p.UserName)
	if err != nil {
		return fmt.Errorf("can't save the page %w", err)
	}
	return nil
}

func (s *Storage) PickRandom(ctx context.Context, username string) (*storage.Page, error) {
	query := `SELECT url FROM pages WHERE user_name = ? ORDER BY RANDOM() LIMIT 1`

	var url string

	err := s.db.QueryRowContext(ctx, query, username).Scan(&url)
	if err == sql.ErrNoRows {
		return nil, storage.ErrNoSavedPage
	}
	if err != nil {
		return nil, fmt.Errorf("can't get the page %w", err)
	}
	return &storage.Page{URL: url, UserName: username}, nil
}

func (s *Storage) Remove(ctx context.Context, page *storage.Page) error {
	query := `DELETE FROM pages WHERE url = ? and user_name = ?`
	_, err := s.db.ExecContext(ctx, query, page.URL, page.UserName)
	if err != nil {
		return fmt.Errorf("can't delete the page %w", err)
	}
	return nil
}

func (s *Storage) IsExists(ctx context.Context, page *storage.Page) (bool, error) {
	query := `SELECT COUNT(*) FROM pages WHERE url = ? and user_name = ?`
	var count int
	err := s.db.QueryRowContext(ctx, query, page.URL, page.UserName).Scan(&count)
	if err != nil {
		return false, fmt.Errorf("can't check the page %w", err)
	}
	return count > 0, nil
}

func (s *Storage) Init(ctx context.Context) error {
	query := `CREATE TABLE IF NOT EXISTS pages (url TEXT, user_name TEXT)`

	_, err := s.db.ExecContext(ctx, query)
	if err != nil {
		return fmt.Errorf("can't create database %w", err)
	}
	return nil
}
