# React Conventions — Rules for AI Agents

> Правила ниже — **строгие**. Нарушение = ошибка реализации.
> Документ пополняется: useEffect → useState → React Query → ...

---

## useEffect

### Канонический сценарий

`useEffect` — только для синхронизации с **внешними системами** вне React:
WebSocket, браузерные API, таймеры, сторонние библиотеки, DOM-мутации.

Если внешней системы нет — `useEffect` не нужен.

### Структура

```tsx
useEffect(() => {
  const connection = createConnection(serverUrl, roomId);
  connection.connect();

  return () => connection.disconnect(); // cleanup обязателен если setup что-то открывает
}, [serverUrl, roomId]);               // все реактивные значения — в deps
```

---

### Правила

| Правило | Детали |
|---|---|
| **Cleanup симметричен setup** | Cleanup отменяет ровно то, что сделал setup |
| **Все реактивные значения — в deps** | Props, state, derived values. Пропускать запрещено |
| **Пустой `[]`** | Эффект запускается один раз при монтировании |
| **Без `[]`** | Запускается после каждого рендера — почти всегда ошибка |
| **ESLint `exhaustive-deps`** | Не подавлять без исправления корневой причины |
| **Объекты/функции в deps** | Создавать внутри эффекта или мемоизировать — иначе infinite loop |
| **Strict Mode** | Dev-режим запускает setup→cleanup→setup на mount для стресс-теста cleanup |

---

### ❌ Плохо → ✅ Хорошо

**Нет cleanup → утечка памяти**
```tsx
// ❌
useEffect(() => {
  window.addEventListener('pointermove', handleMove);
}, []);

// ✅
useEffect(() => {
  window.addEventListener('pointermove', handleMove);
  return () => window.removeEventListener('pointermove', handleMove);
}, []);
```

**Объект в deps → infinite re-run**
```tsx
// ❌ options — новый объект каждый рендер
useEffect(() => {
  const conn = createConnection(options);
  conn.connect();
}, [options]);

// ✅ создать внутри эффекта
useEffect(() => {
  const options = { serverUrl, roomId };
  const conn = createConnection(options);
  conn.connect();
  return () => conn.disconnect();
}, [serverUrl, roomId]);
```

**Счётчик с зависимостью от self → постоянный сброс интервала**
```tsx
// ❌
useEffect(() => {
  const id = setInterval(() => setCount(count + 1), 1000);
  return () => clearInterval(id);
}, [count]);

// ✅ updater-функция убирает зависимость
useEffect(() => {
  const id = setInterval(() => setCount(c => c + 1), 1000);
  return () => clearInterval(id);
}, []);
```

**Race condition при fetch**
```tsx
// ❌ устаревший ответ может перезаписать актуальный
useEffect(() => {
  fetchBio(person).then(result => setBio(result));
}, [person]);

// ✅ ignore-флаг
useEffect(() => {
  let ignore = false;
  fetchBio(person).then(result => {
    if (!ignore) setBio(result);
  });
  return () => { ignore = true; };
}, [person]);
```

---

### Не использовать useEffect для

| Вместо этого |  |
|---|---|
| Вычисление из props/state | Считать прямо при рендере |
| Сброс state при смене prop | Использовать `key` prop |
| Обработка событий | Использовать event handler |
| Загрузка данных | React Query / SWR (не самописный fetch в Effect) |

```tsx
// ❌ Effect для производного значения
const [fullName, setFullName] = useState('');
useEffect(() => {
  setFullName(firstName + ' ' + lastName);
}, [firstName, lastName]);

// ✅ вычислить при рендере
const fullName = firstName + ' ' + lastName;
```

---

### Вынос в Custom Hook

Если логика нетривиальна или переиспользуется — обернуть в hook:

```tsx
function useChatRoom({ serverUrl, roomId }: ChatRoomOptions) {
  useEffect(() => {
    const conn = createConnection(serverUrl, roomId);
    conn.connect();
    return () => conn.disconnect();
  }, [serverUrl, roomId]);
}
```

