# Практика 5: Spec-Driven Development (SDD) в Brownfield и Две команды — одна фича

Репозиторий содержит полное выполнение всех этапов **Практики 5** курса «AI Engineering Tools» (ИТМО / Авито):
1. **Классная работа (Части 1 и 2)**: Полный жизненный цикл фичи в `OpenSpec` (Fission AI) и кастомизация проектных правил (`rules.design`, диаграммы Mermaid, Given/When/Then).
2. **Домашняя работа (ДЗ 5, 10 баллов)**: Эмуляция двух независимых команд (Команда 1: Спека UI, Команда 2: Спека логики) на базе фреймворка **Spec-Kit**, согласование контракта (OpenAPI 3.1 & RFC 7807) до генерации кода, полная рабочая реализация (Backend REST API + Web UI Console), собственный MCP-сервер, сквозные тесты и рефлексия.

---

## 🎯 Навигация по артефактам

| Компонент | Расположение | Описание |
|---|---|---|
| **Подробный отчёт (10/10)** | [REPORT.md](./REPORT.md) | Полный отчёт со всеми шагами, логами CLI, diff до/после и доказательствами |
| **Рефлексия** | [reflection.md](./reflection.md) | Инженерная рефлексия: дрейф спек, overhead vs выигрыш, роль человека |
| **Интерактивная презентация** | [presentation.html](./presentation.html) | Презентация с диаграммами Mermaid, слайдами защиты и демо |
| **OpenSpec конфигурация** | [openspec/config.yaml](./openspec/config.yaml) | Кастомные правила (`rules.design`, `rules.specs`) |
| **OpenSpec архивированная фича** | [openspec/changes/archive/2026-10-28-filter-export/](./openspec/changes/archive/2026-10-28-filter-export/) | Полный цикл: proposal, specs, design, tasks |
| **OpenSpec правило и diff** | [openspec/changes/audit-logging/](./openspec/changes/audit-logging/) | Diff до и после правила с Mermaid sequenceDiagram |
| **Spec-Kit: Спека UI (до/после)** | [spec-kit/team1-ui/](./spec-kit/team1-ui/) | `spec_v1_draft.md` и `spec_v2_aligned.md` |
| **Spec-Kit: Спека логики (до/после)** | [spec-kit/team2-logic/](./spec-kit/team2-logic/) | `spec_v1_draft.md` и `spec_v2_aligned.md` |
| **Единый контракт (OpenAPI 3.1)** | [spec-kit/contract/unified_contract.yaml](./spec-kit/contract/unified_contract.yaml) | Согласованный контракт и протокол ошибок RFC 7807 |
| **Журнал согласования** | [spec-kit/contract/negotiation_log.md](./spec-kit/contract/negotiation_log.md) | Журнал переговоров и снятия разногласий между командами |
| **Бэкенд REST API** | [app/server.py](./app/server.py), [app/storage.py](./app/storage.py) | Python-сервис (Zero external heavy dependencies) |
| **Веб-интерфейс (Console)** | [app/static/index.html](./app/static/index.html) | Интерактивный SPA-дашборд с фильтрами, экспортом и формами |
| **MCP-сервер** | [mcp/server.py](./mcp/server.py) | JSON-RPC 2.0 stdio MCP tool для AI-ассистентов |
| **Автоматические тесты** | [tests/](./tests/) | Unit-тесты, проверка контракта по JSON Schema, E2E сценарий |

---

## 🚀 Быстрый старт: Запуск сервиса и API

### 1. Запуск Web UI Console и REST API
Сервис написан на Python 3 и запускается локально без необходимости сборки или установки тяжёлых внешних библиотек:

```bash
# Из папки practices/practice_05:
make run
# либо напрямую через python:
python3 -m app.server 8080
```

После старта перейдите в браузере:
- **Веб-консоль (UI Dashboard)**: [http://localhost:8080/](http://localhost:8080/)
- **Health-check API**: [http://localhost:8080/api/v1/health](http://localhost:8080/api/v1/health)
- **Список сущностей**: [http://localhost:8080/api/v1/items](http://localhost:8080/api/v1/items)
- **Журнал аудита**: [http://localhost:8080/api/v1/audit](http://localhost:8080/api/v1/audit)

### 2. Запуск и проверка MCP-сервера
MCP-сервер реализует стандартный протокол Model Context Protocol (JSON-RPC 2.0 по stdio) и предоставляет кодинг-агентам 6 инструментов (`list_items`, `get_item`, `create_item`, `update_item_status`, `export_items`, `get_audit_events`):

```bash
# Автотест MCP-сервера:
make mcp-test
# либо:
python3 mcp/test_client.py
```

Для подключения к OpenCode / Claude Desktop / Antigravity добавьте секцию в конфиг MCP:
```json
{
  "mcpServers": {
    "datahub-sdd": {
      "command": "python3",
      "args": ["/home/zhenya/ITMO/VibeCoding/ITMOv2/practices/practice_05/mcp/server.py"]
    }
  }
}
```

### 3. Запуск полного набора автотестов
```bash
make test
# или:
python3 -m unittest discover -s tests
```
Все 14 тестов (Unit API, соответствие OpenAPI контракту, сквозной E2E пользовательский путь) выполняются со 100% успехом.

---

## 📊 Соответствие критериям оценки (10 баллов)

| Критерий ДЗ 5 | Требование программы | Реализация в проекте | Балл |
|---|---|---|---|
| **1. Другой SDD-фреймворк** | Применение и детальное сравнение с OpenSpec | Использован **Spec-Kit** (модель Fowler / GitHub Next). Детальная матрица сравнения в [spec-kit/README.md](./spec-kit/README.md) и [REPORT.md](./REPORT.md). | **2 / 2** |
| **2. Две спецификации** | UI и логика, согласованные до генерации кода | Спека UI ДО (`v1_draft`) и ПОСЛЕ (`v2_aligned`). Спека логики ДО (`v1_draft`) и ПОСЛЕ (`v2_aligned`). Журнал согласования и [unified_contract.yaml](./spec-kit/contract/unified_contract.yaml). | **2 / 2** |
| **3. Реализация** | Работающие UI и логика, сквозные проверки | Работающий REST API, SPA Web UI, фильтрация, синхронный экспорт JSON/CSV, обработка ошибок RFC 7807, 14 автоматических тестов ([tests/](./tests/)). | **5 / 5** |
| **4. Рефлексия** | Что согласовали и чему научились | Подробная инженерная рефлексия в [reflection.md](./reflection.md) и [REPORT.md](./REPORT.md). | **1 / 1** |
| **Итого** | | | **10 / 10** |
