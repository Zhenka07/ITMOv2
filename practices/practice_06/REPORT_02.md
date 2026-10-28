# Отчёт 2. Результаты устранения уязвимостей и повторного тестирования сервиса Mini Shop

**Объект аудита**: Исправленная версия `practices/practice_06/lab/service.py`  
**Дата проведения**: 28 октября 2026 г.  
**Результат**: Все 11 уязвимостей успешно устранены, 26 автоматических тестов (функциональные + регрессионные безопасности) успешно пройдены.

---

## 1. Сводная матрица верификации (До и После исправления)

| ID | Уязвимость | Статус до исправления | Статус после исправления | Примененная мера защиты в коде | Метод проверки |
|---|---|---|---|---|---|
| **VULN-01** | Подделка роли через заголовок `X-Role: staff` | **200 OK** (Утечка всех профилей) | **403 Forbidden** (Требуется сессия сотрудника) | Роль извлекается только из `self.sessions[token]["role"]`, заголовок `X-Role` игнорируется | `test_admin_export_rejects_header_spoofing` |
| **VULN-02** | Неавторизованный доступ к заказам (IDOR) | **200 OK** (Чужие заказы видны всем) | **401 Unauthorized** / **403** (Изоляция по владельцу) | Обязательная аутентификация `X-Token`, фильтрация `WHERE owner = session["id"]` | `test_orders_requires_authentication` |
| **VULN-03** | SQL-инъекция в `GET /profile` | **200 OK** (Выполнение произвольного SQL) | **400 Bad Request** / **403** | Строгая параметризация `WHERE id = ?` и числовая валидация `int(id)` | `test_profile_and_search_sqli_blocked` |
| **VULN-04** | SQL-инъекция в `GET /search` | **200 OK** (Дамп всей таблицы) | **200 OK** (Безопасный поиск по подстроке) | Параметризованный запрос `WHERE name LIKE ?` с аргументом `(%q%,)` | `test_profile_and_search_sqli_blocked` |
| **VULN-05** | Обход каталога (Path Traversal) в `/files` | **200 OK** (Чтение секретов и чужих чеков) | **403 Forbidden** | Блокировка `..`, `private` и проверка `requested_user == session["username"]` | `test_files_path_traversal` |
| **VULN-06** | Утечка паролей и токенов в `/debug/logs` | **200 OK** (Открытые пароли и токены) | **403 Forbidden** для клиентов, маскирование `***` для staff | Доступ только для роли `staff`, автоматическая маскировка паролей и токенов в логе | `test_debug_logs_restricted_to_staff` |
| **VULN-07** | Подмена цены товара при покупке | **201 Created** (Стул куплен за 1 руб.) | **201 Created** (Принудительная цена 5000 руб.) | Цена берётся строго из каталога `self.products[product]`, входное поле `price` игнорируется | `test_price_tampering_ignored` |
| **VULN-08** | Хранимая XSS в отзывах `/reviews/view` | **200 OK** (Исполнение `<script>` в браузере) | **200 OK** (Безопасное экранирование `&lt;script&gt;`) | Вызов `html.escape()` при формировании HTML-разметки | `test_stored_xss_html_escaped` |
| **VULN-09** | SQL-инъекция в `/assistant/context` | **200 OK** (Манипуляция контекстом) | **200 OK** / **400** (Параметризованный запрос) | Запрос с параметром `WHERE id = ? AND owner = ?` с валидацией `int(order_id)` | `test_assistant_context_parameterized` |
| **VULN-10** | Непрямая инъекция промпта через отзывы | **Уязвимо** (Модель исполняла чужие команды) | **Нейтрализовано** (Структурные теги + серверный контроль) | Оборачивание отзывов в `<untrusted_reviews>` + запрет исполнения опасных действий сервером | `test_assistant_context_separates_untrusted_reviews` |
| **VULN-11** | Чрезмерные полномочия инструментов AI (`delete_tree`) | **200 OK** (Песочница удалена) | **403 Forbidden** (Инструмент деактивирован) | Полный запрет инструмента `delete_tree`, ролевой контроль инструментов по сессии | `test_assistant_execute_blocks_delete_tree` |

---

## 2. Архитектурные изменения и принцип Defense in Depth

### Принцип 1. Zero Trust к клиентским заголовкам
Клиент больше не может объявить себя администратором через `X-Role: staff`. Идентификация и авторизация строятся исключительно на основе криптографически стойкого токена сессии `X-Token` (UUIDv4), сопоставляемого с серверным реестром `self.sessions`:
```python
session = self.get_session(headers)
if not session or session["role"] != "staff":
    return 403, {"error": "staff only"}
```

### Принцип 2. Полное устранение SQL-инъекций (Параметризация)
Все небезопасные f-строки вида `f"SELECT ... WHERE id = {query.get('id')}"` заменены на строго параметризованные запросы к движку SQLite:
```python
return 200, self.rows("SELECT * FROM profiles WHERE id = ?", (target_id_int,))
return 200, self.rows("SELECT * FROM profiles WHERE name LIKE ?", (f"%{q}%",))
```

