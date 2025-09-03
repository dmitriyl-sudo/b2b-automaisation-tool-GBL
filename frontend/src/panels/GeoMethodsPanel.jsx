import { useState, useEffect } from 'react';
import {
  Box, Heading, Text, FormControl, FormLabel, Select, Button,
  Table, Thead, Tbody, Tr, Th, Td, Stack, Center, HStack
} from '@chakra-ui/react';
import * as XLSX from "xlsx";

/* ---------------- helpers ---------------- */
const normalizeText = (s) => (s || '').trim().toLowerCase();
const normKey = (t, n) =>
  `${(t||'').toLowerCase().replace(/\s+/g,'').replace(/[^a-z0-9/+-]/g,'')}` +
  '|||' +
  `${(n||'').toLowerCase().replace(/\s+/g,'').replace(/[^a-z0-9/+-]/g,'')}`;

// алиасы тайтлов
const titleAlias = (t) => {
  const s = (t || '').trim();
  if (/^apple\s*pay$/i.test(s)) return 'Applepay';
  if (/^skrl$/i.test(s))       return 'Skrill';
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

export default function GeoMethodsPanel({
  methodsOnly,
  groupedIds,
  conditionsMap,
  recommendedPairs,
  originalOrder,
  hidePaymentName,
  isFullProject,
  geo,
  currency,          // 👈 GEO currency after login
  project,
  env
}) {
  const [filter, setFilter] = useState('all');
  const [isExporting, setIsExporting] = useState(false);

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

  const filteredGroups = (originalOrder || [])
    .map(t => groupedMap.get(titleAlias(t)))
    .filter(Boolean)
    .filter(group => {
      if (filter === 'all') return true;
      if (filter === 'recommended') return group.isRecommended;
      return Array.from(group.conditions).some(tag => tag.includes(filter));
    });

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

    setMinByKey(m);
    setMinByKeyNorm(mNorm);
  }, [methodsOnly]);

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

    const sorted = [...filteredGroups].sort((a, b) => {
      if (a.isRecommended !== b.isRecommended) return a.isRecommended ? -1 : 1;
      return (originalOrder || []).indexOf(a.title) - (originalOrder || []).indexOf(b.title);
    });

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
    if (!filteredGroups || filteredGroups.length === 0) return;
    setIsExporting(true);

    const sorted = [...filteredGroups].sort((a, b) => {
      if (a.isRecommended !== b.isRecommended) return a.isRecommended ? -1 : 1;
      return (originalOrder || []).indexOf(a.title) - (originalOrder || []).indexOf(b.title);
    });

    const data = sorted.map(row => {
      const minVal = getMinDepositForGroup(row);
      return {
        Paymethod: row.title,
        "Payment Name": Array.from(row.names).join('\n'),
        Currency: currency || '-',                                // 👈 GEO-level currency
        Deposit: row.hasDeposit ? "YES" : "NO",
        Withdraw: row.hasWithdraw ? "YES" : "NO",
        Status: env === "prod" ? "PROD" : "STAGE",
        Details: conditionsMap?.[row.title] || (row.conditions.size > 0 ? Array.from(row.conditions).sort().join('\n') : "ALL"),
        "Min Dep": Number.isFinite(minVal) ? `${minVal} ${currency || ''}`.trim() : '—' // 👈
      };
    });

    try {
      const res = await fetch('/export-table-to-sheets', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ data, originalOrder: originalOrder || [] })
      });
      const json = await res.json();
      if (json.success && json.sheet_url) window.open(json.sheet_url, '_blank');
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

      const rows = (data.originalOrder || [])
        .map(t => groupedLocal.get(titleAlias(t)))
        .filter(Boolean)
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
                {filteredGroups.map(group => {
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
