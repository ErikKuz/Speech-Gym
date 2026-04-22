# Подробный план разбора и воспроизведения проекта

## Зачем нужен этот документ

Этот план нужен не для того, чтобы просто "прочитать код", а чтобы:

1. понять, как проект устроен как система;
2. научиться видеть, зачем существует каждый слой;
3. научиться мысленно прогонять запрос от HTTP-входа до базы данных, очереди и объектного хранилища;
4. дойти до состояния, когда ты сможешь сам воспроизвести похожее приложение с другими бизнес-идеями.

Главная идея: не пытайся понять весь проект за один проход. Правильнее изучать его слоями, от внешнего поведения к внутренней реализации.

---

## Что это за проект простыми словами

Этот репозиторий состоит из двух основных частей:

- `speechgym-api` - основной backend на `Spring Boot`, который:
  - регистрирует и логинит пользователей;
  - создает сессии тренировки речи;
  - принимает аудиофайлы;
  - создает асинхронные задачи обработки;
  - хранит артефакты и отчеты;
  - отдает PDF-отчеты;
  - следит за безопасностью и правами доступа.
- `asr-service` - отдельный сервис на `FastAPI`, который умеет принимать аудио и расшифровывать его через `faster-whisper`.

Важный нюанс текущей реализации:

- Python ASR-сервис уже есть как отдельный компонент;
- но текущий `JobWorker` внутри `speechgym-api` пока не вызывает его напрямую;
- вместо этого worker сейчас генерирует демонстрационные JSON/PDF-результаты заглушками.

Это очень полезно понимать с самого начала: архитектура уже рассчитана на внешнюю обработку, но интеграция пока не доведена до конца. Для Junior это отличный пример того, как реальные проекты часто развиваются поэтапно.

---

## Архитектурная карта проекта

Смотри на проект как на цепочку из 10 блоков:

1. `Controller`
   - принимает HTTP-запрос;
   - валидирует вход;
   - возвращает HTTP-ответ.
2. `Service`
   - содержит бизнес-логику;
   - решает, какие проверки нужны;
   - вызывает репозитории, storage, очередь и другие сервисы.
3. `Repository`
   - читает и пишет данные в БД через Spring Data JPA.
4. `Entity`
   - описывает, как Java-объект связан с таблицей в БД.
5. `DTO`
   - определяет форму входных и выходных данных API.
6. `Security`
   - проверяет JWT;
   - достает текущего пользователя из токена.
7. `Idempotency`
   - защищает от повторного создания одной и той же сущности при ретраях.
8. `Queue`
   - отделяет создание задачи от ее выполнения;
   - делает обработку асинхронной.
9. `Storage`
   - сохраняет аудио и артефакты в MinIO.
10. `Worker`
   - выполняет фоновую обработку задачи по этапам.

Мысленная картинка:

`HTTP -> Controller -> Service -> Repository/Storage/Queue -> DB/MinIO/RabbitMQ -> Worker -> Artifacts/Report -> HTTP polling`

---

## В каком порядке изучать проект

Ниже идет не просто список файлов, а оптимальный маршрут. Если будешь идти в этом порядке, мозг будет постоянно опираться на уже понятный слой, а не тонуть в деталях.

---

## Этап 1. Сначала пойми продукт и сценарии пользователя

### Цель

До чтения кода понять, что вообще делает система с точки зрения пользователя.

### Что открыть

- `speechgym-api/src/main/java/com/speechgym/docs/api-contract.md`
- `speechgym-api/test-requests.http`

### Что нужно увидеть

Тут описано внешнее поведение системы:

- как пользователь регистрируется;
- как получает токены;
- как создает speech session;
- как загружает аудио;
- как создает job;
- как опрашивает статус;
- как получает report и PDF.

### Как это представлять в голове

Представь обычный desktop или web-клиент:

1. пользователь регистрируется;
2. получает `accessToken` и `refreshToken`;
3. создает тренировочную сессию;
4. загружает аудио;
5. запускает обработку;
6. backend не держит пользователя в ожидании, а сразу отвечает `202 Accepted`;
7. потом клиент периодически спрашивает статус job;
8. когда job завершена, пользователь получает report.

### Что важно понять

- API-контракт идет раньше кода.
- Если ты понимаешь контракт, то потом уже можешь проверять, как именно код его реализует.
- `test-requests.http` показывает "живые" примеры запросов, а значит помогает быстро связать теорию с практикой.

### Что сделать руками

1. Выпиши все endpoint'ы в тетрадь или Notion.
2. Для каждого endpoint'а подпиши:
   - что получает на вход;
   - что возвращает;
   - нужна ли авторизация;
   - создает ли он данные или только читает.
3. Нарисуй цепочку из 6-8 шагов пользовательского сценария.

### Вопросы для самопроверки

1. Почему `POST /sessions/{sessionId}/jobs` возвращает `202 Accepted`, а не `200 OK`?
2. Почему `Idempotency-Key` нужен именно на операциях создания, а не на всех endpoint'ах?

### Теория

- Spring Boot Reference: https://docs.spring.io/spring-boot/docs/3.3.5/reference/html/
- RFC 9457, Problem Details for HTTP APIs: https://datatracker.ietf.org/doc/html/rfc9457

---

## Этап 2. Разберись, как проект запускается и из чего он состоит

### Цель

Понять инфраструктуру проекта: что именно должно быть поднято, чтобы backend жил.

