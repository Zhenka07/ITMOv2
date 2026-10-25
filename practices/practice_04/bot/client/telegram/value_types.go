package telegram

type Update struct {
	ID      int         `json:"update_id"`
	Message *IncMessage `json:"message"`
}

type IncMessage struct {
	Text string `json:"text"`
	User User   `json:"from"`
	Chat Chat   `json:"chat"`
}

type User struct {
	Username string `json:"username"`
}

type Chat struct {
	ID int `json:"id"`
}

type UpdateResponse struct {
	Ok     bool     `json:"ok"`
	Result []Update `json:"result"`
}
