import { useState, useEffect } from 'react';
import {
  Box, Button, Table, Thead, Tbody, Tr, Th, Td, Text, HStack, Stack,
  FormControl, FormLabel, Select, Center, Heading
} from '@chakra-ui/react';
import * as XLSX from "xlsx";

/* ---------------- helpers ---------------- */

// Единая функция сортировки для UI и экспорта
const sortMethodsUnified = (groups, originalOrder = []) => {
  return groups.sort((a, b) => {
    // 1. Временные методы всегда в самый низ
    if (a.isTemp !== b.isTemp) return a.isTemp ? 1 : -1;
    
    // 2. Withdraw-only методы (deposit=NO, withdraw=YES) в самый низ
    const isWithdrawOnlyA = !a.hasDeposit && a.hasWithdraw;
    const isWithdrawOnlyB = !b.hasDeposit && b.hasWithdraw;
    if (isWithdrawOnlyA !== isWithdrawOnlyB) return isWithdrawOnlyA ? 1 : -1;
    
    // 3. Определяем криптовалюты
    const isCryptoA = a.title.toLowerCase().includes('crypto') || 
                     ['btc', 'eth', 'ltc', 'usdt', 'usdc', 'trx', 'doge', 'ada', 'sol', 'xrp', 'bch', 'ton'].some(crypto => 
                       a.title.toLowerCase().includes(crypto.toLowerCase()));
    const isCryptoB = b.title.toLowerCase().includes('crypto') || 
                     ['btc', 'eth', 'ltc', 'usdt', 'usdc', 'trx', 'doge', 'ada', 'sol', 'xrp', 'bch', 'ton'].some(crypto => 
                       b.title.toLowerCase().includes(crypto.toLowerCase()));
    
    // 4. Binance Pay и Jeton идут перед крипто блоком
    const isBinanceA = a.title === 'Binance Pay';
    const isBinanceB = b.title === 'Binance Pay';
    const isJetonA = a.title === 'Jeton';
    const isJetonB = b.title === 'Jeton';
    
    // Binance и Jeton vs остальные
    const isSpecialA = isBinanceA || isJetonA;
    const isSpecialB = isBinanceB || isJetonB;
    
    // Если один special, а другой крипто - special идет первым
    if (isSpecialA && isCryptoB && !isSpecialB) return -1;
    if (isSpecialB && isCryptoA && !isSpecialA) return 1;
    
    // Внутри special группы: Binance перед Jeton
    if (isSpecialA && isSpecialB) {
      if (isBinanceA && isJetonB) return -1;
      if (isJetonA && isBinanceB) return 1;
      return 0;
    }
    
    // 5. Крипто vs обычные методы
    if (isCryptoA !== isCryptoB) return isCryptoA ? 1 : -1;
    
    // 6. Внутри криптовалют: Crypto первый, остальные по алфавиту
    if (isCryptoA && isCryptoB) {
      if (a.title === "Crypto" && b.title !== "Crypto") return -1;
      if (b.title === "Crypto" && a.title !== "Crypto") return 1;
      
      const baseNameA = a.title.replace(/\s*-\s*.*$/, '').trim();
      const baseNameB = b.title.replace(/\s*-\s*.*$/, '').trim();
      return baseNameA.localeCompare(baseNameB);
    }
    
    // 7. Для обычных методов: рекомендованные вперед, потом originalOrder
    if (!isCryptoA && !isCryptoB && !isSpecialA && !isSpecialB) {
      if (a.isRecommended !== b.isRecommended) return a.isRecommended ? -1 : 1;
      const aIndex = originalOrder.indexOf(a.title);
      const bIndex = originalOrder.indexOf(b.title);
      if (aIndex !== -1 && bIndex !== -1) return aIndex - bIndex;
    }
    
    return 0;
  });
};

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
  
  // ApplePay Visa (Gumballpay) только для GEO с евро валютой
  // Включает: FI, AT, DE, PL_EUR, DK_EUR и другие EUR GEO
  // Исключает: PL_PLN, DK_DKK и другие локальные валюты
  const isEuroGeo = currency === 'EUR' || 
                   (geoUpper.includes('_EUR')) ||
                   (['FI', 'AT', 'DE', 'IT', 'SE', 'GR', 'IE', 'ES', 'PT'].some(geo => geoUpper.startsWith(geo)) && !geoUpper.includes('_'));
  
  if (isEuroGeo) {
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
  }
  
  return methods;
};

