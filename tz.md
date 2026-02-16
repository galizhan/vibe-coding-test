# **Техническое задание: генерация синтетических датасетов для тестирования LLM-агентов**

## **TL;DR — суть за 30 секунд**

* **Что:** сделать программу, которая из *сырого* бизнес-описания **сама** извлекает **use cases** и **ограничения (policy)**, затем строит **test cases** и **dataset** для тестирования.  
* **Критерий успеха:** на вход — markdown-документ, где **не обязаны** быть явно выписаны use cases/policy; на выход — структурированные `use_cases.json`, `policies.json`, `test_cases.json` и `dataset.json`, готовые для прогона evals. (Экспорт в CSV — опционально, но оцениваем JSON.)  
* **Ограничения:** делаем на примере **2 кейсов**: (1) саппорт‑бот (FAQ \+ выгрузка обращений), (2) агент проверки качества оператора (контекстные/бесконтекстные проверки). Язык — Python (предпочтительно); можно использовать LLM API и готовые библиотеки.  
* **Сдать:** ссылка на репозиторий, README с инструкцией запуска, примеры входных документов и сгенерированные артефакты, короткое видео (по желанию)  
  ---

  ## **Контекст продукта**

Команды, которые делают LLM-агентов, упираются в данные для теста: реальных диалогов и сценариев либо мало, либо их нельзя использовать из\-за NDA и чувствительных данных. В итоге тест-кейсы собирают вручную — это долго и не покрывает edge-cases.

**Гипотеза:** из бизнес-требований (ТЗ) можно автоматически получить use cases, test cases и синтетический датасет. Часть сгенерированных примеров будет осмысленной и пригодной для валидации QA.

**Цель задания:** доказать возможность автоматизации на **2 реальных проектах** :

1. Чат-бот техподдержки: **FAQ \+ выгрузка обращений** → use cases → test cases → dataset (включая переформулировки и corner cases).  
2. Агент контроля качества оператора: **общее описание проверок** (контекстные/бесконтекстные) → use cases/правила → test cases → датасеты двух форматов:  
* “фраза → исправленная фраза” (бесконтекстные)  
* “диалог (последняя реплика — оператора) → исправленная последняя реплика” (контекстные)

Код самого агента ещё не написан; нужна только цепочка: ТЗ → артефакты для тестирования.

---

## **Твоя задача**

Реализовать программу (скрипт или модули), которая:

1. Читает *сырой* документ требований (markdown), где **может не быть** явно прописанных use cases/policy, а есть формулировки вида “Дано: FAQ \+ выгрузка обращений” или “Дано: общее задание с контекстными и бесконтекстными проверками”.  
2. **Сама** извлекает из текста:  
   * структурированные **use cases** (бизнес-сценарии/темы/интенты)  
   * структурированные **ограничения (policy/правила/проверки/эскалации)**  
3. Генерирует **test cases** — комбинации варьирующихся параметров для каждого use case.  
4. Генерирует **dataset** — примеры вида «вход пользователя \+ ожидаемый выход / критерии оценки» для каждого test case.

   ### **Вход (Input)**

**Важно:** во входном документе use cases и policy **не обязаны** быть выписаны списком. Программа должна уметь добывать их из “воды” и разрозненных формулировок.

Поддержи как минимум **2 типа входов**:

1. **FAQ \+ выгрузка обращений** : дан FAQ и список обращений/диалогов; нужно понять, какие есть “темы/интенты” и какие ограничения на ответы (например: если нет доступа в ЛК — давать телефон оператора).  
2. **Общее задание на проверки качества** : дано описание набора контекстных и бесконтекстных проверок; нужно превратить это в формальные правила/ограничения и сценарии (в т.ч. синтетические диалоги, которые заканчиваются сообщением оператора).

Примеры входных документов приложены к заданию:

* `example_input_raw_support_faq_and_tickets.md`  
* `example_input_raw_operator_quality_checks.md`  
* `example_input_raw_doctor_booking.md` — усложнённый пример (запись к врачу) для проверки алгоритма

  ### **Выход (Output)**

