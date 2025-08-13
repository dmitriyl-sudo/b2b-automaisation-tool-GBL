import React, { useState, useEffect } from "react";
import axios from "axios";
import {
  Box, Button, Heading, VStack, HStack, Select, Text, Table, Thead, Tbody, Tr, Th, Td, Spinner, Link, Tooltip, Radio, RadioGroup
} from "@chakra-ui/react";

export default function MethodTestPanel() {
  const [projects, setProjects] = useState([]);
  const [selectedProject, setSelectedProject] = useState("");
  const [geoList, setGeoList] = useState([]);
  const [selectedGeo, setSelectedGeo] = useState("");
  const [logins, setLogins] = useState([]);
  const [selectedLogin, setSelectedLogin] = useState("");
  const [env, setEnv] = useState("stage");
  const [mode, setMode] = useState("login");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    axios.get("/list-projects").then(res => setProjects(res.data));
  }, []);

  useEffect(() => {
    if (selectedProject) {
      axios.get('/geo-groups').then(res => {
        setGeoList(Object.keys(res.data));
      });
    }
  }, [selectedProject]);

  useEffect(() => {
    if (selectedGeo) {
      axios.get('/geo-groups').then(res => {
        setLogins(res.data[selectedGeo] || []);
      });
    }
  }, [selectedGeo]);

  const runTest = async () => {
    setLoading(true);
    setResults([]);
    try {
      const payload = {
        project: selectedProject,
        geo: selectedGeo,
        login: selectedLogin,
        mode,
        env
      };
      const res = await axios.post("/test-methods", payload);
      const enriched = res.data.results.map(r => ({
        ...r,
        url: r.url || r.link || r.payment_url || null
      }));
      setResults(enriched);
    } catch (err) {
      alert("Ошибка при запуске тестов методов.");
    } finally {
      setLoading(false);
    }
  };

  const exportToSheets = async () => {
    try {
      const res = await axios.post("/export-table-to-sheets", results);
      if (res.data?.sheet_url) {
        window.open(res.data.sheet_url, "_blank");
      }
    } catch (e) {
      alert("Ошибка экспорта в Google Sheets");
    }
  };

  return (
    <Box>
      <Heading size="md" mb={4}>Проверка платёжных методов</Heading>

      <VStack align="start" spacing={4} mb={6}>
        <HStack spacing={4} wrap="wrap">
          <Select placeholder="Выберите проект" value={selectedProject} onChange={e => setSelectedProject(e.target.value)}>
            {projects.map(p => (
              <option key={p.name} value={p.name}>{p.name}</option>
            ))}
          </Select>
          <Select placeholder="Выберите GEO" value={selectedGeo} onChange={e => setSelectedGeo(e.target.value)} isDisabled={mode === "project"}>
            {geoList.map(g => (
              <option key={g} value={g}>{g}</option>
            ))}
          </Select>
          <Select placeholder="Выберите логин" value={selectedLogin} onChange={e => setSelectedLogin(e.target.value)} isDisabled={mode !== "login"}>
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

        <HStack spacing={4}>
          <Button onClick={runTest} colorScheme="blue" isLoading={loading}>Запустить проверку</Button>
          {results.length > 0 && <Button onClick={exportToSheets} colorScheme="green">Экспорт в Sheets</Button>}
        </HStack>
      </VStack>

      {results.length > 0 && (
        <Box>
          <Heading size="sm" mb={2}>Результаты</Heading>
          <Text fontSize="sm" mb={2}>
            ✅ {results.filter(r => r.status === 'OK').length} / {results.length}
          </Text>
          <Table size="sm" variant="striped" colorScheme="gray">
            <Thead>
              <Tr>
                <Th>GEO</Th>
                <Th>Логин</Th>
                <Th>Метод</Th>
                <Th>Статус</Th>
                <Th>Код</Th>
                <Th>Сообщение</Th>
                <Th>Время</Th>
                <Th>Ссылка</Th>
              </Tr>
            </Thead>
            <Tbody>
              {results.map((r, i) => (
                <Tr key={i} bg={r.status !== "OK" ? "red.50" : undefined}>
                  <Td>{r.geo}</Td>
                  <Td>{r.login}</Td>
                  <Td>{r.method}</Td>
                  <Td>{r.status === "OK" ? "✅" : "❌"}</Td>
                  <Td>{r.code || "-"}</Td>
                  <Td maxW="300px" isTruncated>
                    <Tooltip label={r.message} hasArrow>{r.message || "-"}</Tooltip>
                  </Td>
                  <Td>{r.duration ? `${r.duration}s` : "-"}</Td>
                  <Td>{r.url ? <Link href={r.url} isExternal color="blue.500">Открыть</Link> : "-"}</Td>
                </Tr>
              ))}
            </Tbody>
          </Table>
        </Box>
      )}

      {loading && <Spinner mt={4} />} 
    </Box>
  );
}
