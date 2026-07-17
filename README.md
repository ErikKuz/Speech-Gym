# SpeechGym

SpeechGym - учебная система для тренировки публичной речи. Пользователь создаёт тренировочную сессию, загружает аудиозапись выступления и получает результаты распознавания и аналитический PDF-отчёт.

## Возможности

- регистрация и авторизация по JWT;
- создание и редактирование речевых сессий;
- загрузка аудиофайлов;
- асинхронная обработка заданий через RabbitMQ;
- распознавание речи с помощью faster-whisper;
- хранение файлов и отчётов в MinIO;
- формирование аналитических отчётов;
- REST API и отдельный desktop-клиент на PyQt5.

## Структура проекта

- `speechgym-api` - основной backend на Java 21, Spring Boot, Spring Security и Spring Data JPA;
- `asr-service` - сервис распознавания речи на FastAPI;
- `test_anal` - сервис анализа речи и генерации отчётов;
- `speechlab_pyqt` - desktop-интерфейс на Python/PyQt5;
- `docker-compose.yml` - PostgreSQL, RabbitMQ, MinIO и сервисы приложения;
- `PROJECT_STUDY_PLAN.md` - подробный учебный разбор архитектуры;
- `speechgym-api/src/main/java/com/speechgym/docs` - API-контракт, модель данных и документация по запуску.

## Требования

- Git;
- Docker Desktop с Docker Compose;
- Python 3.10+ для запуска desktop-клиента.

При первом запуске ASR-сервису может потребоваться время для загрузки модели распознавания речи.

## Запуск backend и инфраструктуры

1. Клонируйте и откройте проект:

```bash
git clone https://github.com/Erik6204/Speech-Gym.git
cd Speech-Gym
```

2. Создайте в корне файл `.env` и добавьте ключ GigaChat:

```env
GIGACHAT_AUTH_KEY=your_key
```

Файл `.env` исключён из Git и не должен публиковаться.

3. Соберите и запустите приложение:

```bash
docker compose up --build -d
docker compose ps
```

После запуска доступны:

- API: `http://localhost:8080/api/v1`;
- состояние backend: `http://localhost:8080/actuator/health`;
- RabbitMQ Management: `http://localhost:15672` (`speechgym` / `speechgym`);
- MinIO Console: `http://localhost:9001` (`minioadmin` / `minioadmin`);
- ASR health: `http://localhost:8000/health`;
- report service health: `http://localhost:8001/health`.

Остановить приложение:

```bash
docker compose down
```

## Запуск desktop-клиента

Сначала должен быть запущен backend на порту `8080`.

```powershell
cd speechlab_pyqt
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

Клиент по умолчанию обращается к `http://127.0.0.1:8080/api/v1`. Если PyQt не находит platform plugin, скорректируйте `QT_QPA_PLATFORM_PLUGIN_PATH` в `speechlab_pyqt/main.py` под расположение своей виртуальной среды.

## API

Базовый путь: `/api/v1`. Защищённые endpoint-ы принимают JWT в заголовке:

```http
Authorization: Bearer <access-token>
```

Подробные примеры запросов находятся в `speechgym-api/test-requests.http` и `speechgym-api/src/main/java/com/speechgym/docs/api-contract.md`.