### Принцип 3. Защита на стороне сервера от атак на LLM (Server-side Guardrails)
В AI-инженерии существует опасное заблуждение: «Если мы напишем хороший системный промпт, модель никогда не выполнит опасное действие». В реальности промпт-инъекции недетерминированы и могут обойти любую текстовую инструкцию.
Поэтому в `service.py` реализован **Server-Side Enforcement**:
1. **Деструктивный инструмент `delete_tree` отключен на уровне бэкенда**: Даже если скомпрометированная модель вернет `{"tool": "delete_tree", "arguments": {"path": "."}}`, сервер вернет:
   ```json
   HTTP 403 Forbidden: {"error": "forbidden: destructive tool delete_tree is disabled"}
   ```
2. **Инструмент `export_profiles` ограничен ролью `staff`**: Обычный покупатель (даже через решение AI) не может экспортировать базу клиентов.
3. **Инструмент `read_file` ограничен каталогом текущего пользователя**: Клиент `alice` может прочитать только `files/alice/*`. Пути с `..`, ведущие слэши и каталог `private/` заблокированы.
4. **Контекст разграничен XML-тегами**: Недоверенные отзывы покупателей помещены в теги `<untrusted_reviews>` с явным системным предупреждением об отсутствии у них командной силы.

---

## 3. Результаты выполнения проверочных команд

Вызов проверочного пайплайна:
```bash
make step6
# или
make test
```

### Лог прохождения тестов (26 из 26 OK):
```text
Standard library only: ready
test_health_and_not_found (test_http.HttpTest.test_health_and_not_found) ... ok
test_login_and_purchase_over_http (test_http.HttpTest.test_login_and_purchase_over_http) ... ok
test_transport_only_binds_loopback (test_http.HttpTest.test_transport_only_binds_loopback) ... ok
test_admin_export_rejects_header_spoofing_without_valid_session (test_security.SecurityRegressionTest) ... ok
test_assistant_context_separates_untrusted_reviews (test_security.SecurityRegressionTest) ... ok
test_assistant_execute_blocks_delete_tree (test_security.SecurityRegressionTest) ... ok
test_assistant_execute_blocks_unauthorized_tools_and_files (test_security.SecurityRegressionTest) ... ok
test_debug_logs_restricted_to_staff_and_masks_passwords (test_security.SecurityRegressionTest) ... ok
test_files_path_traversal_and_cross_user_access_blocked (test_security.SecurityRegressionTest) ... ok
test_orders_requires_authentication_and_enforces_user_isolation (test_security.SecurityRegressionTest) ... ok
test_price_tampering_ignored_catalog_price_enforced (test_security.SecurityRegressionTest) ... ok
test_profile_and_search_sqli_blocked (test_security.SecurityRegressionTest) ... ok
test_stored_xss_html_escaped (test_security.SecurityRegressionTest) ... ok
test_delete_of_fixture_root_stays_inside_exercise (test_service.SandboxTest) ... ok
test_external_directory_cannot_be_deleted (test_service.SandboxTest) ... ok
test_parent_paths_cannot_escape_exercise (test_service.SandboxTest) ... ok
test_symlink_cannot_escape_exercise (test_service.SandboxTest) ... ok
test_assistant_can_return_own_receipt (test_service.ShopTest) ... ok
test_customer_can_buy_at_catalog_price (test_service.ShopTest) ... ok
test_health_and_catalog (test_service.ShopTest) ... ok
test_own_profile_and_receipt (test_service.ShopTest) ... ok
test_review_can_be_submitted_and_viewed (test_service.ShopTest) ... ok
test_staff_can_export_with_staff_session (test_service.ShopTest) ... ok
test_tokens_identify_distinct_users (test_service.ShopTest) ... ok
test_unknown_product_rejected (test_service.ShopTest) ... ok
test_wrong_password_rejected (test_service.ShopTest) ... ok

----------------------------------------------------------------------
Ran 26 tests in 0.623s

OK
```

---

## 4. Оценка остаточных рисков (Residual Risks)

1. **In-Memory хранилище сессий**: Сессии хранятся в памяти процесса Python. При перезапуске сервера токены инвалидируются. Для производственной среды рекомендуется использовать Redis / Keycloak с контролем времени жизни (TTL) и ротацией токенов.
2. **Отсутствие Rate Limiting**: Сервис не ограничивает частоту вызовов эндпоинтов `/login` (риск подбора паролей). В проде требуется внедрить алгоритм Token Bucket или Nginx limit_req.
3. **Транспортный уровень**: В учебном стенде используется HTTP (без TLS) на `127.0.0.1`. В промышленной среде обязателен HTTPS (TLS 1.3).
