import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';

const GlobalSelectionContext = createContext();

export const useGlobalSelection = () => {
  const context = useContext(GlobalSelectionContext);
  if (!context) {
    throw new Error('useGlobalSelection must be used within a GlobalSelectionProvider');
  }
  return context;
};

export const GlobalSelectionProvider = ({ children }) => {
  const [project, setProject] = useState('');
  const [geo, setGeo] = useState('');
  const [env, setEnv] = useState('stage');
  const [projects, setProjects] = useState([]);
  const [geoGroups, setGeoGroups] = useState({});
  const [loading, setLoading] = useState(true);

  // Загружаем проекты и GEO группы при инициализации
  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        const [projectsRes, geoGroupsRes] = await Promise.all([
          axios.get('/list-projects'),
          axios.get('/geo-groups')
        ]);
        
        setProjects(projectsRes.data);
        setGeoGroups(geoGroupsRes.data);
      } catch (error) {
        console.error('Error loading projects/geo groups:', error);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

  // Получаем логины для выбранного GEO
  const getLoginsForGeo = (selectedGeo = geo) => {
    return geoGroups[selectedGeo] || [];
  };

  // Проверяем валидность выбранного проекта
  const isValidProject = (selectedProject = project) => {
    return projects.some(p => p.name === selectedProject);
  };

  // Проверяем валидность выбранного GEO
  const isValidGeo = (selectedGeo = geo) => {
    return Object.keys(geoGroups).includes(selectedGeo);
  };

  const value = {
    // State
    project,
    geo,
    env,
    projects,
    geoGroups,
    loading,
    
    // Setters
    setProject,
    setGeo,
    setEnv,
    
    // Helpers
    getLoginsForGeo,
    isValidProject,
    isValidGeo,
    
    // Computed values
    logins: getLoginsForGeo(),
    geoOptions: Object.keys(geoGroups),
    projectOptions: projects.map(p => p.name)
  };

  return (
    <GlobalSelectionContext.Provider value={value}>
      {children}
    </GlobalSelectionContext.Provider>
  );
};
