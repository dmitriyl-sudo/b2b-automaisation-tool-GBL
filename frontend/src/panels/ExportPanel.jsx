import { useEffect, useState } from 'react';
import axios from 'axios';

export default function ExportPanel() {
  const [projects, setProjects] = useState([]);
  const [geoGroups, setGeoGroups] = useState({});
  const [project, setProject] = useState('');
  const [geo, setGeo] = useState('');
  const [env, setEnv] = useState('stage');
  const [status, setStatus] = useState('');

  useEffect(() => {
    axios.get('/list-projects').then(res => setProjects(res.data));
    axios.get('/geo-groups').then(res => setGeoGroups(res.data));
  }, []);

  const handleExport = async () => {
    const firstLogin = (geoGroups[geo] || [])[0];
    if (!project || !geo || !env || !firstLogin) {
      setStatus("❗ Укажите все поля и выберите GEO с логинами");
      return;
    }

    setStatus("🔄 Экспорт...");
    try {
      const res = await axios.post('/export-to-sheets', {
        project,
        geo,
        env,
        login: firstLogin
      });

      if (res.data?.sheet_url) {
        setStatus("✅ Успешно. Открываем файл...");
        window.open(res.data.sheet_url, '_blank');
      } else {
        setStatus("⚠️ Ответ без ссылки на файл");
      }
    } catch (err) {
      setStatus("❌ Ошибка: " + (err?.response?.data?.detail || err.message));
    }
  };

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-bold">📤 Экспорт в Google Sheets</h2>

      <div className="grid grid-cols-2 gap-4 max-w-2xl">
        <select value={project} onChange={(e) => setProject(e.target.value)} className="border p-2">
          <option value="">-- select project --</option>
          {projects.map(p => <option key={p.name} value={p.name}>{p.name}</option>)}
        </select>

        <select value={geo} onChange={(e) => setGeo(e.target.value)} className="border p-2">
          <option value="">-- select geo --</option>
          {Object.keys(geoGroups).map(g => <option key={g} value={g}>{g}</option>)}
        </select>

        <select value={env} onChange={(e) => setEnv(e.target.value)} className="border p-2 col-span-2">
          <option value="stage">stage</option>
          <option value="prod">prod</option>
        </select>
      </div>

      <button onClick={handleExport} className="bg-yellow-500 text-white px-4 py-2 rounded">
        Export
      </button>

      {status && (
        <div className="text-sm text-gray-700">{status}</div>
      )}
    </div>
  );
}
