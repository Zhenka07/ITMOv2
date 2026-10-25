package files

import (
	"context"
	"encoding/gob"
	"errors"
	"fmt"
	"math/rand"
	"os"
	"path/filepath"
	"time"

	"github.com/Zhenka07/TelegramBot/storage"
)

type Storage struct {
	basePath string
}

func New(path string) Storage {
	return Storage{path}
}

const DefaultPermission = 0774

func (s Storage) Save(ctx context.Context, page *storage.Page) error {
	filePath := filepath.Join(s.basePath, page.UserName)
	if err := os.MkdirAll(filePath, DefaultPermission); err != nil {
		return fmt.Errorf("Can't create directory %w", err)
	}

	filename, err := FileName(page)
	if err != nil {
		return fmt.Errorf("Can't create filename %w", err)
	}

	filePath = filepath.Join(filePath, filename)

	file, err := os.Create(filePath)
	if err != nil {
		return fmt.Errorf("Can't create file %w", err)
	}
	defer file.Close()

	if err := gob.NewEncoder(file).Encode(page); err != nil {
		return fmt.Errorf("Can't convert file to gob %w", err)
	}
	return nil
}

func (s Storage) PickRandom(ctx context.Context, username string) (*storage.Page, error) {
	filePath := filepath.Join(s.basePath, username)

	files, err := os.ReadDir(filePath)
	if err != nil {
		return nil, fmt.Errorf("Can't read directory %w", err)
	}
	if len(files) == 0 {
		return nil, storage.ErrNoSavedPage
	}

	rand.Seed(int64(time.Now().Second()))
	n := rand.Intn(len(files))

	file := files[n]

	filename := filepath.Join(filePath, file.Name())

	rawBits, err := os.Open(filename)
	if err != nil {
		return nil, fmt.Errorf("Can't open this file %w", err)
	}
	defer rawBits.Close()

	var p storage.Page

	if err := gob.NewDecoder(rawBits).Decode(&p); err != nil {
		return nil, fmt.Errorf("Can't open decode file %w", err)
	}

	return &p, nil
}

func (s Storage) Remove(ctx context.Context, p *storage.Page) error {
	fileName, err := FileName(p)
	if err != nil {
		return fmt.Errorf("Can't create filename %w", err)
	}
	path := filepath.Join(s.basePath, p.UserName, fileName)
	if err := os.Remove(path); err != nil {
		msg := fmt.Sprintf("can't delete file %s", fileName)
		return fmt.Errorf(msg+"%w", err)
	}
	return nil
}

func (s Storage) IsExists(ctx context.Context, p *storage.Page) (bool, error) {
	fileName, err := FileName(p)
	if err != nil {
		return false, fmt.Errorf("Can't create filename %w", err)
	}

	path := filepath.Join(s.basePath, p.UserName, fileName)

	_, err = os.Stat(path)
	if errors.Is(err, os.ErrNotExist) {
		return false, nil
	}
	if err != nil {
		return false, fmt.Errorf("Can't check file: %w", err)
	}
	return true, nil
}

func FileName(p *storage.Page) (string, error) {
	return p.Hash()
}