1. **use\_cases.json** — список use cases с id, названием, описанием и `evidence[]` (откуда в тексте это извлечено).  
2. **policies.json** — список извлечённых policy/правил/проверок с id, `type`, `statement` и `evidence[]`.  
3. **test\_cases.json** — список test cases с id, привязкой к use\_case\_id, `parameters` и ссылками на релевантные policy (`policy_ids`).  
4. **dataset.json** — список примеров с полями:  
   * `id` (уникальный id примера)  
   * `case`: `support_bot` | `operator_quality`  
   * `format`: `single_turn_qa` | `single_utterance_correction` | `dialog_last_turn_correction`  
   * `use_case_id`, `test_case_id`  
   * `input` (структурированный формат, см. ниже; минимум: `messages[]`)  
   * `expected_output` (**обязательно**; референс-ответ или исправленная фраза/реплика)  
   * `evaluation_criteria` (**обязательно**; 3+ критериев проверки, которыми потом можно оценивать ответ агента)  
   * `policy_ids` (**обязательно**; минимум 1: какие политики релевантны этому примеру)  
   * `metadata` (опционально: параметры, теги). Рекомендуемые ключи:  
     * `source`: `tickets` | `faq_paraphrase` | `corner` (обязательно для саппорт‑кейса)  
     * `split`: `train` | `test` | `corner`

   ---

   ## **Data contract (обязательно; без этого задание считается не выполненным)**

Цель этого раздела — убрать двусмысленность форматов, чтобы результат можно было:

* автоматически валидировать,  
* руками быстро ревьюить,  
* потом без боли загрузить в Langfuse / прогонять в eval-раннере.

  ### **1\) Конвенции ID**

* `use_case_id`: строка с префиксом `uc_` (пример: `uc_delivery_status`)  
* `policy_id`: строка с префиксом `pol_` (пример: `pol_no_account_access`)  
* `test_case_id`: строка с префиксом `tc_` (пример: `tc_delivery_status_negative_tone_no_account_access`)  
* `example_id`: строка с префиксом `ex_` (пример: `ex_support_0001`)

ID должны быть **уникальными** внутри соответствующего файла.

### **2\) Evidence / traceability (обязательно для `use_cases.json` и `policies.json`)**

Каждый извлечённый use case и policy должен иметь **минимум 1 evidence**, привязанный к исходному входному документу.

Формат evidence:

* evidence\[\]:  
*   \- input\_file: string            // например "example\_input\_raw\_support\_faq\_and\_tickets.md"  
*     line\_start: int               // 1-based  
*     line\_end: int                 // 1-based, \>= line\_start  
*     quote: string                 // дословная цитата из исходника (1–5 строк достаточно)


Это нужно, чтобы отличать “извлекли из ТЗ” от “придумали”.

**Правило (строго):** `quote` должен **в точности** совпадать с текстом строк `line_start..line_end` из файла `input_file` (после нормализации переводов строк). Это проверяется независимым валидатором (см. раздел “Официальный валидатор”).

Чтобы решение нельзя было захардкодить под конкретные файлы:

* при проверке мы можем подавать те же входы под **другими именами файлов** и из другой директории;  
* мы также запускаем генерацию на 1–2 **скрытых входах** того же типа.

  ### **3\) Структуры выходных файлов (минимальный контракт)**

`use_cases.json`

* {  
*   "use\_cases": \[  
*     {  
*       "id": "uc\_...",  
*       "case": "support\_bot",  
*       "name": "…",  
*       "description": "…",  
*       "evidence": \[  
*         { "input\_file": "…", "line\_start": 1, "line\_end": 2, "quote": "…" }  
*       \]  
*     }  
*   \]  
* }


`policies.json`

* {  
*   "policies": \[  
*     {  
*       "id": "pol\_...",  
*       "case": "support\_bot",  
*       "type": "must\_not",  
*       "statement": "…",  
*       "evidence": \[  
*         { "input\_file": "…", "line\_start": 1, "line\_end": 2, "quote": "…" }  
*       \]  
*     }  
*   \]  
* }


Где `type` — один из (можно расширять, но минимум из этого списка):

* `must` (обязательное действие)  
* `must_not` (запрет)  
* `escalate` (эскалация)  
* `style` (tone-of-voice/вежливость)  
* `format` (форматирование/ограничения на текст)

`test_cases.json`

* {  
*   "test\_cases": \[  
*     {  
*       "id": "tc\_...",  
*       "case": "support\_bot",  
*       "use\_case\_id": "uc\_...",  
*       "parameters": {  
*         "tone": "negative",  
*         "has\_order\_id": true  
*       },  
*       "policy\_ids": \["pol\_..."\]  
*     }  
*   \]  
* }


