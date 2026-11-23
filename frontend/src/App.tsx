import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { MainLayout } from './layouts/MainLayout';
import { OverviewPage } from './pages/OverviewPage';
import { SalesPage } from './pages/SalesPage';
import { ProductIntelligencePage } from './pages/ProductIntelligencePage';
import { CustomerInsightsPage } from './pages/CustomerInsightsPage';
import { DemandForecastingPage } from './pages/DemandForecastingPage';
import { InventoryPage } from './pages/InventoryPage';
import { PipelinePage } from './pages/PipelinePage';
import { DataQualityPage } from './pages/DataQualityPage';
import { SettingsPage } from './pages/SettingsPage';

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<MainLayout />}>
          <Route index element={<OverviewPage />} />
          <Route path="sales" element={<SalesPage />} />
          <Route path="products" element={<ProductIntelligencePage />} />
          <Route path="customers" element={<CustomerInsightsPage />} />
          <Route path="forecast" element={<DemandForecastingPage />} />
          <Route path="inventory" element={<InventoryPage />} />
          <Route path="pipeline" element={<PipelinePage />} />
          <Route path="quality" element={<DataQualityPage />} />
          <Route path="settings" element={<SettingsPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
};

export default App;
