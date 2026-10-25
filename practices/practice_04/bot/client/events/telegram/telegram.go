package telegram

import (
	"context"
	"errors"
	"fmt"

	"github.com/Zhenka07/TelegramBot/client/events"
	"github.com/Zhenka07/TelegramBot/client/telegram"
	"github.com/Zhenka07/TelegramBot/storage"
)

type Storage interface {
	Save(ctx context.Context, p *storage.Page) error
	PickRandom(ctx context.Context, username string) (*storage.Page, error)
	Remove(ctx context.Context, p *storage.Page) error
	IsExists(ctx context.Context, p *storage.Page) (bool, error)
}

type Fetcher struct {
	tg     *telegram.Client
	offset int
}

type Processor struct {
	tg      *telegram.Client
	storage Storage
}

var (
	ErrUnknownEventType = errors.New("Unknown event type")
	ErrUnknownMeta      = errors.New("Unknown meta")
)

type Meta struct {
	ChatID   int
	Username string
}

func New(client *telegram.Client, storage Storage) (*Processor, *Fetcher) {
	pr := &Processor{
		tg:      client,
		storage: storage,
	}
	ft := &Fetcher{
		tg: client,
	}
	return pr, ft
}

func (p *Processor) Process(event events.Event) error {
	switch event.Type {
	case events.Message:
		return p.ProcessMessage(event)
	default:
		return fmt.Errorf("Can't process this event %w", ErrUnknownEventType)
	}
}

func (p *Processor) ProcessMessage(event events.Event) error {
	meta, err := GetMeta(event)
	if err != nil {
		return fmt.Errorf("Can't process message %w", err)
	}
	if err := p.doCmd(event.Text, meta.ChatID, meta.Username); err != nil {
		return fmt.Errorf("Can't process message %w", err)
	}

	return nil
}

func GetMeta(event events.Event) (Meta, error) {
	res, good := event.Meta.(Meta)
	if !good {
		return Meta{}, fmt.Errorf("Can't find the meta %w", ErrUnknownMeta)
	}
	return res, nil
}

func Event(upd telegram.Update) events.Event {
	upd_type := FetchType(upd)
	res := events.Event{
		Type: upd_type,
		Text: FetchText(upd),
	}

	if upd_type == events.Message {
		res.Meta = Meta{
			ChatID:   upd.Message.Chat.ID,
			Username: upd.Message.User.Username,
		}
	}

	return res
}

func (p *Fetcher) Fetch(limit int) ([]events.Event, error) {
	updates, err := p.tg.Updates(p.offset, limit)
	if err != nil {
		return nil, fmt.Errorf("Can't get updates %w", err)
	}

	if len(updates) == 0 {
		return nil, nil
	}

	res := make([]events.Event, 0, len(updates))

	for _, upd := range updates {
		res = append(res, Event(upd))
	}

	p.offset = updates[len(updates)-1].ID + 1

	return res, nil
}

func FetchType(upd telegram.Update) events.Type {
	if upd.Message == nil {
		return events.Unknown
	}
	return events.Message
}

func FetchText(upd telegram.Update) string {
	if upd.Message == nil {
		return ""
	}
	return upd.Message.Text
}
