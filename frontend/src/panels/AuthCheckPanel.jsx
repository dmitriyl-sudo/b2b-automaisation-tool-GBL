import { useState, useRef } from 'react';
import axios from 'axios';
import {
  Box, Heading, Text, FormControl, FormLabel, Select, Checkbox,
  Button, Table, Thead, Tbody, Tr, Th, Td, useToast, Icon, Stack, Alert, AlertIcon, Center, SimpleGrid
} from '@chakra-ui/react';
import { MdCheckCircle, MdWarning } from 'react-icons/md';
import { useGlobalSelection } from '../contexts/GlobalSelectionContext';

export default function AuthCheckPanel() {
  const [localLogin, setLocalLogin] = useState('');
  const [result, setResult] = useState(null);
  const [multiResults, setMultiResults] = useState([]);
  const [checkAllGeo, setCheckAllGeo] = useState(false);
  const [checkAllProject, setCheckAllProject] = useState(false);
  const [progressMessage, setProgressMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const toast = useToast();
  const projectRef = useRef(null);

  const { 
    project, geo, env, projects, geoGroups, logins,
    setProject, setGeo, setEnv, loading: contextLoading
  } = useGlobalSelection();

  const validateSingle = () => {
    const validProjects = projects.map(p => p.name);
    if (!validProjects.includes(project)) {
      toast({ title: 'Ошибка', description: '❗ Выберите существующий Project', status: 'error', duration: 3000 });
      return false;
    }
    if (!geoGroups[geo]) {
      toast({ title: 'Ошибка', description: '❗ GEO должен быть из списка', status: 'error', duration: 3000 });
      return false;
    }
    if (!logins.includes(localLogin)) {
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

    if (!project || !env) {
      toast({ title: 'Ошибка', description: '❗ Укажи project и environment', status: 'error', duration: 3000 });
      setLoading(false);
      return;
    }

    if (checkAllProject) {
      const geoList = Object.keys(geoGroups).filter(geoKey => (geoGroups[geoKey] || []).length > 0);
      let allResults = [];

      for (let i = 0; i < geoList.length; i++) {
        const currentGeo = geoList[i];
        setProgressMessage(`🔄 Обработка GEO: ${currentGeo} (${i + 1}/${geoList.length})...`);

        try {
          const res = await axios.post('/run-multi-auth-check', { project, geo: currentGeo, env, mode: "geo" });
          if (res.data?.results?.length) {
            allResults = allResults.concat(res.data.results.map(r => ({ ...r, geo: currentGeo, project })));
          }
        } catch {
          allResults.push({ login: `❌ Ошибка GEO: ${currentGeo}`, success: false, geo: currentGeo, project });
        }
      }

      setMultiResults(allResults);
      setProgressMessage("✅ Завершено");
      setLoading(false);
      return;
    }

    if (checkAllGeo) {
      if (!geo || !geoGroups[geo]) {
        toast({ title: 'Ошибка', description: '❗ Выбери валидный GEO', status: 'error', duration: 3000 });
        setLoading(false);
        return;
      }

      setProgressMessage(`🔄 Обработка GEO: ${geo}...`);

      try {
        const res = await axios.post('/run-multi-auth-check', { project, geo, env, mode: "geo" });
        setMultiResults((res.data.results || []).map(r => ({ ...r, geo, project })));
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
      const res = await axios.post('/run-login-check', { project, geo, env, login: localLogin });
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
                  <Select ref={projectRef} placeholder="Выберите проект" value={project} onChange={(e) => setProject(e.target.value)} textAlign="center">
                    {projects.map(p => <option key={p.name} value={p.name}>{p.name}</option>)}
                  </Select>
                </FormControl>
              </Box>
              <Box w="100%">
                <FormControl>
                  <FormLabel>GEO</FormLabel>
                  <Select placeholder="Выберите GEO" value={geo} onChange={(e) => setGeo(e.target.value)} textAlign="center">
                    {Object.keys(geoGroups).map(g => <option key={g} value={g}>{g}</option>)}
                  </Select>
                </FormControl>
              </Box>
              <Box w="100%">
                <FormControl>
                  <FormLabel>Login</FormLabel>
                  <Select placeholder="Выберите логин" value={localLogin} onChange={(e) => setLocalLogin(e.target.value)} textAlign="center">
                    {logins.map(l => <option key={l} value={l}>{l}</option>)}
                  </Select>
                </FormControl>
              </Box>
            </SimpleGrid>

            <FormControl maxW="sm">
              <FormLabel>Environment</FormLabel>
              <Select value={env} onChange={(e) => setEnv(e.target.value)} textAlign="center">
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