`dataset.json`

* {  
*   "examples": \[  
*     {  
*       "id": "ex\_...",  
*       "case": "support\_bot",  
*       "format": "single\_turn\_qa",  
*       "use\_case\_id": "uc\_...",  
*       "test\_case\_id": "tc\_...",  
*       "input": {  
*         "messages": \[  
*           { "role": "user", "content": "..." }  
*         \]  
*       },  
*       "expected\_output": "...",  
*       "evaluation\_criteria": \[  
*         "..."  
*       \],  
*       "policy\_ids": \["pol\_..."\],  
*       "metadata": {  
*         "source": "tickets",  
*         "split": "test"  
*       }  
*     }  
*   \]  
* }


Правила для `input.messages[]`:

* `role` должен быть одним из: `user`, `operator`, `assistant`, `system`  
* `content` — строка  
* для формата `dialog_last_turn_correction` обязательно поле `target_message_index` внутри `input`, и оно должно указывать на **последнюю реплику оператора** (т.е. `target_message_index == len(messages) - 1` и `messages[target_message_index].role == "operator"`).  
  ---

  ## **Пошаговый сценарий (Flow)**

1. **Извлечение структуры из “сырого” ТЗ**  
   * Прочитать markdown-файл.  
   * Выделить: домен, акторов (пользователь/оператор), сущности (FAQ, обращения, правила), цели.  
   * Извлечь use cases **без явного списка** (через суммаризацию+нормализацию/кластеризацию/LLM extraction — на твой выбор).  
   * Извлечь policy/проверки/ограничения **без явного списка** (например: “если нет доступа в ЛК — дать телефон”; “контекстные и бесконтекстные проверки”; “tone of voice”).  
   * Сохранить это как JSON-артефакты.  
2. **Генерация test cases**  
   * Для каждого use case определить 2–3 оси вариации.  
   * Примеры осей для **саппорт‑бота**: есть/нет номера заказа; тон (нейтральный/негативный); запрос “невозможного” (требует доступа в ЛК); язык (RU/EN); наличие мата/оскорблений; пустое/мусорное сообщение.  
   * Примеры осей для **оператор‑качества**: длина фразы; пунктуация/опечатки; сленг/мат/эмодзи/пустота; наличие медицинских терминов (их нельзя “исправлять”); степень агрессии пользователя; необходимость эскалации.  
   * Сгенерировать комбинации параметров — это и есть test cases.  
3. **Генерация dataset**  
   * Для каждого test case сгенерировать N примеров (N ≥ 1 для MVP).  
   * Каждый пример: естественный «вход» (в формате `messages[]`) \+ `expected_output` \+ `evaluation_criteria`.  
   * Учесть ограничения: например, “нет доступа в ЛК → не придумывать статус”; “на жалобы/агрессию → эскалация/нейтральный тон”; “нельзя выдавать личные контакты врача”.  
4. **Сохранение артефактов**  
   * Записать `use_cases.json`, `policies.json`, `test_cases.json`, `dataset.json` в указанную директорию.

   ---

   ## **Два кейса (что именно нужно покрыть)**

   ### **Кейс A: чат-бот техподдержки (FAQ \+ выгрузка обращений)**

* **Дано:** FAQ \+ выгрузка обращений/диалогов.  
* **Ключевые ограничения:** нет доступа в ЛК; если вопрос требует такого доступа — дать контакт/эскалировать; не придумывать данные.  
* **Что должна сделать программа:** извлечь use cases/ограничения, затем сгенерировать test cases и dataset items (в т.ч. переформулировки и corner cases).

Требования к `dataset.json` для саппорт‑кейса:

* **`metadata.source = tickets`**  
  * `input.messages` содержит 1 сообщение пользователя из выгрузки.  
  * `expected_output` — “разумный” ответ поддержки с учётом ограничений (не фантазировать доступ к ЛК, запросить недостающее, при необходимости эскалировать/дать контакты).  
* **`metadata.source = faq_paraphrase`**  
  * `input.messages` — переформулированный вопрос по одному из пунктов FAQ.  
  * `expected_output` — ответ, который по смыслу соответствует FAQ (это “золотой” референс).  
* **`metadata.source = corner`**  
  * `input.messages` — corner cases (мусор, не по теме, мат, попытки “сломать” бота).  
  * `expected_output` — безопасная реакция: уточнение/отказ/эскалация, без галлюцинаций.

  ### **Кейс B: агент проверки качества оператора (контекстные/бесконтекстные проверки)**

