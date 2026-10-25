/**
 * Test runner to verify .opencode/plugins/check-after-edit.js hook behavior.
 */

import { exec } from "child_process";
import { promisify } from "util";
import hookPlugin from "./check-after-edit.js";

const execAsync = promisify(exec);

async function testHook() {
  console.log("=== ТЕСТИРОВАНИЕ HOOK ПЛАГИНА (check-after-edit.js) ===\n");

  let registeredHook = null;
  const mockCtx = {
    tool: {
      hook: (event, handler) => {
        if (event === "execute.after") {
          registeredHook = handler;
        }
      }
    },
    exec: async (command) => {
      try {
        const { stdout, stderr } = await execAsync(command);
        return { exitCode: 0, stdout, stderr };
      } catch (err) {
        return { exitCode: err.code || 1, stdout: err.stdout, stderr: err.stderr };
      }
    }
  };

  // 1. Инициализация плагина
  hookPlugin(mockCtx);
  console.log("1. Плагин успешно зарегистрировал хук 'execute.after'");

  // 2. Проверка не-edit инструмента (например, read_file)
  const readToolCall = { name: "read_file", args: { path: "README.md" } };
  const readResult = await registeredHook(readToolCall, { content: "ok" });
  console.log("2. Инструмент 'read_file' пропущен без запуска проверок:", readResult === undefined ? "PASS" : "FAIL");

  // 3. Проверка успешного редактирования (PASS)
  console.log("3. Симуляция успешного редактирования: запуск scripts/check.sh...");
  const editToolCall = { name: "edit_file", args: { path: "client/events/telegram/commands.go" } };
  const passResult = await registeredHook(editToolCall, { success: true });
  console.log("   Результат проверки при валидном коде (PASS):", passResult === undefined ? "Проверки успешно пройдены (нет ошибок)" : passResult);

  // 4. Симуляция поломки кода (FAIL)
  console.log("4. Симуляция правки с ошибкой (mock context возвращает ошибку сборки):");
  const failingCtx = {
    ...mockCtx,
    exec: async () => ({
      exitCode: 1,
      stdout: "",
      stderr: "client/events/telegram/commands.go:42: syntax error: unexpected semicolon"
    })
  };
  hookPlugin(failingCtx);
  const failResult = await registeredHook(editToolCall, { success: true });
  console.log("   Результат проверки при ошибке (FAIL перехвачен хуком):");
  console.log("   ", failResult.warning);

  console.log("\n=== ТЕСТ HOOK УСПЕШНО ЗАВЕРШЕН ===");
}

testHook().catch(console.error);
