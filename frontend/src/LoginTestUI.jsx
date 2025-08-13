import { useState, useEffect } from 'react';
import axios from 'axios';
import GeoMethodsPanel from './panels/GeoMethodsPanel';
import * as XLSX from "xlsx";

/**
 * Компонент для тестирования авторизации и получения методов оплаты.
 */
export default function LoginTestUI() {
  // Состояния для данных и UI
  const [projects, setProjects] = useState([]);
  const [geoGroups, setGeoGroups] = useState({});
  const [form, setForm] = useState({ project: '', login: '', geo: '', env: 'stage' });
  const [logins, setLogins] = useState([]);
  const [result, setResult] = useState(null);
  const [methodsOnly, setMethodsOnly] = useState(null);
  const [groupedIds, setGroupedIds] = useState({});
  const [conditionsMap, setConditionsMap] = useState({});
  const [recommendedPairs, setRecommendedPairs] = useState([]);
  const [methodTypes, setMethodTypes] = useState({});
  const [originalOrder, setOriginalOrder] = useState([]);
  const [isGeoMode, setIsGeoMode] = useState(false);

  // Загрузка начальных данных при монтировании компонента
  useEffect(() => {
    axios.get('/list-projects').then(res => setProjects(res.data));
    axios.get('/geo-groups').then(res => setGeoGroups(res.data));
  }, []);

  // Обновление списка логинов при изменении GEO
  useEffect(() => {
    if (form.geo && geoGroups[form.geo]) {
      setLogins(geoGroups[form.geo]);
    } else {
      setLogins([]);
      // Сбрасываем только логин, чтобы не терять другие поля формы
      setForm(f => ({ ...f, login: '' }));
    }
  }, [form.geo, geoGroups]);

  /**
   * Обработчик изменений в полях формы с расширенным логированием.
   * @param {React.ChangeEvent<HTMLSelectElement>} e - Событие изменения.
   */
  const handleChange = (e) => {
    const { name, value } = e.target;
    console.log(`handleChange triggered for [${name}] with value: [${value}]`);
    setForm(prev => {
      const newForm = { ...prev, [name]: value };
      // Логируем состояние, которое ДОЛЖНО быть установлено после этого обновления
      console.log("Updated form state should be:", newForm);
      return newForm;
    });
  };

  /**
   * Нормализация текста для сравнения.
   * @param {string} text - Входной текст.
   * @returns {string} - Нормализованный текст.
   */
  const normalize = (text) => (text || '').trim().toLowerCase();

  /**
   * Извлечение тегов из имени метода.
   * @param {string} name - Имя метода.
   * @returns {string} - Строка с тегами.
   */
  const extractTag = (name) => {
    const dep = name.match(/(\d+)DEP/i)?.[1];
    const isAff = /aff/i.test(name);
    const isMob = /mob/i.test(name);
    const tags = [];
    if (dep) tags.push(`${dep}DEP`);
    if (isAff) tags.push('AFF');
    if (isMob) tags.push('MOB');
    return tags.join('+');
  };

  /**
   * Запускает проверку и агрегацию методов для всех логинов в выбранном GEO.
   */
  const handleAllLoginsCheck = async () => {
    if (!form.geo) {
      console.error("Пожалуйста, выберите GEO");
      return;
    }

    const allLogins = [...(geoGroups[form.geo] || [])].sort().reverse();
    const titleMap = new Map();
    const conditionMap = new Map();
    const methodTypeMap = {};
    const recommendedSet = new Set();
    const seenTitles = new Set();
    const order = [];

    // Итерация по всем логинам для сбора данных
    for (const login of allLogins) {
      try {
        const res = await axios.post('/get-methods-only', { ...form, login });
        const { data } = res;

        // Обработка рекомендованных методов
        data.recommended_methods?.forEach(([title, name]) => {
          recommendedSet.add(`${normalize(title)}|||${normalize(name)}`);
        });

        const processMethods = (methods, type) => {
          methods?.forEach(([title, name]) => {
            const normTitle = normalize(title);
            const normName = normalize(name);
            const key = `${normTitle}|||${normName}`;
            
            methodTypeMap[key] = methodTypeMap[key] || {};
            methodTypeMap[key][type] = true;

            if (!titleMap.has(title)) titleMap.set(title, new Set());
            titleMap.get(title).add(name);

            const tag = extractTag(name);
            if (tag) {
              if (!conditionMap.has(title)) conditionMap.set(title, new Set());
              conditionMap.get(title).add(tag);
            }

            if (!seenTitles.has(title)) {
              order.push(title);
              seenTitles.add(title);
            }
          });
        };

        processMethods(data.deposit_methods, 'deposit');
        processMethods(data.withdraw_methods, 'withdraw');

      } catch (err) {
        console.warn(`Ошибка при проверке логина ${login}:`, err);
      }
    }

    // Форматирование собранных данных для передачи в дочерний компонент
    const grouped = Object.fromEntries(
      Array.from(titleMap.entries()).map(([title, names]) => [title, Array.from(names).join('\n')])
    );

    const conditions = Object.fromEntries(
      Array.from(conditionMap.entries()).map(([title, tags]) => {
        const unique = Array.from(tags).filter(Boolean);
        return [title, unique.length ? unique.sort().join('\n') : 'ALL'];
      })
    );

    const depositList = Object.entries(methodTypeMap)
      .filter(([, t]) => t.deposit)
      .map(([key]) => key.split('|||').map(s => originalOrder.find(o => normalize(o) === s) || s));

    const withdrawList = Object.entries(methodTypeMap)
      .filter(([, t]) => t.withdraw)
      .map(([key]) => key.split('|||').map(s => originalOrder.find(o => normalize(o) === s) || s));

    const recommendedList = Array.from(recommendedSet).map(s => s.split('|||'));

    // Обновление состояния
    setGroupedIds(grouped);
    setConditionsMap(conditions);
    setRecommendedPairs(recommendedList);
    setMethodTypes(methodTypeMap);
    setOriginalOrder(order);
    setIsGeoMode(true);
    setMethodsOnly({
      deposit_methods: depositList,
      withdraw_methods: withdrawList,
      recommended_methods: recommendedList
    });
  };

  /**
   * Обработчик отправки формы для проверки одного логина.
   * @param {React.FormEvent<HTMLFormElement>} e - Событие отправки формы.
   */
  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsGeoMode(false);
    setMethodsOnly(null);
    try {
      const res = await axios.post('/run-login-check', form);
      setResult(res.data);
    } catch (err) {
      setResult({ success: false, error: err.message });
    }
  };
  
  // Логирование состояния формы для отладки на каждом рендере
  console.log("Текущее состояние формы в LoginTestUI:", form);

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6 bg-gray-50 font-sans">
      <h1 className="text-3xl font-bold text-gray-800">Инструмент проверки методов</h1>

      <form onSubmit={handleSubmit} className="p-6 bg-white rounded-lg shadow-md space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">Проект:</label>
            <select name="project" value={form.project} onChange={handleChange} className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md">
              <option value="">-- Выберите проект --</option>
              {projects.map(p => <option key={p.name} value={p.name}>{p.name}</option>)}
            </select>
            {/* Отладочный вывод прямо в интерфейсе */}
            <div className="mt-2 text-xs text-gray-500">Текущее значение project: <strong>{form.project || "<пусто>"}</strong></div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">GEO:</label>
            <select name="geo" value={form.geo} onChange={handleChange} className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md">
              <option value="">-- Выберите GEO --</option>
              {Object.keys(geoGroups).sort().map(geo => <option key={geo} value={geo}>{geo}</option>)}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Логин:</label>
            <select name="login" value={form.login} onChange={handleChange} className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md" disabled={!form.geo}>
              <option value="">-- Выберите логин --</option>
              {logins.map(login => <option key={login} value={login}>{login}</option>)}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Окружение:</label>
            <select name="env" value={form.env} onChange={handleChange} className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md">
              <option value="stage">stage</option>
              <option value="prod">prod</option>
            </select>
          </div>
        </div>

        <div className="flex gap-4 flex-wrap pt-4 border-t">
          <button type="submit" className="bg-blue-600 text-white px-4 py-2 rounded-md shadow-sm hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">Проверить логин</button>
          <button type="button" onClick={handleAllLoginsCheck} className="bg-indigo-600 text-white px-4 py-2 rounded-md shadow-sm hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">Агрегировать по GEO</button>
        </div>
      </form>

      {result && !isGeoMode && (
        <div className="mt-6 p-4 bg-white rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-2 text-gray-800">Результат проверки авторизации</h3>
          <p><strong>Валюта:</strong> {result.currency}</p>
          <p><strong>Количество депозитов:</strong> {result.deposit_count}</p>
          {result.error && <p className="text-red-600"><strong>Ошибка:</strong> {result.error}</p>}
        </div>
      )}

      {/* Рендер панели с методами только если есть данные и выбран проект */}
      {isGeoMode && methodsOnly && form.project && form.env ? (
        <div className="mt-6">
          {/* 4. Лог перед рендером GeoMethodsPanel для проверки props */}
          {console.log("Перед рендером GeoMethodsPanel, form.project:", form.project, "form.env:", form.env)}
          <h3 className="text-2xl font-bold mb-4 text-gray-800">
            Агрегированные методы для GEO: {form.geo}
          </h3>
          <GeoMethodsPanel
            methodsOnly={methodsOnly}
            groupedIds={groupedIds}
            conditionsMap={conditionsMap}
            recommendedPairs={recommendedPairs}
            originalOrder={originalOrder}
            isFullProject={isGeoMode}
            project={form.project}
            env={form.env}
            geo={form.geo}
            currency={result?.currency}
          />
        </div>
      ) : (
        isGeoMode && (
          <div className="mt-6 p-4 bg-yellow-100 text-yellow-800 rounded-lg shadow">
            <p>Не удалось отобразить панель методов. Убедитесь, что вы выбрали проект и GEO, а затем нажали "Агрегировать по GEO".</p>
          </div>
        )
      )}
    </div>
  );
}