* **Дано:** одно общее задание с кучей контекстных и бесконтекстных проверок.  
* **Что должна сделать программа:**  
  * извлечь use cases/правила (policy) из “воды”  
  * сгенерировать тест‑кейсы и датасеты **двух форматов**:  
    * **`single_utterance_correction` (бесконтекстный):** “фраза оператора → исправленная фраза”  
    * **`dialog_last_turn_correction` (контекстный):** “диалог (последняя реплика — оператора) → исправленная последняя реплика оператора”

Требования к `dataset.json` для оператор‑кейса:

* В `single_utterance_correction`:  
  * `input.messages` содержит ровно 1 сообщение с `role = operator`  
  * `expected_output` — исправленная версия (пунктуация/опечатки/tone-of-voice/ограничения)  
* В `dialog_last_turn_correction`:  
  * `input.messages` содержит минимум 2 сообщения (`user` …, затем последняя реплика `operator`)  
  * `input.target_message_index` указывает на последнюю реплику оператора  
  * `expected_output` — исправленная последняя реплика, учитывающая контекст и правила (например, эскалацию при жалобе)

  ---

  ## **Ограничения**

* **Кейсы:** обязательно покрыть **оба** кейса (саппорт‑бот и оператор‑качество).  
* **Язык:** Python предпочтителен; допустимы и другие, если реализация понятна.  
* **Инструменты:** можно использовать LLM API (OpenAI, Claude и т.д.), готовые библиотеки (DeepEval Synthesizer, Pydantic Evals, Ragas, SDialog — по выбору) или собственные промпты.  
* **Объём (минимум):** по каждому кейсу: минимум 5 use cases, 5 policies, 3 test case на use case, 1 пример на test case.  
  ---

  ## **Что мы ожидаем на выходе**

1. **Репозиторий** с кодом (скрипт или модули), инструкцией по запуску и конфигурации (env, API-ключи — без коммита секретов).  
2. **README:** как запустить, зависимости, переменные окружения.  
3. **Примеры входных документов** (см. ниже) и **сгенерированные артефакты** для обоих кейсов.

Ожидаем, что в репозитории будет папка `out/` с уже сгенерированными файлами (чтобы можно было открыть и проверить без запуска):

* out/  
*   support/  
*     run\_manifest.json  
*     use\_cases.json  
*     policies.json  
*     test\_cases.json  
*     dataset.json  
*   operator\_quality/  
*     run\_manifest.json  
*     use\_cases.json  
*     policies.json  
*     test\_cases.json  
*     dataset.json


`run_manifest.json` — это файл с параметрами запуска генерации (seed, модель/провайдер, temperature, версии, пути входа/выхода). Формат — свободный, но должен содержать минимум: `input_path`, `out_path`, `seed`, `timestamp`, `generator_version` (строка), и блок `llm` (даже если `provider = \\\\"none\\\\"`).

### **Обязательные примеры входных документов (должны быть в репозитории)**

* `example_input_raw_support_faq_and_tickets.md`  
* `example_input_raw_operator_quality_checks.md`  
  ---

  ## **Acceptance criteria (как мы поймём, что решение “сработало”)**

Минимальные критерии (MVP):

1. **Data contract соблюдён**  
   * Все выходные файлы соответствуют разделу **Data contract**: обязательные поля, конвенции ID, форматы `input.messages`, и т.п.  
   * В `use_cases.json` и `policies.json` у **каждого** элемента есть `evidence[]` с корректными `input_file/line_start/line_end/quote`.  
   * В репозитории присутствуют сгенерированные артефакты в `out/support/*` и `out/operator_quality/*` (как в дереве выше).  
   * Команды `python -m dataset_generator validate --out out/support` и `python -m dataset_generator validate --out out/operator_quality` завершаются успешно (exit code 0).  
   * Независимый валидатор (из этого пакета задания) проходит:  
     * `python official_validator.py --input example_input_raw_support_faq_and_tickets.md --out out/support`  
     * `python official_validator.py --input example_input_raw_operator_quality_checks.md --out out/operator_quality`  
2. **Извлечение use cases (2 входа)**  
   * По каждому из двух raw-входов программа генерирует `use_cases.json` с минимум **5** use cases.  
   * Use cases не должны быть дубликатами (нормализуй названия).  
   * Для **каждого** use case есть `evidence[]` из соответствующего input-файла.  
