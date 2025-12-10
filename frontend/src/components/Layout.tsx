import React, { useEffect, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { 
  BuildingOffice2Icon, 
  Bars3Icon, 
  XMarkIcon,
  ChartBarIcon,
  DocumentTextIcon,
  CheckCircleIcon,
  ChevronDownIcon
} from '@heroicons/react/24/outline';
import { useQuery } from 'react-query';
import { useEntity } from '../contexts/EntityContext';
import { ENTITY_LIST } from '../config/entities';
import { apiService } from '../services/api';
import PeriodSelector from './PeriodSelector';

interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const location = useLocation();
  const { selectedEntity, setSelectedEntity } = useEntity();

  // Fetch entities from API (backend is source of truth)
  const { data: apiEntities } = useQuery(
    'entities',
    async () => {
      const response = await apiService.getEntities();
      return response.data;
    },
    {
      staleTime: 5 * 60 * 1000, // Cache for 5 minutes
      // Fallback to hardcoded entities if API fails
      placeholderData: ENTITY_LIST.map(e => ({
        code: e.code,
        name: e.name,
        short_code: e.code
      })),
    }
  );

  // Use API entities if available, otherwise fallback to hardcoded
  const entities = (apiEntities && Array.isArray(apiEntities))
    ? apiEntities.map((e: any) => ({ 
        code: e.short_code || e.code, 
        name: e.name 
      }))
    : ENTITY_LIST;

  // Ensure the selected entity always matches the available list so period fetches run for the right entity
  useEffect(() => {
    if (!entities || entities.length === 0) return;
    const exists = entities.some((e: any) => e.code === selectedEntity);
    if (!exists) {
      setSelectedEntity(entities[0].code);
    }
  }, [entities, selectedEntity, setSelectedEntity]);

  const navigation = [
    {
      name: 'Dashboard',
      href: '/dashboard',
      icon: ChartBarIcon,
      current: location.pathname === '/dashboard',
      section: 'Overview'
    },
    {
      name: '1: Upload Trial Balance',
      href: '/step1',
      icon: DocumentTextIcon,
      current: location.pathname === '/step1',
      section: 'PART 1: Trial Balance Preparation'
    },
    {
      name: '2: Upload Adjustments',
      href: '/step2',
      icon: DocumentTextIcon,
      current: location.pathname === '/step2',
      section: 'PART 1: Trial Balance Preparation'
    },
    {
      name: '3: Apply Adjustments',
      href: '/step3',
      icon: CheckCircleIcon,
      current: location.pathname === '/step3',
      section: 'PART 1: Trial Balance Preparation'
    },
    // {
    //   name: '4: Map Categories',
    //   href: '/step4',
    //   icon: CheckCircleIcon,
    //   current: location.pathname === '/step4',
    //   section: 'PART 1: Trial Balance Preparation'
    // },
    {
      name: '4: Category Mapping',
      href: '/step4-category-mapping',
      icon: CheckCircleIcon,
      current: location.pathname === '/step4-category-mapping',
      section: 'PART 1: Trial Balance Preparation'
    },
    // {
    //   name: '5: Validate 6 Rules',
    //   href: '/step5',
    //   icon: CheckCircleIcon,
    //   current: location.pathname === '/step5',
    //   section: 'PART 1: Trial Balance Preparation'
    // },
    {
      name: '5: Perform Validation',
      href: '/step5-updated',
      icon: CheckCircleIcon,
      current: location.pathname === '/step5-updated',
      section: 'PART 1: Trial Balance Preparation'
    },
    // {
    //   name: '6: Generate Notes',
    //   href: '/step6',
    //   icon: DocumentTextIcon,
    //   current: location.pathname === '/step6',
    //   section: 'PART 2: Financial Statement Generation'
    // },
    {
      name: '6: Generate Notes',
      href: '/step6-tabular',
      icon: DocumentTextIcon,
      current: location.pathname === '/step6-tabular',
      section: 'PART 2: Financial Statement Generation'
    },
    {
      name: '7: Generate P&L',
      href: '/step7',
      icon: ChartBarIcon,
      current: location.pathname === '/step7',
      section: 'PART 2: Financial Statement Generation'
    },
    // {
    //   name: '8: Generate BS Notes',
    //   href: '/step8',
    //   icon: DocumentTextIcon,
    //   current: location.pathname === '/step8',
    //   section: 'PART 2: Financial Statement Generation'
    // },
    {
      name: '8: Generate Balance Sheet',
      href: '/step8',
      icon: ChartBarIcon,
      current: location.pathname === '/step8',
      section: 'PART 2: Financial Statement Generation'
    },
    {
      name: '9: Generate Cash Flow',
      href: '/step9',
      icon: ChartBarIcon,
      current: location.pathname === '/step9',
      section: 'PART 2: Financial Statement Generation'
    },
    // COMMENTED OUT - FinAnalyzer Reports
    // {
    //   name: 'Generate FinAnalyzer Reports',
    //   href: '/finalyzer-reports',
    //   icon: DocumentTextIcon,
    //   current: location.pathname === '/finalyzer-reports',
    //   section: 'PART 3: Generate FinAnalyzer Reports'
    // },
    {
      name: 'View Statements',
      href: '/view-statements',
      icon: DocumentTextIcon,
      current: location.pathname.startsWith('/view-statements'),
      section: 'PART 3: View Financial Statements'
    },
    {
      name: 'Feedback & Support',
      href: '/feedback',
      icon: DocumentTextIcon,
      current: location.pathname === '/feedback',
      section: 'Support'
    },
  ];

  const groupedNavigation = navigation.reduce((acc, item) => {
    const section = item.section || 'Other';
    if (!acc[section]) {
      acc[section] = [];
    }
    acc[section].push(item);
    return acc;
  }, {} as Record<string, typeof navigation>);

  return (
    <div className="h-screen flex overflow-hidden bg-gray-100">
      {/* Mobile sidebar */}
      <div className={`fixed inset-0 flex z-40 md:hidden ${sidebarOpen ? '' : 'hidden'}`}>
        <div className="fixed inset-0 bg-gray-600 bg-opacity-75" onClick={() => setSidebarOpen(false)} />
        <div className="relative flex-1 flex flex-col max-w-xs w-full bg-white">
          <div className="absolute top-0 right-0 -mr-12 pt-2">
            <button
              type="button"
              className="ml-1 flex items-center justify-center h-10 w-10 rounded-full focus:outline-none focus:ring-2 focus:ring-inset focus:ring-white"
              onClick={() => setSidebarOpen(false)}
            >
              <XMarkIcon className="h-6 w-6 text-white" />
            </button>
          </div>
          <div className="flex-1 h-0 pt-5 pb-4 overflow-y-auto">
            <div className="flex-shrink-0 flex items-center px-4">
              <BuildingOffice2Icon className="h-8 w-8 text-primary-600" />
              <span className="ml-2 text-xl font-bold text-gray-900">Integris</span>
            </div>
            
            {/* Entity Dropdown - Mobile */}
            <div className="mt-5 px-4">
              <label htmlFor="entity-mobile" className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
                Choose Entity
              </label>
              <div className="relative">
                <select
                  id="entity-mobile"
                  value={selectedEntity}
                  onChange={(e) => setSelectedEntity(e.target.value)}
                  className="block w-full pl-3 pr-10 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent bg-white"
                >
                  {entities.map((entity) => (
                    <option key={entity.code} value={entity.code}>
                      {entity.name}
                    </option>
                  ))}
                </select>
                <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-gray-700">
                  <ChevronDownIcon className="h-4 w-4" />
                </div>
              </div>
            </div>

            <nav className="mt-5 px-2 space-y-1">
              {Object.entries(groupedNavigation).map(([section, items]) => (
                <div key={section}>
                  <div className="px-3 py-2 text-xs font-semibold text-gray-500 uppercase tracking-wider">
                    {section}
                  </div>
                  {items.map((item) => (
                    <Link
                      key={item.name}
                      to={item.href}
                      className={`${
                        item.current
                          ? 'bg-primary-100 text-primary-900'
                          : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                      } group flex items-center px-2 py-2 text-sm font-medium rounded-md`}
                    >
                      <item.icon
                        className={`${
                          item.current ? 'text-primary-500' : 'text-gray-400 group-hover:text-gray-500'
                        } mr-3 flex-shrink-0 h-6 w-6`}
                      />
                      {item.name}
                    </Link>
                  ))}
                </div>
              ))}
            </nav>
          </div>
        </div>
      </div>

      {/* Desktop sidebar */}
      <div className="hidden md:flex md:flex-shrink-0">
        <div className="flex flex-col w-64">
          <div className="flex flex-col h-0 flex-1 bg-white border-r border-gray-200">
            <div className="flex-1 flex flex-col pt-5 pb-4 overflow-y-auto">
              <div className="flex items-center flex-shrink-0 px-4">
                <BuildingOffice2Icon className="h-8 w-8 text-primary-600" />
                <span className="ml-2 text-xl font-bold text-gray-900">Integris</span>
              </div>
              
              {/* Entity Dropdown - Desktop */}
              <div className="mt-5 px-4">
                <label htmlFor="entity-desktop" className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
                  Choose Entity
                </label>
                <div className="relative">
                  <select
                    id="entity-desktop"
                    value={selectedEntity}
                    onChange={(e) => setSelectedEntity(e.target.value)}
                    className="block w-full pl-3 pr-10 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent bg-white"
                  >
                    {entities.map((entity) => (
                      <option key={entity.code} value={entity.code}>
                        {entity.name}
                      </option>
                    ))}
                  </select>
                  <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-gray-700">
                    <ChevronDownIcon className="h-4 w-4" />
                  </div>
                </div>
              </div>

<div className="mt-5">
  <PeriodSelector showInSidebar={true} />
</div>

              <nav className="mt-5 flex-1 px-2 space-y-1">
                {Object.entries(groupedNavigation).map(([section, items]) => (
                  <div key={section}>
                    <div className="px-3 py-2 text-xs font-semibold text-gray-500 uppercase tracking-wider">
                      {section}
                    </div>
                    {items.map((item) => (
                      <Link
                        key={item.name}
                        to={item.href}
                        className={`${
                          item.current
                            ? 'bg-primary-100 text-primary-900'
                            : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                        } group flex items-center px-2 py-2 text-sm font-medium rounded-md`}
                      >
                        <item.icon
                          className={`${
                            item.current ? 'text-primary-500' : 'text-gray-400 group-hover:text-gray-500'
                          } mr-3 flex-shrink-0 h-6 w-6`}
                        />
                        {item.name}
                      </Link>
                    ))}
                  </div>
                ))}
              </nav>
            </div>
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="flex flex-col w-0 flex-1 overflow-hidden">
        <div className="md:hidden pl-1 pt-1 sm:pl-3 sm:pt-3">
          <button
            type="button"
            className="-ml-0.5 -mt-0.5 h-12 w-12 inline-flex items-center justify-center rounded-md text-gray-500 hover:text-gray-900 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-primary-500"
            onClick={() => setSidebarOpen(true)}
          >
            <Bars3Icon className="h-6 w-6" />
          </button>
        </div>
        <main className="flex-1 relative overflow-y-auto focus:outline-none">
          <div className="py-6">
            <div className="mx-auto px-4 sm:px-6 md:px-8">
              {children}
            </div>
          </div>
        </main>
      </div>
    </div>
  );
};

export default Layout;
