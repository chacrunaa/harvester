# State Management Rules — TanStack Query + Zustand

> Правила ниже — **строгие**, если явно не помечено иначе.
> Нарушение строгого правила = архитектурная ошибка.
> Документ детализирует разделение из [`architecture.md`](architecture.md) и развивает
> грамматику работы с данными вместе с [`react-conversations.md`](react-conversations.md).
> Источники: `docs/structure/architecture.md`, `docs/structure/modules/`.

Файл отвечает на один вопрос: **где живёт данная единица данных и кто её обновляет**.
Каждая единица — ровно одно место хранения и ровно один путь обновления. Дубликаты запрещены.

---

## Строго запрещено

### Источник данных и кэш

- **Копировать server-данные в Zustand store.** Данные с API/WS живут в кэше TanStack Query. Zustand хранит только client state (UI-флаги, выбор, черновики, статус соединения).
- **Хранить server-данные в `useState`.** Если данные пришли из `useQuery` — они уже в кэше; локальная копия отписывает компонент от фоновых обновлений.
- **Дублировать одну сущность в Zustand и в кэше TQ одновременно.** Один источник истины на единицу данных.
- **Использовать `setQueryData` вне колбэков мутации и подписок WS.** В остальных местах кэш меняется только через `invalidateQueries` или новый `fetch` (другой `queryKey`).

### Query Keys

