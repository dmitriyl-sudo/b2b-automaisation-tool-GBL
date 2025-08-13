import { useState } from 'react';
import {
  Box, Heading, Text, FormControl, FormLabel, Select, Button,
  Table, Thead, Tbody, Tr, Th, Td, Stack, Center, HStack
} from '@chakra-ui/react';
import * as XLSX from "xlsx";

export default function GeoMethodsPanel({
  methodsOnly,
  groupedIds,
  conditionsMap,
  recommendedPairs,
  originalOrder,
  hidePaymentName,
  isFullProject,
  geo,
  currency,
  project,
  env
}) {
  // Log to check the props when the component renders
  console.log("GeoMethodsPanel props:", { project, env });

  const [filter, setFilter] = useState('all');
  // Состояние для отслеживания процесса экспорта
  const [isExporting, setIsExporting] = useState(false);

  const normalize = (text) => (text || '').trim().toLowerCase();

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
  [...(methodsOnly?.deposit_methods || []), ...(methodsOnly?.withdraw_methods || [])].forEach(([title, name]) => {
    if (!groupedMap.has(title)) {
      groupedMap.set(title, {
        title,
        names: new Set(),
        conditions: new Set(),
        isRecommended: false,
        hasDeposit: false,
        hasWithdraw: false
      });
    }
    const group = groupedMap.get(title);
    group.names.add(name);

    const tags = extractTag(name);
    tags.forEach(tag => group.conditions.add(tag));

    const isInDeposit = methodsOnly?.deposit_methods?.some(
      ([t, n]) => normalize(t) === normalize(title) && normalize(n) === normalize(name)
    );
    const isInWithdraw = methodsOnly?.withdraw_methods?.some(
      ([t, n]) => normalize(t) === normalize(title) && normalize(n) === normalize(name)
    );

    if (isInDeposit) group.hasDeposit = true;
    if (isInWithdraw) group.hasWithdraw = true;

    const recommended = recommendedPairs?.some(([recTitle, recName]) =>
      normalize(recTitle) === normalize(title) && normalize(recName) === normalize(name));
    if (recommended) group.isRecommended = true;
  });

  const filteredGroups = originalOrder
    .map(title => groupedMap.get(title))
    .filter(Boolean)
    .filter(group => {
      if (filter === 'all') return true;
      if (filter === 'recommended') return group.isRecommended;
      return Array.from(group.conditions).some(tag => tag.includes(filter));
    });

  // Original handler for exporting only the current GEO's data to Google Sheets
  const handleExportToGoogleSheets = async () => {
    if (!filteredGroups || filteredGroups.length === 0) {
      console.log("No data to export.");
      return;
    }
    setIsExporting(true);
    const sortedGroups = [...filteredGroups].sort((a, b) => {
      if (a.isRecommended !== b.isRecommended) return a.isRecommended ? -1 : 1;
      return originalOrder.indexOf(a.title) - originalOrder.indexOf(b.title);
    });

    const exportData = sortedGroups.map(row => ({
      Paymethod: row.title,
      Recommended: row.isRecommended ? '⭐\u200B' : '',
      "Payment Name": Array.from(row.names).join('\n'),
      Currency: currency || '-',
      Deposit: row.hasDeposit ? "YES" : "NO",
      Withdraw: row.hasWithdraw ? "YES" : "NO",
      Status: (env === "prod" ? "PROD" : "STAGE"),
      Details: conditionsMap?.[row.title] || (row.conditions.size > 0 ? Array.from(row.conditions).sort().join('\n') : "ALL"),
      RecommendedSort: row.isRecommended ? 1 : 0 // Added RecommendedSort
    }));

    const payload = {
      data: exportData,
      originalOrder: originalOrder || []
    };

    try {
      const res = await fetch('/export-table-to-sheets', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const json = await res.json();
      if (json.success) {
        window.open(json.sheet_url, '_blank');
      } else {
        console.error("Export error: " + json.detail);
        // Add user notification here
      }
    } catch (err) {
      console.error("Error exporting to Google Sheets:", err);
    } finally {
      setIsExporting(false);
    }
  };

  // Final handleExportAllGeosToSheetsIfNeeded (Google Sheets export, from frontend)
  const handleExportAllGeosToSheetsIfNeeded = async () => {
    // Fallback to original single-GEO export if not in Full Project Mode or global data is missing
    if (!isFullProject || !window.__ALL_GEO_DATA__) {
      console.log("Not in full project mode or __ALL_GEO_DATA__ not found. Exporting current GEO only.");
      return handleExportToGoogleSheets(); // Call the original export function
    }

    setIsExporting(true); // Set exporting state to true

    // Prepare data for all GEOs, mapping each GEO to a separate sheet
    const allGeoSheets = Object.entries(window.__ALL_GEO_DATA__).map(([geoKey, data]) => {
      const normalizeLocal = (t) => (t || '').trim().toLowerCase();
      const extractTagLocal = (name) => {
        const dep = name.match(/(\d+)DEP/i)?.[1];
        const isAff = /aff/i.test(name);
        const isMob = /mob/i.test(name);
        const tags = [];
        if (dep) tags.push(`${dep}DEP`);
        if (isAff) tags.push('AFF');
        if (isMob) tags.push('MOB');
        return tags;
      };

      const groupedMapLocal = new Map();
      [...(data.methodsOnly.deposit_methods || []), ...(data.methodsOnly.withdraw_methods || [])].forEach(([title, name]) => {
        if (!groupedMapLocal.has(title)) {
          groupedMapLocal.set(title, {
            title,
            names: new Set(),
            conditions: new Set(),
            isRecommended: false,
            hasDeposit: false,
            hasWithdraw: false
          });
        }
        const group = groupedMapLocal.get(title);
        group.names.add(name);

        const tags = extractTagLocal(name);
        tags.forEach(tag => group.conditions.add(tag));

        const isDep = data.methodsOnly.deposit_methods.some(([t, n]) => normalizeLocal(t) === normalizeLocal(title) && normalizeLocal(n) === normalizeLocal(name));
        const isWdr = data.methodsOnly.withdraw_methods.some(([t, n]) => normalizeLocal(t) === normalizeLocal(title) && normalizeLocal(n) === normalizeLocal(name));
        if (isDep) group.hasDeposit = true;
        if (isWdr) group.hasWithdraw = true;

        const isRec = data.recommendedPairs.some(([t, n]) => normalizeLocal(t) === normalizeLocal(title) && normalizeLocal(n) === normalizeLocal(name));
        if (isRec) group.isRecommended = true;
      });

      const rows = data.originalOrder.map(title => {
        const row = groupedMapLocal.get(title);
        if (!row) return null;
        return {
          Paymethod: row.isRecommended ? `${row.title}*` : row.title,
          "Payment Name": Array.from(row.names).join('\n'),
          Currency: data.currency || '-',
          Deposit: row.hasDeposit ? "YES" : "NO",
          Withdraw: row.hasWithdraw ? "YES" : "NO",
          Status: env === 'prod' ? 'PROD' : 'STAGE', // Use the component's env prop
          Details: data.conditionsMap?.[title] || (row.conditions.size > 0 ? Array.from(row.conditions).sort().join('\n') : "ALL"),
          RecommendedSort: row.isRecommended ? 1 : 0 // Added RecommendedSort
        };
      }).filter(Boolean);

      return {
        geo: geoKey,
        rows
      };
    });

    try {
      // Send the prepared payload to the new /export-multi-sheet endpoint
      const res = await fetch('/export-multi-sheet', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          project, // Use the component's project prop
          env,     // Use the component's env prop
          sheets: allGeoSheets
        })
      });

      const json = await res.json();
      if (json.success && json.sheet_url) {
        window.open(json.sheet_url, '_blank');
      } else {
        console.error("Export error:", json.message || json.detail);
        // Add user notification here
      }
    } catch (err) {
      console.error("❌ Error during export:", err);
    } finally {
      setIsExporting(false); // Reset exporting state
    }
  };

  const handleExportFrontendGeo = () => {
    if (!filteredGroups || filteredGroups.length === 0) {
      console.log("No data to export.");
      return;
    }

    const sortedGroups = [...filteredGroups].sort((a, b) => {
      if (a.isRecommended !== b.isRecommended) return a.isRecommended ? -1 : 1;
      return originalOrder.indexOf(a.title) - originalOrder.indexOf(b.title);
    });

    const exportData = sortedGroups.map(row => ({
      Paymethod: row.title,
      Recommended: row.isRecommended ? '⭐\u200B' : '',
      "Payment Name": Array.from(row.names).join('\n'),
      Currency: currency || '-',
      Deposit: row.hasDeposit ? "YES" : "NO",
      Withdraw: row.hasWithdraw ? "YES" : "NO",
      Status: (env === "prod" ? "PROD" : "STAGE"),
      Details: conditionsMap?.[row.title] || (row.conditions.size > 0 ? Array.from(row.conditions).sort().join('\n') : "ALL"),
      RecommendedSort: row.isRecommended ? 1 : 0 // Added RecommendedSort
    }));

    const worksheet = XLSX.utils.json_to_sheet(exportData);
    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, worksheet, "GEO Methods");
    XLSX.writeFile(workbook, `GeoMethods_${project || 'unknown'}_${geo || 'unknown'}_${env || 'stage'}.xlsx`);
  };

  // New function to handle full project export from frontend data
  const handleExportFullProjectFromFrontend = async () => {
    if (!isFullProject || !window.__ALL_GEO_DATA__) {
      console.warn("⛔ Full project mode not active or data not loaded");
      return;
    }

    setIsExporting(true);

    const sheets = Object.entries(window.__ALL_GEO_DATA__).map(([geoKey, data]) => {
      // Replicate the groupedMap creation logic for each GEO's data
      const groupedMapLocal = new Map();
      [...(data.methodsOnly?.deposit_methods || []), ...(data.methodsOnly?.withdraw_methods || [])].forEach(([title, name]) => {
        if (!groupedMapLocal.has(title)) {
          groupedMapLocal.set(title, {
            title,
            names: new Set(),
            conditions: new Set(),
            isRecommended: false,
            hasDeposit: false,
            hasWithdraw: false
          });
        }
        const group = groupedMapLocal.get(title);
        group.names.add(name);

        const tags = extractTag(name); // Use the shared extractTag
        tags.forEach(tag => group.conditions.add(tag));

        const isInDeposit = data.methodsOnly?.deposit_methods?.some(
          ([t, n]) => normalize(t) === normalize(title) && normalize(n) === normalize(name) // Use shared normalize
        );
        const isInWithdraw = data.methodsOnly?.withdraw_methods?.some(
          ([t, n]) => normalize(t) === normalize(title) && normalize(n) === normalize(name) // Use shared normalize
        );

        if (isInDeposit) group.hasDeposit = true;
        if (isInWithdraw) group.hasWithdraw = true;

        const recommended = data.recommendedPairs?.some(([recTitle, recName]) =>
          normalize(recTitle) === normalize(title) && normalize(recName) === normalize(name)); // Use shared normalize
        if (recommended) group.isRecommended = true;
      });

      // Generate rows using the local groupedMap
      const rows = data.originalOrder
        .map(title => groupedMapLocal.get(title))
        .filter(Boolean) // Filter out any titles not found in groupedMapLocal
        .map(row => ({
          Paymethod: row.isRecommended ? `${row.title}*` : row.title,
          "Payment Name": Array.from(row.names).join('\n'),
          Currency: data.currency || '-',
          Deposit: row.hasDeposit ? "YES" : "NO",
          Withdraw: row.hasWithdraw ? "YES" : "NO",
          Status: env === "prod" ? "PROD" : "STAGE", // Use the component's env prop
          Details: data.conditionsMap?.[row.title] || (row.conditions.size > 0 ? Array.from(row.conditions).sort().join('\n') : "ALL"),
          RecommendedSort: row.isRecommended ? 1 : 0 // Added RecommendedSort
        }));

      return {
        geo: geoKey,
        rows
      };
    });

    try {
      const res = await fetch('/export-table-to-sheets-multi', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sheets })
      });

      const json = await res.json();
      if (json.success && json.sheet_url) {
        window.open(json.sheet_url, '_blank');
      } else {
        console.error("❌ Ошибка экспорта:", json.detail || json.message);
      }
    } catch (err) {
      console.error("❌ Ошибка отправки:", err);
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
          
          {/* Блок с кнопками экспорта */}
          <HStack spacing={4}>
            <Button 
              variant="outline" 
              colorScheme="blue" 
              onClick={handleExportFrontendGeo}
              isLoading={isExporting}
              >
              📥 Export (Frontend)
            </Button>
            {/* Modified button: now purple and calls the new smart export function */}
            <Button 
              variant="outline" 
              colorScheme="purple" 
              onClick={handleExportAllGeosToSheetsIfNeeded}
              isLoading={isExporting}
              >
              📤 Export to Google Sheets
            </Button>
            {/* The original "Export Full Project" button remains, now calling the new frontend-based export */}
            {isFullProject && (
              <Button 
                variant="solid" 
                colorScheme="purple" 
                onClick={handleExportFullProjectFromFrontend} // Changed onClick here
                isLoading={isExporting}
                >
                📦 Export Full Project (Google Sheets)
              </Button>
            )}
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
                  <Th textAlign="center">Env</Th>
                </Tr>
              </Thead>
              <Tbody>
                {filteredGroups.map(({ title, names, conditions, isRecommended, hasDeposit, hasWithdraw }) => (
                  <Tr key={title} bg={isRecommended ? 'green.50' : undefined} fontWeight={isRecommended ? 'semibold' : 'normal'}>
                    <Td whiteSpace="nowrap">{title}</Td>
                    <Td textAlign="center">{isRecommended ? '⭐' : ''}</Td>
                    <Td textAlign="center">{hasDeposit ? 'YES' : 'NO'}</Td>
                    <Td textAlign="center">{hasWithdraw ? 'YES' : 'NO'}</Td>
                    {!hidePaymentName && (
                      <Td whiteSpace="pre-wrap" fontSize="xs" fontFamily="mono">
                        {groupedIds?.[title] || Array.from(names).join('\n')}
                      </Td>
                    )}
                    <Td whiteSpace="pre-wrap" fontSize="xs" fontFamily="mono">
                      {conditionsMap?.[title] || (conditions.size > 0 ? Array.from(conditions).sort().join('\n') : 'ALL')}
                    </Td>
                    <Td textAlign="center">{env?.toUpperCase()}</Td>
                  </Tr>
                ))}
              </Tbody>
            </Table>
          </Box>
        </Stack>
      </Box>
    </Center>
  );
}
