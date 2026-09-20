# Анализ процесса: AS IS и TO BE

## AS IS

- Событие: клиент отправляет POST `/api/reviews` с телом `payload: dict`.
- Обработка: `create_review(payload: dict)` достаёт `payload["diff"]` без схемы/валидации и передаёт в `ReviewService.review`.
- ReviewService: формирует `prompt = f"Review this pull request and find problems:\n{diff}"` и вызывает `llm.generate(prompt)` без таймаута и обработки ошибок.
- Результат: возвращается `{"comment": answer}`; при отсутствии `diff` — `KeyError` и HTTP 500.
- Риски: отсутствие валидации, отсутствие контролируемых ошибок LLM, риск prompt-injection/утечки секретов.

Участники: Клиент → FastAPI `/api/reviews` → ReviewService → внешний LLM.

## TO BE

- Схема: Pydantic-модель `ReviewRequest(diff: constr(strip=True))` с автоматической 422 при невалидном вводе.
- Ограничения входа: отклонять diff > 20000 символов (HTTP 413).
- Санитизация: `sanitize(diff)` удаляет секреты (SEC-1) перед отправкой во внешний LLM.
- Надёжность: LLM-клиент с таймаутом 10с, обработкой ошибок (REL-1), маппингом на контролируемый ответ.
- Формат: нормализованный ответ `{summary, risks<=3, checks}` (OUT-1); без изменения кода/действий (SCOPE-1); логи без содержимого diff/ответа (OBS-1).

```mermaid
flowchart LR
    A[Client] --> B[FastAPI /api/reviews]
    B --> C[Pydantic ReviewRequest]
    C -->|valid| D[Check length <= 20k]
    C -->|invalid| I[422 Validation Error]
    D -->|>20k| J[413 Payload Too Large]
    D -->|ok| E[Sanitize diff (SEC-1)]
    E --> F[LLM client (timeout=10s, REL-1)]
    F --> G[Normalize to {summary, risks<=3, checks} (OUT-1)]
    F -- error/timeout --> H[Controlled error mapping]
    G --> R[200 Response]
```

## Разница

| Что меняется | AS IS | TO BE | Как проверим изменение | Evidence |
|---|---|---|---|---|
| Валидация тела | `payload: dict`, `KeyError` → 500 | Pydantic-модель `ReviewRequest`, 422 | Отправить `{}` → HTTP 422 | `context.md` |
| Длина diff | Не ограничено (риск DoS/переполнения) | Отклонение при >20000 симв. → HTTP 413 | Отправить diff длиной 20001 симв. → HTTP 413 | `CASE.md` API-1 |
| Секреты в prompt | Сырые данные передаются в LLM | `sanitize(diff)` → `[REDACTED]` | Передать diff с `token=...`, проверить prompt к LLM | `CASE.md` SEC-1 |
| Ошибки LLM | Необработанное исключение → HTTP 500 | Таймаут 10с, контролируемый ответ HTTP 502/504 | Мок `llm.generate` с `TimeoutError` → HTTP 504 | `CASE.md` REL-1 |
| Формат ответа | Произвольный `{"comment": answer}` | Контракт `{summary, risks<=3, checks}` | Проверка схемы JSON-ответа | `CASE.md` OUT-1 |
| Наблюдаемость (логи) | Сырой ввод/стектрейс в консоли | Логируются только `request_id`, длительность, статус | Проверка логов: отсутствие diff и токенов в stdout | `CASE.md` OBS-1 |

## Как использовали AI

- Для чего: Сводка AS IS/TO BE, устранение противоречий и верификация через CoV (Chain of Verification).
- Тип промпта: chain of verification (в рамках Практики 2) / master prompt (в Практике 1).
- Строка в [`prompts.md`](prompts.md): P1-02 (первичная версия); Практика 2: [`chain_of_verification/experiment.md`](../practice_02/chain_of_verification/experiment.md).
- Что проверили и исправили сами: Сопоставили шаги TO BE с правилами SEC-1, API-1, REL-1, OUT-1, OBS-1; исключили предположение о допустимости логирования начала diff (отклонено по OBS-1).
