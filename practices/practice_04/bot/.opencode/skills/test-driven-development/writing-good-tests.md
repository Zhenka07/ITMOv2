# Best Practices написания тестов в Go

## 1. Table-Driven Tests (Табличные тесты)
Используй анонимные структуры со срезом сценариев:
```go
tests := []struct {
    name    string
    input   string
    wantErr bool
}{
    {name: "valid https url", input: "https://example.com", wantErr: false},
    {name: "missing scheme", input: "example.com", wantErr: true},
}
for _, tt := range tests {
    t.Run(tt.name, func(t *testing.T) {
        ...
    })
}
```

## 2. Изоляция тестов
- Не используй реальную базу данных в юнит-тестах бизнес-логики без необходимости.
- Для SQLite используй `:memory:` базу в тестах хранилища.
- Очищай ресурсы через `t.Cleanup(func() { ... })`.

## 3. Четкие сообщения об ошибках
- Форматируй ошибки как: `t.Errorf("got %v, want %v", got, want)` с достаточным контекстом для локализации проблемы.
