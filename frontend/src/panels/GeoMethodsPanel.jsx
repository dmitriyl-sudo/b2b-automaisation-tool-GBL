import { useState, useEffect } from 'react';
import {
  Box, Button, Table, Thead, Tbody, Tr, Th, Td, Text, HStack, VStack, Stack,
  FormControl, FormLabel, Select, useToast, Center, Heading
} from '@chakra-ui/react';
import * as XLSX from "xlsx";

/* ---------------- helpers ---------------- */
// 🔧 ВРЕМЕННОЕ РЕШЕНИЕ: Binance Pay
// 🔧 ВРЕМЕННОЕ РЕШЕНИЕ: Binance Pay
// Добавляет "Binance Pay - EUR - YES - YES - STATUS - prod - ALL - 50 EUR" в самый низ
// (но выше методов только для вывода)
// ❗ ЧТОБЫ ОТКЛЮЧИТЬ: поставить ENABLE_BINANCE_PAY_TEMP = false
const ENABLE_BINANCE_PAY_TEMP = false;

// 🔧 ВРЕМЕННОЕ РЕШЕНИЕ: Jeton
// Добавляет "Jeton - EUR - YES - YES - STATUS - prod - ALL - 20 EUR" в самый низ
// ❗ ЧТОБЫ ОТКЛЮЧИТЬ: поставить ENABLE_JETON_TEMP = false
const ENABLE_JETON_TEMP = false;

const normalizeText = (s) => (s || '').trim().toLowerCase();
const normKey = (t, n) =>
  `${(t||'').toLowerCase().replace(/\s+/g,'').replace(/[^a-z0-9/+-]/g,'')}` +
  '|||' +
  `${(n||'').toLowerCase().replace(/\s+/g,'').replace(/[^a-z0-9/+-]/g,'')}`;

// алиасы тайтлов
const titleAlias = (t) => {
  const s = (t || '').trim();
  if (/^apple\s*pay$/i.test(s)) return 'Applepay';
  // 🔧 УБИРАЕМ ПРЕОБРАЗОВАНИЕ SKRL -> Skrill чтобы они были отдельными группами
  // if (/^skrl$/i.test(s))       return 'Skrill';
  if (/^visa\/?mc$/i.test(s))  return 'Visa/Mastercard';
  return s;
};

// крипта
const isCryptoTitle = (t) => {
  const s = (t || '').trim().toLowerCase();
  if (s === 'crypto') return true;
  const prefixes = [
    'usdtt', 'usdt', 'usdte', 'usdc',
    'btc', 'eth', 'ltc', 'trx', 'xrp', 'sol', 'ada', 'bch', 'ton', 'doge'
  ];
  return prefixes.some(p => s.startsWith(p));
};
const isCryptoName = (n) =>
  /Coinspaid|Crypto(pay)?|Tether|Bitcoin|Ethereum|Litecoin|Ripple|Tron|USDT|USDC|BTC|ETH|LTC|TRX|XRP|SOL|ADA|BCH|TON|DOGE/i.test(n || '');

// Функции для хардкод методов
const getCurrencyFromGeoName = (geoName) => {
  if (!geoName) return 'EUR';
  const geoUpper = geoName.toUpperCase();
  
  // Проверяем локальные валюты в названии GEO
  if (geoUpper.includes('_PLN')) return 'PLN';
  if (geoUpper.includes('_DKK')) return 'DKK';
  if (geoUpper.includes('_CHF')) return 'CHF';
  if (geoUpper.includes('_NOK')) return 'NOK';
  if (geoUpper.includes('_HUF')) return 'HUF';
  if (geoUpper.includes('_AUD')) return 'AUD';
  if (geoUpper.includes('_CAD')) return 'CAD';
  if (geoUpper.includes('_USD')) return 'USD';
  
  // Если локальная валюта не указана - EUR по умолчанию
  return 'EUR';
};

const getHardcodedMethodsForGeo = (geoName, currency) => {
  const methods = [];
  const geoUpper = (geoName || '').toUpperCase();
  
  // Zimpler для Финляндии
  if (geoUpper.startsWith('FI')) {
    methods.push({
      title: 'Zimpler',
      names: new Set(['Zimpler_Zimpler_Wallet_0DEP']),
      conditions: new Set(['0DEP']),
      isRecommended: true,
      hasDeposit: true,
      hasWithdraw: true,
      isCrypto: false,
      isHardcoded: true,
      currency: currency,
      minDeposit: 10
    });
  }
  
  // 🔧 BLIK ВРЕМЕННО ОТКЛЮЧЕН - для включения раскомментируйте блок ниже
  // Blik для Польши
  // if (geoUpper.startsWith('PL')) {
  //   methods.push({
  //     title: 'Blik',
  //     names: new Set(['Blik_Blik_Wallet']),
  //     conditions: new Set(['ALL']),
  //     isRecommended: false,
  //     hasDeposit: true,
  //     hasWithdraw: false,
  //     isCrypto: false,
  //     isHardcoded: true,
  //     currency: currency,
  //     minDeposit: 10
  //   });
  // }
  
  // ApplePay Visa (Gumballpay) для всех GEO
  methods.push({
    title: 'ApplePay Visa',
    names: new Set(['Applepay_Gumballpay_Cards_1DEP']),
    conditions: new Set(['1DEP']),
    isRecommended: false,
    hasDeposit: true,
    hasWithdraw: false,
    isCrypto: false,
    isHardcoded: true,
    currency: currency,
    minDeposit: 20
  });
  
  return methods;
};

