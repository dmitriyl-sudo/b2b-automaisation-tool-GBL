import { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import {
  Box, Heading, Text, FormControl, FormLabel, Select, Checkbox,
  Button, Table, Thead, Tbody, Tr, Th, Td, useToast, Icon, Stack, Alert, AlertIcon, Center, SimpleGrid
} from '@chakra-ui/react';
import { MdCheckCircle, MdWarning } from 'react-icons/md';

export default function AuthCheckPanel() {
  const [form, setForm] = useState({ project: '', login: '', geo: '', env: 'stage' });
  const [projects, setProjects] = useState([]);
  const [geoGroups, setGeoGroups] = useState({});
  const [logins, setLogins] = useState([]);
  const [result, setResult] = useState(null);
  const [multiResults, setMultiResults] = useState([]);
  const [checkAllGeo, setCheckAllGeo] = useState(false);
  const [checkAllProject, setCheckAllProject] = useState(false);
  const [progressMessage, setProgressMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const toast = useToast();
  const projectRef = useRef(null);

  useEffect(() => {
    axios.get('/list-projects').then(res => setProjects(res.data));
    axios.get('/geo-groups').then(res => {
      setGeoGroups(res.data);
      if (form.geo && res.data[form.geo]) {
        setLogins(res.data[form.geo]);
      }
    });
    setTimeout(() => projectRef.current?.focus(), 300);
  }, []);

  const { geo } = form;
  useEffect(() => {
    if (geo && geoGroups[geo]) {
      setLogins(geoGroups[geo]);
    }
  }, [geo, geoGroups]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm(prev => ({ ...prev, [name]: value }));
  };

  const validateSingle = () => {
    const validProjects = projects.map(p => p.name);
    if (!validProjects.includes(form.project)) {
      toast({ title: 'Ошибка', description: '❗ Выберите существующий Project', status: 'error', duration: 3000 });
      return false;
    }
    if (!geoGroups[form.geo]) {
      toast({ title: 'Ошибка', description: '❗ GEO должен быть из списка', status: 'error', duration: 3000 });
      return false;
    }
    if (!logins.includes(form.login)) {
      toast({ title: 'Ошибка', description: '❗ Login не найден в выбранном GEO', status: 'error', duration: 3000 });
      return false;
    }
    return true;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setResult(null);
    setMultiResults([]);
    setProgressMessage("");
    setLoading(true);

    if (!form.project || !form.env) {
      toast({ title: 'Ошибка', description: '❗ Укажи project и environment', status: 'error', duration: 3000 });
      setLoading(false);
      return;
    }

    if (checkAllProject) {
      const geoList = Object.keys(geoGroups).filter(geo => (geoGroups[geo] || []).length > 0);
      let allResults = [];

      for (let i = 0; i < geoList.length; i++) {
        const geo = geoList[i];
        setProgressMessage(`🔄 Обработка GEO: ${geo} (${i + 1}/${geoList.length})...`);

        try {
          const res = await axios.post('/run-multi-auth-check', { ...form, geo, mode: "geo" });
          if (res.data?.results?.length) {
            allResults = allResults.concat(res.data.results.map(r => ({ ...r, geo, project: form.project })));
          }
        } catch {
          allResults.push({ login: `❌ Ошибка GEO: ${geo}`, success: false, geo, project: form.project });
        }
      }

      setMultiResults(allResults);
      setProgressMessage("✅ Завершено");
      setLoading(false);
      return;
    }

    if (checkAllGeo) {
      if (!form.geo || !geoGroups[form.geo]) {
        toast({ title: 'Ошибка', description: '❗ Выбери валидный GEO', status: 'error', duration: 3000 });
        setLoading(false);
        return;
      }

      setProgressMessage(`🔄 Обработка GEO: ${form.geo}...`);

      try {
        const res = await axios.post('/run-multi-auth-check', { ...form, mode: "geo" });
        setMultiResults((res.data.results || []).map(r => ({ ...r, geo: form.geo, project: form.project })));
        setProgressMessage("✅ Завершено");
      } catch {
        toast({ title: 'Ошибка', description: 'Ошибка при проверке GEO', status: 'error', duration: 3000 });
      }
      setLoading(false);
      return;
    }

    if (!validateSingle()) {
      setLoading(false);
      return;
    }

    try {
      const res = await axios.post('/run-login-check', form);
      setResult(res.data);
    } catch (err) {
      setResult({ success: false, error: err.message });
    }
    setLoading(false);
  };

  return (
    <Center>
      <Box bg="white" boxShadow="xl" borderRadius="2xl" p={6} w="full" maxW="4xl" fontFamily="Inter, sans-serif">
        <Heading size="lg" borderBottom="1px" pb={2} mb={4}>🔐 Проверка логинов (Auth)</Heading>

        <Box as="form" onSubmit={handleSubmit} bg="gray.50" borderRadius="xl" px={6} py={5}>
          <Stack spacing={5}>
            <SimpleGrid columns={{ base: 1, md: 3 }} spacing={4}>
              <Box w="100%">
                <FormControl>
                  <FormLabel>Project</FormLabel>
                  <Select ref={projectRef} placeholder="Выберите проект" name="project" value={form.project} onChange={handleChange} textAlign="center">
                    {projects.map(p => <option key={p.name} value={p.name}>{p.name}</option>)}
                  </Select>
                </FormControl>
              </Box>
              <Box w="100%">
                <FormControl>
                  <FormLabel>GEO</FormLabel>
                  <Select placeholder="Выберите GEO" name="geo" value={form.geo} onChange={handleChange} textAlign="center">
                    {Object.keys(geoGroups).map(g => <option key={g} value={g}>{g}</option>)}
                  </Select>
                </FormControl>
              </Box>
              <Box w="100%">
                <FormControl>
                  <FormLabel>Login</FormLabel>
                  <Select placeholder="Выберите логин" name="login" value={form.login} onChange={handleChange} textAlign="center">
                    {logins.map(l => <option key={l} value={l}>{l}</option>)}
                  </Select>
                </FormControl>
              </Box>
            </SimpleGrid>

            <FormControl maxW="sm">
              <FormLabel>Environment</FormLabel>
              <Select name="env" value={form.env} onChange={handleChange} textAlign="center">
                <option value="stage">stage</option>
                <option value="prod">prod</option>
              </Select>
            </FormControl>

            <Checkbox isChecked={checkAllGeo} onChange={() => { setCheckAllGeo(!checkAllGeo); setCheckAllProject(false); }}>
              Проверить все логины в выбранном GEO
            </Checkbox>
            <Checkbox isChecked={checkAllProject} onChange={() => { setCheckAllProject(!checkAllProject); setCheckAllGeo(false); }}>
              Проверить все логины во всём проекте
            </Checkbox>

            <Button type="submit" isLoading={loading} isDisabled={loading} colorScheme="blue" alignSelf="start">
              Проверить авторизацию
            </Button>
          </Stack>
        </Box>

        {progressMessage && <Text fontSize="sm" color="gray.700" mt={4}>{progressMessage}</Text>}

        {result && (
          <Box mt={4}>
            {result.success ? (
              <Alert status="success" rounded="md">
                <AlertIcon />
                Авторизация успешна — 💱 {result.currency}, 💰 {result.deposit_count}
              </Alert>
            ) : (
              <Alert status="error" rounded="md">
                <AlertIcon /> {result.error}
              </Alert>
            )}
          </Box>
        )}

        {multiResults.length > 0 && (
          <Box mt={6} overflowX="auto">
            <Heading size="md" mb={2}>Результаты по {multiResults.length} логинам</Heading>
            <Table size="sm" variant="simple" boxShadow="md">
              <Thead bg="gray.100">
                <Tr>
                  <Th>Login</Th>
                  <Th>✅ Auth</Th>
                  <Th>Currency</Th>
                  <Th>Deposit Count</Th>
                  <Th>Project</Th>
                  <Th>GEO</Th>
                </Tr>
              </Thead>
              <Tbody>
                {multiResults.map(r => (
                  <Tr key={r.login + r.geo} bg={r.success ? 'green.100' : 'red.100'}>
                    <Td fontFamily="mono" maxW="250px" isTruncated>{r.login}</Td>
                    <Td textAlign="center">
                      <Icon as={r.success ? MdCheckCircle : MdWarning} color={r.success ? 'green.500' : 'red.500'} boxSize={5} />
                    </Td>
                    <Td>{r.currency || '-'}</Td>
                    <Td textAlign="center">{r.deposit_count ?? '-'}</Td>
                    <Td>{r.project}</Td>
                    <Td>{r.geo}</Td>
                  </Tr>
                ))}
              </Tbody>
            </Table>
          </Box>
        )}
      </Box>
    </Center>
  );
}