3. **Извлечение policies/правил (2 входа)**  
   * По каждому raw-входу программа генерирует `policies.json` с минимум **5** правил.  
   * В правилах представлены хотя бы **2 разных** `type` из списка (например: `must_not` \+ `escalate`).  
   * Для **каждой** policy есть `evidence[]`.  
   * Для саппорт‑кейса должны быть policy (по смыслу): “нет доступа в ЛК → не придумывать/эскалировать/дать контакты”, “tone-of-voice на агрессию”.  
   * Для оператор‑кейса должны быть policy (по смыслу): “исправлять пунктуацию/опечатки”, “не капслок/не \!\!\!”, “медицинские термины не портить”, “не давать личный номер врача”, “эскалация при жалобе”.  
4. **Test cases**  
   * На каждый use case — минимум **3** test case (оси вариации \+ конкретные значения в `parameters`).  
   * У каждого test case есть минимум 1 `policy_id` (ссылка на извлечённую policy).  
5. **Dataset**  
   * На каждый test case — минимум **1** пример в `dataset.json`.  
   * В каждом примере есть: `input.messages[]`, `expected_output`, `evaluation_criteria` (3+), `policy_ids` (1+), `case`, `format`, `use_case_id`, `test_case_id`.  
   * Для кейса **саппорт‑бот**: в `dataset.json` есть примеры минимум трёх источников (`metadata.source`): `tickets`, `faq_paraphrase`, `corner`.  
   * Для кейса **оператор‑качество**: есть примеры и для `single_utterance_correction`, и для `dialog_last_turn_correction`. Для `dialog_last_turn_correction` соблюдается правило `target_message_index` (последняя реплика оператора).  
6. **Повторяемость**  
   * Повторный запуск на одном и том же входе должен давать сопоставимый результат (допускается стохастика, но структура/валидность/покрытие — стабильны).

   ---

   ## **Требования к интерфейсу (чтобы можно было запускать без пояснений)**

Сделай простой CLI (пример — один из вариантов, можешь предложить лучше):

* python \-m dataset\_generator \\\\\\\\  
*   \--input example\_input\_raw\_support\_faq\_and\_tickets.md \\\\\\\\  
*   \--out out/support \\\\\\\\  
*   \--seed 42 \\\\\\\\  
*   \--n-use-cases 8 \\\\\\\\  
*   \--n-test-cases-per-uc 5 \\\\\\\\  
*   \--n-examples-per-tc 2


И аналогично для второго входа:

* python \-m dataset\_generator \\\\\\\\  
*   \--input example\_input\_raw\_operator\_quality\_checks.md \\\\\\\\  
*   \--out out/operator\_quality \\\\\\\\  
*   \--seed 42


Требования к воспроизводимости:

* При каждом запуске генератор должен создавать/перезаписывать `run_manifest.json` в директории `-out`.  
* В `run_manifest.json` зафиксируй минимум: `input_path`, `out_path`, `seed`, `timestamp`, `generator_version`, `llm` (provider/model/temperature). Если LLM не используется — `llm.provider = \\\\"none\\\\"`.

После генерации должен быть доступен режим проверки (валидирует **Data contract** и acceptance criteria на уровне структуры/связей):

* python \-m dataset\_generator validate \--out out/support  
* python \-m dataset\_generator validate \--out out/operator\_quality


`validate` должен завершаться с exit code **0**, если всё ок, и **\>0**, если есть ошибки, и печатать краткий отчёт (сколько use cases/policies/test cases/examples, какие форматы покрыты).

### **Официальный валидатор (то, чем будем проверять мы)**

В пакете задания есть файл `official_validator.py`. Мы используем его при проверке, потому что он не зависит от вашей реализации `validate` и проверяет в том числе:

* структуру файлов по **Data contract**  
* целостность ссылок (use\_case\_id/policy\_ids/test\_case\_id)  
* корректность `evidence[]` (строки/цитаты реально совпадают с исходным файлом)  
* минимальные покрытие/форматы по acceptance criteria

Также в пакете задания лежат JSON Schema файлы (их можно использовать локально для быстрой валидации формата):

* `schema_use_cases.json`  
* `schema_policies.json`  
* `schema_test_cases.json`  
* `schema_dataset.json`  
* `schema_run_manifest.json`

Пример запуска:

* python official\_validator.py \--input example\_input\_raw\_support\_faq\_and\_tickets.md \--out out/support  
* python official\_validator.py \--input example\_input\_raw\_operator\_quality\_checks.md \--out out/operator\_quality


**Анти‑хардкод:** при проверке мы можем:

* запускать на тех же входах, но под другими именами файлов/в другой директории  
* прогонять на 1–2 скрытых входах того же типа

  ### **(Опционально) Интеграции с готовыми сервисами (сильно приветствуется)**

Цель этого блока — **не строить всё самому** (UI, версионирование, сравнение прогонов, human review), а собрать пайплайн на готовых платформах.

Важно:

* Все обязательные критерии и `official_validator.py` должны проходить **без** внешних сервисов.  
* Интеграции ниже — **bonus**: они не обязаны проходить у нас при проверке (мы можем не иметь ключей), но сильно повышают качество результата и “продуктовость”.

  ### **1\) Langfuse или LangSmith (датасеты, эксперименты, сравнение прогонов)**

Что можно сделать:

* Загружать сгенерированный `dataset.json` как dataset items в **Langfuse** или **LangSmith**.  
* Прогонять baseline (например, простой “ответчик”/“корректор”) по датасету и сохранять результаты как эксперимент, чтобы сравнивать версии генерации/промптов/моделей.

Что сдать:

* `out/*/run_manifest.json` (уже обязателен) \+ добавить поля `langfuse`/`langsmith` (например: `dataset_name`, `run_url`), если используете.  
* (Опционально) `out/*/dataset_items.jsonl` — экспорт dataset items в JSONL (чтобы можно было загрузить в UI руками).

  ### **2\) Giskard Hub (baseline генератор “business tests” из KB)**

Для саппорт‑кейса можно использовать **Giskard Hub** как baseline:

* импортировать FAQ как knowledge base  
* сгенерировать document-based business tests (queries \+ expected outputs)  
* затем “привести” результат к нашему `dataset.json` формату (`metadata.source = faq_paraphrase`) и дополнить corner cases

Важно: даже если используете Giskard, вам всё равно нужно выполнить **evidence/traceability** и пройти `official_validator.py`.

### **3\) Confident AI / DeepEval Synthesizer (генерация goldens)**

Для `faq_paraphrase` и части `corner` удобно использовать DeepEval Synthesizer:

* генерация из документов (FAQ \+ фрагменты тикетов)  
* evolutions (сложность/шум/переформулировки)

Что сдать (если используете): ссылка на конфиг/код генерации \+ указание модели и стоимости в `run_manifest.json`.

### **4\) Evidently (data-quality гейты)**

Можно добавить отдельный отчёт качества датасета:

* near-duplicates (повторы вопросов/ответов)  
* распределения по `metadata.source`, `format`, длине сообщений  
* наличие плейсхолдеров/“…”/пустых expected outputs

Что сдать (если используете): `out/*/quality_report.json` или `out/*/quality_report.md`.

### **5\) Patronus (guardrails / safety slice)**

Опционально: прогнать часть `corner` примеров через Patronus (или аналог) и пометить:

* возможные галлюцинации/необоснованные утверждения  
* prompt injection (для саппорт‑кейса)

Что сдать (если используете): `out/*/guardrails_report.json` \+ как вы это используете (например, фильтрация/тегирование).

### **6\) Surge / Scale (human review)**

Опционально: сделать human review на 20–50 примерах (стратифицированно по `case/format/source`) и собрать рубрику “годно/не годно” \+ причины.

Что сдать (если используете): `out/*/human_review.csv` или ссылка/скриншоты, плюс короткое резюме в README.

Если используешь LLM API — опиши в README, какие переменные окружения нужны (например: `OPENAI_API_KEY`).

---

## **Ограничения по заданию**

* Срок и объём работ — определи самостоятельно и напиши в чат.  
* Описание продукта и гипотез — внутреннее; не выкладывать в открытый доступ без согласования.  
* AI-инструменты (Copilot, Cursor, ChatGPT и т.п.) использовать можно.  
  ---

  ## **Формат результата**

Пришли:

1. **Ссылку на репозиторий** с кодом и README (запуск, зависимости, env).  
2. **Примеры входных документов** и **сгенерированные артефакты** (`use_cases.json`, `policies.json`, `test_cases.json`, `dataset.json`).  
3. **Краткий отчёт:** стек, как запускать, что настроить (API-ключи и т.п.).  
4. (Опционально) короткое видео-пример генерации  
   ---

   ## **Appendix**

   ### **1\. Входные документы (2 кейса \+ опциональный усложнённый)**