### Что открыть

- `docker-compose.yml`
- `speechgym-api/pom.xml`
- `speechgym-api/src/main/resources/application.yml`
- `speechgym-api/src/main/resources/application-local.yml`
- `speechgym-api/src/main/java/com/speechgym/docs/runbook-dev.md`
- `speechgym-api/Dockerfile`
- `asr-service/Dockerfile`

### Что нужно увидеть

Инфраструктурные компоненты:

- `PostgreSQL` для хранения данных;
- `RabbitMQ` для очередей;
- `MinIO` для хранения файлов и артефактов;
- `Spring Boot` как основной API;
- `FastAPI` как сервис ASR.

### Как это представлять в голове

`docker-compose.yml` не "про бизнес-логику". Он отвечает на вопрос:

"Какие внешние сервисы нужны приложению, чтобы его код вообще смог нормально работать?"

`application.yml` отвечает на другой вопрос:

"Куда приложению подключаться и какие у него прикладные настройки?"

`pom.xml` отвечает на третий вопрос:

"Из каких библиотек вообще собран этот backend?"

### Что важно понять

- `spring-boot-starter-web` = HTTP API.
- `spring-boot-starter-security` и `oauth2-resource-server` = защита API и работа с JWT.
- `spring-boot-starter-data-jpa` = работа с БД через сущности и репозитории.
- `spring-boot-starter-amqp` = интеграция с RabbitMQ.
- `minio` = объектное хранилище.
- `pdfbox` = генерация PDF.
- `flyway` = миграции схемы БД.

### Что сделать руками

1. Сделай таблицу из трех колонок:
   - компонент;
   - зачем нужен;
   - что сломается без него.
2. Выпиши все зависимости из `pom.xml` и подпиши назначение каждой.
3. Найди в `application.yml`, какие настройки относятся:
   - к JWT;
   - к MinIO;
   - к RabbitMQ;
   - к idempotency.

### Вопросы для самопроверки

1. Почему база, очередь и object storage вынесены в отдельные сервисы, а не живут "внутри Spring Boot"?
2. Чем `application-local.yml` отличается по смыслу от `application.yml`?

### Теория

- Spring Boot externalized configuration: https://docs.spring.io/spring-boot/docs/3.3.5/reference/html/features.html#features.external-config
- Flyway docs: https://documentation.red-gate.com/fd
- RabbitMQ tutorials: https://www.rabbitmq.com/tutorials
- MinIO Java SDK: https://github.com/minio/minio-java

---

## Этап 3. Пойми архитектурные решения, а не только реализацию

### Цель

Научиться видеть не только "что написано", но и "почему выбрали именно так".

### Что открыть

- `speechgym-api/src/main/java/com/speechgym/docs/decisions.md`
- `speechgym-api/src/main/java/com/speechgym/docs/data-model.md`

### Что нужно увидеть

В `decisions.md` зафиксированы важные архитектурные решения:

- почему JWT выпускаются локально;
- почему upload идет через backend;
- почему worker пока находится в том же Spring Boot приложении;
- почему используется RabbitMQ;
- почему выбран idempotency;
- почему доступ к данным ограничивается по `user_id`.

### Как это представлять в голове

Архитектурное решение всегда похоже на ответ на вопрос:

"Из нескольких возможных путей мы сознательно выбрали вот этот, потому что..."

Если ты научишься читать такие решения, ты перестанешь смотреть на код как на магию. Ты увидишь, что код почти всегда является следствием компромиссов.

### Что важно понять

- MVP почти всегда проще, чем production-идеал.
- Хорошая архитектура не обязана быть "максимально сложной".
- В проекте уже видны места для эволюции:
  - вынос worker в отдельный сервис;
  - полноценная интеграция с ASR;
  - presigned upload flow;
  - outbox pattern для более надежной доставки сообщений.

### Что сделать руками

1. Для каждого ADR выпиши:
   - какое решение принято;
   - какой плюс это дает сейчас;
   - какое ограничение это создает позже.
2. Отдельно выпиши, какие куски проекта выглядят как "точки для будущего расширения".

### Вопросы для самопроверки

1. Почему в MVP допустимо держать API и worker в одном приложении?
2. Почему доступ к чужому объекту возвращает `404`, а не `403`?

### Теория

- Spring Security JWT resource server: https://docs.spring.io/spring-security/reference/servlet/oauth2/resource-server/jwt.html
- JWT RFC 7519: https://datatracker.ietf.org/doc/html/rfc7519

---

## Этап 4. Разбери входную точку приложения и конфигурацию Spring

### Цель

Понять, как приложение стартует и откуда Spring берет свои бины.

### Что открыть

- `speechgym-api/src/main/java/com/speechgym/SpeechgymApiApplication.java`
- `speechgym-api/src/main/java/com/speechgym/common/config/AppProperties.java`
- `speechgym-api/src/main/java/com/speechgym/common/config/MinioConfig.java`
- `speechgym-api/src/main/java/com/speechgym/common/config/RabbitMessagingConfig.java`
- `speechgym-api/src/main/java/com/speechgym/common/persistence/AbstractAuditableEntity.java`

### Что нужно увидеть

Здесь ты изучаешь каркас приложения:

- `@SpringBootApplication` запускает автоконфигурацию и сканирование;
- `@ConfigurationPropertiesScan` поднимает typed-config;
- `AppProperties` собирает настройки в типизированную структуру;
- config-классы создают инфраструктурные бины;
- `AbstractAuditableEntity` централизует `created_at` и `updated_at`.