// Функция для создания GooglePay из ApplePay
const createGooglePayFromApplePay = (applePayGroup) => {
  // Исключаем методы с colibrix
  const hasColibrix = Array.from(applePayGroup.names).some(name => 
    name.toLowerCase().includes('colibrix')
  );
  
  if (hasColibrix) {
    return null; // Не создаем GooglePay для colibrix методов
  }
  
  // Создаем новые names для GooglePay, заменяя applepay на googlepay (в названиях методов)
  const googlePayNames = new Set();
  applePayGroup.names.forEach(name => {
    const googlePayName = name.replace(/applepay/gi, 'googlepay').replace(/Applepay/gi, 'Googlepay');
    googlePayNames.add(googlePayName);
  });
  
  // Создаем GooglePay группу на основе ApplePay (title с заглавной буквы)
  return {
    title: applePayGroup.title.replace(/applepay/gi, 'GooglePay').replace(/Applepay/gi, 'GooglePay'),
    names: googlePayNames,
    conditions: new Set(applePayGroup.conditions),
    isRecommended: applePayGroup.isRecommended,
    hasDeposit: applePayGroup.hasDeposit,
    hasWithdraw: applePayGroup.hasWithdraw,
    isCrypto: applePayGroup.isCrypto,
    isHardcoded: applePayGroup.isHardcoded || false,
    currency: applePayGroup.currency,
    minDeposit: applePayGroup.minDeposit,
    isAutoGenerated: true // Помечаем как автоматически созданный
  };
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

  let baseFilteredGroups = (originalOrder || [])
    .map(t => groupedMap.get(titleAlias(t)))
    .filter(Boolean)
    .filter(group => {
      if (filter === 'all') return true;
      if (filter === 'recommended') return group.isRecommended;
      return Array.from(group.conditions).some(tag => tag.includes(filter));
    });

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
    
    // Вставляем хардкод методы в правильные позиции согласно originalOrder
    const allHardcodedMethods = [...nonApplePayMethods, ...applePayMethods];
    
    allHardcodedMethods.forEach(method => {
      // Находим правильную позицию для метода согласно originalOrder
      const methodIndex = (originalOrder || []).indexOf(method.title);
      
      if (methodIndex !== -1) {
        // Находим позицию в baseFilteredGroups где нужно вставить метод
        let insertIndex = 0;
        for (let i = 0; i < baseFilteredGroups.length; i++) {
          const currentMethodIndex = (originalOrder || []).indexOf(baseFilteredGroups[i].title);
          if (currentMethodIndex !== -1 && currentMethodIndex > methodIndex) {
            insertIndex = i;
            break;
          }
          insertIndex = i + 1;
        }
        
        // Вставляем метод в правильную позицию
        baseFilteredGroups.splice(insertIndex, 0, method);
        console.log(`Вставлен хардкод метод ${method.title} на позицию ${insertIndex + 1}`);
      } else {
        // Если метода нет в originalOrder, добавляем в конец
        baseFilteredGroups.push(method);
        console.log(`Добавлен хардкод метод ${method.title} в конец (не найден в originalOrder)`);
      }
    });
  }

  // Автоматическое добавление GooglePay рядом с каждым ApplePay (если включен чекбокс)
  if (addHardcodedMethods) {
    const newGroups = [];
    
    baseFilteredGroups.forEach(group => {
      // Добавляем оригинальную группу
      newGroups.push(group);
      
      // Если это ApplePay, создаем и добавляем GooglePay рядом
      if (group.title && group.title.toLowerCase().includes('applepay')) {
        const googlePayGroup = createGooglePayFromApplePay(group);
        if (googlePayGroup) {
          console.log(`Автоматически создан GooglePay для ${group.title}:`, googlePayGroup.title);
          newGroups.push(googlePayGroup);
        } else {
          console.log(`GooglePay не создан для ${group.title} (содержит colibrix)`);
        }
      }
    });
    
    baseFilteredGroups = newGroups;
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
      
      // Сортировка по категориям:
      // 1. Рекомендованные не-крипто методы (в оригинальном порядке)
      // 2. Обычные не-крипто методы (в оригинальном порядке)
      // 3. Криптовалюты: "Crypto" первая, остальные по алфавиту
      // 4. Withdraw-only методы (в оригинальном порядке)
      
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
        Details: conditionsMap?.[row.title] || (row.conditions.size > 0 ? Array.from(row.conditions).join('\n') : "ALL"),
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
      // 🔧 ИСПОЛЬЗУЕМ ДАННЫЕ ИЗ UI (включая GooglePay методы) с единой сортировкой
      // Формируем данные из тех же отсортированных групп что отображаются в таблице
      const sortedGroups = sortMethodsUnified([...filteredGroups], originalOrder);
      const data = sortedGroups.map(group => {
        const minVal = getMinDepositForGroup(group);
        return {
          Paymethod: group.isRecommended ? `${group.title}*` : group.title,
          "Payment Name": Array.from(group.names).join('\n'),
          Currency: currency || 'EUR',
          Deposit: group.hasDeposit ? "YES" : "NO",
          Withdraw: group.hasWithdraw ? "YES" : "NO",
          Status: env === 'prod' ? 'PROD' : 'STAGE',
          Details: group.conditions.size > 0 ? Array.from(group.conditions).join('\n') : "ALL",
          "Min Dep": Number.isFinite(minVal) ? `${minVal} ${currency || 'EUR'}`.trim() : '—'
        };
      });
      
      console.log(`Экспортируем ${data.length} методов (включая GooglePay) для ${geo}:`, data);
      
      // Экспортируем данные в Google Sheets
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
      
      // Автоматическое добавление GooglePay рядом с каждым ApplePay (для All Projects Mode)
      // ВАЖНО: Делаем это ДО сортировки чтобы GooglePay остался рядом с ApplePay
      let allGroupsWithGooglePay = allGroups;
      if (addHardcodedMethods) {
        const newGroups = [];
        
        allGroups.forEach(group => {
          // Добавляем оригинальную группу
          newGroups.push(group);
          
          // Если это ApplePay, создаем и добавляем GooglePay рядом
          if (group.title && group.title.toLowerCase().includes('applepay')) {
            const googlePayGroup = createGooglePayFromApplePay(group);
            if (googlePayGroup) {
              console.log(`Автоматически создан GooglePay для ${group.title} в GEO ${geoKey}:`, googlePayGroup.title);
              newGroups.push(googlePayGroup);
            } else {
              console.log(`GooglePay не создан для ${group.title} в GEO ${geoKey} (содержит colibrix)`);
            }
          }
        });
        
        allGroupsWithGooglePay = newGroups;
      }

      // Единая сортировка для All Projects Mode (такая же как в UI)
      const sortedGroups = sortMethodsUnified([...allGroupsWithGooglePay], data.originalOrder);

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
            Details: data.conditionsMap?.[row.title] || (row.conditions.size > 0 ? Array.from(row.conditions).join('\n') : "ALL"),
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
                  // Единая сортировка для UI и экспорта
                  return sortMethodsUnified([...filteredGroups], originalOrder);
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
                        {conditionsMap?.[group.title] || (group.conditions.size > 0 ? Array.from(group.conditions).join('\n') : 'ALL')}
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
