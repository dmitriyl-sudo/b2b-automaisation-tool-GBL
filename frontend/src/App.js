// App.js — с поддержкой Full Project Mode, Multi-GEO и экспортом
import { useState, useEffect } from 'react';
import axios from 'axios';
import {
  Box, Button, Heading, HStack, VStack, Select, Text, Spacer, Flex, Checkbox,
  ChakraProvider, extendTheme // Added ChakraProvider and extendTheme for full app
} from '@chakra-ui/react';
import { LogOut } from 'lucide-react';
// Assuming these components are in the correct paths relative to App.js
import LoginPage from './LoginPage';
import ExportPanel from './panels/ExportPanel';
import AuthCheckPanel from './panels/AuthCheckPanel';
import SingleLoginPanel from './panels/SingleLoginPanel';
import GeoMethodsPanel from './panels/GeoMethodsPanel';
import LoginTestUI from './LoginTestUI';
import MethodTestPanel from './panels/MethodTestPanel';

// Extend Chakra UI theme for Inter font
const theme = extendTheme({
  fonts: {
    heading: 'Inter, sans-serif',
    body: 'Inter, sans-serif',
  },
});

export default function App() {
  const [user, setUser] = useState(null);
  const [activeTab, setActiveTab] = useState("Auth");
  const [project, setProject] = useState('');
  const [geo, setGeo] = useState('');
  const [env, setEnv] = useState('stage'); // State for environment
  const [projects, setProjects] = useState([]);
  const [geoGroups, setGeoGroups] = useState({});
  const [isFullProject, setIsFullProject] = useState(false);
  const [perGeoData, setPerGeoData] = useState({});
  const [loadingMessage, setLoadingMessage] = useState("");
  const [exportStatus, setExportStatus] = useState("");

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      axios.get('/me', { headers: { Authorization: `Bearer ${token}` } })
        .then(res => setUser({ ...res.data, token }))
        .catch(() => setUser(null));
    }
    axios.get('/list-projects').then(res => setProjects(res.data));
    axios.get('/geo-groups').then(res => setGeoGroups(res.data));
  }, []);

  if (!user) return <LoginPage onLogin={setUser} />;

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

  const getMinDEP = (condStr) => {
    const matches = condStr.match(/(\d)DEP/g);
    if (!matches) return 99;
    return Math.min(...matches.map(d => parseInt(d)));
  };

  const getCryptoSortIndex = (title) => {
    if (title === 'Crypto') return -1; // ⬅️ явно ставим первым
    const order = [
      'USDTT', 'LTC', 'ETH', 'TRX', 'BTC', 'SOL', 'XRP',
      'USDTE', 'DOGE', 'ADA', 'USDC', 'BCH', 'TON'
    ];
    for (let i = 0; i < order.length; i++) {
      if (title.toUpperCase().startsWith(order[i])) return i;
    }
    return 999;
  };

  const handleLoadGeoMethods = async () => {
    const geoList = isFullProject ? Object.keys(geoGroups) : [geo];
    const newData = {};

    for (let g = 0; g < geoList.length; g++) {
      const currentGeo = geoList[g];
      const allLogins = [...(geoGroups[currentGeo] || [])].sort((a, b) => {
        const getDep = (str) => parseInt((str.match(/(\d)DEP/i) || [])[1] || 0);
        return getDep(b) - getDep(a);
      });

      const titleMap = {};
      const conditionMap = {};
      const methodTypeMap = {};
      const recommendedSet = new Set();
      const seen = new Set();
      const order = []; // This 'order' variable is not used after its declaration.
      const currencySet = new Set();

      setLoadingMessage(`🔄 GEO: ${currentGeo} (${allLogins.length} логинов)...`);

      for (let i = 0; i < allLogins.length; i++) {
        const login = allLogins[i];
        setLoadingMessage(`🔄 GEO: ${currentGeo} (${i + 1}/${allLogins.length}) — ${login}`);
        try {
          const authRes = await axios.post('/run-login-check', { project, geo: currentGeo, env, login });
          if (authRes.data.currency) currencySet.add(authRes.data.currency);

          const res = await axios.post('/get-methods-only', { project, geo: currentGeo, env, login });

          res.data.recommended_methods?.forEach(([title, name]) => {
            recommendedSet.add(`${title}|||${name}`);
          });

          [...(res.data.deposit_methods || []), ...(res.data.withdraw_methods || [])].forEach(([title, name]) => {
            const key = `${title}|||${name}`;
            const isCrypto = /Coinspaid|Crypto|Tether|Bitcoin|Ethereum|Litecoin|Ripple|Tron|USDC|USDT|DOGE|Cardano|Solana|Toncoin|Binance|Jeton/i.test(name);

            methodTypeMap[key] = methodTypeMap[key] || {};
            if (res.data.deposit_methods.some(([t, n]) => t === title && n === name)) methodTypeMap[key].deposit = true;
            if (res.data.withdraw_methods.some(([t, n]) => t === title && n === name)) methodTypeMap[key].withdraw = true;
            methodTypeMap[key].group = isCrypto ? 'crypto' : 'regular';

            titleMap[title] = titleMap[title] || new Set();
            titleMap[title].add(name);

            const tag = extractTag(name);
            if (tag) {
              conditionMap[title] = conditionMap[title] || new Set();
              conditionMap[title].add(tag);
            }

            if (!seen.has(title)) {
              // 'order' is declared but not used elsewhere. You might want to remove this if it's not needed.
              order.push(title);
              seen.add(title);
            }
          });
        } catch (err) {
          console.warn(`❌ Ошибка логина ${login}:`, err);
        }
      }

      const groupedIds = Object.fromEntries(Object.entries(titleMap).map(([t, s]) => [t, Array.from(s).join('\n')]));
      const conditionsMap = Object.fromEntries(Object.entries(conditionMap).map(([t, s]) => [t, s.size ? Array.from(s).sort().join('\n') : 'ALL']));

      const sortedOrder = Array.from(seen).sort((a, b) => {
        const aNames = Array.from(titleMap[a] || []);
        const bNames = Array.from(titleMap[b] || []);
        const aKey = `${a}|||${aNames[0] || ''}`;
        const bKey = `${b}|||${bNames[0] || ''}`;
        const aType = methodTypeMap[aKey] || {};
        const bType = methodTypeMap[bKey] || {};

        // 1. Группировка: regular < crypto
        const aGroup = aType.group || 'regular';
        const bGroup = bType.group || 'regular';
        if (aGroup !== bGroup) return aGroup === 'crypto' ? 1 : -1;
        // 2. Внутри crypto — явно ставим "Crypto" заголовок вверх
        if (aGroup === 'crypto' && bGroup === 'crypto') {
          return getCryptoSortIndex(a) - getCryptoSortIndex(b);
        }

        // 3. Рекомендованные первыми
        const aRec = recommendedSet.has(aKey);
        const bRec = recommendedSet.has(bKey);
        if (aRec !== bRec) return aRec ? -1 : 1;

        // 4. DEP-сортировка
        const aDep = getMinDEP(conditionsMap[a] || '');
        const bDep = getMinDEP(conditionsMap[b] || '');
        if (aDep !== bDep) return aDep - bDep;

        // 5. Методы без Withdraw — вниз
        const aNoWithdraw = !aType.withdraw;
        const bNoWithdraw = !bType.withdraw;
        if (aNoWithdraw !== bNoWithdraw) return aNoWithdraw ? 1 : -1;

        // 6. Финальный fallback — по алфавиту
        return a.localeCompare(b);
      });


      newData[currentGeo] = {
        currency: currencySet.size === 1 ? Array.from(currencySet)[0] : '—',
        groupedIds,
        conditionsMap,
        recommendedPairs: Array.from(recommendedSet).map(s => s.split('|||')),
        methodTypes: methodTypeMap,
        originalOrder: sortedOrder,
        methodsOnly: {
          deposit_methods: Object.entries(methodTypeMap).filter(([_, t]) => t.deposit).map(([k]) => k.split('|||')),
          withdraw_methods: Object.entries(methodTypeMap).filter(([_, t]) => t.withdraw).map(([k]) => k.split('|||')),
          recommended_methods: Array.from(recommendedSet).map(s => s.split('|||')),
        }
      };
    }
    window.__ALL_GEO_DATA__ = newData;
    setPerGeoData(newData);
    setLoadingMessage("✅ Готово");
  };

  const handleExportFullProject = async () => {
    if (!project || !env) {
      setExportStatus("❗ Укажи проект и окружение");
      return;
    }
    setExportStatus("📤 Экспорт проекта...");
    try {
      const res = await axios.post('/export-full-project', { project, env }, {
        headers: { Authorization: `Bearer ${user.token}` }
      });
      if (res.data?.sheet_url) {
        setExportStatus("✅ Успешно, открываем...");
        window.open(res.data.sheet_url, '_blank');
      } else {
        setExportStatus("⚠️ Нет ссылки");
      }
    } catch (err) {
      setExportStatus(`❌ Ошибка: ${err.response?.data?.detail || err.message}`);
    }
  };

  const tabs = [
    { label: "Auth", key: "Auth" },
    { label: "Single Login", key: "Single" },
    { label: "GEO Methods", key: "Geo" },
    { label: "Test Methods", key: "TestMethods" },
    { label: "Export", key: "Export" },
    ...(user.role !== 'viewer' ? [{ label: "Dev Panel", key: "Dev" }] : [])
  ];

  return (
    <ChakraProvider theme={theme}> {/* Wrap the entire app with ChakraProvider */}
      <Box px={6} py={4} maxW="6xl" mx="auto">
        <Flex align="center" mb={6} gap={4} wrap="wrap">
          <Heading size="lg">💳 Payment Checker</Heading>
          <Spacer />
          <Button onClick={() => { localStorage.removeItem('token'); setUser(null); }}
            leftIcon={<LogOut size={18} />} colorScheme="red" variant="solid" size="sm">
            Выйти
          </Button>
        </Flex>
        <HStack spacing={3} mb={4} wrap="wrap">
          {tabs.map(tab => (
            <Button key={tab.key} onClick={() => setActiveTab(tab.key)}
              colorScheme={activeTab === tab.key ? 'blue' : 'gray'}
              variant={activeTab === tab.key ? 'solid' : 'outline'} size="sm">
              {tab.label}
            </Button>
          ))}
        </HStack>
        {loadingMessage && <Text fontSize="sm" color="gray.600" mb={2}>{loadingMessage}</Text>}
        {exportStatus && <Text fontSize="sm" color="gray.600" mb={2}>{exportStatus}</Text>}

        {activeTab === "Auth" && <AuthCheckPanel />}
        {activeTab === "Single" && <SingleLoginPanel />}
        {activeTab === "Geo" && (
          <VStack align="stretch" spacing={3} mb={4}>
            <Select value={project} onChange={(e) => setProject(e.target.value)} placeholder="-- select project --">
              {projects.map(p => <option key={p.name} value={p.name}>{p.name}</option>)}
            </Select>
            <Select value={geo} onChange={(e) => setGeo(e.target.value)} placeholder="-- select geo --" isDisabled={isFullProject}>
              {Object.keys(geoGroups).map(g => <option key={g} value={g}>{g}</option>)}
            </Select>
            <Select value={env} onChange={(e) => setEnv(e.target.value)} placeholder="-- environment --">
              <option value="stage">stage</option>
              <option value="prod">prod</option>
            </Select>
            <Checkbox isChecked={isFullProject} onChange={() => setIsFullProject(!isFullProject)}>
              📦 Full project mode (все GEO)
            </Checkbox>
            <HStack spacing={4}>
              <Button onClick={handleLoadGeoMethods} colorScheme="blue">Load GEO Methods</Button>
              <Button onClick={handleExportFullProject} colorScheme="yellow">Export Full Project</Button>
            </HStack>
          </VStack>
        )}
        {activeTab === "Geo" && Object.keys(perGeoData).length > 0 && (
          <>
            {Object.entries(perGeoData).map(([geoKey, data]) => (
              <GeoMethodsPanel
                key={geoKey}
                geo={geoKey}
                currency={data.currency}
                methodsOnly={data.methodsOnly}
                groupedIds={data.groupedIds}
                conditionsMap={data.conditionsMap}
                recommendedPairs={data.recommendedPairs}
                methodTypes={data.methodTypes}
                originalOrder={data.originalOrder}
                hidePaymentName={user.role === 'viewer'}
                isFullProject={isFullProject}
                env={env} 
                project={project}
              />
            ))}
          </>
        )}
        {activeTab === "TestMethods" && <MethodTestPanel />}
        {activeTab === "Export" && <ExportPanel />}
        {activeTab === "Dev" && <LoginTestUI />}
      </Box>
    </ChakraProvider>
  );
}