### Как это представлять в голове

До первого HTTP-запроса Spring делает огромную подготовительную работу:

1. читает конфигурацию;
2. создает beans;
3. собирает filter chain безопасности;
4. готовит JPA;
5. настраивает RabbitMQ-конвертер;
6. готовит MinIO-клиент.

То есть приложение "оживает" еще до того, как кто-то открыл endpoint.

### Что важно понять

- Config-класс не делает бизнес-логику. Он только говорит Spring, что и как создать.
- `record AppProperties` делает настройки типобезопасными.
- `AbstractAuditableEntity` избавляет от повторения `createdAt/updatedAt` в каждой сущности.

### Что сделать руками

1. Нарисуй схему: `application.yml -> AppProperties -> Config beans -> Services`.
2. Ответь письменно:
   - откуда берется `MinioClient`;
   - откуда берется exchange/queue;
   - кто заполняет `createdAt` и `updatedAt`.

### Вопросы для самопроверки

1. Почему конфиги выносят в отдельные классы, а не создают клиентов прямо внутри сервисов?
2. Что дает `ConfigurationProperties`, чего не дает просто `@Value` в нескольких местах?

### Теория

- Spring Boot configuration properties: https://docs.spring.io/spring-boot/docs/3.3.5/reference/html/features.html#features.external-config.typesafe-configuration-properties
- Spring AMQP reference: https://docs.spring.io/spring-amqp/reference/

---

## Этап 5. Разбери безопасность: как приложение понимает, кто перед ним

### Цель

Понять аутентификацию и авторизацию не "по словам", а по реальному пути данных.

### Что открыть

- `speechgym-api/src/main/java/com/speechgym/common/security/SecurityConfig.java`
- `speechgym-api/src/main/java/com/speechgym/common/security/CurrentUserService.java`
- `speechgym-api/src/main/java/com/speechgym/auth/JwtTokenService.java`
- `speechgym-api/src/main/java/com/speechgym/auth/AuthController.java`
- `speechgym-api/src/main/java/com/speechgym/auth/AuthService.java`
- `speechgym-api/src/main/java/com/speechgym/auth/UserEntity.java`
- `speechgym-api/src/main/java/com/speechgym/auth/SubscriptionEntity.java`

### Что нужно увидеть

Тут скрыт один из самых важных сквозных механизмов проекта:

1. пользователь регистрируется;
2. пароль хешируется через `BCryptPasswordEncoder`;
3. создается `UserEntity`;
4. создается `SubscriptionEntity`;
5. `JwtTokenService` выпускает access и refresh токены;
6. при защищенном запросе Spring валидирует JWT;
7. `CurrentUserService` берет `sub` из токена;
8. `userId` идет дальше в сервисы;
9. все запросы к данным фильтруются по `userId`.

### Как это представлять в голове

Здесь есть две разные задачи:

- аутентификация: "кто ты?"
- авторизация: "что тебе можно?"

В этом проекте:

- аутентификация строится на JWT;
- авторизация строится в основном через объектную принадлежность по `user_id`.

То есть не клиент говорит "это мой объект", а сервер сам это проверяет через БД.

### Что важно понять

- `SecurityFilterChain` определяет, какие маршруты публичные, а какие защищенные.
- `JwtDecoder` и `JwtEncoder` работают с одним секретом.
- `JwtAuthenticationConverter` превращает claim `role` в Spring authority.
- `CurrentUserService` - маленький, но очень важный мост между Spring Security и бизнес-логикой.

### Что сделать руками

1. Нарисуй полный поток `POST /auth/register`.
2. Нарисуй полный поток `GET /me`.
3. Отдельно выпиши, какие claims попадают в JWT.
4. Объясни самому себе вслух:
   - почему пароль хранится не в открытом виде;
   - почему `sub` используется как user id.

### Вопросы для самопроверки

1. Зачем приложению одновременно `accessToken` и `refreshToken`?
2. Почему сервисы работают с `UUID userId`, а не доверяют какому-нибудь `X-User-Id` из заголовка?

### Теория

- Spring Security JWT resource server: https://docs.spring.io/spring-security/reference/servlet/oauth2/resource-server/jwt.html
- Password storage guidance via Spring Security docs: https://docs.spring.io/spring-security/reference/features/authentication/password-storage.html

---

## Этап 6. Разбери стандартный CRUD-паттерн на примере Sessions

### Цель

Понять базовый шаблон backend-модуля, который потом ты сможешь повторить в своих проектах.

### Что открыть

- `speechgym-api/src/main/java/com/speechgym/sessions/SessionController.java`
- `speechgym-api/src/main/java/com/speechgym/sessions/SessionService.java`
- `speechgym-api/src/main/java/com/speechgym/sessions/SessionRepository.java`
- `speechgym-api/src/main/java/com/speechgym/sessions/SessionEntity.java`
- `speechgym-api/src/main/java/com/speechgym/sessions/dto/CreateSessionRequest.java`
- `speechgym-api/src/main/java/com/speechgym/sessions/dto/UpdateSessionRequest.java`
- `speechgym-api/src/main/java/com/speechgym/sessions/dto/SessionResponse.java`
- `speechgym-api/src/main/java/com/speechgym/sessions/dto/SessionListResponse.java`