- **Строковые литералы в `queryKey` запрещены.** Только через фабрику ключей модуля: `chatKeys.detail(id)`, не `['chat', 'detail', id]` инлайн (правило из [`architecture.md`](architecture.md#L36)).
- **Фабрики ключей живут в `query.ts` модуля-владельца.** В `utils/`, `constants/`, `services.ts` фабрика ключей не размещается.
- **Хранение query-ключей в Zustand или передача через пропсы запрещено.** Ключ всегда вычисляется из доступных аргументов в `query.ts`.

### Хуки запросов

- **`useQuery`/`useMutation` напрямую в JSX модуля запрещено.** Любой вызов оборачивается в именованный хук `useGetX(...)` / `useMutateX(...)` в `query.ts`.
- **Один хук = один запрос или одна мутация.** Комбайны `useChatBundle()` с тремя `useQuery` внутри запрещены — это четыре независимых хука в `query.ts`.
- **`fetch` напрямую через `apiClient` в JSX, `useEffect`, `services.ts` запрещён.** Сетевой вызов идёт только через `useQuery`/`useMutation` или явный `queryClient.fetchQuery` в колбэке мутации.

### Zustand store

- **`useStore()` без селектора запрещено.** Любое чтение store сопровождается селектором: `useStore(s => s.field)`. Без селектора компонент ре-рендерится на каждое изменение любого поля store.
- **Селектор, создающий новый объект/массив, без `useShallow` запрещён.** Иначе ссылочное сравнение всегда возвращает «изменилось» и ре-рендер бесконечен.
- **Мутация state без `set(...)` запрещена.** `state.field = x` или `state.list.push(x)` без immer не вызывает ре-рендер и ломает иммутабельность.
- **WS бизнес-данные (сообщения, отчёты, события) в `websocket.store` запрещены.** Там только статус соединения — повторение правила из [`architecture.md`](architecture.md#L23).

### Конфигурация

- **`staleTime: 0` ради «всегда свежих данных» запрещён.** Свежесть управляется `invalidateQueries` после мутации, а не штормом запросов на каждый рендер.
- **Несколько `QueryClient` в одном приложении запрещены.** Один инстанс создаётся в `app/clients/queryClient.ts`, оборачивается в `QueryClientProvider` в `app/AppProviders.tsx`.

---

## Избегать

- **`useEffect` для синхронизации server-данных в Zustand или local state.** Если возникает соблазн — данные не там лежат. Перенести в `useQuery` или `select` (см. [`react-conversations.md`](react-conversations.md#L111)).
- **Глобальный store в `stores/` для состояния одного модуля.** Глобальный store оправдан только при кросс-модульной необходимости (`project`, `workspace`, `websocket` — список зафиксирован в [`modules-map.md`](../structure/modules/modules-map.md#L8-L15)).
- **Immer middleware при flat state.** Подключать только при вложенности глубже двух уровней, иначе — `set(state => ({ field: value }))` без middleware.
- **Хранение производных значений в Zustand.** Если можно вычислить из других полей store или из props — вычислять при рендере, не хранить.
- **`enabled: false` + ручной `refetch()` через `useEffect`.** Если есть условие активации — оно идёт в `enabled`, рефетч делает сам TanStack при изменении ключа или условия.
- **Polling через `setInterval` в `useEffect`.** Использовать `refetchInterval` опцию `useQuery` — она уважает фокус окна, видимость вкладки и mount-state.
- **`select` с тяжёлыми трансформациями без мемоизации.** `select: data => normalize(data)` пересоздаёт объект каждый ре-рендер. Если трансформация дорогая — фабрика селектора через `useMemo` или вынос в `services.ts`.

---

## Принятые соглашения

### Decision tree — куда положить данные

Применяется к **каждой** единице данных при её добавлении:

```
1. Данные приходят с сервера (REST/WS)?
   ├── да → TanStack Query (modules/X/query.ts)
   └── нет → шаг 2

2. Состояние нужно только текущему компоненту, не другим?
   ├── да → useState (или useReducer при сложной логике)
   └── нет → шаг 3

3. Состояние нужно 2+ компонентам внутри одного модуля?
   ├── да → Zustand модуля (modules/X/store.ts)
   └── нет → шаг 4

4. Состояние пересекает границы модулей?
   ├── да → Zustand глобальный (stores/X.store.ts)
   └── нет → шаг 1

5. Значение можно вычислить из других значений?
   ├── да → не хранить, вычислять при рендере (или select для useQuery)
   └── нет → решение принято на шаге 1–4
```

Server-данные **никогда** не идут в шаги 2–4. Это снимает классическую рассинхронизацию.

### Разделение по типам данных

| Тип данных | Хранилище | Где описано |
|---|---|---|
| Данные с REST (списки, детали, агрегаты) | TanStack Query кэш | `modules/X/query.ts` |
| Данные WS (новые сообщения, апдейты сущностей) | TanStack Query кэш (через `setQueryData`) | `modules/X/hooks/useXSocket.ts` |
| Статус WS-соединения | Zustand | `stores/websocket.store.ts` |
| Активный выбор (`activeChatId`, `selectedProjectId`) | Zustand | `stores/workspace.store.ts`, `stores/project.store.ts` |
| Черновик ввода, UI-флаг открытия | Zustand модуля или `useState` | `modules/X/store.ts` |
| Состояние формы (uncontrolled) | React Hook Form | — |
| Чисто локальный UI (hover, focus) | `useState` / `useRef` | — |

### TanStack Query — конфигурация по умолчанию

Один `QueryClient` на приложение. Дефолты задаются явно — без них поведение «refetch на каждом mount» приводит к шторму запросов:

```ts
// app/clients/queryClient.ts
import { QueryClient } from '@tanstack/react-query'

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,         // 30s — минимум для дедупликации между mount-ами
      gcTime: 5 * 60_000,        // 5 мин — кэш живёт после размонтирования
      refetchOnWindowFocus: true,
      refetchOnReconnect: 'always',
      retry: 1,
    },
    mutations: {
      retry: 0,
    },
  },
})
```

```ts
// app/AppProviders.tsx
<QueryClientProvider client={queryClient}>
  {children}
</QueryClientProvider>
```

Per-query кастомизация допустима: длинный `staleTime` для справочников, короткий — для отчётов в реальном времени. Изменение делается через аргумент в конкретный `useQuery`, а не глобально.

### Query Keys — фабрика на модуль

Каждый модуль экспортирует фабрику ключей с иерархией `all → группа → элемент`. Иерархия нужна для прицельной инвалидации одной строкой:

```ts
// modules/Chat/query.ts
import type { ChatId } from './entity'

export const chatKeys = {
  all: ['chat'] as const,
  lists: () => [...chatKeys.all, 'list'] as const,
  list: (filters: ChatFilters) => [...chatKeys.lists(), filters] as const,
  details: () => [...chatKeys.all, 'detail'] as const,
  detail: (chatId: ChatId) => [...chatKeys.details(), chatId] as const,
  messages: (chatId: ChatId) => [...chatKeys.detail(chatId), 'messages'] as const,
}
```

Инвалидация:
- `queryClient.invalidateQueries({ queryKey: chatKeys.all })` — все запросы модуля.
- `queryClient.invalidateQueries({ queryKey: chatKeys.detail(id) })` — конкретный чат и его дочерние ключи.
- `queryClient.invalidateQueries({ queryKey: chatKeys.messages(id) })` — только сообщения.

`as const` обязателен — TypeScript выводит литеральный тип, и в коде нельзя случайно подставить произвольный ключ.

### Custom query hooks — обязательная обёртка

Все `useQuery`/`useMutation` живут в `query.ts` модуля и экспортируются как именованные хуки. JSX модуля видит только хуки, не `useQuery` напрямую:

```ts
// modules/Chat/query.ts
export const useChatMessages = (chatId: ChatId) => useQuery({
  queryKey: chatKeys.messages(chatId),
  queryFn: () => apiClient.getMessages(chatId),
  staleTime: 10_000,
})

export const useSendMessage = (chatId: ChatId) => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (text: string) => apiClient.sendMessage(chatId, text),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: chatKeys.messages(chatId) }),
  })
}
```

```tsx
// modules/Chat/MessageList/MessageList.tsx
const { data: messages, isPending } = useChatMessages(activeChatId)
```

Преимущества: единственное место конфигурации запроса, типизированный возврат, тривиальная замена API.

### Мутации — инвалидация и оптимистичные обновления

**Базовый шаблон:** мутация инвалидирует все затронутые ключи в `onSuccess`. TanStack сам выполнит ре-фетч активных запросов:

```ts
export const useSendMessage = (chatId: ChatId) => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (text: string) => apiClient.sendMessage(chatId, text),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: chatKeys.messages(chatId) })
      queryClient.invalidateQueries({ queryKey: chatKeys.detail(chatId) })
    },
  })
}
```

**Оптимистичные обновления** — паттерн `onMutate / onError / onSettled` с rollback:

```ts
export const useSendMessage = (chatId: ChatId) => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (text: string) => apiClient.sendMessage(chatId, text),
    onMutate: async (text) => {
      await queryClient.cancelQueries({ queryKey: chatKeys.messages(chatId) })
      const previous = queryClient.getQueryData<Message[]>(chatKeys.messages(chatId))
      const optimistic: Message = { id: `tmp-${Date.now()}`, chatId, type: 'user', content: text, createdAt: new Date().toISOString() }
      queryClient.setQueryData<Message[]>(chatKeys.messages(chatId), (old = []) => [...old, optimistic])
      return { previous }
    },
    onError: (_err, _vars, ctx) => {
      if (ctx?.previous) queryClient.setQueryData(chatKeys.messages(chatId), ctx.previous)
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: chatKeys.messages(chatId) })
    },
  })
}
```

`onSettled` — единственное место, где `invalidateQueries` запускается всегда (и при успехе, и при ошибке). `onError` восстанавливает предыдущий snapshot. `cancelQueries` нужен, чтобы фоновый refetch не перетёр оптимистичное значение.

### Зависимые запросы

Запрос B зависит от данных A → `enabled`:

```ts
const { data: project } = useProject(projectId)
const { data: reports } = useReports(project?.taskId, {
  enabled: !!project?.taskId,
})
```

Запрет: `useEffect(() => { if (project) fetchReports() }, [project])`. Это переизобретает зависимость.

Пауза/возобновление поллинга — через `enabled` от Zustand-флага:

```ts
const isModalOpen = useUiStore(s => s.isModalOpen)
const { data } = useStatus({
  refetchInterval: isModalOpen ? false : 5_000,
})
```

### Zustand store — структура

Один store на модуль (`modules/X/store.ts`) с типизированной формой и actions как методы store. Глобальные store-ы в `stores/` — только из списка в [`modules-map.md`](../structure/modules/modules-map.md#L8-L15).

```ts
// stores/workspace.store.ts
import { create } from 'zustand'
import type { ChatId } from '@/modules/Chat/entity'

type WorkspaceState = {
  activeChatId: ChatId
  enabledChats: Set<ChatId>
  currentTaskId: string | null
}

type WorkspaceActions = {
  setActiveChatId: (id: ChatId) => void
  enableChat: (id: ChatId) => void
  setCurrentTask: (taskId: string | null) => void
}

export const useWorkspaceStore = create<WorkspaceState & WorkspaceActions>((set) => ({
  activeChatId: 'analytics',
  enabledChats: new Set(['analytics']),
  currentTaskId: null,
  setActiveChatId: (id) => set({ activeChatId: id }),
  enableChat: (id) => set((state) => ({ enabledChats: new Set(state.enabledChats).add(id) })),
  setCurrentTask: (taskId) => set({ currentTaskId: taskId }),
}))
```

### Zustand slices pattern — при росте store

Когда `store.ts` модуля разрастается (5+ блоков несвязанной логики, 100+ строк), разбить на срезы внутри одного файла. Файл остаётся един — slices, не разные файлы:

```ts
// modules/Chat/store.ts
import { create } from 'zustand'
import type { StateCreator } from 'zustand'

type InputSlice = {
  inputDraft: Record<ChatId, string>
  setInputDraft: (chatId: ChatId, value: string) => void
}

type ScrollSlice = {
  scrollPosition: Record<ChatId, number>
  setScrollPosition: (chatId: ChatId, pos: number) => void
}

const createInputSlice: StateCreator<InputSlice & ScrollSlice, [], [], InputSlice> = (set) => ({
  inputDraft: {},
  setInputDraft: (chatId, value) => set((s) => ({ inputDraft: { ...s.inputDraft, [chatId]: value } })),
})

const createScrollSlice: StateCreator<InputSlice & ScrollSlice, [], [], ScrollSlice> = (set) => ({
  scrollPosition: {},
  setScrollPosition: (chatId, pos) => set((s) => ({ scrollPosition: { ...s.scrollPosition, [chatId]: pos } })),
})

export const useChatStore = create<InputSlice & ScrollSlice>()((...a) => ({
  ...createInputSlice(...a),
  ...createScrollSlice(...a),
}))
```

Cross-slice доступ — через `get()` внутри срезов, не через прямое чтение чужого slice снаружи.

### Zustand селекторы — обязательное правило

```tsx
// ❌ — компонент ре-рендерится на любое изменение store
const state = useWorkspaceStore()
return <div>{state.activeChatId}</div>

// ✅ — один селектор, один примитив
const activeChatId = useWorkspaceStore(s => s.activeChatId)
```

Несколько полей за один вызов — через `useShallow`:

```tsx
import { useShallow } from 'zustand/react/shallow'

// ✅ — shallow-сравнение объекта, ре-рендер только при изменении одного из полей
const { activeChatId, enabledChats } = useWorkspaceStore(useShallow((s) => ({
  activeChatId: s.activeChatId,
  enabledChats: s.enabledChats,
})))
```

Без `useShallow` любой селектор, возвращающий новый объект, ломает мемоизацию и приводит к бесконечному ре-рендеру.

### Мутация Zustand state — иммутабельно

Flat state — через `set`:

```ts
// ✅
set((state) => ({ count: state.count + 1 }))
set({ activeChatId: 'systemic' })
```

Вложенное обновление без middleware:

```ts
// ✅
set((state) => ({
  inputDraft: { ...state.inputDraft, [chatId]: value },
}))
```

Вложенность глубже двух уровней — подключить `immer` middleware и работать с draft-ом:

```ts
import { immer } from 'zustand/middleware/immer'

export const useDeepStore = create<DeepState>()(
  immer((set) => ({
    chats: {},
    appendMessage: (chatId, msg) => set((draft) => {
      draft.chats[chatId] ??= { messages: [] }
      draft.chats[chatId].messages.push(msg)
    }),
  })),
)
```

### WebSocket — синхронизация с кэшем

WS — это **источник server-данных**, не отдельное состояние. Бизнес-события идут в кэш TanStack через `setQueryData`:

```ts
// modules/Chat/hooks/useChatSocket.ts
export const useChatSocket = () => {
  const queryClient = useQueryClient()
  const activeChatId = useWorkspaceStore(s => s.activeChatId)

  useEffect(() => {
    const off = websocketClient.subscribe('chat_message', (evt) => {
      if (evt.chatId !== activeChatId) return
      queryClient.setQueryData<Message[]>(chatKeys.messages(activeChatId), (old = []) => [...old, evt.message])
    })
    return off
  }, [activeChatId, queryClient])
}
```

Статус соединения — в `stores/websocket.store.ts` (не в кэше TQ):

```ts
// stores/websocket.store.ts
type WsState = {
  status: 'connecting' | 'connected' | 'disconnected' | 'error'
  lastError: string | null
  setStatus: (s: WsState['status']) => void
}
```

Полная архитектура слоёв WS — в [`architecture.md`](architecture.md#L82-L90).

### Адаптер API

`app/clients/apiClient.ts` — единственное место сетевых вызовов. `query.ts` импортирует функции `apiClient`, не `fetch`/`axios` напрямую. Это позволяет заменить транспорт (HTTP → IPC, REST → gRPC) точечно.

---

## Антипаттерны — свод

Все примеры — `❌ Плохо → ✅ Хорошо`.

**1. `useState` рядом с `useQuery` для копии server-данных**
```tsx
// ❌ — копия server-данных, отписка от фоновых обновлений
const { data } = useChatMessages(chatId)
const [messages, setMessages] = useState<Message[]>([])
useEffect(() => { if (data) setMessages(data) }, [data])

// ✅ — используем данные из useQuery напрямую
const { data: messages = [] } = useChatMessages(chatId)
```

**2. `useEffect` для синхронизации server-данных в Zustand**
```tsx
// ❌ — store рассинхронизируется с кэшем при invalidate
const { data } = useChatMessages(chatId)
useEffect(() => { useChatStore.getState().setMessages(data ?? []) }, [data])

// ✅ — server-данные не лежат в store. В Zustand — только activeChatId, черновик ввода
```

**3. Inline `queryKey` без фабрики**
```ts
// ❌ — опечатка → разные ключи → битый кэш
useQuery({ queryKey: ['chat', 'messages', chatId], queryFn: ... })

// ✅
useQuery({ queryKey: chatKeys.messages(chatId), queryFn: ... })
```

**4. `useQuery` напрямую в JSX модуля**
```tsx
// ❌ — конфигурация запроса размазана по дереву
const Chat = () => {
  const { data } = useQuery({ queryKey: chatKeys.messages(id), queryFn: ... })
}

// ✅ — единая точка в query.ts
const Chat = () => {
  const { data } = useChatMessages(id)
}
```

**5. `setQueryData` вне колбэков мутации и WS-подписок**
```tsx
// ❌ — ручная правка кэша в обработчике клика, без инвалидации
<Button onClick={() => queryClient.setQueryData(chatKeys.messages(id), [])} />

// ✅ — мутация с onSuccess + invalidate, либо WS-подписка
```

**6. `useStore()` без селектора**
```tsx
// ❌ — ре-рендер на каждое изменение любого поля
const store = useWorkspaceStore()

// ✅
const activeChatId = useWorkspaceStore(s => s.activeChatId)
```

**7. Селектор без `useShallow` создаёт новый объект**
```tsx
// ❌ — каждый рендер новая ссылка → бесконечный ре-рендер
const { a, b } = useStore(s => ({ a: s.a, b: s.b }))

// ✅
const { a, b } = useStore(useShallow(s => ({ a: s.a, b: s.b })))
```

**8. Мутация Zustand state без `set`**
```ts
// ❌ — мутация поля, ре-рендер не происходит
useStore.getState().list.push(item)

// ✅
useStore.setState((s) => ({ list: [...s.list, item] }))
```

**9. Дублирование данных WS в Zustand и кэше TQ**
```ts
// ❌ — две копии одного сообщения, рассинхронизация
ws.subscribe('chat_message', (evt) => {
  queryClient.setQueryData(chatKeys.messages(id), (old) => [...old, evt.message])
  useChatStore.getState().appendMessage(evt.message)  // ← дубль
})

// ✅ — только в кэше TQ
ws.subscribe('chat_message', (evt) => {
  queryClient.setQueryData(chatKeys.messages(id), (old = []) => [...old, evt.message])
})
```

**10. `staleTime: 0` для «свежести»**
```ts
// ❌ — шторм запросов при каждом mount
useQuery({ queryKey: chatKeys.messages(id), queryFn: ..., staleTime: 0 })

// ✅ — нормальный staleTime + invalidate после мутаций
useQuery({ queryKey: chatKeys.messages(id), queryFn: ... })
// и в мутации:
onSuccess: () => queryClient.invalidateQueries({ queryKey: chatKeys.messages(id) })
```

**11. Глобальный store для модульного state**
```ts
// ❌ — состояние формы ввода одного модуля попало в stores/
stores/chatInput.store.ts

// ✅ — внутри модуля
modules/Chat/store.ts
```

**12. `setInterval` polling вместо `refetchInterval`**
```tsx
// ❌ — игнорирует focus/visibility, утечка таймера
useEffect(() => {
  const id = setInterval(() => queryClient.invalidateQueries(...), 3000)
  return () => clearInterval(id)
}, [])

// ✅
useQuery({ queryKey: ..., queryFn: ..., refetchInterval: 3000 })
```

---

## Чеклист при добавлении нового модуля

- [ ] `query.ts` создан, экспортирует `xxxKeys` (фабрика) и хуки `useGetX` / `useMutateX`.
- [ ] Все `queryKey` ссылаются на фабрику — никаких inline-литералов.
- [ ] `useQuery` / `useMutation` нигде не вызваны напрямую в JSX модуля.
- [ ] `store.ts` создан только при наличии client state, специфичного модулю; иначе — `useState`.
- [ ] Server-данных в `store.ts` нет — только UI-флаги, выбор, черновики.
- [ ] Все обращения к store используют селекторы; для множественных полей — `useShallow`.
- [ ] Каждая мутация имеет `onSuccess`/`onSettled` с `invalidateQueries`.
- [ ] Оптимистичные обновления реализованы по паттерну `onMutate → snapshot → onError rollback → onSettled invalidate`.
- [ ] WS-события модуля обновляют кэш через `setQueryData` соответствующего ключа (не пишут в Zustand).
- [ ] Зависимые запросы используют `enabled`, не `useEffect`.
- [ ] Polling — через `refetchInterval`, не `setInterval`.

---

## К чему стремимся

**Один источник истины на единицу данных.** Каждая сущность лежит ровно в одном месте: server-данные — в кэше TanStack, client state — в Zustand, локальный UI — в `useState`. Дубликаты невозможны по правилам.

**Минимум сетевых запросов.** Дедупликация по ключу, кэш с `staleTime`, smart refetch на фокусе и реконнекте, оптимистичные обновления вместо ожидания ответа. Идентичные запросы из разных модулей превращаются в один сетевой вызов.

**Минимум ре-рендеров.** Селекторы Zustand с `useShallow` и `select` в TanStack гарантируют, что компонент перерисовывается только при изменении наблюдаемых полей. Глобальная подписка на весь store запрещена.

**Замена бэкенда не трогает UI.** Транспорт изолирован в `app/clients/apiClient.ts` и `app/clients/websocketClient.ts`. `query.ts` ссылается на функции клиента, JSX — на хуки `useGetX`. Переход с REST на gRPC, с HTTP на IPC — точечная правка двух файлов.

**Масштабирование без переписывания.** Новый модуль = свой `query.ts` + при необходимости `store.ts`. Существующие модули не правятся. Slices pattern Zustand покрывает рост store без новых файлов.

**Предсказуемость для AI-агента.** Правила выше формализуют каждый шаг: фабрика ключей, обёртка-хук, паттерн мутации, селектор Zustand. Два независимых исполнителя одинаковую задачу решат одинаково.