export default function GeoMethodsPanel({
  methodsOnly,
  groupedIds,
  conditionsMap,
  recommendedPairs,
  methodTypes,
  originalOrder,
  geo,
  currency,
  hidePaymentName = false,
  isFullProject = false,
  env,
  project,
  globalAddHardcodedMethods = false
}) {
  const [filter, setFilter] = useState('all');
  const [isExporting, setIsExporting] = useState(false);
  // Используем глобальное состояние вместо локального
  const addHardcodedMethods = globalAddHardcodedMethods;
  

  /* ---------- группировка текущего GEO (UI) ---------- */
  const extractTag = (name) => {
    const dep = name.match(/(\d+)DEP/i)?.[1];
    const isAff = /aff/i.test(name);
    const isMob = /mob/i.test(name);
    const tags = [];
    if (dep) tags.push(`${dep}DEP`);
    if (isAff) tags.push('AFF');
    if (isMob) tags.push('MOB');
    return tags;
  };

  const groupedMap = new Map();
  [...(methodsOnly?.deposit_methods || []), ...(methodsOnly?.withdraw_methods || [])].forEach(([titleRaw, name]) => {
    const title = titleAlias(titleRaw);

    if (!groupedMap.has(title)) {
      groupedMap.set(title, {
        title,
        names: new Set(),
        conditions: new Set(),
        isRecommended: false,
        hasDeposit: false,
        hasWithdraw: false,
        isCrypto: false,
      });
    }
    const group = groupedMap.get(title);
    group.names.add(name);
    extractTag(name).forEach(tag => group.conditions.add(tag));

    const inDep = methodsOnly?.deposit_methods?.some(
      ([t, n]) => normalizeText(titleAlias(t)) === normalizeText(title) &&
                  normalizeText(n) === normalizeText(name)
    );
    const inWdr = methodsOnly?.withdraw_methods?.some(
      ([t, n]) => normalizeText(titleAlias(t)) === normalizeText(title) &&
                  normalizeText(n) === normalizeText(name)
    );
    if (inDep) group.hasDeposit = true;
    if (inWdr) group.hasWithdraw = true;

    // крипта → всегда YES/YES
    const crypto = isCryptoTitle(title) || isCryptoName(name);
    if (crypto) {
      group.isCrypto = true;
      group.hasDeposit = true;
      group.hasWithdraw = true;
    }

    const isRec = recommendedPairs?.some(
      ([rt, rn]) => normalizeText(titleAlias(rt)) === normalizeText(title) &&
                    normalizeText(rn) === normalizeText(name)
    );
    if (isRec) group.isRecommended = true;
  });

  // 🔧 ВРЕМЕННОЕ РЕШЕНИЕ: добавляем Binance Pay (флаг в начале файла)
  let baseFilteredGroups = (originalOrder || [])
    .map(t => groupedMap.get(titleAlias(t)))
    .filter(Boolean)
    .filter(group => {
      if (filter === 'all') return true;
      if (filter === 'recommended') return group.isRecommended;
      return Array.from(group.conditions).some(tag => tag.includes(filter));
    });

  // Добавляем временный Binance Pay если включен флаг
  if (false) {
    const binancePayGroup = {
      title: 'Binance Pay',
      names: new Set(['Binancepay_Binancepay_Crypto']),
      conditions: new Set(['ALL']),
      isRecommended: false,
      hasDeposit: true,
      hasWithdraw: true,
      isCrypto: true,
      isTemp: true // маркер что это временный метод
    };

    // Добавляем в самый низ списка
    baseFilteredGroups.push(binancePayGroup);
  }

  // Добавляем временный Jeton если включен флаг
  if (false) {
    const jetonGroup = {
      title: 'Jeton',
      names: new Set(['Jeton_Jeton_Wallet']),
      conditions: new Set(['ALL']),
      isRecommended: false,
      hasDeposit: true,
      hasWithdraw: true,
      isCrypto: false, // Jeton НЕ криптовалюта
      isTemp: true // маркер что это временный метод
    };

    // Добавляем в самый низ списка
    baseFilteredGroups.push(jetonGroup);
  }

  // Добавляем хардкод методы если включен чекбокс
  if (addHardcodedMethods && env === 'prod' && baseFilteredGroups.length > 0) {
    console.log('Добавляем хардкод методы в непустое GEO');
    
    const geoCurrency = getCurrencyFromGeoName(geo);
    const hardcodedMethods = getHardcodedMethodsForGeo(geo, geoCurrency);
    
    // Удаляем существующие хардкод методы чтобы избежать дубликатов
    baseFilteredGroups = baseFilteredGroups.filter(group => !group.isHardcoded);
    
    // Проверяем существующие методы чтобы избежать дубликатов
    const existingTitles = new Set(baseFilteredGroups.map(group => group.title.toLowerCase()));
    
    // Разделяем методы на ApplePay и остальные
    const nonApplePayMethods = [];
    const applePayMethods = [];
    
    hardcodedMethods.forEach(method => {
      // Проверяем что метод еще не существует
      if (existingTitles.has(method.title.toLowerCase())) {
        console.log(`Метод ${method.title} уже существует, пропускаем`);
        return;
      }
      
      // Проверяем фильтр
      const passesFilter = (() => {
        if (filter === 'all') return true;
        if (filter === 'recommended') return method.isRecommended;
        return Array.from(method.conditions).some(tag => tag.includes(filter));
      })();
      
      if (passesFilter) {
        if (method.title === 'ApplePay Visa') {
          applePayMethods.push(method);
        } else {
          nonApplePayMethods.push(method);
        }
      }
    });
    
    // Добавляем не-ApplePay методы в обычном порядке
    nonApplePayMethods.forEach(method => {
      baseFilteredGroups.push(method);
    });
    
    // Вставляем ApplePay точно на 11-е место (индекс 10)
    const targetIndex = 10;
    applePayMethods.forEach(applePayMethod => {
      if (baseFilteredGroups.length >= targetIndex) {
        baseFilteredGroups.splice(targetIndex, 0, applePayMethod);
      } else {
        baseFilteredGroups.push(applePayMethod);
      }
    });
  }

  const filteredGroups = baseFilteredGroups;

  /* ---------- min-deps (число) ---------- */
  const [minByKey, setMinByKey] = useState(new Map());
  const [minByKeyNorm, setMinByKeyNorm] = useState(new Map());

  useEffect(() => {
    const m = new Map();
    const mNorm = new Map();

    const put = (title, name, val) => {
      if (!title || !name) return;
      const t = titleAlias(title);
      const k = `${t}|||${name}`;
      if (Number.isFinite(val)) {
        m.set(k, val);
        mNorm.set(normKey(t, name), val);
      }
    };

    const md = methodsOnly || {};
    if (md.min_deposit_by_key && typeof md.min_deposit_by_key === 'object') {
      for (const [k, v] of Object.entries(md.min_deposit_by_key)) {
        const num = Number(v);
        if (!Number.isFinite(num)) continue;
        const [t, n] = String(k).split('|||');
        put(t, n, num);
      }
      (md.min_deposit_map || []).forEach(r => put(r?.title, r?.name, Number(r?.min_deposit)));
      (md.min_deposits || []).forEach(r => put(r?.Title, r?.Name, Number(r?.MinDeposit)));
    } else if (Array.isArray(md.min_deposit_map)) {
      md.min_deposit_map.forEach(r => put(r?.title, r?.name, Number(r?.min_deposit)));
    } else if (Array.isArray(md.min_deposits)) {
      md.min_deposits.forEach(r => put(r?.Title, r?.Name, Number(r?.MinDeposit)));
    }

    // 🔧 ВРЕМЕННОЕ РЕШЕНИЕ: добавляем минимальный депозит для Binance Pay
    if (false) {
      put('Binance Pay', 'Binancepay_Binancepay_Crypto', 50);
    }

    // 🔧 ВРЕМЕННОЕ РЕШЕНИЕ: добавляем минимальный депозит для Jeton
    if (false) {
      put('Jeton', 'Jeton_Jeton_Wallet', 20);
    }

    // Добавляем минимальные депозиты для хардкод методов
    if (addHardcodedMethods && env === 'prod' && methodsOnly && methodsOnly.length > 0) {
      const geoCurrency = getCurrencyFromGeoName(geo);
      const hardcodedMethods = getHardcodedMethodsForGeo(geo, geoCurrency);
      
      hardcodedMethods.forEach(method => {
        const methodName = Array.from(method.names)[0];
        put(method.title, methodName, method.minDeposit);
      });
    }

    setMinByKey(m);
    setMinByKeyNorm(mNorm);
  }, [methodsOnly, env, addHardcodedMethods, geo]);

  const getMinDepositForGroup = (group) => {
    let minVal = Infinity;
    let found = false;
    for (const name of group.names) {
      const titleFixed = titleAlias(group.title);
      const exactKey = `${titleFixed}|||${name}`;
      const nk = normKey(titleFixed, name);
      const val = minByKey.get(exactKey) ?? minByKeyNorm.get(nk);
      if (Number.isFinite(val)) { minVal = Math.min(minVal, val); found = true; }
    }
    return found ? minVal : null;
  };

  /* ---------- быстрый фронтовый XLSX ---------- */
  const handleExportFrontendGeo = () => {
    if (!filteredGroups || filteredGroups.length === 0) return;

    // Специальная сортировка с размещением ApplePay на 11-м месте
    const groups = [...filteredGroups];
    
    // Отделяем ApplePay от остальных
    const applePayGroups = groups.filter(group => group.title === 'ApplePay Visa' && group.isHardcoded);
    const otherGroups = groups.filter(group => !(group.title === 'ApplePay Visa' && group.isHardcoded));
    
    // Сортируем остальные группы по стандартной логике
    const sortedOthers = otherGroups.sort((a, b) => {
      // Временные методы всегда в самый низ
      if (a.isTemp !== b.isTemp) return a.isTemp ? 1 : -1;
      
      // Определяем является ли метод криптовалютой
      const isCryptoA = a.title.toLowerCase().includes('crypto') || 
                       ['btc', 'eth', 'ltc', 'usdt', 'usdc', 'trx', 'doge', 'ada', 'sol', 'xrp', 'bch', 'ton'].some(crypto => 
                         a.title.toLowerCase().includes(crypto.toLowerCase()));
      const isCryptoB = b.title.toLowerCase().includes('crypto') || 
                       ['btc', 'eth', 'ltc', 'usdt', 'usdc', 'trx', 'doge', 'ada', 'sol', 'xrp', 'bch', 'ton'].some(crypto => 
                         b.title.toLowerCase().includes(crypto.toLowerCase()));
      
      // Определяем является ли метод только withdraw
      const isWithdrawOnlyA = !a.hasDeposit && a.hasWithdraw;
      const isWithdrawOnlyB = !b.hasDeposit && b.hasWithdraw;
      
      // Специальная логика для Binance Pay и Jeton - размещаем выше "Crypto"
      const isSpecialA = (a.title === 'Binance Pay' || a.title === 'Jeton');
      const isSpecialB = (b.title === 'Binance Pay' || b.title === 'Jeton');
      const isCryptoMethodA = (a.title === 'Crypto');
      const isCryptoMethodB = (b.title === 'Crypto');
      
      // Если один из методов - Binance Pay/Jeton, а другой - именно "Crypto"
      if (isSpecialA && isCryptoMethodB) return -1; // Binance Pay/Jeton выше Crypto
      if (isCryptoMethodA && isSpecialB) return 1;  // Crypto ниже Binance Pay/Jeton
      
      // Сортировка по категориям:
      // 1. Рекомендованные не-крипто методы (в оригинальном порядке)
      // 2. Обычные не-крипто методы (в оригинальном порядке)
      // 3. Binance Pay и Jeton (выше "Crypto")
      // 4. Криптовалюты: "Crypto" первая, остальные по алфавиту
      // 5. Withdraw-only методы (в оригинальном порядке)
      
      if (isWithdrawOnlyA !== isWithdrawOnlyB) return isWithdrawOnlyA ? 1 : -1;
      if (isCryptoA !== isCryptoB) return isCryptoA ? 1 : -1;
      
      // Для не-крипто методов: рекомендованные вперед, потом оригинальный порядок
      if (!isCryptoA && !isCryptoB) {
        if (a.isRecommended !== b.isRecommended) return a.isRecommended ? -1 : 1;
        return (originalOrder || []).indexOf(a.title) - (originalOrder || []).indexOf(b.title);
      }
      
      // Внутри криптовалют: "Crypto" всегда первая, остальные по алфавиту
      if (isCryptoA && isCryptoB) {
        // "Crypto" всегда первая
        if (a.title === "Crypto" && b.title !== "Crypto") return -1;
        if (b.title === "Crypto" && a.title !== "Crypto") return 1;
        
        // Остальные криптовалюты по базовому названию
        const baseNameA = a.title.replace(/\s*-\s*.*$/, '').trim();
        const baseNameB = b.title.replace(/\s*-\s*.*$/, '').trim();
        return baseNameA.localeCompare(baseNameB);
      }
      
      return 0;
    });
    
    // Вставляем ApplePay на 11-е место (индекс 10)
    const targetIndex = 10;
    const finalGroups = [...sortedOthers];
    
    applePayGroups.forEach(applePayGroup => {
      if (finalGroups.length >= targetIndex) {
        finalGroups.splice(targetIndex, 0, applePayGroup);
      } else {
        finalGroups.push(applePayGroup);
      }
    });
    
    const sorted = finalGroups;

    const exportData = sorted.map(row => {
      const minVal = getMinDepositForGroup(row);
      return {
        Paymethod: row.title,
        Recommended: row.isRecommended ? '⭐\u200B' : '',
        "Payment Name": Array.from(row.names).join('\n'),
        Currency: currency || '-',                                // 👈 GEO-level currency
        Deposit: row.hasDeposit ? "YES" : "NO",
        Withdraw: row.hasWithdraw ? "YES" : "NO",
        Status: env === "prod" ? "PROD" : "STAGE",
        Details: conditionsMap?.[row.title] || (row.conditions.size > 0 ? Array.from(row.conditions).sort().join('\n') : "ALL"),
        "Min Dep": Number.isFinite(minVal) ? `${minVal} ${currency || ''}`.trim() : '—' // 👈 number + GEO currency
      };
    });

    const worksheet = XLSX.utils.json_to_sheet(exportData);
    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, worksheet, "GEO Methods");
    XLSX.writeFile(workbook, `GeoMethods_${project || 'unknown'}_${geo || 'unknown'}_${env || 'stage'}.xlsx`);
  };

  /* ---------- экспорт: один GEO в Google Sheets ---------- */
  const handleExportSingleGeoToSheets = async () => {
    if (!project || !geo || !env) return;
    setIsExporting(true);

    try {
      // 🔧 НОВАЯ ЛОГИКА: Получаем готовые данные от бэкенда
      const sheetsDataRes = await fetch('/get-sheets-data-fixed', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ project, geo, env })
      });
      
      const sheetsDataJson = await sheetsDataRes.json();
      
      if (!sheetsDataJson.success) {
        console.error('Ошибка получения данных для Google Sheets:', sheetsDataJson.error);
        return;
      }
      
      const data = sheetsDataJson.data || [];
      
      // Экспортируем готовые данные в Google Sheets
      const exportRes = await fetch('/export-table-to-sheets', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ data, originalOrder: [], project, geo, env })
      });
      
      const exportJson = await exportRes.json();
      if (exportJson.success && exportJson.sheet_url) {
        window.open(exportJson.sheet_url, '_blank');
      }
    } catch (e) {
      console.error('Export single GEO error:', e);
    } finally {
      setIsExporting(false);
    }
  };

  /* ---------- экспорт: Full Project → Google Sheets (мульти-лист) ---------- */
  const handleExportAllGeosToSheetsIfNeeded = async () => {
    if (!isFullProject || !window.__ALL_GEO_DATA__) {
      return handleExportSingleGeoToSheets();
    }
    setIsExporting(true);

    const allGeoSheets = Object.entries(window.__ALL_GEO_DATA__).map(([geoKey, data]) => {
      // локальные min-dep числа
      const localMinByKey = new Map();
      const localMinByKeyNorm = new Map();
      const putLocal = (title, name, val) => {
        if (!title || !name) return;
        const t = titleAlias(title);
        const k = `${t}|||${name}`;
        if (Number.isFinite(val)) {
          localMinByKey.set(k, val);
          localMinByKeyNorm.set(normKey(t, name), val);
        }
      };
      const md = data.methodsOnly || {};
      if (md.min_deposit_by_key && typeof md.min_deposit_by_key === 'object') {
        for (const [k, v] of Object.entries(md.min_deposit_by_key)) {
          const num = Number(v);
          if (!Number.isFinite(num)) continue;
          const [t, n] = String(k).split('|||');
          putLocal(t, n, num);
        }
        (md.min_deposit_map || []).forEach(r => putLocal(r?.title, r?.name, Number(r?.min_deposit)));
        (md.min_deposits || []).forEach(r => putLocal(r?.Title, r?.Name, Number(r?.MinDeposit)));
      } else if (Array.isArray(md.min_deposit_map)) {
        md.min_deposit_map.forEach(r => putLocal(r?.title, r?.name, Number(r?.min_deposit)));
      } else if (Array.isArray(md.min_deposits)) {
        md.min_deposits.forEach(r => putLocal(r?.Title, r?.Name, Number(r?.MinDeposit)));
      }

      const getMinForGroupLocal = (group) => {
        let minVal = Infinity; let found = false;
        for (const name of group.names) {
          const t = titleAlias(group.title);
          const exact = `${t}|||${name}`;
          const nk = normKey(t, name);
          const val = localMinByKey.get(exact) ?? localMinByKeyNorm.get(nk);
          if (Number.isFinite(val)) { minVal = Math.min(minVal, val); found = true; }
        }
        return found ? minVal : null;
      };

      // группировка для листа
      const groupedLocal = new Map();
      const norm = (t) => (t || '').trim().toLowerCase();

      [...(md.deposit_methods || []), ...(md.withdraw_methods || [])].forEach(([titleRaw, name]) => {
        const title = titleAlias(titleRaw);
        if (!groupedLocal.has(title)) {
          groupedLocal.set(title, {
            title, names: new Set(), conditions: new Set(),
            isRecommended: false, hasDeposit: false, hasWithdraw: false, isCrypto: false
          });
        }
        const g = groupedLocal.get(title);
        g.names.add(name);
        extractTag(name).forEach(tag => g.conditions.add(tag));
        if (md.deposit_methods?.some(([tt, nn]) => norm(titleAlias(tt)) === norm(title) && norm(nn) === norm(name))) g.hasDeposit = true;
        if (md.withdraw_methods?.some(([tt, nn]) => norm(titleAlias(tt)) === norm(title) && norm(nn) === norm(name))) g.hasWithdraw = true;
        if (isCryptoTitle(title) || isCryptoName(name)) { g.isCrypto = true; g.hasDeposit = true; g.hasWithdraw = true; }
        if (data.recommendedPairs?.some(([rt, rn]) => norm(titleAlias(rt)) === norm(title) && norm(rn) === norm(name))) g.isRecommended = true;
      });

      // 🔧 ВРЕМЕННОЕ РЕШЕНИЕ: добавляем Binance Pay в groupedLocal для экспорта
      if (false) {
        if (!groupedLocal.has('Binance Pay')) {
          groupedLocal.set('Binance Pay', {
            title: 'Binance Pay',
            names: new Set(['Binancepay_Binancepay_Crypto']),
            conditions: new Set(['ALL']),
            isRecommended: false,
            hasDeposit: true,
            hasWithdraw: true,
            isCrypto: true,
            isTemp: true
          });
        }
        // Добавляем минимальный депозит для Binance Pay
        putLocal('Binance Pay', 'Binancepay_Binancepay_Crypto', 50);
      }

      // 🔧 ВРЕМЕННОЕ РЕШЕНИЕ: добавляем Jeton в groupedLocal для экспорта
      if (false) {
        if (!groupedLocal.has('Jeton')) {
          groupedLocal.set('Jeton', {
            title: 'Jeton',
            names: new Set(['Jeton_Jeton_Wallet']),
            conditions: new Set(['ALL']),
            isRecommended: false,
            hasDeposit: true,
            hasWithdraw: true,
            isCrypto: false, // Jeton НЕ криптовалюта
            isTemp: true
          });
        }
        // Добавляем минимальный депозит для Jeton
        putLocal('Jeton', 'Jeton_Jeton_Wallet', 20);
      }

      // Добавляем хардкод методы если включен чекбокс (для All Projects Mode)
      if (addHardcodedMethods && env === 'prod' && groupedLocal.size > 0) {
        console.log(`Добавляем хардкод методы в непустое GEO: ${geoKey}`);
        
        const geoCurrency = getCurrencyFromGeoName(geoKey);
        const hardcodedMethods = getHardcodedMethodsForGeo(geoKey, geoCurrency);
        
        hardcodedMethods.forEach(method => {
          // Проверяем что метод еще не существует в этом GEO
          if (!groupedLocal.has(method.title)) {
            groupedLocal.set(method.title, {
              title: method.title,
              names: method.names,
              conditions: method.conditions,
              isRecommended: method.isRecommended,
              hasDeposit: method.hasDeposit,
              hasWithdraw: method.hasWithdraw,
              isCrypto: method.isCrypto,
              isHardcoded: true,
              sortOrder: method.title === 'ApplePay Visa' ? 11 : undefined // 11-е место для ApplePay
            });
            
            // Добавляем минимальный депозит для хардкод метода
            putLocal(method.title, Array.from(method.names)[0], method.minDeposit);
          }
        });
      }

      // Собираем все группы и размещаем ApplePay на 11-м месте
      const allGroups = Array.from(groupedLocal.values());
      
      // Специальная сортировка для размещения ApplePay на 11-м месте
      const methodsWithoutApplePay = allGroups.filter(group => group.title !== 'ApplePay Visa');
      const applePayMethods = allGroups.filter(group => group.title === 'ApplePay Visa');
      
      // Сначала сортируем остальные методы по стандартной логике
      const sortedOtherGroups = methodsWithoutApplePay.sort((a, b) => {
        // Временные методы всегда в самый низ
        if (a.isTemp !== b.isTemp) return a.isTemp ? 1 : -1;
        
        // Определяем является ли метод криптовалютой
        const isCryptoA = a.title.toLowerCase().includes('crypto') || 
                         ['btc', 'eth', 'ltc', 'usdt', 'usdc', 'trx', 'doge', 'ada', 'sol', 'xrp', 'bch', 'ton'].some(crypto => 
                           a.title.toLowerCase().includes(crypto.toLowerCase()));
        const isCryptoB = b.title.toLowerCase().includes('crypto') || 
                         ['btc', 'eth', 'ltc', 'usdt', 'usdc', 'trx', 'doge', 'ada', 'sol', 'xrp', 'bch', 'ton'].some(crypto => 
                           b.title.toLowerCase().includes(crypto.toLowerCase()));
        
        // Определяем является ли метод только withdraw
        const isWithdrawOnlyA = !a.hasDeposit && a.hasWithdraw;
        const isWithdrawOnlyB = !b.hasDeposit && b.hasWithdraw;
        
        // Специальная логика для Binance Pay и Jeton - размещаем выше "Crypto"
        const isSpecialA = (a.title === 'Binance Pay' || a.title === 'Jeton');
        const isSpecialB = (b.title === 'Binance Pay' || b.title === 'Jeton');
        const isCryptoMethodA = (a.title === 'Crypto');
        const isCryptoMethodB = (b.title === 'Crypto');
        
        // Если один из методов - Binance Pay/Jeton, а другой - именно "Crypto"
        if (isSpecialA && isCryptoMethodB) return -1; // Binance Pay/Jeton выше Crypto
        if (isCryptoMethodA && isSpecialB) return 1;  // Crypto ниже Binance Pay/Jeton
        
        // Сортировка по категориям:
        // 1. Рекомендованные не-крипто методы (в оригинальном порядке)
        // 2. Обычные не-крипто методы (в оригинальном порядке)
        // 3. Binance Pay и Jeton (выше "Crypto")
        // 4. Криптовалюты: "Crypto" первая, остальные по алфавиту
        // 5. Withdraw-only методы (в оригинальном порядке)
        
        if (isWithdrawOnlyA !== isWithdrawOnlyB) return isWithdrawOnlyA ? 1 : -1;
        if (isCryptoA !== isCryptoB) return isCryptoA ? 1 : -1;
        
        // Для не-крипто методов: рекомендованные вперед, потом оригинальный порядок
        if (!isCryptoA && !isCryptoB) {
          if (a.isRecommended !== b.isRecommended) return a.isRecommended ? -1 : 1;
          const aIndex = (data.originalOrder || []).indexOf(a.title);
          const bIndex = (data.originalOrder || []).indexOf(b.title);
          return aIndex - bIndex;
        }
        
        // Внутри криптовалют: "Crypto" всегда первая, остальные по алфавиту
        if (isCryptoA && isCryptoB) {
          // "Crypto" всегда первая
          if (a.title === "Crypto" && b.title !== "Crypto") return -1;
          if (b.title === "Crypto" && a.title !== "Crypto") return 1;
          
          // Остальные криптовалюты по базовому названию
          const baseNameA = a.title.replace(/\s*-\s*.*$/, '').trim();
          const baseNameB = b.title.replace(/\s*-\s*.*$/, '').trim();
          return baseNameA.localeCompare(baseNameB);
        }
        
        return 0;
      });
      
      // Вставляем ApplePay на 11-е место (индекс 10)
      const targetIndex = 10; // 11-е место (индекс с 0)
      const finalGroups = [...sortedOtherGroups];
      
      applePayMethods.forEach(applePayMethod => {
        if (finalGroups.length >= targetIndex) {
          finalGroups.splice(targetIndex, 0, applePayMethod);
        } else {
          finalGroups.push(applePayMethod);
        }
      });
      
      const sortedGroups = finalGroups;

      const rows = sortedGroups
        .map(row => {
          const minVal = getMinForGroupLocal(row);
          const geoCurrency = data.currency || '-';        // 👈 листовая валюта от логина
          return {
            Paymethod: row.isRecommended ? `${row.title}*` : row.title,
            "Payment Name": Array.from(row.names).join('\n'),
            Currency: geoCurrency,                          // 👈 GEO-level for sheet
            Deposit: row.hasDeposit ? "YES" : "NO",
            Withdraw: row.hasWithdraw ? "YES" : "NO",
            Status: env === 'prod' ? 'PROD' : 'STAGE',
            Details: data.conditionsMap?.[row.title] || (row.conditions.size > 0 ? Array.from(row.conditions).sort().join('\n') : "ALL"),
            "Min Dep": Number.isFinite(minVal) ? `${minVal} ${geoCurrency || ''}`.trim() : '—' // 👈 number + GEO currency
          };
        });

      return { geo: geoKey, rows };
    });

    try {
      const res = await fetch('/export-table-to-sheets-multi', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sheets: allGeoSheets, project, env })
      });
      const json = await res.json();
      if (json.success && json.sheet_url) window.open(json.sheet_url, '_blank');
      else console.error('Export multi error:', json.detail || json.message);
    } catch (e) {
      console.error('Export multi error:', e);
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <Center>
      <Box bg="white" boxShadow="xl" borderRadius="2xl" p={6} w="full" maxW="6xl" fontFamily="Inter, sans-serif">
        <Heading size="lg" borderBottom="1px" pb={2} mb={4}>📊 Методы (GEO)</Heading>
        {isFullProject && geo && project && env && (
          <Text fontSize="md" color="gray.600" fontWeight="semibold">
            🌍 {project} — {geo} — {env}
          </Text>
        )}
        {isFullProject && (
          <Text fontSize="sm" color="purple.600" fontWeight="bold" mt={-2} mb={2}>
            📦 Full project mode: объединены все GEO
          </Text>
        )}

        <Stack spacing={5}>
          <FormControl maxW="xs">
            <FormLabel>Фильтр</FormLabel>
            <Select value={filter} onChange={e => setFilter(e.target.value)} textAlign="center">
              <option value="all">All</option>
              <option value="recommended">Recommended</option>
              <option value="0DEP">0DEP</option>
              <option value="1DEP">1DEP</option>
              <option value="2DEP">2DEP</option>
              <option value="3DEP">3DEP</option>
              <option value="4DEP">4DEP</option>
              <option value="AFF">AFF</option>
              <option value="MOB">MOB</option>
            </Select>
          </FormControl>

          <HStack spacing={4} wrap="wrap">
            <Button variant="outline" colorScheme="blue" onClick={handleExportFrontendGeo} isLoading={isExporting}>
              📥 Export (Frontend)
            </Button>
            <Button variant="solid" colorScheme="purple" onClick={handleExportAllGeosToSheetsIfNeeded} isLoading={isExporting}>
              📤 Export to Google Sheets
            </Button>
          </HStack>

          <Box overflowX="auto">
            <Table size="sm" variant="simple">
              <Thead bg="gray.100">
                <Tr>
                  <Th>Title</Th>
                  <Th textAlign="center">Recommended</Th>
                  <Th textAlign="center">Deposit</Th>
                  <Th textAlign="center">Withdraw</Th>
                  {!hidePaymentName && <Th>ID (name)</Th>}
                  <Th>Conditions</Th>
                  <Th textAlign="right">Min Dep</Th>
                  <Th textAlign="center">Env</Th>
                </Tr>
              </Thead>
              <Tbody>
                {(() => {
                  // Специальная сортировка с размещением ApplePay на 11-м месте
                  const groups = [...filteredGroups];
                  
                  // Отделяем ApplePay от остальных
                  const applePayGroups = groups.filter(group => group.title === 'ApplePay Visa' && group.isHardcoded);
                  const otherGroups = groups.filter(group => !(group.title === 'ApplePay Visa' && group.isHardcoded));
                  
                  // Сортируем остальные группы по стандартной логике
                  const sortedOthers = otherGroups.sort((a, b) => {
                    // Временные методы всегда в самый низ
                    if (a.isTemp !== b.isTemp) return a.isTemp ? 1 : -1;
                    
                    // Специальная логика для Binance Pay и Jeton - размещаем выше "Crypto"
                    const isSpecialA = (a.title === 'Binance Pay' || a.title === 'Jeton');
                    const isSpecialB = (b.title === 'Binance Pay' || b.title === 'Jeton');
                    const isCryptoA = (a.title === 'Crypto');
                    const isCryptoB = (b.title === 'Crypto');
                    
                    // Если один из методов - Binance Pay/Jeton, а другой - Crypto
                    if (isSpecialA && isCryptoB) return -1; // Binance Pay/Jeton выше Crypto
                    if (isCryptoA && isSpecialB) return 1;  // Crypto ниже Binance Pay/Jeton
                    
                    // Рекомендованные методы идут вверх
                    if (a.isRecommended !== b.isRecommended) return a.isRecommended ? -1 : 1;
                    // Остальные по исходному порядку
                    const aIndex = (originalOrder || []).indexOf(a.title);
                    const bIndex = (originalOrder || []).indexOf(b.title);
                    return aIndex - bIndex;
                  });
                  
                  // Вставляем ApplePay на 11-е место (индекс 10)
                  const targetIndex = 10;
                  const finalGroups = [...sortedOthers];
                  
                  applePayGroups.forEach(applePayGroup => {
                    if (finalGroups.length >= targetIndex) {
                      finalGroups.splice(targetIndex, 0, applePayGroup);
                    } else {
                      finalGroups.push(applePayGroup);
                    }
                  });
                  
                  return finalGroups;
                })().map(group => {
                  const minVal = getMinDepositForGroup(group);
                  return (
                    <Tr key={group.title} bg={group.isRecommended ? 'green.50' : undefined} fontWeight={group.isRecommended ? 'semibold' : 'normal'}>
                      <Td whiteSpace="nowrap">{group.title}</Td>
                      <Td textAlign="center">{group.isRecommended ? '⭐' : ''}</Td>
                      <Td textAlign="center">{group.hasDeposit ? 'YES' : 'NO'}</Td>
                      <Td textAlign="center">{group.hasWithdraw ? 'YES' : 'NO'}</Td>
                      {!hidePaymentName && (
                        <Td whiteSpace="pre-wrap" fontSize="xs" fontFamily="mono">
                          {groupedIds?.[group.title] || Array.from(group.names).join('\n')}
                        </Td>
                      )}
                      <Td whiteSpace="pre-wrap" fontSize="xs" fontFamily="mono">
                        {conditionsMap?.[group.title] || (group.conditions.size > 0 ? Array.from(group.conditions).sort().join('\n') : 'ALL')}
                      </Td>
                      <Td textAlign="right">
                        {Number.isFinite(minVal) ? `${minVal} ${currency || ''}`.trim() : '—'}
                      </Td>
                      <Td textAlign="center">{(env || '').toUpperCase()}</Td>
                    </Tr>
                  );
                })}
              </Tbody>
            </Table>
          </Box>
        </Stack>
      </Box>
    </Center>
  );
}