### Что нужно увидеть

Это почти идеальный учебный модуль для старта:

- `Controller` принимает запрос и передает его дальше;
- `DTO` валидирует форму запроса;
- `Service` решает, что делать;
- `Repository` делает поиск/сохранение;
- `Entity` описывает таблицу;
- response DTO оформляет выход.

### Как это представлять в голове

На запрос `POST /sessions` происходит примерно следующее:

1. HTTP-запрос приходит в `SessionController`.
2. `@RequestHeader("Idempotency-Key")` проверяет наличие заголовка.
3. `@Valid @RequestBody CreateSessionRequest` валидирует тело.
4. `CurrentUserService.requireUserId()` достает `userId` из JWT.
5. `SessionService.createSession(...)` запускает бизнес-логику.
6. Логика проверяет idempotency.
7. Если нужно, создает `SessionEntity`.
8. `SessionRepository.save(...)` пишет в БД.
9. Сервис маппит сущность в `SessionResponse`.
10. Контроллер отдает `201 Created` и `Location`.

### Что важно понять

- Контроллер здесь максимально тонкий. Это хорошо.
- Вся важная логика сидит в сервисе.
- DTO и Entity не одно и то же:
  - DTO описывает контракт API;
  - Entity описывает модель хранения.
- Метод `requireOwnedSession(...)` - это очень важный паттерн инкапсуляции правила владения ресурсом.

### Что сделать руками

1. Возьми лист и распиши по строчкам поток `GET /sessions/{sessionId}`.
2. Ответь:
   - где именно происходит проверка владения сессией;
   - где строится pagination;
   - где формируется response.
3. Попробуй вручную переписать этот модуль в упрощенном виде:
   - только `title`;
   - только create/list/get;
   - без idempotency.

### Вопросы для самопроверки

1. Почему `SessionRepository` не должен решать бизнес-вопрос "можно ли пользователю создавать сессию"?
2. Чем DTO полезнее, чем отдавать `SessionEntity` прямо наружу?

### Теория

- Spring Data JPA reference: https://docs.spring.io/spring-data/jpa/reference/
- Spring validation with Bean Validation: https://docs.spring.io/spring-framework/reference/core/validation/beanvalidation.html

---

## Этап 7. Разбери idempotency как отдельную инженерную идею

### Цель

Понять, почему надежный backend думает не только о happy path, но и о повторах, ретраях и нестабильной сети.

### Что открыть

- `speechgym-api/src/main/java/com/speechgym/common/idempotency/IdempotencyService.java`
- `speechgym-api/src/main/java/com/speechgym/common/idempotency/IdempotencyKeyEntity.java`
- `speechgym-api/src/main/java/com/speechgym/common/idempotency/IdempotencyKeyRepository.java`
- `speechgym-api/src/main/resources/db/migration/V3__idempotency_keys.sql`
- `speechgym-api/src/test/java/com/speechgym/speechgym_api/IdempotencyIT.java`

### Что нужно увидеть

Механизм здесь такой:

1. request body сериализуется в JSON;
2. от него считается `SHA-256` hash;
3. если для данного `userId + idempotencyKey` уже есть сохраненный ответ:
   - и hash совпадает, возвращается старый ответ;
   - и hash не совпадает, возвращается `409 Conflict`.

### Как это представлять в голове

Представь, что клиент отправил `POST /sessions`, но интернет оборвался в момент ответа. Клиент не знает, создалась сессия или нет. Он делает повторную отправку. Без idempotency:

- возможно, создастся дубликат.

С idempotency:

- сервер скажет: "Я уже видел этот запрос, вот тот же самый ответ".

### Что важно понять

- Idempotency - это не "декоративная фича", а защита от дублирования данных.
- Здесь хранится не только ключ, но и тело ответа.
- TTL ограничивает срок хранения таких записей.

### Что сделать руками

1. Нарисуй таблицу `idempotency_keys` и подпиши каждое поле.
2. Объясни себе, зачем нужен `request_hash`, а не только сам `idempotency_key`.
3. Сформулируй своими словами:
   - какой баг предотвращает этот механизм;
   - почему он особенно важен для create-операций.

### Вопросы для самопроверки

1. Почему одинаковый ключ с другим body должен возвращать `409`, а не молча создавать новую запись?
2. Почему idempotency обычно не нужна для `GET`?

### Теория

- Spring Boot Reference: https://docs.spring.io/spring-boot/docs/3.3.5/reference/html/
- HTTP methods overview: https://developer.mozilla.org/en-US/docs/Web/HTTP/Methods

---

## Этап 8. Разбери загрузку файлов и object storage

### Цель

Понять, как backend работает с бинарными файлами и почему аудио хранится не в самой БД.

### Что открыть

- `speechgym-api/src/main/java/com/speechgym/uploads/UploadController.java`
- `speechgym-api/src/main/java/com/speechgym/uploads/UploadService.java`
- `speechgym-api/src/main/java/com/speechgym/uploads/UploadEntity.java`
- `speechgym-api/src/main/java/com/speechgym/uploads/UploadRepository.java`
- `speechgym-api/src/main/java/com/speechgym/storage/StorageService.java`
- `speechgym-api/src/main/java/com/speechgym/storage/MinioStorageService.java`
- `speechgym-api/src/main/java/com/speechgym/common/config/MinioConfig.java`

### Что нужно увидеть

Логика загрузки разделена на две части:

- метаданные файла хранятся в PostgreSQL;
- сам бинарный файл хранится в MinIO.

### Как это представлять в голове

При upload происходит следующее:

1. приходит multipart-запрос;
2. сервис проверяет, что сессия принадлежит текущему пользователю;
3. собираются метаданные файла;
4. строится `objectKey`;
5. `StorageService.putObject(...)` пишет байты в MinIO;
6. `UploadEntity` сохраняется в БД;
7. клиент получает metadata response.

### Что важно понять

- В БД хранить большие бинарные файлы неудобно и дорого.
- Object storage лучше подходит для файлов.
- Путь вида `userId/sessionId/uploads/...` помогает логически организовать данные.
- `StorageService` как интерфейс отделяет бизнес-логику от конкретной реализации MinIO.

### Что сделать руками

1. Выпиши, какие поля файла идут в БД, а какие только в object storage.
2. Нарисуй схему `MultipartFile -> InputStream -> MinIO -> metadata in Postgres`.
3. Попробуй придумать, как бы ты заменил MinIO на S3 без переписывания `UploadService`.

### Вопросы для самопроверки

1. Почему `UploadService` зависит от `StorageService`, а не напрямую от `MinioClient`?
2. Почему для файла нужен и `bucketName`, и `objectKey`?

### Теория

- Spring file upload guide: https://spring.io/guides/gs/uploading-files
- MinIO Java SDK: https://github.com/minio/minio-java

---

## Этап 9. Разбери асинхронную обработку задач

### Цель

Понять, как проект организует фоновые jobs и зачем здесь очередь.

### Что открыть

- `speechgym-api/src/main/java/com/speechgym/jobs/JobController.java`
- `speechgym-api/src/main/java/com/speechgym/jobs/JobService.java`
- `speechgym-api/src/main/java/com/speechgym/jobs/JobPublisher.java`
- `speechgym-api/src/main/java/com/speechgym/jobs/JobWorker.java`
- `speechgym-api/src/main/java/com/speechgym/jobs/ProcessJobMessage.java`
- `speechgym-api/src/main/java/com/speechgym/jobs/JobEntity.java`
- `speechgym-api/src/main/java/com/speechgym/jobs/JobEventEntity.java`
- `speechgym-api/src/main/java/com/speechgym/common/config/RabbitMessagingConfig.java`

### Что нужно увидеть

Это центральный инженерный кусок проекта.

Логика выглядит так:

1. пользователь создает job;
2. backend сохраняет запись `jobs`;
3. backend сохраняет `job_events`;
4. backend публикует сообщение в RabbitMQ;
5. `JobWorker` слушает очередь;
6. worker пошагово обновляет статус job;
7. в процессе создаются артефакты;
8. после завершения job помечается как `DONE` или `FAILED`.

### Как это представлять в голове

Здесь очень важно различать два действия:

- создать задачу;
- выполнить задачу.

Они специально разделены.

Почему:

- создание должно быть быстрым;
- тяжелая обработка не должна блокировать HTTP-запрос;
- пользователь может опрашивать статус отдельно;
- систему потом проще масштабировать.

### Что важно понять

- `JobController` не делает обработку сам.
- `JobService.createJob(...)` создает запись и ставит ее в очередь.
- `JobPublisher` - это мост к RabbitMQ.
- `JobWorker` - потребитель сообщений.
- `JobEventEntity` хранит историю этапов, а не только финальный статус.

### Особо важный нюанс текущего проекта

Сейчас `JobWorker` не вызывает реальный ASR/NLP pipeline. Он создает демонстрационные артефакты:

- transcript JSON;
- NLP analysis JSON;
- voice metrics JSON;
- PDF report.

Это значит, что тебе нужно разделять в голове:

- "архитектурный конвейер уже есть";
- "реальные внешние вычисления пока заменены заглушками".

### Что сделать руками

1. Нарисуй sequence diagram для `POST /sessions/{sessionId}/jobs`.
2. Нарисуй state machine по `JobStatus`:
   - `QUEUED`
   - `RUNNING_ASR`
   - `RUNNING_NLP`
   - `RUNNING_VOICE`
   - `RUNNING_REPORT`
   - `DONE`
   - `FAILED`
3. Отдельно ответь:
   - где начинается асинхронность;
   - где job переходит в `DONE`;
   - где фиксируются ошибки.

### Вопросы для самопроверки

1. Почему job не обрабатывается прямо внутри контроллера?
2. Зачем хранить и `jobs`, и `job_events`, если статус job уже есть в таблице `jobs`?

### Теория

- RabbitMQ tutorials: https://www.rabbitmq.com/tutorials
- Spring AMQP reference: https://docs.spring.io/spring-amqp/reference/

---

## Этап 10. Разбери отчеты и артефакты

### Цель

Понять, как из промежуточных результатов рождается конечный пользовательский результат.

### Что открыть

- `speechgym-api/src/main/java/com/speechgym/artifacts/ArtifactService.java`
- `speechgym-api/src/main/java/com/speechgym/artifacts/ArtifactEntity.java`
- `speechgym-api/src/main/java/com/speechgym/artifacts/ArtifactType.java`
- `speechgym-api/src/main/java/com/speechgym/reports/ReportService.java`
- `speechgym-api/src/main/java/com/speechgym/reports/ReportEntity.java`
- `speechgym-api/src/main/java/com/speechgym/reports/ReportController.java`
- `speechgym-api/src/main/java/com/speechgym/reports/PdfReportGenerator.java`
- `speechgym-api/src/main/resources/db/migration/V4__reports.sql`

