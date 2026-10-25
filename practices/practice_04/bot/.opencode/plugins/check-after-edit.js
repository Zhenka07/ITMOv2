/**
 * OpenCode 2 Plugin: Hook автоматической проверки после редактирования файлов
 * Запускает доверенный runner `sh scripts/check.sh` при вызове инструментов изменения кода.
 */

export default function (ctx) {
  ctx.tool.hook("execute.after", async (toolCall, result) => {
    // Проверяем, изменил ли инструмент файл в проекте
    const editTools = ["edit_file", "write_to_file", "replace_file_content", "apply_patch"];
    if (!editTools.includes(toolCall.name)) {
      return;
    }

    // Запускаем единый runner проверок проекта
    try {
      const execResult = await ctx.exec("sh scripts/check.sh");
      if (execResult.exitCode !== 0) {
        return {
          ...result,
          warning: `[Auto-check FAILED] scripts/check.sh завершился с ошибкой (код ${execResult.exitCode}):\n${execResult.stderr || execResult.stdout}`
        };
      }
    } catch (err) {
      return {
        ...result,
        warning: `[Auto-check ERROR] Не удалось запустить scripts/check.sh: ${err.message}`
      };
    }
  });
}