В репозитории должны лежать 2 входных файла (сырые, без явных use cases/policy):

* `example_input_raw_support_faq_and_tickets.md` — саппорт‑бот: FAQ \+ выгрузка обращений (аналогично `new ТЗ.md:52-63`).  
* `example_input_raw_operator_quality_checks.md` — агент проверки качества оператора: контекстные/бесконтекстные проверки (аналогично `new ТЗ.md:65-78`).

**Опционально (для проверки алгоритма):** `example_input_raw_doctor_booking.md` — запись к врачу, усложнённый пример: разрозненные memo, FAQ, инструкции операторов и выгрузка обращений в одном документе; информацию приходится собирать из разных форматов и контекстов.

### **2\. Примеры `dataset.json` (3 формата)**

Ниже — canonical примеры (смотри также раздел **Data contract** выше).

### **A) `support_bot`: `single_turn_qa`**

* {  
*   "examples": \[  
*     {  
*       "id": "ex\_support\_0001",  
*       "case": "support\_bot",  
*       "format": "single\_turn\_qa",  
*       "use\_case\_id": "uc\_delivery\_status",  
*       "test\_case\_id": "tc\_delivery\_status\_no\_account\_access\_negative\_tone",  
*       "input": {  
*         "messages": \[  
*           { "role": "user", "content": "Где мой заказ 123456??? уже неделя прошла" }  
*         \]  
*       },  
*       "expected\_output": "Понимаю. У меня нет доступа к вашему личному кабинету, поэтому не могу проверить статус напрямую. Подскажите, пожалуйста, номер заказа и дату оформления — я передам запрос оператору/в поддержку.",  
*       "evaluation\_criteria": \[  
*         "Не утверждать, что есть доступ к ЛК/статусу заказа",  
*         "Сохранить вежливый тон даже при агрессии",  
*         "Если требуется доступ в ЛК — предложить эскалацию/контакты поддержки"  
*       \],  
*       "policy\_ids": \["pol\_no\_account\_access", "pol\_escalate\_if\_needed"\],  
*       "metadata": {  
*         "source": "tickets",  
*         "split": "test"  
*       }  
*     }  
*   \]  
* }


  ### **B) `operator_quality`: `single_utterance_correction`**

* {  
*   "examples": \[  
*     {  
*       "id": "ex\_operator\_0001",  
*       "case": "operator\_quality",  
*       "format": "single\_utterance\_correction",  
*       "use\_case\_id": "uc\_spelling\_punctuation",  
*       "test\_case\_id": "tc\_spelling\_punctuation\_exclamations\_med\_terms",  
*       "input": {  
*         "messages": \[  
*           {  
*             "role": "operator",  
*             "content": "Извините\! Сейчас отменю. Напишите вашу фамилию и время приема\!\!\!"  
*           }  
*         \],  
*         "target\_message\_index": 0  
*       },  
*       "expected\_output": "Извините. Сейчас отменю запись. Подскажите, пожалуйста, вашу фамилию и время приёма.",  
*       "evaluation\_criteria": \[  
*         "Исправить пунктуацию и убрать лишние восклицательные знаки",  
*         "Сохранить вежливый тон без грубости/сарказма",  
*         "Не портить медицинские термины и имена собственные (если есть)"  
*       \],  
*       "policy\_ids": \["pol\_no\_excess\_exclamations", "pol\_polite\_tone"\],  
*       "metadata": {  
*         "split": "test"  
*       }  
*     }  
*   \]  
* }


  ### **C) `operator_quality`: `dialog_last_turn_correction`**