### Что нужно увидеть

В проекте разделены:

- артефакты обработки;
- финальный report.

Артефакт - это технический результат этапа:

- transcript JSON;
- NLP JSON;
- voice metrics JSON;
- PDF-файл.

Report - это уже бизнес-сущность, которую получает пользователь в виде структурированной аналитики.

### Как это представлять в голове

Представь конвейер:

1. worker производит промежуточные данные;
2. `ArtifactService` складывает их в object storage;
3. метаданные сохраняются в таблицу `artifacts`;
4. `ReportEntity` агрегирует финальные показатели;
5. `ReportController` отдает summary и PDF.

### Что важно понять

- Не все результаты конвейера нужно сразу отдавать пользователю.
- Артефакты удобны для отладки, повторной обработки и расширения pipeline.
- PDF здесь не "магия", а просто байтовый файл, сгенерированный отдельным сервисом.

### Что сделать руками

1. Выпиши все `ArtifactType`.
2. Ответь, чем report отличается от artifact.
3. Прочитай `PdfReportGenerator` и своими словами опиши:
   - как создается документ;
   - откуда берутся данные;
   - почему generator вынесен в отдельный класс.

### Вопросы для самопроверки

1. Почему PDF не хранится прямо в таблице `reports`?
2. Почему `ReportService.downloadPdf(...)` сначала ищет report, а потом artifact?

### Теория

- Apache PDFBox getting started: https://pdfbox.apache.org/3.0/getting-started.html

---

## Этап 11. Разбери обработку ошибок и валидацию

### Цель

Понять, как backend делает API предсказуемым и удобным для клиента.

### Что открыть

- `speechgym-api/src/main/java/com/speechgym/common/error/GlobalExceptionHandler.java`
- `speechgym-api/src/main/java/com/speechgym/common/error/ResourceNotFoundException.java`
- `speechgym-api/src/main/java/com/speechgym/common/error/ConflictException.java`
- `speechgym-api/src/main/java/com/speechgym/common/error/UnprocessableEntityException.java`
- `speechgym-api/src/test/java/com/speechgym/speechgym_api/ProblemDetailIT.java`
- `speechgym-api/src/main/java/com/speechgym/sessions/dto/CreateSessionRequest.java`

### Что нужно увидеть

Здесь код заботится о том, чтобы ошибки были:

- структурированными;
- читаемыми;
- одинаковыми по формату;
- удобными для frontend/desktop-клиента.

### Как это представлять в голове

Если валидация не прошла, контроллер не должен просто "упасть".

Нужен управляемый ответ:

- какой status;
- что произошло;
- где именно ошибка;
- какие поля неправильные.

Именно это делает `ProblemDetail`.

### Что важно понять

- Валидация на DTO ловит неверный input раньше бизнес-логики.
- `GlobalExceptionHandler` централизует формат ошибок.
- Это упрощает клиентскую разработку и отладку.

### Что сделать руками

1. Возьми любой endpoint и перечисли, какие ошибки он потенциально может вернуть.
2. Нарисуй разницу между:
   - validation error;
   - resource not found;
   - conflict;
   - unprocessable entity.
3. Объясни, почему централизованный exception handler лучше, чем `try/catch` в каждом контроллере.

### Вопросы для самопроверки

1. Чем `400 Bad Request` отличается от `422 Unprocessable Entity` в этом проекте?
2. Почему одинаковый формат ошибок полезен клиенту?

### Теория

- Spring MVC exception handling: https://docs.spring.io/spring-framework/reference/web/webmvc/mvc-controller/ann-exceptionhandler.html
- RFC 9457, Problem Details: https://datatracker.ietf.org/doc/html/rfc9457

---

## Этап 12. Разбери схему БД и связь между таблицами

### Цель

Понять, как данные проекта организованы в реляционной модели.

### Что открыть

- `speechgym-api/src/main/resources/db/migration/V2__init.sql`
- `speechgym-api/src/main/resources/db/migration/V3__idempotency_keys.sql`
- `speechgym-api/src/main/resources/db/migration/V4__reports.sql`
- `speechgym-api/src/main/java/com/speechgym/docs/data-model.md`

### Что нужно увидеть

Основные таблицы:

- `users`
- `subscriptions`
- `sessions`
- `uploads`
- `jobs`
- `job_events`
- `artifacts`
- `idempotency_keys`
- `reports`

### Как это представлять в голове

Думай не "по таблицам", а "по жизненному циклу сущности":

1. появляется `user`;
2. у него создается `subscription`;
3. он создает `session`;
4. внутри session появляется `upload`;
5. на основе upload создается `job`;
6. job порождает `job_events` и `artifacts`;
7. job завершает создание `report`.

### Что важно понять

- В таблицах почти везде есть `user_id`, и это сознательный выбор безопасности.
- Индексы отражают реальные паттерны запросов.
- Constraints защищают целостность данных на уровне БД, не только на уровне Java-кода.

### Что сделать руками

1. Нарисуй ER-диаграмму.
2. Подпиши тип связи между сущностями:
   - `user -> sessions`
   - `session -> uploads`
   - `session -> jobs`
   - `job -> job_events`
   - `job -> artifacts`
   - `job -> report`
