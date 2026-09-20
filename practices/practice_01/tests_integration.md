# Integration-проверки

| Связь компонентов | Что может сломаться | Как воспроизводим | Ожидаемый результат | Evidence (строгие ссылки) |
|---|---|---|---|---|
| API ↔ Pydantic | Отсутствие схемы и `KeyError` | `POST /api/reviews` с телом `{}` | HTTP 422 Unprocessable Entity с деталями валидации | [`TRAINING_PR.diff:36`](TRAINING_PR.diff#L36), [`context.md:17`](context.md#L17) |
| API ↔ ReviewService | DoS длинным diff без ограничения длины | `POST /api/reviews` с телом `diff` длиной 20001 символ | HTTP 413 Payload Too Large | [`CASE.md:65`](CASE.md#L65) (правило API-1) |
| ReviewService ↔ LLM | Падение приложения при сбое провайдера LLM | Мок `llm.generate` с выбросом `TimeoutError` (>10c) | HTTP 504 Gateway Timeout с телом `{"error": "LLM timeout exceeded"}` | [`CASE.md:66`](CASE.md#L66) (правило REL-1) |
| ReviewService ↔ LLM | Утечка чувствительных данных во внешний API | Отправка diff с `token=ghp_secret123` | Проверка входящего аргумента `llm.generate`: токен заменен на `[REDACTED]` | [`CASE.md:64`](CASE.md#L64) (правило SEC-1) |
| Service ↔ Response | Неструктурированный или избыточный ответ LLM | Ответ модели, содержащий 5 рисков без `file:line` | Нормализованный JSON: `risks` строго <= 3 элементов, все поля валидны | [`CASE.md:67`](CASE.md#L67) (правило OUT-1) |

## Как использовали AI

- Строка в [`prompts.md`](prompts.md): P1-02 (первичная версия); Практика 2: [`rag/experiment.md`](../practice_02/rag/experiment.md).
- Что проверили и исправили сами: Выполнили grounding (RAG) всех тестовых кейсов: добавили точные ссылки на строки `CASE.md` и `TRAINING_PR.diff`, специфицировали коды HTTP 413, 422, 504 и точные входные данные (20001 символ, `ghp_secret123`).