---

## useState

### Канонический сценарий

`useState` — для хранения данных, изменение которых должно вызывать ре-рендер компонента:
значения форм, флаги открытия/закрытия, локальные счётчики, выбранный элемент.

Если значение не влияет на рендер — использовать `useRef`, не `useState`.

### Структура

```tsx
const [value, setValue] = useState<Type>(initialValue);
// или с initializer-функцией (дорогое начальное значение):
const [todos, setTodos] = useState(() => createInitialTodos());
```

---

### Правила

| Правило | Детали |
|---|---|
| **Top-level only** | Запрещено внутри условий, циклов, вложенных функций |
| **Иммутабельность** | Объекты/массивы — всегда новые (`...spread`), мутация не вызывает ре-рендер |
| **Updater-функция** | Если новое значение зависит от предыдущего — `s => newValue`, иначе батчинг даст неверный результат |
| **Initializer-функция** | Передавать `fn`, не `fn()` — иначе запускается на каждом рендере |
| **Batching** | React группирует все `setState` внутри одного обработчика в один ре-рендер |
| **Object.is сравнение** | Если новое значение `===` старому — ре-рендера нет |
| **Strict Mode** | Initializer и updater запускаются дважды в dev — должны быть чистыми функциями |

---

### ❌ Плохо → ✅ Хорошо

**Чтение state сразу после set — стейт не обновился**
```tsx
// ❌
setName('Robin');
console.log(name); // всё ещё старое значение

// ✅ читать из промежуточной переменной
const nextName = 'Robin';
setName(nextName);
console.log(nextName);
```

**Несколько set подряд без updater → только последний эффект**
```tsx
// ❌ age становится 43, а не 45
setAge(age + 1); // 42 → 43
setAge(age + 1); // 42 → 43 (перезаписывает)
setAge(age + 1); // 42 → 43 (перезаписывает)

// ✅ updater-функции выстраиваются в очередь
setAge(a => a + 1); // 42 → 43
setAge(a => a + 1); // 43 → 44
setAge(a => a + 1); // 44 → 45
```

**Мутация объекта — ре-рендера нет**
```tsx
// ❌
form.firstName = 'Taylor';
setForm(form); // то же самое, React не видит изменений

// ✅ создать новый объект
setForm({ ...form, firstName: 'Taylor' });

// ✅ вложенный объект
setPerson({ ...person, artwork: { ...person.artwork, title: 'Новое' } });

// ✅ массив
setTodos([...todos, newTodo]);
setTodos(todos.filter(t => t.id !== id));
```

**Initializer — передать функцию, не результат вызова**
```tsx
// ❌ createInitialTodos() вызывается на каждом рендере
const [todos, setTodos] = useState(createInitialTodos());

// ✅ передать ссылку на функцию
const [todos, setTodos] = useState(createInitialTodos);
```

**Хранение функции в state**
```tsx
// ❌ React воспримет fn как initializer и вызовет её
const [fn, setFn] = useState(someFunction);

// ✅ обернуть в анонимную функцию
const [fn, setFn] = useState(() => someFunction);
```

---

### Не использовать useState для

| Случай | Альтернатива |
|---|---|
| Производное значение из props/state | Вычислить при рендере |
| Значение не влияет на рендер | `useRef` |
| Сброс всего state дочернего компонента | `key` prop на дочернем компоненте |
| Синхронизация state с prop (большинство случаев) | Вычислить из prop напрямую |

```tsx
// ❌ дублирование prop в state
const [color, setColor] = useState(props.color);
// при обновлении props.color state не изменится

// ✅ использовать prop напрямую
const color = props.color;
// или если нужна локальная модификация:
const [color, setColor] = useState(props.initialColor); // explicit "initial"
```

```tsx
// ❌ производное значение в state
const [fullName, setFullName] = useState('');
useEffect(() => setFullName(firstName + ' ' + lastName), [firstName, lastName]);

// ✅ вычислить при рендере
const fullName = firstName + ' ' + lastName;
```