* {  
*   "examples": \[  
*     {  
*       "id": "ex\_operator\_0002",  
*       "case": "operator\_quality",  
*       "format": "dialog\_last\_turn\_correction",  
*       "use\_case\_id": "uc\_escalation\_on\_complaint",  
*       "test\_case\_id": "tc\_escalation\_angry\_user",  
*       "input": {  
*         "messages": \[  
*           {  
*             "role": "user",  
*             "content": "Да что за сервис, никто не отвечает\!\!\! Мне надо срочно отменить прием завтра"  
*           },  
*           {  
*             "role": "operator",  
*             "content": "Извините\! Сейчас отменю. Напишите вашу фамилию и время приема\!\!\!"  
*           }  
*         \],  
*         "target\_message\_index": 1  
*       },  
*       "expected\_output": "Понимаю ваше недовольство. Давайте отменим запись: подскажите, пожалуйста, вашу фамилию и время приёма. Если вам удобнее, могу передать диалог старшему специалисту.",  
*       "evaluation\_criteria": \[  
*         "Учитывать контекст: пользователь агрессивен/недоволен → смягчить тон",  
*         "Запросить идентификатор для отмены (ФИО/время/дата)",  
*         "При сильной жалобе предусмотреть эскалацию"  
*       \],  
*       "policy\_ids": \["pol\_escalate\_on\_complaint", "pol\_cancel\_requires\_identifiers"\],  
*       "metadata": {  
*         "split": "test"  
*       }  
*     }  
*   \]  
* }


  ### **3\. Рекомендуемые инструменты и ссылки**

| Инструмент | Назначение | Ссылка |
| ----- | ----- | ----- |
| **DeepEval Synthesizer** | Генерация goldens из документов | [https://deepeval.com/docs/synthesizer-introduction](https://deepeval.com/docs/synthesizer-introduction) |
| **Pydantic Evals** | `generate_dataset()` — генерация Cases из типов и инструкций | [https://ai.pydantic.dev/evals/](https://ai.pydantic.dev/evals/) |
| **Ragas** | Синтетическая генерация testset для RAG | [https://docs.ragas.io/](https://docs.ragas.io/) |
| **Giskard Hub** | Document-based генерация из knowledge base | [https://docs.giskard.ai/hub/ui/datasets/business.html](https://docs.giskard.ai/hub/ui/datasets/business.html) |
| **Evidently** | Генерация синтетики \+ quality checks (OSS/Cloud) | [https://www.evidentlyai.com/llm-guide/llm-test-dataset-synthetic-data](https://www.evidentlyai.com/llm-guide/llm-test-dataset-synthetic-data) |
| **SDialog** | Симуляция диалогов, генерация синтетики, оценка диалогов/метрики | [https://github.com/idiap/sdialog](https://github.com/idiap/sdialog) |
| **Langfuse Datasets** | Генерация/загрузка synthetic datasets, эксперименты и сравнение прогонов | [https://langfuse.com/guides/cookbook/example\_synthetic\_datasets](https://langfuse.com/guides/cookbook/example_synthetic_datasets) |
| **LangSmith** | Датасеты \+ эксперименты/evals для LLM приложений (UI+SDK) | [https://docs.smith.langchain.com/evaluation/concepts](https://docs.smith.langchain.com/evaluation/concepts) |
| **Confident AI (platform)** | Платформа для датасетов/аннотаций/запусков DeepEval | [https://www.confident-ai.com/](https://www.confident-ai.com/) |
| **Patronus** | API для evaluation/guardrails (галлюцинации/инъекции/safety) | [https://www.patronus.ai/](https://www.patronus.ai/) |
| **Surge AI** | Human-in-the-loop: разметка/оценка качества примеров и правил (опционально) | [https://www.surgehq.ai/](https://www.surgehq.ai/) |
| **Scale AI** | Human eval / RLHF / eval platform (альтернатива Surge) | [https://scale.com/rlhf](https://scale.com/rlhf) |

Можно использовать любой из них или реализовать конвейер на основе промптов к LLM без сторонних библиотек.

### **4\. Типы тест-кейсов (рекомендация)**

* **Happy path:** типовые, положительные сценарии.  
* **Edge cases:** нестандартные или сложные (очень длинные сообщения, двусмысленные вопросы, смешанные языки, мусорный ввод).  
* **Policy violations:** сценарии, где агент должен отказать/не фантазировать/эскалировать (например: запрос данных из ЛК при отсутствии доступа; агрессия/жалоба; просьба дать личные контакты врача).

  ### **5\. Технический стек (рекомендация)**

* **Python 3.10+**  
* **LLM:** OpenAI API, Anthropic Claude или аналог (через env: `OPENAI_API_KEY` и т.п.)  
* **Парсинг markdown:** можно использовать регулярные выражения или библиотеки (markdown, mistletoe).  
* **Структурированный вывод:** строго по **Data contract** выше: `use_cases.json`, `policies.json`, `test_cases.json`, `dataset.json` \+ валидация (`validate`).

