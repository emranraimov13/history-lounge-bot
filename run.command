#!/bin/zsh
# Запуск бота двойным кликом. Окно терминала должно оставаться открытым.
cd "$(dirname "$0")" || exit 1

if [ ! -d ".venv" ]; then
  echo "Первый запуск: устанавливаю зависимости…"
  python3 -m venv .venv || exit 1
  .venv/bin/pip install --upgrade pip
  .venv/bin/pip install -r requirements.txt || exit 1
fi

exec .venv/bin/python -m bot.main