3. Отдельно выпиши все `UNIQUE`, `CHECK`, `FOREIGN KEY` ограничения и подумай, какие баги они предотвращают.

### Вопросы для самопроверки

1. Почему проверка целостности на уровне БД так же важна, как проверка в Java-коде?
2. Зачем для `jobs.progress` сделан `CHECK (progress >= 0 AND progress <= 100)`?

### Теория

- PostgreSQL docs: https://www.postgresql.org/docs/
- Flyway docs: https://documentation.red-gate.com/fd

---

## Этап 13. Разбери тесты как карту ожидаемого поведения

### Цель

Научиться читать тесты не как "дополнение", а как спецификацию поведения.

### Что открыть

- `speechgym-api/src/test/java/com/speechgym/speechgym_api/AbstractIntegrationTest.java`
- `speechgym-api/src/test/java/com/speechgym/speechgym_api/AuthIT.java`
- `speechgym-api/src/test/java/com/speechgym/speechgym_api/SessionIT.java`
- `speechgym-api/src/test/java/com/speechgym/speechgym_api/UploadIT.java`
- `speechgym-api/src/test/java/com/speechgym/speechgym_api/JobIT.java`
- `speechgym-api/src/test/java/com/speechgym/speechgym_api/IdempotencyIT.java`
- `speechgym-api/src/test/java/com/speechgym/speechgym_api/ProblemDetailIT.java`

### Что нужно увидеть

Тесты здесь отлично показывают реальные гарантии системы:

- auth-flow работает;
- владение объектами соблюдается;
- idempotency работает;
- ошибки имеют правильный формат;
- job создается и отдает ожидаемые заголовки.

### Как это представлять в голове

Если документация отвечает на вопрос "что должно быть", то тест отвечает на вопрос:

"Как мы автоматически проверяем, что это правда?"

### Что важно понять

- `AbstractIntegrationTest` готовит среду.
- Storage и publisher подменяются test-реализациями.
- Это значит, что тесты проверяют API и бизнес-логику без зависимости от реального MinIO и RabbitMQ.

### Что сделать руками

1. Для каждого теста сформулируй на русском одну бизнес-гарантию.
2. Попробуй по памяти восстановить один тест, не подглядывая.
3. После этого сравни с оригиналом и выпиши, что ты упустил.

### Вопросы для самопроверки

1. Почему в тестах полезно подменять `StorageService` и `JobPublisher`?
2. Чем integration test отличается от unit test в контексте этого проекта?

### Теория

- Spring Boot testing reference: https://docs.spring.io/spring-boot/docs/3.3.5/reference/html/features.html#features.testing

---

## Этап 14. Разбери Python ASR-сервис как отдельный компонент

### Цель

Понять второй стек проекта и увидеть, как в систему можно добавлять специализированные сервисы.

### Что открыть

- `asr-service/app.py`
- `asr-service/requirements.txt`

### Что нужно увидеть

Здесь отдельный маленький сервис со своей ролью:

- FastAPI поднимает HTTP API;
- на старте загружается `WhisperModel`;
- endpoint `/transcribe` принимает файл;
- файл временно сохраняется;
- модель делает транскрибацию;
- результат сериализуется в JSON.

### Как это представлять в голове

Это не "второй backend с той же логикой", а специализированный вычислительный сервис.

Он нужен, когда:

- основному API не хочется тащить в себя тяжелые ML-зависимости;
- вычисления хочется изолировать;
- модель имеет свои ресурсные требования.

### Что важно понять

- Python-сервис уже готов как самостоятельный модуль;
- но связь с текущим `JobWorker` еще не реализована;
- именно это хороший кандидат на будущую учебную доработку.

### Что сделать руками

1. Выпиши, какие параметры модели зафиксированы в коде.
2. Опиши, зачем нужен временный файл перед вызовом `model.transcribe(...)`.
3. Сформулируй, как ты бы интегрировал этот сервис в `JobWorker`:
   - HTTP-клиент;
   - отправка файла;
   - получение JSON;
   - сохранение как artifact.

### Вопросы для самопроверки

1. Почему ASR удобно вынести в отдельный сервис, а не держать в Spring Boot?
2. Чем специализированный ML-сервис отличается по роли от обычного CRUD backend?

### Теория

- FastAPI tutorial: https://fastapi.tiangolo.com/tutorial/
- faster-whisper repository: https://github.com/SYSTRAN/faster-whisper

---

## Как именно читать код, чтобы действительно его понять

Вот правильная техника чтения для каждого нового файла:

1. Сначала посмотри на имя класса.
   - Какую роль он, вероятно, играет?
2. Потом посмотри на аннотации.
   - `@RestController`, `@Service`, `@Entity`, `@Configuration`, `@Repository`.
3. Потом посмотри на поля-конструктор.
   - От чего этот класс зависит?
4. Потом быстро просмотри public-методы.
   - Какие сценарии он обслуживает?
5. Только потом читай детали реализации.
6. После чтения ответь себе:
   - что этот класс получает;
   - что он делает;
   - что он возвращает;
   - кто его вызывает;
   - какие правила он защищает.

Если файл большой, дели его на микровопросы:

- где вход;
- где проверка;
- где запись;
- где преобразование;
- где ошибка;
- где выход.

---

## Как фиксировать понимание, чтобы потом воспроизвести самому

После каждого этапа делай 4 вещи:

1. Пиши своими словами краткое объяснение модуля.
   - не копируй из кода;
   - именно пересказывай.
2. Рисуй схему потока данных.
3. Выписывай повторяющийся шаблон.
   - controller -> service -> repository -> response
   - config -> bean -> service
   - entity -> migration -> repository
4. Переписывай кусок логики в мини-варианте в отдельном учебном проекте.

Если ты только читаешь и не пересказываешь, тебе кажется, что ты понял больше, чем понял на самом деле.

---

## План воспроизведения проекта с нуля

Это уже второй трек: не разбор, а именно путь к самостоятельному повторению.

### Шаг 1. Пересобери самый маленький backend-скелет

Сделай новый учебный проект и реализуй только:

- `Spring Boot`;
- один `HelloController`;
- один защищенный endpoint;
- JWT-вход;
- PostgreSQL подключение.

Цель:

- почувствовать каркас без перегруза.

### Шаг 2. Реализуй auth-модуль

Повтори отдельно:

- `register`
- `login`
- `refresh`
- `me`

Не трогай пока jobs, uploads и MinIO.

### Шаг 3. Реализуй один CRUD-модуль по шаблону Sessions

Повтори:

- entity;
- repository;
- create DTO;
- response DTO;
- controller;
- service;
- ownership by `userId`.

### Шаг 4. Добавь idempotency только на create

Сначала только для одного endpoint.

Если это получится, ты уже поймешь ключевую идею и потом перенесешь ее куда угодно.

### Шаг 5. Добавь upload в object storage

Сделай:

- upload endpoint;
- metadata table;
- storage abstraction;
- MinIO implementation.

### Шаг 6. Добавь очередь и jobs

Повтори минимальный pipeline:

- create job;
- publish message;
- consumer;
- статус `QUEUED -> RUNNING -> DONE`.

### Шаг 7. Добавь artifacts и report

Сделай хотя бы:

- один JSON artifact;
- один PDF artifact;
- один report record;
- endpoint скачивания PDF.

### Шаг 8. Добавь тесты

Повтори не все тесты сразу, а по одному классу:

- сначала auth;
- потом sessions;
- потом idempotency;
- потом jobs.

### Шаг 9. Интегрируй внешний Python-сервис

Когда все базовое уже работает, подключай `asr-service`.

Это очень правильный порядок:

- сначала каркас;
- потом надежность;
- потом интеграция со специализированным сервисом.

---

## Самый быстрый маршрут к самостоятельности

Если хочешь прогрессировать максимально быстро, используй такой цикл:

1. Читаешь один модуль текущего проекта.
2. Закрываешь файл.
3. Пересказываешь по памяти, как он работает.
4. Пишешь упрощенную копию модуля в отдельном мини-проекте.
5. Сравниваешь свою версию с оригиналом.
6. Выписываешь 3 различия.
7. Исправляешь свою версию.

Именно шаги 4-6 превращают "узнавание кода" в реальный навык написания.

---

## Рекомендуемый темп изучения на 14 дней

### Дни 1-2

- контракт API;
- сценарии пользователя;
- инфраструктура;
- архитектурные решения.

### Дни 3-4

- Spring startup;
- конфигурация;
- security;
- JWT flow.

### Дни 5-6

- sessions;
- DTO;
- repository;
- entity;
- validation.

### Дни 7-8

- idempotency;
- error handling;
- ownership rules.

### Дни 9-10

- uploads;
- MinIO;
- storage abstraction.

### Дни 11-12

- jobs;
- RabbitMQ;
- worker;
- job events.

### День 13

- reports;
- artifacts;
- PDF generation.

### День 14

- tests;
- ASR-service;
- план собственной упрощенной реализации.

---

## Что нужно уметь объяснить после полного разбора

Если после изучения ты можешь уверенно ответить на эти вопросы, значит ты реально понял проект:

1. Как запрос проходит путь от контроллера до БД?
2. Как приложение узнает текущего пользователя?
3. Почему доступ к чужим объектам возвращает `404`?
4. Как и зачем работает `Idempotency-Key`?
5. Почему файл хранится в MinIO, а не в таблице?
6. Почему job создается через `202 Accepted` и polling?
7. Что делает RabbitMQ в этой архитектуре?
8. Чем artifact отличается от report?
9. Почему тесты подменяют storage и publisher?
10. Как бы ты встроил реальный вызов `asr-service` в существующий pipeline?

---

## Финальное практическое задание для себя

После того как пройдешь весь документ, сделай без подсказок свой mini-project со схожими идеями, но другой тематикой.

Примеры:

- сервис анализа интервью;
- сервис проверки чтения вслух;
- сервис обработки голосовых заметок;
- сервис оценки презентаций.

Минимальная цель:

- auth;
- один CRUD;
- file upload;
- async job;
- polling status;
- result endpoint.

Если ты сможешь это сделать сам, значит ты уже не просто "понимаешь чужой код", а действительно перенес паттерны в свою инженерную практику.

---

## Последний совет

Не пытайся воспроизвести "красоту" проекта целиком с первого раза. Твоя задача не в том, чтобы сразу написать такой же объемный код. Твоя задача:

- понять шаблоны;
- увидеть, зачем они нужны;
- научиться собирать их по частям;
- только потом объединить в одну систему.

Хороший backend почти всегда собирается именно так: не одним большим озарением, а последовательной укладкой понятных инженерных блоков.
