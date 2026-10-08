package telegram_test

import (
	"context"
	"crypto/tls"
	"errors"
	"net/http"
	"net/http/httptest"
	"net/url"
	"strings"
	"sync"
	"testing"

	eventsTg "github.com/Zhenka07/TelegramBot/client/events/telegram"
	clientTg "github.com/Zhenka07/TelegramBot/client/telegram"
	"github.com/Zhenka07/TelegramBot/storage"
)

func TestValidateURL(t *testing.T) {
	tests := []struct {
		name    string
		url     string
		wantErr error
	}{
		{
			name:    "valid https url",
			url:     "https://github.com/obra/superpowers",
			wantErr: nil,
		},
		{
			name:    "valid http url with query params",
			url:     "http://example.com/path?foo=bar&num=42",
			wantErr: nil,
		},
		{
			name:    "invalid scheme ftp",
			url:     "ftp://example.com/files",
			wantErr: eventsTg.ErrInvalidScheme,
		},
		{
			name:    "invalid scheme javascript",
			url:     "javascript:alert(1)",
			wantErr: eventsTg.ErrInvalidScheme,
		},
		{
			name:    "url too long (over 2048 chars)",
			url:     "https://example.com/" + strings.Repeat("a", 2040),
			wantErr: eventsTg.ErrURLTooLong,
		},
		{
			name:    "forbidden localhost",
			url:     "http://localhost:8080/admin",
			wantErr: eventsTg.ErrForbiddenHost,
		},
		{
			name:    "forbidden 127.0.0.1",
			url:     "http://127.0.0.1:9090",
			wantErr: eventsTg.ErrForbiddenHost,
		},
		{
			name:    "missing host",
			url:     "http:///no-host-here",
			wantErr: eventsTg.ErrInvalidHost,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := eventsTg.ValidateURL(tt.url)
			if tt.wantErr == nil {
				if err != nil {
					t.Fatalf("expected no error, got: %v", err)
				}
			} else {
				if !errors.Is(err, tt.wantErr) {
					t.Fatalf("expected error %v, got: %v", tt.wantErr, err)
				}
			}
		})
	}
}

func TestIsURL(t *testing.T) {
	if !eventsTg.IsURL("https://example.com") {
		t.Errorf("expected 'https://example.com' to be a valid URL")
	}
	if eventsTg.IsURL("http://localhost:8080") {
		t.Errorf("expected localhost to be rejected as valid URL")
	}
	if eventsTg.IsURL("not-a-url") {
		t.Errorf("expected 'not-a-url' to be false")
	}
}

// Mock storage for Feature B testing
type mockStorage struct {
	isExistsFunc   func(ctx context.Context, p *storage.Page) (bool, error)
	saveFunc       func(ctx context.Context, p *storage.Page) error
	pickRandomFunc func(ctx context.Context, username string) (*storage.Page, error)
	removeFunc     func(ctx context.Context, p *storage.Page) error
}

func (m *mockStorage) IsExists(ctx context.Context, p *storage.Page) (bool, error) {
	if m.isExistsFunc != nil {
		return m.isExistsFunc(ctx, p)
	}
	return false, nil
}

func (m *mockStorage) Save(ctx context.Context, p *storage.Page) error {
	if m.saveFunc != nil {
		return m.saveFunc(ctx, p)
	}
	return nil
}

func (m *mockStorage) PickRandom(ctx context.Context, username string) (*storage.Page, error) {
	if m.pickRandomFunc != nil {
		return m.pickRandomFunc(ctx, username)
	}
	return nil, storage.ErrNoSavedPage
}

func (m *mockStorage) Remove(ctx context.Context, p *storage.Page) error {
	if m.removeFunc != nil {
		return m.removeFunc(ctx, p)
	}
	return nil
}

func setupTestProcessor(t *testing.T, st eventsTg.Storage) (*eventsTg.Processor, *[]string) {
	var mu sync.Mutex
	var sentMessages []string

	srv := httptest.NewTLSServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		text := r.URL.Query().Get("text")
		mu.Lock()
		sentMessages = append(sentMessages, text)
		mu.Unlock()
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte(`{"ok": true, "result": {}}`))
	}))
	t.Cleanup(srv.Close)

	parsed, err := url.Parse(srv.URL)
	if err != nil {
		t.Fatalf("failed to parse test server url: %v", err)
	}

	// Настраиваем DefaultTransport на доверие тестовому TLS-сертификату
	http.DefaultTransport.(*http.Transport).TLSClientConfig = &tls.Config{InsecureSkipVerify: true}

	client := clientTg.New(parsed.Host, "test-token")
	processor, _ := eventsTg.New(client, st)
	return processor, &sentMessages
}

func TestAddPage_StorageDependencyError(t *testing.T) {
	mockSt := &mockStorage{
		isExistsFunc: func(ctx context.Context, p *storage.Page) (bool, error) {
			return false, errors.New("sqlite database is locked (5)")
		},
	}

	processor, messages := setupTestProcessor(t, mockSt)

	err := processor.AddPage(12345, "https://example.com/article", "test_user")
	if err == nil {
		t.Fatal("expected error from AddPage when storage fails, got nil")
	}

	if len(*messages) == 0 {
		t.Fatal("expected bot to notify user about storage error, but no messages were sent")
	}

	lastMsg := (*messages)[0]
	if !strings.Contains(lastMsg, "Storage service is temporarily unavailable") {
		t.Errorf("expected storage error message to user, got: %q", lastMsg)
	}
}

func TestAddPage_TimeoutError(t *testing.T) {
	mockSt := &mockStorage{
		isExistsFunc: func(ctx context.Context, p *storage.Page) (bool, error) {
			return false, context.DeadlineExceeded
		},
	}

	processor, messages := setupTestProcessor(t, mockSt)

	err := processor.AddPage(12345, "https://example.com/article", "test_user")
	if err == nil {
		t.Fatal("expected error from AddPage when operation times out, got nil")
	}

	if len(*messages) == 0 {
		t.Fatal("expected bot to notify user about timeout, but no messages were sent")
	}

	lastMsg := (*messages)[0]
	if !strings.Contains(lastMsg, "Request timed out") {
		t.Errorf("expected timeout message to user, got: %q", lastMsg)
	}
}

func TestSendRandom_TimeoutError(t *testing.T) {
	mockSt := &mockStorage{
		pickRandomFunc: func(ctx context.Context, username string) (*storage.Page, error) {
			return nil, context.DeadlineExceeded
		},
	}

	processor, messages := setupTestProcessor(t, mockSt)

	err := processor.SendRandom(12345, "test_user")
	if err == nil {
		t.Fatal("expected error from SendRandom when operation times out, got nil")
	}

	if len(*messages) == 0 {
		t.Fatal("expected bot to notify user about timeout, but no messages were sent")
	}

	lastMsg := (*messages)[0]
	if !strings.Contains(lastMsg, "Request timed out") {
		t.Errorf("expected timeout message to user, got: %q", lastMsg)
	}
}
