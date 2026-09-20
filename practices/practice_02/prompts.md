# Журнал экспериментов Практики 2

- Выбранный слабый артефакт Практики 1: [`practices/practice_01/project_management.md`](../practice_01/project_management.md) (разделы «Инкременты и ответственность» и «Диаграмма Ганта»)
- Что в нём нужно улучшить: Устранить разрыв зависимостей задач в диаграмме Ганта (висящая задача без ID и `after`), удалить шаблонный текст-заглушку («Замените даты...»), формализовать Definition of Done инкрементов и роли Человек/AI.
- Как поймём, что изменение полезно: Критический путь проекта в диаграмме Ганта становится непрерывным (`a1 -> a2 -> (a3, a4) -> a5 -> a6`), синтаксис Mermaid валиден, каждый инкремент имеет привязку к тестам проверки, `make step1` проходит успешно.

| Техника | Файл эксперимента | Изменённый файл Практики 1 | Конкретное изменение | Проверка | Что отклонили |
|---|---|---|---|---|---|
| Few-shot | [`few_shot/experiment.md`](few_shot/experiment.md) | [`project_management.md`](../practice_01/project_management.md) | Добавлена зависимость `:a6, after a5` для этапа тестов, для `a5` задано `after a3 a4`, детализирован DoD инкрементов, удален плейсхолдер | Рендеринг Mermaid, проверка зависимостей, `make step1` | Включение деплоя в k8s и CI/CD пайплайнов (SCOPE-1) |
| R.C.T.F. | [`rctf/experiment.md`](rctf/experiment.md) | [`tests_load.md`](../practice_01/tests_load.md), [`problem.md`](../practice_01/problem.md) | Замена неизмеримых формулировок сбоев LLM и injection на численные SLA (RPS, p95/p99, 100% 502/504, 0% 500) | Проверка соответствия правилам REL-1, API-1, `make step1` | Нагрузка 10k RPS на распределенный кластер (вне скоупа) |
| Chain of Verification | [`chain_of_verification/experiment.md`](chain_of_verification/experiment.md) | [`analysis.md`](../practice_01/analysis.md) | Верификация TO BE: фиксация статус-кодов 413 и 502/504, добавление строки OBS-1 с запретом логирования тел diff | Проверка цитат по CASE.md (API-1, REL-1, SEC-1, OBS-1) | Логирование части diff для отладки (запрещено OBS-1) |
| Tree of Thoughts | [`tree_of_thoughts/experiment.md`](tree_of_thoughts/experiment.md) | [`adr.md`](../practice_01/adr.md) | Замена тривиальных альтернатив на 3 архитектурных варианта конвейера (Middleware, Pydantic, Послойный конвейер) с матрицей критериев | Сравнение по 4 критериям (RFC/CASE, unit-тестируемость, оверхед, безопасность) | Монолитный глобальный Middleware (Альтернатива A) |
| RAG | [`rag/experiment.md`](rag/experiment.md) | [`tests_integration.md`](../practice_01/tests_integration.md) | Grounding тестовых сценариев: привязка каждого теста к строкам CASE.md (64–67), фиксация кодов 413/422/504 | Сверка точных цитат и номеров строк в CASE.md и TRAINING_PR.diff | Проверка контекстного окна LLM и JWT-авторизации (вне скоупа) |
| ReAct | [`react/experiment.md`](react/experiment.md) | [`project_management.md`](../practice_01/project_management.md) | Автономная локализация и исправление дефектов Mermaid (задача a6) и удаление плейсхолдера за 3 шага | Автоматический вызов `make step1` в терминале ReAct (код 0) | Изменение файлов за пределами скоупа задачи |

## Независимое ревью

| Замечание другой команды | Где исправили | Evidence |
|---|---|---|
| Двусмысленность: неоднозначность места валидации длины diff и конфликта статус-кодов 422 vs 413 | [`practices/practice_01/analysis.md`](../practice_01/analysis.md), [`project_management.md`](../practice_01/project_management.md) | Зафиксировано: длина > 20000 симв. отсекается до сервиса с кодом HTTP 413 Payload Too Large согласно [`CASE.md:65`](../practice_01/CASE.md#L65) (API-1), а невалидная схема возвращает HTTP 422 |
| Непроверяемое требование: качественные формулировки «контролируемые ошибки» и «нейтрализация инъекций» | [`practices/practice_01/tests_load.md`](../practice_01/tests_load.md), [`problem.md`](../practice_01/problem.md) | Введены точные SLA: 100% сбоев LLM маппятся в HTTP 504/502 с контролируемым JSON, 0% 500, p99 < 10.5с ([`CASE.md:66`](../practice_01/CASE.md#L66), REL-1); 0% успешных инъекций |
| Пропущенный риск или источник: риск утечки кода и секретов через stdout-логирование сервиса | [`practices/practice_01/analysis.md`](../practice_01/analysis.md) (строка OBS-1), [`chain_of_verification/experiment.md`](chain_of_verification/experiment.md) | В конвейер добавлено ограничение [`CASE.md:70`](../practice_01/CASE.md#L70) (OBS-1): логируются только `request_id`, длительность и статус; сырой diff и ответ модели в лог не пишутся |

