package telegram

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"path"
	"strconv"
	"time"
)

type Client struct {
	host   string
	Path   string
	client http.Client
}

const (
	getUpd  = "getUpdates"
	sendMsg = "sendMessage"
)

func New(host string, token string) *Client {
	return &Client{
		host: host,
		Path: newPath(token),
		client: http.Client{
			Timeout: 30 * time.Second,
		},
	}
}

func newPath(token string) string {
	return "bot" + token
}

func (c *Client) SendMessage(ChatID int, text string) error {
	q := url.Values{}
	q.Add("chat_id", strconv.Itoa(ChatID))
	q.Add("text", text)

	_, err := c.DoRequest(q, sendMsg)
	if err != nil {
		return fmt.Errorf("can't send message %w", err)
	}

	return nil
}

func (c *Client) Updates(offset int, limit int) ([]Update, error) {
	q := url.Values{}
	q.Add("offset", strconv.Itoa(offset))
	q.Add("limit", strconv.Itoa(limit))

	data, err := c.DoRequest(q, getUpd)
	if err != nil {
		return nil, err
	}
	var res UpdateResponse
	if err := json.Unmarshal(data, &res); err != nil {
		return nil, err
	}

	return res.Result, err
}

func (c *Client) DoRequest(q url.Values, method string) ([]byte, error) {
	u := url.URL{
		Scheme: "https",
		Host:   c.host,
		Path:   path.Join(c.Path, method),
	}
	req, err := http.NewRequest(http.MethodGet, u.String(), nil)
	if err != nil {
		return nil, fmt.Errorf("can't do request %w", err)
	}

	req.URL.RawQuery = q.Encode()

	resp, err := c.client.Do(req)
	if err != nil {
		return nil, fmt.Errorf("can't do request %w", err)
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("can't do request %w", err)
	}

	return body, nil
}
