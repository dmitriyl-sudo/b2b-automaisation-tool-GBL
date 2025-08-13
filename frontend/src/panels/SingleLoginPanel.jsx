import { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import {
  Box, Heading, Text, FormControl, FormLabel, Select, Checkbox,
  Button, Table, Thead, Tbody, Tr, Th, Td, useToast, Stack, Center, SimpleGrid, Spinner
} from '@chakra-ui/react';

export default function SingleLoginPanel() {
  const [projects, setProjects] = useState([]);
  const [geoGroups, setGeoGroups] = useState({});
  const [form, setForm] = useState({ project: '', login: '', geo: '', env: 'stage' });
  const [logins, setLogins] = useState([]);
  const [methodsData, setMethodsData] = useState(null);
  const [filterRecommended, setFilterRecommended] = useState(false);
  const [loading, setLoading] = useState(false);
  const [statusMessage, setStatusMessage] = useState("");
  const toast = useToast();
  const projectRef = useRef(null);

  useEffect(() => {
    axios.get('/list-projects').then(res => setProjects(res.data));
    axios.get('/geo-groups').then(res => setGeoGroups(res.data));
    setTimeout(() => projectRef.current?.focus(), 300);
  }, []);

  useEffect(() => {
    if (form.geo && geoGroups[form.geo]) {
      setLogins(geoGroups[form.geo]);
    }
  }, [form.geo, geoGroups]);

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const handleFetch = async () => {
    setLoading(true);
    setStatusMessage('⏳ Загрузка методов...');
    try {
      const res = await axios.post('/get-methods-only', form);
      setMethodsData(res.data);
      setStatusMessage('✅ Методы загружены');
    } catch (err) {
      toast({ title: 'Ошибка', description: 'Ошибка загрузки методов', status: 'error', duration: 3000 });
      setStatusMessage('❌ Ошибка при загрузке');
    } finally {
      setLoading(false);
    }
  };

  const renderTable = () => {
    if (!methodsData) return null;

    const { deposit_methods, withdraw_methods, recommended_methods } = methodsData;
    const all = [...deposit_methods, ...withdraw_methods];
    const recommendedSet = new Set(recommended_methods.map(([t, n]) => `${t}|||${n}`));

    const filtered = filterRecommended
      ? all.filter(([title, name]) => recommendedSet.has(`${title}|||${name}`))
      : all;

    const grouped = new Map();
    filtered.forEach(([title, name]) => {
      if (!grouped.has(title)) grouped.set(title, []);
      grouped.get(title).push(name);
    });

    return (
      <Box overflowX="auto" mt={4}>
        <Table size="sm" variant="simple">
          <Thead bg="gray.100">
            <Tr>
              <Th>Title</Th>
              <Th>Names</Th>
              <Th>Recommended</Th>
            </Tr>
          </Thead>
          <Tbody>
            {Array.from(grouped.entries()).map(([title, names]) => {
              const isRec = names.some(name => recommendedSet.has(`${title}|||${name}`));
              return (
                <Tr key={title} bg={isRec ? 'green.50' : undefined} fontWeight={isRec ? 'semibold' : 'normal'}>
                  <Td whiteSpace="nowrap">{title}</Td>
                  <Td whiteSpace="pre-wrap" fontFamily="mono" fontSize="xs">{names.join('\n')}</Td>
                  <Td textAlign="center">{isRec ? '⭐' : ''}</Td>
                </Tr>
              );
            })}
          </Tbody>
        </Table>
      </Box>
    );
  };

  return (
    <Center>
      <Box bg="white" boxShadow="xl" borderRadius="2xl" p={6} w="full" maxW="4xl" fontFamily="Inter, sans-serif">
        <Heading size="lg" borderBottom="1px" pb={2} mb={4}>📥 Методы (Single Login)</Heading>

        <Stack spacing={5}>
          <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4}>
            <FormControl>
              <FormLabel>Project</FormLabel>
              <Select ref={projectRef} placeholder="Выберите проект" name="project" value={form.project} onChange={handleChange} textAlign="center">
                {projects.map(p => <option key={p.name} value={p.name}>{p.name}</option>)}
              </Select>
            </FormControl>
            <FormControl>
              <FormLabel>GEO</FormLabel>
              <Select placeholder="Выберите GEO" name="geo" value={form.geo} onChange={handleChange} textAlign="center">
                {Object.keys(geoGroups).map(g => <option key={g} value={g}>{g}</option>)}
              </Select>
            </FormControl>
            <FormControl>
              <FormLabel>Login</FormLabel>
              <Select placeholder="Выберите логин" name="login" value={form.login} onChange={handleChange} textAlign="center">
                {logins.map(l => <option key={l} value={l}>{l}</option>)}
              </Select>
            </FormControl>
            <FormControl>
              <FormLabel>Environment</FormLabel>
              <Select name="env" value={form.env} onChange={handleChange} textAlign="center">
                <option value="stage">stage</option>
                <option value="prod">prod</option>
              </Select>
            </FormControl>
          </SimpleGrid>

          <Box display="flex" gap={4} alignItems="center">
            <Button onClick={handleFetch} colorScheme="green" shadow="md" isLoading={loading}>
              Get Methods (Single Login)
            </Button>
            <Checkbox isChecked={filterRecommended} onChange={() => setFilterRecommended(!filterRecommended)}>
              Только рекомендованные
            </Checkbox>
          </Box>

          {statusMessage && (
            <Text fontSize="sm" color="gray.600">{statusMessage}</Text>
          )}

          {renderTable()}
        </Stack>
      </Box>
    </Center>
  );
}
