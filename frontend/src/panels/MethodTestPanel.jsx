import React, { useState, useMemo, useRef } from "react";
import axios from "axios";
import {
  Box, Button, Heading, VStack, HStack, Select, Input, Text, Table, Thead, Tbody, Tr, Th, Td, Spinner, Link, Tooltip, Radio, RadioGroup, Badge, Progress, Code, useDisclosure, Modal, ModalOverlay, ModalContent, ModalHeader, ModalBody, ModalCloseButton, IconButton, Checkbox, Tabs, TabList, TabPanels, Tab, TabPanel
} from "@chakra-ui/react";
import { FaChevronDown, FaChevronUp, FaInfoCircle, FaCopy } from "react-icons/fa";
import { useGlobalSelection } from '../contexts/GlobalSelectionContext';

export default function MethodTestPanel() {
  const [localLogin, setLocalLogin] = useState("");
  const [mode, setMode] = useState("login");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [statusFilter, setStatusFilter] = useState("all"); // all | ok | err
  const [query, setQuery] = useState("");                  // поиск по method/message
  const [onlyFailedChecks, setOnlyFailedChecks] = useState(false);
  const [rerunLoading, setRerunLoading] = useState(false);
  // прогресс/логи
  const [phase, setPhase] = useState("");               // текущий этап
  const [progressNow, setProgressNow] = useState(0);    // выполнено
  const [progressTotal, setProgressTotal] = useState(0);// всего задач
  const [logLines, setLogLines] = useState([]);         // массив строк лога
  const logBoxRef = useRef(null);
  // сортировка
  const [sortBy, setSortBy] = useState(null); // 'geo'|'login'|'method'|'status'|'code'|'duration'
  const [sortDir, setSortDir] = useState('asc'); // 'asc'|'desc'
  // модал деталей
  const { isOpen, onOpen, onClose } = useDisclosure();
  const [selectedRow, setSelectedRow] = useState(null);

  const pushLog = (msg) => {
    setLogLines((prev) => {
      const next = [...prev, msg];
      // авто-скролл вниз
      setTimeout(() => {
        try { logBoxRef.current?.scrollTo({ top: logBoxRef.current.scrollHeight, behavior: "smooth" }); } catch {}
      }, 0);
      return next;
    });
  };

  const { project, geo, env, logins, setProject, setGeo, setEnv, projects, geoOptions } = useGlobalSelection();

  const runTest = async () => {
    setLoading(true);
    setResults([]);
    // прогресс
    setPhase("Подготовка запуска");
    setLogLines([]);
    setProgressNow(0);
    setProgressTotal(1);
    try {
      const payload = {
        project,
        geo,
        login: localLogin,
        mode,
        env
      };
      pushLog(`▶️ Запрос /test-methods-v2: project=${project || "-"}, mode=${mode}, geo=${geo || "-"}, login=${localLogin || "-"}`);
      const res = await axios.post("/test-methods-v2", payload);
      const enriched = res.data.results.map(r => ({
        ...r,
        url: r.url || r.link || r.payment_url || null,
        checks: r.checks || [],
        checks_summary: r.checks_summary || {passed:0, failed:0}
      }));
      setResults(enriched);
      setPhase("Готово");
      setProgressNow(1);
      pushLog(`✅ Получено результатов: ${enriched.length}`);
    } catch (err) {
      setPhase("Ошибка запуска");
      pushLog(`❌ Ошибка запуска: ${err?.response?.data?.detail || err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const filteredResults = useMemo(() => {
    const q = (query || "").toLowerCase().trim();
    return (results || []).filter(r => {
      const byStatus =
        statusFilter === "all" ||
        (statusFilter === "ok" && r.status === "OK") ||
        (statusFilter === "err" && r.status !== "OK");
      if (!byStatus) return false;
      if (onlyFailedChecks && !(r.checks_summary?.failed > 0)) return false;
      if (!q) return true;
      const hay = `${r.method || ""} ${r.message || ""}`.toLowerCase();
      return hay.includes(q);
    });
  }, [results, statusFilter, query, onlyFailedChecks]);

  const sortedResults = useMemo(() => {
    if (!sortBy) return filteredResults;
    const dir = sortDir === 'asc' ? 1 : -1;
    const getVal = (r) => {
      if (sortBy === 'duration') return Number(r.duration ?? 0);
      const v = r[sortBy];
      return v == null ? '' : String(v).toLowerCase();
    };
    return [...filteredResults].sort((a, b) => {
      const av = getVal(a), bv = getVal(b);
      if (av < bv) return -1 * dir;
      if (av > bv) return  1 * dir;
      return 0;
    });
  }, [filteredResults, sortBy, sortDir]);

  const toggleSort = (col) => {
    if (sortBy !== col) { setSortBy(col); setSortDir('asc'); return; }
    setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
  };


  const okCount = useMemo(() => results.filter(r => r.status === "OK").length, [results]);
  const errCount = useMemo(() => results.filter(r => r.status !== "OK").length, [results]);

  const exportCSV = () => {
    const rows = sortedResults;
    if (!rows.length) {
      alert("Нет данных для экспорта (попробуй снять фильтры).");
      return;
    }
    const headers = ["geo","login","method","status","code","message","duration","url"];
    const escape = (v) => {
      if (v === null || v === undefined) return "";
      const s = String(v).replace(/"/g, '""');
      // всегда оборачиваем в кавычки — безопасно для запятых/переносов
      return `"${s}"`;
    };
    const lines = [
      headers.join(","), // заголовок
      ...rows.map(r => headers.map(h => escape(r[h])).join(","))
    ];
    const blob = new Blob([lines.join("\n")], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `method_tests_${project || "project"}_${geo || "geo"}_${env}.csv`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  };

  const exportToSheets = async () => {
    try {
      const payload = {
        data: sortedResults,
        originalOrder: []
      };
      const res = await axios.post("/export-table-to-sheets", payload);
      if (res.data?.sheet_url) {
        window.open(res.data.sheet_url, "_blank");
      } else if (res.data?.detail || res.data?.message) {
        alert(`Экспорт не выполнен: ${res.data.detail || res.data.message}`);
      }
    } catch (e) {
      const msg = e?.response?.data?.detail || e?.message || "Unknown error";
      alert(`Ошибка экспорта в Google Sheets: ${msg}`);
    }
  };

  // Повторный прогон только для логинов с ошибками (mode: 'login')
  const rerunFailed = async () => {
    const failed = results.filter(r => r.status !== "OK");
    if (!failed.length) {
      alert("Нет ошибок для повторного запуска.");
      return;
    }
    setRerunLoading(true);
    // прогресс
    setPhase("Сбор пар логинов для повтора");
    setLogLines([]);
    try {
      // уникальные пары (geo, login) среди упавших
      const pairs = Array.from(new Set(failed.map(r => `${r.geo}|||${r.login}`)))
        .map(s => { const [geo, login] = s.split("|||"); return { geo, login }; });

      setProgressNow(0);
      setProgressTotal(pairs.length);
      pushLog(`🔎 Найдено пар для повтора: ${pairs.length}`);

      // карта для мерджа по ключу geo|login|method (заполним текущими результатами)
      const key = (r) => `${r.geo}|${r.login}|${r.method}`;
      const merged = new Map(results.map(r => [key(r), r]));

      const CONC = 3; // лимит параллельных запросов
      let i = 0;
      const worker = async () => {
        while (i < pairs.length) {
          const my = i++;
          const { geo, login } = pairs[my];
          setPhase(`Запуск ${my + 1}/${pairs.length}: ${geo} / ${login}`);
          pushLog(`▶️ Повтор /test-methods для ${geo} / ${login}`);
          const payload = { project, geo, login, mode: "login", env };
          const res = await axios.post("/test-methods", payload);
          const arr = (res.data?.results || []).map(r => ({
            ...r,
            url: r.url || r.link || r.payment_url || null
          }));
          arr.forEach(r => merged.set(key(r), r));
          const ok = arr.filter(x => x.status === "OK").length;
          const err = arr.length - ok;
          pushLog(`✅ Успешно: ${ok} • ❌ Ошибок: ${err} (для ${geo}/${login})`);
          setProgressNow((x) => x + 1);
        }
      };
      await Promise.all(new Array(Math.min(CONC, pairs.length)).fill(0).map(() => worker()));

      setResults(Array.from(merged.values()));
      setPhase("Повторное выполнение завершено");
      pushLog("🏁 Повторный прогон завершён, таблица обновлена");
    } catch (e) {
      setPhase("Ошибка повтора");
      pushLog(`❌ Ошибка повтора: ${e?.response?.data?.detail || e.message}`);
    } finally {
      setRerunLoading(false);
    }
  };

  return (
    <Box>
      <Heading size="md" mb={4}>Проверка платёжных методов</Heading>

      <VStack align="start" spacing={4} mb={6}>
        <HStack spacing={4} wrap="wrap">
          <Select placeholder="Выберите проект" value={project} onChange={e => setProject(e.target.value)}>
            {projects.map(p => (
              <option key={p.name} value={p.name}>{p.name}</option>
            ))}
          </Select>
          <Select placeholder="Выберите GEO" value={geo} onChange={e => setGeo(e.target.value)} isDisabled={mode === "project"}>
            {geoOptions.map(g => (
              <option key={g} value={g}>{g}</option>
            ))}
          </Select>
          <Select placeholder="Выберите логин" value={localLogin} onChange={e => setLocalLogin(e.target.value)} isDisabled={mode !== "login"}>
            {logins.map(l => (
              <option key={l} value={l}>{l}</option>
            ))}
          </Select>
          <Select value={env} onChange={(e) => setEnv(e.target.value)} placeholder="-- environment --">
            <option value="stage">stage</option>
            <option value="prod">prod</option>
          </Select>
        </HStack>

        <RadioGroup onChange={setMode} value={mode}>
          <HStack spacing={6}>
            <Radio value="login">По логину</Radio>
            <Radio value="geo">По GEO</Radio>
            <Radio value="project">По проекту</Radio>
          </HStack>
        </RadioGroup>

        {/* Панель управления результатами */}
        <HStack spacing={4} wrap="wrap" w="100%">
          <Button onClick={runTest} colorScheme="blue" isLoading={loading}>Запустить проверку</Button>
          {results.length > 0 && (
            <>
              <Button onClick={exportToSheets} colorScheme="green" variant="solid">Экспорт в Sheets</Button>
              <Button onClick={exportCSV} variant="outline">Export CSV</Button>
              <Button 
                onClick={async () => {
                  try {
                    const res = await axios.post("/snapshot/project", { 
                      project: project, 
                      env, 
                      save: true 
                    }, { 
                      responseType: "text" 
                    });
                    // Download YAML file locally
                    const blob = new Blob([res.data], { type: "text/yaml;charset=utf-8" });
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement("a");
                    a.href = url; 
                    a.download = `snapshot_${project}_${env}.yaml`;
                    document.body.appendChild(a); 
                    a.click(); 
                    a.remove(); 
                    URL.revokeObjectURL(url);
                  } catch(e) {
                    alert("Ошибка snapshot: " + (e?.response?.data?.detail || e.message));
                  }
                }}
                variant="outline"
                colorScheme="purple"
              >
                📸 Snapshot YAML
              </Button>
              <Button
                onClick={rerunFailed}
                colorScheme="orange"
                variant="solid"
                isDisabled={errCount === 0}
                isLoading={rerunLoading}
                title="Перезапустить только строки с ошибками (по логинам)"
              >
                Повторить ошибки
              </Button>
            </>
          )}
          <HStack spacing={2} ml="auto">
            <Badge colorScheme="green">OK: {okCount}</Badge>
            <Badge colorScheme="red">ERR: {errCount}</Badge>
          </HStack>
        </HStack>

        {/* Фильтры */}
        {results.length > 0 && (
          <HStack spacing={4} wrap="wrap" w="100%">
            <Select value={statusFilter} onChange={e => setStatusFilter(e.target.value)} maxW="200px">
              <option value="all">All</option>
              <option value="ok">Only OK</option>
              <option value="err">Only Errors</option>
            </Select>
            <Input
              placeholder="Поиск: метод или текст ошибки…"
              value={query}
              onChange={e => setQuery(e.target.value)}
              maxW="360px"
            />
            <Checkbox isChecked={onlyFailedChecks} onChange={(e)=>setOnlyFailedChecks(e.target.checked)}>
              Только с проваленными checks
            </Checkbox>
          </HStack>
        )}

        {/* Панель прогресса/логов */}
        {(loading || rerunLoading || phase || logLines.length > 0) && (
          <Box w="100%" bg="gray.50" border="1px solid" borderColor="gray.200" rounded="md" p={3}>
            <HStack justify="space-between" mb={2}>
              <Text fontSize="sm"><b>Этап:</b> {phase || "—"}</Text>
              {progressTotal > 0 && (
                <Text fontSize="sm" color="gray.600">
                  {progressNow}/{progressTotal}
                </Text>
              )}
            </HStack>
            {progressTotal > 0 && (
              <Progress value={progressTotal ? (progressNow / progressTotal) * 100 : 0} size="sm" mb={2} />
            )}
            <Box ref={logBoxRef} maxH="140px" overflowY="auto" bg="white" border="1px solid" borderColor="gray.200" rounded="md" p={2}>
              {logLines.length === 0 ? (
                <Text fontSize="xs" color="gray.500">Здесь будут появляться сообщения о ходе выполнения…</Text>
              ) : (
                logLines.map((line, idx) => (
                  <Text key={idx} fontSize="xs" fontFamily="mono">
                    <Code colorScheme={
                      line.startsWith("✅") ? "green" :
                      line.startsWith("❌") ? "red" :
                      line.startsWith("▶️") ? "blue" : undefined
                    }>{line}</Code>
                  </Text>
                ))
              )}
            </Box>
          </Box>
        )}
      </VStack>

      {sortedResults.length > 0 && (
        <Box overflowX="auto" maxH="500px" overflowY="auto">
          <Table variant="simple" size="sm">
            <Thead position="sticky" top={0} bg="white" zIndex={1}>
              <Tr>
                <Th cursor="pointer" onClick={() => toggleSort('geo')}>
                  <HStack spacing={1}>
                    <Text>GEO</Text>
                    {sortBy === 'geo' && (sortDir === 'asc' ? <FaChevronUp /> : <FaChevronDown />)}
                  </HStack>
                </Th>
                <Th cursor="pointer" onClick={() => toggleSort('login')}>
                  <HStack spacing={1}>
                    <Text>Login</Text>
                    {sortBy === 'login' && (sortDir === 'asc' ? <FaChevronUp /> : <FaChevronDown />)}
                  </HStack>
                </Th>
                <Th cursor="pointer" onClick={() => toggleSort('method')}>
                  <HStack spacing={1}>
                    <Text>Method</Text>
                    {sortBy === 'method' && (sortDir === 'asc' ? <FaChevronUp /> : <FaChevronDown />)}
                  </HStack>
                </Th>
                <Th cursor="pointer" onClick={() => toggleSort('status')}>
                  <HStack spacing={1}>
                    <Text>Status</Text>
                    {sortBy === 'status' && (sortDir === 'asc' ? <FaChevronUp /> : <FaChevronDown />)}
                  </HStack>
                </Th>
                <Th cursor="pointer" onClick={() => toggleSort('code')}>
                  <HStack spacing={1}>
                    <Text>Code</Text>
                    {sortBy === 'code' && (sortDir === 'asc' ? <FaChevronUp /> : <FaChevronDown />)}
                  </HStack>
                </Th>
                <Th>Message</Th>
                <Th cursor="pointer" onClick={() => toggleSort('duration')}>
                  <HStack spacing={1}>
                    <Text>Duration</Text>
                    {sortBy === 'duration' && (sortDir === 'asc' ? <FaChevronUp /> : <FaChevronDown />)}
                  </HStack>
                </Th>
                <Th>URL</Th>
                <Th>Checks</Th>
                <Th>Details</Th>
              </Tr>
            </Thead>
            <Tbody>
              {sortedResults.map((r, idx) => (
                <Tr key={idx}>
                  <Td>{r.geo || "-"}</Td>
                  <Td>{r.login || "-"}</Td>
                  <Td>{r.method || "-"}</Td>
                  <Td>{r.status === "OK" ? "✅" : "❌"}</Td>
                  <Td>{r.code || "-"}</Td>
                  <Td maxW="300px" isTruncated>
                    <Tooltip label={r.message} hasArrow>{r.message || "-"}</Tooltip>
                  </Td>
                  <Td>{r.duration ? `${r.duration}s` : "-"}</Td>
                  <Td>{r.url ? <Link href={r.url} isExternal color="blue.500">Открыть</Link> : "-"}</Td>
                  <Td>
                    <Badge colorScheme={r.checks_summary?.failed ? 'red' : 'green'}>
                      {r.checks_summary?.passed || 0}/{(r.checks_summary?.passed || 0) + (r.checks_summary?.failed || 0)}
                    </Badge>
                  </Td>
                  <Td>
                    <IconButton
                      size="xs"
                      icon={<FaInfoCircle />}
                      onClick={() => {
                        setSelectedRow(r);
                        onOpen();
                      }}
                      aria-label="View details"
                    />
                  </Td>
                </Tr>
              ))}
            </Tbody>
          </Table>
        </Box>
      )}

      {loading && <Spinner mt={4} />}

      {/* Details Modal */}
      <Modal isOpen={isOpen} onClose={onClose} size="xl">
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>Test Result Details</ModalHeader>
          <ModalCloseButton />
          <ModalBody pb={6}>
            {selectedRow && (
              <VStack align="stretch" spacing={4}>
                <HStack justify="space-between">
                  <Text fontSize="lg" fontWeight="bold">
                    {selectedRow.geo} / {selectedRow.login} / {selectedRow.method}
                  </Text>
                  <IconButton
                    size="sm"
                    icon={<FaCopy />}
                    onClick={() => {
                      navigator.clipboard.writeText(JSON.stringify(selectedRow, null, 2));
                      alert("JSON copied to clipboard!");
                    }}
                    aria-label="Copy JSON"
                  />
                </HStack>
                <Tabs>
                  <TabList>
                    <Tab>JSON</Tab>
                    <Tab>Checks</Tab>
                  </TabList>
                  <TabPanels>
                    <TabPanel>
                      <Code
                        display="block"
                        whiteSpace="pre-wrap"
                        p={3}
                        bg="gray.50"
                        border="1px solid"
                        borderColor="gray.200"
                        rounded="md"
                        fontSize="xs"
                        maxH="400px"
                        overflowY="auto"
                      >
                        {JSON.stringify(selectedRow, null, 2)}
                      </Code>
                    </TabPanel>
                    <TabPanel>
                      {selectedRow?.checks?.length ? selectedRow.checks.map((c,i)=>(
                        <HStack key={i} spacing={2} mb={1}>
                          <Badge colorScheme={c.pass ? 'green' : 'red'}>{c.name}</Badge>
                          <Text fontSize="sm" color="gray.600">{c.details}</Text>
                        </HStack>
                      )) : <Text fontSize="sm" color="gray.500">Нет checks</Text>}
                    </TabPanel>
                  </TabPanels>
                </Tabs>
              </VStack>
            )}
          </ModalBody>
        </ModalContent>
      </Modal>
    </Box>
  );
}
